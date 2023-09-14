## Copyright (c) 2023 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       BootFrame.py
## @brief:      Device firmware upgrade
## @date:		16.08.2023
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from gui.GuiCommon import *
import struct
import os
import time

from com.IpcProtocol import IpcMsg, IpcMsgType
from com.BootProtocol import BootProtocol

from com.Timer import _TimerReset

#################################################################################################
##  DEFINITIONS
#################################################################################################

# Enter bootloader command (to application)
BOOT_ENTER_BOOT_CMD         = "enter_boot"

# Enter bootloader success command
BOOT_ENTER_BOOT_RSP_CMD     = "OK, Entering bootloader..."

# Serial command end symbol
MAIN_WIN_COM_STRING_TERMINATION = "\r\n"


# Number of bytes to transfer in flash data
BOOT_FLASH_DATA_FRAME_SIZE      = 64 #bytes


#################################################################################################
##  FUNCTIONS
#################################################################################################

#################################################################################################
##  CLASSES
#################################################################################################   


# ===============================================================================
# @brief  Binary file Class
# ===============================================================================
class BinFile:

    # Access type
    READ_WRITE  = "r+b"      # Puts pointer to start of file 
    WRITE_ONLY  = "wb"       # Erase complete file
    READ_ONLY   = "rb"
    APPEND      = "a+b"      # This mode puts pointer to EOF. Access: Read & Write

    # ===============================================================================
    # @brief  Binary file constructor
    #
    # @param[in]    file    - File name
    # @param[in]    access  - Access level
    # @return       void
    # ===============================================================================
    def __init__(self, file, access=READ_ONLY):

        # Store file name
        self.file_name = file

        try:
            if os.path.isfile(file):
                self.file = open( file, access )
        except Exception as e:
            print(e)

    # ===============================================================================
    # @brief  Write to binary file
    #
    # @param[in]    addr    - Address to write to
    # @param[in]    val     - Value to write as list
    # @return       void
    # ===============================================================================
    def write(self, addr, val):
        self.__set_ptr(addr)
        self.file.write( bytearray( val ))

    # ===============================================================================
    # @brief  Read from binary file
    #
    # @param[in]    addr    - Address to read from
    # @param[in]    size    - Sizeof read in bytes
    # @return       data    - Readed data
    # ===============================================================================
    def read(self, addr, size):
        self.__set_ptr(addr)
        data = self.file.read(size)
        return data
    
    # ===============================================================================
    # @brief  Get size of binary file
    #
    # @return       data    - Readed data
    # ===============================================================================    
    def size(self):
        return len( self.read( 0, None ))

    # ===============================================================================
    # @brief  Set file pointer
    #
    # @note     Pointer is being evaluated based on binary file value
    #
    # @param[in]    offset  - Pointer offset
    # @return       void
    # ===============================================================================
    def __set_ptr(self, offset):
        self.file.seek(offset) 


# ===============================================================================
# @brief  Firmware Image Class
# ===============================================================================
class FwImage(BinFile):

    # Expected application header version
    APP_HEADER_VER_EXPECTED         = 1

    # Application header addresses
    APP_HEADER_APP_SW_VER_ADDR      = 0x00
    APP_HEADER_APP_HW_VER_ADDR      = 0x04
    APP_HEADER_APP_SIZE_ADDR        = 0x08
    APP_HEADER_APP_CRC_ADDR         = 0x0C
    APP_HEADER_VER_ADDR             = 0xFE
    APP_HEADER_CRC_ADDR             = 0xFF

    # Application header size in bytes
    APP_HEADER_SIZE_BYTE            = 0x100

    # ===============================================================================
    # @brief    Firmware Image Constructor
    #
    # @param[in]    file - Inputed firmware image file
    # @return       void
    # =============================================================================== 
    def __init__(self, file):
        self.file = BinFile(file=file, access=BinFile.READ_ONLY)

    # ===============================================================================
    # @brief    Get firmware image software version
    #
    # @return       sw version
    # =============================================================================== 
    def get_sw_ver(self):
        return int.from_bytes( self.file.read( FwImage.APP_HEADER_APP_SW_VER_ADDR, 4 ), byteorder="little" )
    
    # ===============================================================================
    # @brief    Get firmware image software version in raw format
    #
    # @return       sw version in raw
    # =============================================================================== 
    def get_sw_ver_raw(self):
        return self.file.read( FwImage.APP_HEADER_APP_SW_VER_ADDR, 4 )

    # ===============================================================================
    # @brief    Get firmware image hardware version
    #
    # @return       hw version
    # =============================================================================== 
    def get_hw_ver(self):
        return int.from_bytes( self.file.read( FwImage.APP_HEADER_APP_HW_VER_ADDR, 4 ), byteorder="little" )

    # ===============================================================================
    # @brief    Get firmware image hardware version in raw format
    #
    # @return       hw version raw
    # =============================================================================== 
    def get_hw_ver_raw(self):
        return self.file.read( FwImage.APP_HEADER_APP_HW_VER_ADDR, 4 )

    # ===============================================================================
    # @brief    Get firmware image size in bytes
    #
    # @return       firmware image size
    # =============================================================================== 
    def get_fw_size(self):
        return int.from_bytes( self.file.read( FwImage.APP_HEADER_APP_SIZE_ADDR, 4 ), byteorder="little" )

    def read(self, addr, size):
        return self.file.read( addr, size )

# ===============================================================================
#
# @brief:   Boot frame
#
# ===============================================================================
class BootFrame(tk.Frame):

    def __init__(self, parent, ipc_msg_send, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.main_bg)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=100)
        #self.columnconfigure(1, weight=1)

        # Firmware image
        self.fw_file = None

        self.boot_in_progress = False

        self.__ipc_msg_send = ipc_msg_send

        self.com_rx_buf = ""

        # Init widgets
        self.__init_widgets()

        # Create boot protocol
        callbacks = [   self.__boot_connect_rx_cmpt_cb, self.__boot_prepare_rx_cmpt_cb, 
                        self.__boot_flash_rx_cmpt_cb, self.__boot_exit_rx_cmpt_cb, self.__boot_info_rx_cmpt_cb ]

        self.bootProtocol = BootProtocol(send_fn=self.msg_send_bin, cb=callbacks)

        # Working address for bootloader
        self.working_addr = 0



    # ===============================================================================
    # @brief:   Initialize widgets
    #
    # @return:      void
    # ===============================================================================
    def __init_widgets(self):

        # Create info label
        self.frame_label = tk.Label(self, text="Firmware Upgrade", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)

        # Boot frame
        self.boot_frame         = tk.Frame(self, bg=GuiColor.sub_1_bg, padx=10, pady=20)
        self.boot_frame_label   = tk.Label(self, text="Bootloader Informations", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        
        self.app_frame          = tk.Frame(self, bg=GuiColor.sub_1_bg, padx=10, pady=20)
        self.app_frame_label    = tk.Label(self, text="Application Infromations", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)

        self.rowconfigure(1, weight=1)
        
        self.boot_frame.rowconfigure(10, weight=1)
        #self.boot_frame.columnconfigure(0, weight=100)

        # Self frame widgets
        self.progress_bar   = ttk.Progressbar( self, orient='horizontal', mode='determinate', style='text.Horizontal.TProgressbar' )
        self.progress_text  = tk.Label(self, text="   0%", font=GuiFont.heading_2_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.browse_btn     = NormalButton( self, "Browse", command=self.__browse_btn_press)
        self.update_btn     = NormalButton( self, "Upgrade", command=self.__update_btn_press)
        self.update_btn.config(state=tk.DISABLED)

        # App frame widgets
        self.file_text      = tk.Label(self.app_frame, text="---", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, width=50, anchor=tk.W   )
        self.fw_ver_text    = tk.Label(self.app_frame, text="---", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, width=50, anchor=tk.W   )
        self.fw_size_text   = tk.Label(self.app_frame, text="---", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, width=50, anchor=tk.W   )
        self.hw_ver_text    = tk.Label(self.app_frame, text="---", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, width=50, anchor=tk.W   )
        
        # Boot frame widgets
        self.boot_ver_text  = tk.Label(self.boot_frame, text="---", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, width=50, anchor=tk.W )
        self.status_text    = tk.Label(self.boot_frame, text="---", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, width=50, anchor=tk.W )

        # Self frame layout
        self.frame_label.grid(              column=0, row=0,                sticky=tk.W,                    padx=10, pady=10 )
        self.browse_btn.grid(               column=0, row=2,                sticky=tk.W,                    padx=20, pady=10    )
        self.update_btn.grid(               column=0, row=3,                sticky=tk.W,                    padx=20, pady=10    )
        self.app_frame_label.grid(          column=0, row=4, columnspan=3,  sticky=tk.W,                    padx=20, pady=0 )
        self.app_frame.grid(                column=0, row=5, columnspan=3,  sticky=tk.W+tk.N+tk.S+tk.E,     padx=10, pady=10 )
        self.boot_frame_label.grid(         column=0, row=6,                sticky=tk.W,                    padx=20, pady=0 )
        self.boot_frame.grid(               column=0, row=7, columnspan=3,  sticky=tk.W+tk.N+tk.S+tk.E,     padx=10, pady=10 )
        self.progress_bar.grid(             column=0, row=8,                sticky=tk.W+tk.N+tk.S+tk.E,     padx=10, pady=20    )
        self.progress_text.grid(            column=2, row=8,                sticky=tk.W+tk.N+tk.S+tk.E,     padx=10, pady=20  )

        # Boot frame layout
        self.boot_ver_text.grid(    column=1, row=0,                sticky=tk.W,                   padx=5, pady=10    )
        self.status_text.grid(      column=1, row=1,                sticky=tk.W,                   padx=5, pady=10    )
        tk.Label(self.boot_frame, text="Status:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,               width=20, anchor=tk.E ).grid(                 column=0, row=1, sticky=tk.E,     padx=5, pady=10    )
        tk.Label(self.boot_frame, text="Bootloader version:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,   width=20, anchor=tk.E ).grid(     column=0, row=0, sticky=tk.E,     padx=5, pady=10    )

        # App frame layout
        self.file_text.grid(        column=1, row=2,                sticky=tk.W,                   padx=5, pady=10    )
        self.fw_size_text.grid(     column=1, row=3,                sticky=tk.W,                   padx=5, pady=10    )
        self.fw_ver_text.grid(      column=1, row=4,                sticky=tk.W,                   padx=5, pady=10    )
        self.hw_ver_text.grid(      column=1, row=5,                sticky=tk.W,                   padx=5, pady=10    )
        
        tk.Label(self.app_frame, text="Application file:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,  width=20, anchor=tk.E  ).grid(    column=0, row=2, sticky=tk.E,    padx=5, pady=10    )
        tk.Label(self.app_frame, text="Application size:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,  width=20, anchor=tk.E ).grid(    column=0, row=3, sticky=tk.E,    padx=5, pady=10    )
        tk.Label(self.app_frame, text="Software ver:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,      width=20, anchor=tk.E ).grid(        column=0, row=4, sticky=tk.E,    padx=5, pady=10    )
        tk.Label(self.app_frame, text="Hardware ver:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,      width=20, anchor=tk.E ).grid(        column=0, row=5, sticky=tk.E,    padx=5, pady=10    )

    def __browse_btn_press(self):

        # Select file to visualize
        fw_file_path =  tk.filedialog.askopenfilename(initialdir=self.fw_file, title = "Select firmware image",filetypes = (("Binary files","*.bin"),("all files","*.*")))
        
        # File selected
        if fw_file_path:

            print("Selected FW image: %s" % fw_file_path )

            self.update_btn.config(state=tk.NORMAL)
            self.file_text["text"] = fw_file_path.split("/")[-1]

            # Open file
            self.fw_file = FwImage(file=fw_file_path)

            fw_size = self.fw_file.get_fw_size()
            sw_ver = self.fw_file.get_sw_ver()
            sw_ver = struct.pack('I', int(sw_ver))
            hw_ver = self.fw_file.get_hw_ver()
            hw_ver = struct.pack('I', int(hw_ver))

            self.fw_size_text["text"] = "%d kB" % ( fw_size / 1024 )
            self.fw_ver_text["text"] = "V%d.%d.%d.%d" % ( sw_ver[3], sw_ver[2], sw_ver[1], sw_ver[0] )
            self.hw_ver_text["text"] = "V%d.%d.%d.%d" % ( hw_ver[3], hw_ver[2], hw_ver[1], hw_ver[0] )

            self.status_text["fg"] = GuiColor.sub_1_fg
            self.status_text["text"] = "Idle"



    def com_timer_expire(self):
        print( "Communication timeouted" );

        # Are we in upgrade process
        if "Cancel" == self.update_btn.get_text():

            # Reset progress bar
            self.progress_text["text"] = "%3d%%" % 0
            self.progress_bar["mode"] = "determinate"
            self.progress_bar.stop()

            # Update status
            self.status_text["fg"] = "red"
            self.status_text["text"] = "ERROR: Communication with bootloader timeouted!"

            self.update_btn.text( "Upgrade" )

        else:
            # Reset progress bar
            self.progress_text["text"] = "%3d%%" % 0
            self.progress_bar["mode"] = "determinate"
            self.progress_bar.stop()

            # Update status
            self.status_text["fg"] = "red"
            self.status_text["text"] = "ERROR: Connecting with bootloader timeouted!"


        # Delete timer
        del self.com_timer


    def __update_btn_press(self):  

        print( self.update_btn.get_text() )

        if "Upgrade" == self.update_btn.get_text():

            # If in application -> reset and enter bootloader
            self.msg_send_ascii( "reset" )
            
            # Wait for 20 ms
            time.sleep( 0.02 )

            # Connect to bootloader
            self.bootProtocol.send_connect()

            # Reset progress bar
            self.progress_text["text"] = "%3d%%" % 0
            self.progress_bar["mode"] = "indeterminate"
            self.progress_bar.start()

            # Update status
            self.status_text["fg"] = GuiColor.sub_1_fg
            self.status_text["text"] = "Connecting..."

            # Start timeout timer
            self.com_timer = _TimerReset( interval=3, function=self.com_timer_expire )
            self.com_timer.start()
        
        else:
            self.com_timer.cancel()
            del self.com_timer
            self.bootProtocol.reset_rx_queue()

            # Reset progress bar
            self.progress_text["text"] = "%3d%%" % 0
            self.progress_bar.stop()

            self.status_text["fg"] = GuiColor.sub_1_fg
            self.status_text["text"] = "Upgrade canceled!"

            self.update_btn.text( "Upgrade" )


    def msg_send_ascii(self, cmd):

        # Append end string termiantion 
        dev_cmd = str(cmd) + MAIN_WIN_COM_STRING_TERMINATION

        # Send cmd to serial process
        msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComTxFrame, payload=dev_cmd)
        self.__ipc_msg_send(msg)


    def msg_send_bin(self, cmd):

        # Send cmd to serial process
        msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComTxBinary, payload=cmd)
        self.__ipc_msg_send(msg)


    # ===============================================================================
    # @brief:   Message received callback
    #
    # @note     Come here either ASCII or binary character is received!
    #
    # @return:      void
    # ===============================================================================
    def msg_receive_cb(self, payload):

        self.bootProtocol.parser( payload )



    def __boot_connect_rx_cmpt_cb(self, status):
        print( "Connect callback: %s" % status )

        # At that point we are conected to bootloader
        self.waiting_for_connect_rsp = False

        # Bootloader connect success
        if BootProtocol.MSG_OK == status:

            self.update_btn.text( "Cancel" )

            # Get firmware info
            fw_size = self.fw_file.get_fw_size()
            sw_ver = self.fw_file.get_sw_ver()
            hw_ver = self.fw_file.get_hw_ver()

            # Send prepare message
            self.bootProtocol.send_prepare( fw_size, sw_ver, hw_ver )

            # Update status
            self.status_text["fg"] = GuiColor.sub_1_fg
            self.status_text["text"] = "Preparing"

            # Restart communiction timeout timer
            self.com_timer.reset( 5 )

        else:
            self.status_text["fg"] = "red"
            self.status_text["text"] = "ERROR:" + self.bootProtocol.get_status_str( status )

            # Stop communication timeout timer
            self.com_timer.cancel()
            self.progress_bar.stop()
            self.update_btn.text( "Upgrade" )


    def __boot_prepare_rx_cmpt_cb(self, status):
        print( "Prepare callback: %s" % status )

        # Are we in upgrade process
        if "Cancel" == self.update_btn.get_text():

            # Bootloader prepare success
            if BootProtocol.MSG_OK == status:

                self.progress_bar.stop()
                self.progress_bar["value"] = 0

                # Reset working address
                self.working_addr = 0

                data = self.fw_file.read( self.working_addr, BOOT_FLASH_DATA_FRAME_SIZE )
                data_len = len( data )

                if data_len > 0:
                    self.bootProtocol.send_flash_data( data, data_len )
                    self.working_addr += data_len

                self.status_text["fg"] = GuiColor.sub_1_fg
                self.status_text["text"] = "Flashing"

                # Restart communiction timeout timer
                self.com_timer.reset( 0.1 )

            else:
                self.status_text["fg"] = "red"
                self.status_text["text"] = "ERROR:" + self.bootProtocol.get_status_str( status )

                # Stop communication timeout timer
                self.com_timer.cancel()
                self.progress_bar.stop()
                self.update_btn.text( "Upgrade" )


    def __boot_flash_rx_cmpt_cb(self, status):

        # Are we in upgrade process
        if "Cancel" == self.update_btn.get_text():

            # Response received from flash command
            self.waiting_for_flash_rsp = False

            # Bootloader flashing success
            if BootProtocol.MSG_OK == status:

                data = self.fw_file.read( self.working_addr, BOOT_FLASH_DATA_FRAME_SIZE )
                data_len = len( data )

                if data_len > 0:
                    self.bootProtocol.send_flash_data( data, data_len )
                    self.working_addr += data_len

                    # Restart communiction timeout timer
                    self.com_timer.reset( 0.1 )

                # No more bytes to flash
                else:
                    self.bootProtocol.send_exit()

                    # Restart communiction timeout timer
                    self.com_timer.reset( 0.5 )

            else:
                self.status_text["fg"] = "red"
                self.status_text["text"] = "ERROR:" + self.bootProtocol.get_status_str( status )

                # Stop communication timeout timer
                self.com_timer.cancel()
                self.update_btn.text( "Upgrade" )

            # Calculate progress
            progress = (( self.working_addr / self.fw_file.get_fw_size()) * 100 )

            self.progress_bar["mode"] = "determinate"
            self.progress_text["text"] = "%3d%%" % progress
            self.progress_bar["value"] = progress




    def __boot_exit_rx_cmpt_cb(self, status):
        print( "Exit callback: %s" % status )

        # Are we in upgrade process
        if "Cancel" == self.update_btn.get_text():

            # Stop communiction timeout timer
            self.com_timer.cancel()

            # Bootloader exit success
            if BootProtocol.MSG_OK == status:
                self.status_text["fg"] = GuiColor.btn_success_bg
                self.status_text["text"] = "Application successfully upgraded"
            else:
                self.status_text["fg"] = "red"
                self.status_text["text"] = "ERROR: " + self.bootProtocol.get_status_str( status )

            # Final step -> change back to upgrade
            self.update_btn.text( "Upgrade" )

        

    def __boot_info_rx_cmpt_cb(self, status):
        print( "Info callback: %s" % status )






#################################################################################################
##  END OF FILE
#################################################################################################  





