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

from com.IpcProtocol import IpcMsg, IpcMsgType
from com.BootProtocol import BootProtocol

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

    def __init__(self, file):
        self.file = BinFile(file=file, access=BinFile.READ_ONLY)


    def get_sw_ver(self):
        return int.from_bytes( self.file.read( FwImage.APP_HEADER_APP_SW_VER_ADDR, 4 ), byteorder="little" )
    
    def get_sw_ver_raw(self):
        return self.file.read( FwImage.APP_HEADER_APP_SW_VER_ADDR, 4 )

    def get_hw_ver(self):
        return int.from_bytes( self.file.read( FwImage.APP_HEADER_APP_HW_VER_ADDR, 4 ), byteorder="little" )

    def get_hw_ver_raw(self):
        return self.file.read( FwImage.APP_HEADER_APP_HW_VER_ADDR, 4 )

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
        self.boot_frame = tk.Frame(self, bg=GuiColor.sub_1_bg, padx=20, pady=20)

        self.boot_frame.rowconfigure(10, weight=1)
        #self.boot_frame.columnconfigure(0, weight=100)

        # Progress bar
        self.progress_bar   = ttk.Progressbar( self, orient='horizontal', mode='determinate', style='text.Horizontal.TProgressbar' )
        self.progress_text  = tk.Label(self, text="   0%", font=GuiFont.heading_2_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.file_text      = tk.Label(self.boot_frame, text="", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.fw_ver_text    = tk.Label(self.boot_frame, text="", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.fw_size_text   = tk.Label(self.boot_frame, text="", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.hw_ver_text    = tk.Label(self.boot_frame, text="", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.status_text    = tk.Label(self.boot_frame, text="", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.browse_btn     = NormalButton( self.boot_frame, "Browse", command=self.__browse_btn_press)
        self.update_btn     = NormalButton( self.boot_frame, "Update", command=self.__update_btn_press)

        self.update_btn.config(state=tk.DISABLED)


        # Self frame layout
        self.frame_label.grid(      column=0, row=0,                sticky=tk.W,                padx=20, pady=10 )
        self.boot_frame.grid(       column=0, row=1, columnspan=3,  sticky=tk.W+tk.N+tk.S+tk.E, padx=20, pady=10 )

        # Boot frame layout
        self.browse_btn.grid(       column=0, row=0,                sticky=tk.W,                    padx=20, pady=10    )
        self.update_btn.grid(       column=0, row=1,                sticky=tk.W,                    padx=20, pady=10    )
        self.progress_bar.grid(     column=0, row=6,  sticky=tk.W+tk.N+tk.S+tk.E,     padx=20, pady=20    )
        self.progress_text.grid(    column=2, row=6,                sticky=tk.W+tk.N+tk.S+tk.E,     padx=20, pady=20    )

        
        self.file_text.grid(        column=1, row=2,                sticky=tk.W,                   padx=10, pady=10    )
        self.fw_size_text.grid(     column=1, row=3,                sticky=tk.W,                   padx=10, pady=10    )
        self.fw_ver_text.grid(      column=1, row=4,                sticky=tk.W,                   padx=10, pady=10    )
        self.hw_ver_text.grid(      column=1, row=5,                sticky=tk.W,                   padx=10, pady=10    )
        self.status_text.grid(      column=1, row=6,                sticky=tk.W,                   padx=10, pady=10    )
        tk.Label(self.boot_frame, text="Firmware file:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg).grid(  column=0, row=2, sticky=tk.E,    padx=10, pady=10    )
        tk.Label(self.boot_frame, text="Firmware size:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg).grid(  column=0, row=3, sticky=tk.E,    padx=10, pady=10    )
        tk.Label(self.boot_frame, text="Firmware ver:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg).grid(   column=0, row=4, sticky=tk.E,     padx=10, pady=10    )
        tk.Label(self.boot_frame, text="Hardware ver:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg).grid(   column=0, row=5, sticky=tk.E,     padx=10, pady=10    )
        tk.Label(self.boot_frame, text="Status:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg).grid(         column=0, row=6, sticky=tk.E,     padx=10, pady=10    )


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

            self.status_text["text"] = "Idle"


    def __com_timeout_event(self):
        print( "Communication timeouted" );
    
        self.bootProtocol.com_timeout_event()


    def __update_btn_press(self):  

        self.progress_text["text"] = "%3d%%" % 0
        self.bootProtocol.send_connect()
        self.progress_bar.start()

        self.status_text["text"] = "Connecting"

        #self.after( 100, self.__com_timeout_event) 




        """
        import time

        time.sleep( 0.1 )

        fw_size = self.fw_file.get_fw_size()
        sw_ver = self.fw_file.get_sw_ver()
        hw_ver = self.fw_file.get_hw_ver()

        print( "Firmware size: %s kB" % ( fw_size/1024 ))
        print( "SW version: %s" % self.fw_file.get_sw_ver_raw() )
        print( "HW version: %s" % self.fw_file.get_hw_ver_raw() )

        self.bootProtocol.send_prepare( fw_size, sw_ver, hw_ver )

        time.sleep( 3.0 )

        addr = 0
        SIZE = 64

        #for _ in range( 16 ):
        
        while True:


            data = self.fw_file.read( addr, SIZE )
            data_len = len( data )

            if data_len > 0:
                self.bootProtocol.send_flash_data( data, data_len )
                addr += data_len
            else:
                break                

            time.sleep(0.01)



        time.sleep(0.01)
        self.bootProtocol.send_exit()
        """

        #self.__send_connect_cmd()

        #self.__send_prepare_cmd( 1, 1, 1 )

        """
        # Update started
        if False == self.boot_in_progress:

            # Send message to enter bootloader
            self.com_rx_buf = ""
            #self.msg_send( BOOT_ENTER_BOOT_CMD )
            pass


        # Update canceled
        else:

            # Update button text
            self.update_btn.text( "Update" )
        """
            



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

        # Bootloader connect success
        if BootProtocol.MSG_OK == status:




            # Get firmware info
            fw_size = self.fw_file.get_fw_size()
            sw_ver = self.fw_file.get_sw_ver()
            hw_ver = self.fw_file.get_hw_ver()

            # Send prepare message
            self.bootProtocol.send_prepare( fw_size, sw_ver, hw_ver )

            self.status_text["text"] = "Preparing"


    def __boot_prepare_rx_cmpt_cb(self, status):
        print( "Prepare callback: %s" % status )

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

            self.status_text["text"] = "Flashing"



    def __boot_flash_rx_cmpt_cb(self, status):

        # Bootloader flashing success
        if BootProtocol.MSG_OK == status:

            data = self.fw_file.read( self.working_addr, BOOT_FLASH_DATA_FRAME_SIZE )
            data_len = len( data )

            if data_len > 0:
                self.bootProtocol.send_flash_data( data, data_len )
                self.working_addr += data_len

            # No more bytes to flash
            else:
                self.bootProtocol.send_exit()

        # Calculate progress
        progress = (( self.working_addr / self.fw_file.get_fw_size()) * 100 )

        self.progress_text["text"] = "%3d%%" % progress
        self.progress_bar["value"] = progress


    def __boot_exit_rx_cmpt_cb(self, status):
        print( "Exit callback: %s" % status )

        self.status_text["text"] = "Done"


    def __boot_info_rx_cmpt_cb(self, status):
        print( "Info callback: %s" % status )



        """
        print("Boot msg receive: %s" % payload )

        # Append received chars to buffer
        self.com_rx_buf += str(payload)

        # Check for termiantion char
        str_term = str(self.com_rx_buf).find(MAIN_WIN_COM_STRING_TERMINATION)

        # Termination char founded
        if str_term >= 0:

            # Parsed response from device
            dev_resp = self.com_rx_buf[:str_term]

            # Error entering bootloader
            if "ERR" in dev_resp:
                self.update_btn.show_error()
                
                self.boot_in_progress = False

            # Successfull enter to bootloader
            elif "BOOT_ENTER_BOOT_RSP_CMD" in dev_resp:
                self.update_btn.show_success()

                self.boot_in_progress = True

                # Update button text
                self.update_btn.text( "Cancel" )

            
            # Ignore
            else:
                pass
        """


#################################################################################################
##  END OF FILE
#################################################################################################  





