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
BOOT_ENTER_BOOT_CMD             = "enter_boot"

# Serial command end symbol
MAIN_WIN_COM_STRING_TERMINATION = "\r\n"

# Number of bytes to transfer in flash data
BOOT_FLASH_DATA_FRAME_SIZE      = 1024 #bytes

# Communication timeout settings
BOOT_COM_CONNECT_TIMEOUT_SEC    = 5.0
BOOT_COM_PREPARE_TIMEOUT_SEC    = 10.0
BOOT_COM_FLASH_TIMEOUT_SEC      = 0.5
BOOT_COM_EXIT_TIMEOUT_SEC       = 5.0

# Reconnect pause time between COM port connect and disconnect command
BOOT_COM_RECONNECT_PAUSE        = 1.0

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

    # Application header size in bytes
    APP_HEADER_SIZE_BYTE            = 0x100

    # Expected application header version
    APP_HEADER_VER_EXPECTED         = 1

    # Application header addresses
    APP_HEADER_CRC_ADDR             = 0x00
    APP_HEADER_VER_ADDR             = 0x01

    # Application header data fields
    APP_HEADER_SW_VER_ADDR          = 0x08
    APP_HEADER_HW_VER_ADDR          = 0x0C
    APP_HEADER_APP_SIZE_ADDR        = 0x10
    APP_HEADER_APP_CRC_ADDR         = 0x14
    APP_HEADER_ENC_TYPE             = 0x18
    APP_HEADER_SIG_TYPE             = 0x1C
    APP_HEADER_SIG_SHA256           = 0x20    

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
        return int.from_bytes( self.file.read( FwImage.APP_HEADER_SW_VER_ADDR, 4 ), byteorder="little" )
    
    # ===============================================================================
    # @brief    Get firmware image software version in raw format
    #
    # @return       sw version in raw
    # =============================================================================== 
    def get_sw_ver_raw(self):
        return self.file.read( FwImage.APP_HEADER_SW_VER_ADDR, 4 )

    # ===============================================================================
    # @brief    Get firmware image hardware version
    #
    # @return       hw version
    # =============================================================================== 
    def get_hw_ver(self):
        return int.from_bytes( self.file.read( FwImage.APP_HEADER_HW_VER_ADDR, 4 ), byteorder="little" )

    # ===============================================================================
    # @brief    Get firmware image hardware version in raw format
    #
    # @return       hw version raw
    # =============================================================================== 
    def get_hw_ver_raw(self):
        return self.file.read( FwImage.APP_HEADER_HW_VER_ADDR, 4 )

    # ===============================================================================
    # @brief    Get firmware image size in bytes
    #
    # @return       firmware image size
    # =============================================================================== 
    def get_fw_size(self):
        return int.from_bytes( self.file.read( FwImage.APP_HEADER_APP_SIZE_ADDR, 4 ), byteorder="little" )

    # ===============================================================================
    # @brief  Read from binary file
    #
    # @param[in]    addr    - Address to read from
    # @param[in]    size    - Sizeof read in bytes
    # @return       data    - Readed data
    # ===============================================================================
    def read(self, addr, size):
        return self.file.read( addr, size )
    
    # ===============================================================================
    # @brief  Check if application image is OK
    #
    # @return       valid    - Validation flag
    # ===============================================================================
    def validate(self):
        valid = False

        # Calculate header crc
        crc_calc = self.__calc_header_crc()

        # App Header crc
        app_header_crc = self.read( FwImage.APP_HEADER_CRC_ADDR, 1 )[0]

        # Check crc
        if crc_calc == app_header_crc:
            valid = True

        return valid

    # ===============================================================================
    # @brief  Calculate application header CRC
    #
    # @return       app_header_crc - Appplication header CRC
    # ===============================================================================
    def __calc_header_crc(self):

        # Calculate application header CRC
        # NOTE: Ignore last CRC field!
        app_header_crc = self.__calc_crc8( self.file.read( 1, FwImage.APP_HEADER_SIZE_BYTE - 1 ))

        return app_header_crc

    # ===============================================================================
    # @brief  Calculate CRC-8
    #
    # @param[in]    data    - Inputed data
    # @return       crc8    - Calculated CRC8
    # ===============================================================================
    def __calc_crc8(self, data):
        poly = 0x07
        seed = 0xB6
        crc8 = seed

        for byte in data:
            crc8 = (( crc8 ^ byte ) & 0xFF )

            for n in range( 8 ):
                if 0x80 == ( crc8 & 0x80 ):
                    crc8 = (( crc8 << 1 ) ^ poly )
                else:
                    crc8 = ( crc8 << 1 );

        return crc8 & 0xFF


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

        # Firmware image
        self.fw_file = None

        # Send message function
        self.__ipc_msg_send = ipc_msg_send

        # Init widgets
        self.__init_widgets()

        # Create boot protocol
        callbacks = [   self.__boot_connect_rx_cmpt_cb, self.__boot_prepare_rx_cmpt_cb, 
                        self.__boot_flash_rx_cmpt_cb, self.__boot_exit_rx_cmpt_cb, self.__boot_info_rx_cmpt_cb ]

        self.bootProtocol = BootProtocol(send_fn=self.msg_send_bin, cb=callbacks)

        # Working address for bootloader
        self.working_addr = 0

        # Start tick
        self.start_tick = 0

        # Upgrade btn init state
        self.upgrade_btn_active = False

    # ===============================================================================
    # @brief:   Send ASCII format of message
    #
    # @param[in]:   cmd - Message to send
    # @return:      void
    # ===============================================================================
    def msg_send_ascii(self, cmd):

        # Append end string termiantion 
        dev_cmd = str(cmd) + MAIN_WIN_COM_STRING_TERMINATION

        # Send cmd to serial process
        msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComTxFrame, payload=dev_cmd)
        self.__ipc_msg_send(msg)

    # ===============================================================================
    # @brief:   Send binary format of message
    #
    # @param[in]:   cmd - Message to send
    # @return:      void
    # ===============================================================================
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
        
        # Bootloader protocol parser
        self.bootProtocol.parser( payload )

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
        self.boot_frame_label   = tk.Label(self, text="Bootloader informations", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        
        self.app_frame          = tk.Frame(self, bg=GuiColor.sub_1_bg, padx=10, pady=20)
        self.app_frame_label    = tk.Label(self, text="Application informations", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)

        self.rowconfigure(1, weight=1)
        self.boot_frame.rowconfigure(10, weight=1)

        # Self frame widgets
        self.progress_bar   = ttk.Progressbar( self, orient='horizontal', mode='determinate', style='text.Horizontal.TProgressbar' )
        self.progress_text  = tk.Label(self, text="   0%", font=GuiFont.heading_2_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.browse_btn     = NormalButton( self, "Browse", command=self.__browse_btn_press)
        self.update_btn     = NormalButton( self, "Upgrade", command=self.__update_btn_press)
        self.update_btn.config(state=tk.DISABLED)

        # Configuration buttongs
        self.image_valid_btn    = ConfigSwitch( self, "Validate FW image",    initial_state=False )
        self.usb_com_btn        = ConfigSwitch( self, "USB communication", initial_state=False )

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
        self.image_valid_btn.grid(          column=1, row=2,                sticky=tk.W+tk.E, )
        self.usb_com_btn.grid(              column=1, row=3,                sticky=tk.W+tk.E, )
        
        self.app_frame_label.grid(          column=0, row=4, columnspan=3,  sticky=tk.W,                    padx=20, pady=0 )
        self.app_frame.grid(                column=0, row=5, columnspan=3,  sticky=tk.W+tk.N+tk.S+tk.E,     padx=10, pady=10 )
        self.boot_frame_label.grid(         column=0, row=6,                sticky=tk.W,                    padx=20, pady=0 )
        self.boot_frame.grid(               column=0, row=7, columnspan=3,  sticky=tk.W+tk.N+tk.S+tk.E,     padx=10, pady=10 )
        self.progress_bar.grid(             column=0, row=8, columnspan=2,  sticky=tk.W+tk.N+tk.S+tk.E,     padx=10, pady=20    )
        self.progress_text.grid(            column=2, row=8,                sticky=tk.W+tk.N+tk.S+tk.E,     padx=10, pady=20  )

        # Boot frame layout
        self.boot_ver_text.grid(    column=1, row=0,                sticky=tk.W,                   padx=5, pady=5    )
        self.status_text.grid(      column=1, row=1,                sticky=tk.W,                   padx=5, pady=5    )
        tk.Label(self.boot_frame, text="General status:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,               width=20, anchor=tk.E ).grid(   column=0, row=1, sticky=tk.E,     padx=5, pady=5    )
        tk.Label(self.boot_frame, text="Bootloader version:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,   width=20, anchor=tk.E ).grid(           column=0, row=0, sticky=tk.E,     padx=5, pady=5    )

        # App frame layout
        self.file_text.grid(        column=1, row=2,                sticky=tk.W,                   padx=5, pady=5    )
        self.fw_size_text.grid(     column=1, row=3,                sticky=tk.W,                   padx=5, pady=5    )
        self.fw_ver_text.grid(      column=1, row=4,                sticky=tk.W,                   padx=5, pady=5    )
        self.hw_ver_text.grid(      column=1, row=5,                sticky=tk.W,                   padx=5, pady=5    )
        
        tk.Label(self.app_frame, text="Application file:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,  width=20, anchor=tk.E  ).grid(      column=0, row=2, sticky=tk.E,    padx=5, pady=5    )
        tk.Label(self.app_frame, text="Application size:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,  width=20, anchor=tk.E ).grid(       column=0, row=3, sticky=tk.E,    padx=5, pady=5    )
        tk.Label(self.app_frame, text="Software ver:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,      width=20, anchor=tk.E ).grid(       column=0, row=4, sticky=tk.E,    padx=5, pady=5    )
        tk.Label(self.app_frame, text="Hardware ver:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg,      width=20, anchor=tk.E ).grid(       column=0, row=5, sticky=tk.E,    padx=5, pady=5    )

    # ===============================================================================
    # @brief:   Browse button pressed
    #
    # @return:      void
    # ===============================================================================
    def __browse_btn_press(self):

        # Select file to visualize
        fw_file_path = tk.filedialog.askopenfilename(initialdir=self.fw_file, title = "Select firmware image",filetypes = (("Binary files","*.bin"),("all files","*.*")))
        
        # File selected
        if fw_file_path:

            # Get file name
            self.file_text["text"] = fw_file_path.split("/")[-1]

            # Open file
            self.fw_file = FwImage(file=fw_file_path)

            # Image valuidation enabled
            if True == self.image_valid_btn.state():

                # Application image valid
                if self.fw_file.validate():

                    # Get FW image size
                    fw_size = self.fw_file.get_fw_size()

                    # Get FW image SW version
                    sw_ver = self.fw_file.get_sw_ver()
                    sw_ver = struct.pack('I', int(sw_ver))

                    # Get HW image SW version
                    hw_ver = self.fw_file.get_hw_ver()
                    hw_ver = struct.pack('I', int(hw_ver))

                    # Show firmware info
                    self.fw_size_text["text"] = "%.2f kB" % ( fw_size / 1024 )
                    self.fw_ver_text["text"] = "V%d.%d.%d.%d" % ( sw_ver[3], sw_ver[2], sw_ver[1], sw_ver[0] )
                    self.hw_ver_text["text"] = "V%d.%d.%d.%d" % ( hw_ver[3], hw_ver[2], hw_ver[1], hw_ver[0] )

                    self.file_text["fg"]    = GuiColor.btn_success_bg
                    self.fw_size_text["fg"] = GuiColor.sub_1_fg
                    self.fw_ver_text["fg"]  = GuiColor.sub_1_fg
                    self.hw_ver_text["fg"]  = GuiColor.sub_1_fg

                    # Change status to idle
                    self.status_text["fg"] = GuiColor.sub_1_fg
                    self.status_text["text"] = "Idle"

                    # Enable update button
                    self.update_btn.config(state=tk.NORMAL)
                    self.upgrade_btn_active = True

                else:
                    self.fw_size_text["text"]   = "Invalid application!"
                    self.fw_ver_text["text"]    = "Invalid application!"
                    self.hw_ver_text["text"]    = "Invalid application!"

                    self.file_text["fg"]    = "red"
                    self.fw_size_text["fg"] = "red"
                    self.fw_ver_text["fg"]  = "red"
                    self.hw_ver_text["fg"]  = "red"

                    # Change status to idle
                    self.status_text["fg"] = GuiColor.sub_1_fg
                    self.status_text["text"] = "---"

                    # Disable update button
                    self.update_btn.config(state=tk.DISABLED)
                    self.upgrade_btn_active = False

            else:
                # Enable update button
                self.update_btn.config(state=tk.NORMAL)
                self.upgrade_btn_active = True                

    # ===============================================================================
    # @brief:   Update button pressed
    #
    # @return:      void
    # ===============================================================================
    def __update_btn_press(self):  

        if "Upgrade" == self.update_btn.get_text():

            # Disable browse button
            self.browse_btn.config(state=tk.DISABLED)

            # Enter bootloader
            self.msg_send_ascii( BOOT_ENTER_BOOT_CMD )
            
            # Wait for 50 ms
            time.sleep( 0.050 )

            # Re-connection needed only for USB devices
            if True == self.usb_com_btn.state():
                self.__com_port_reconnect(BOOT_COM_RECONNECT_PAUSE);            

            # Reset input queue 
            self.bootProtocol.reset_rx_queue()

            # Get bootloader info
            self.bootProtocol.send_info()
            time.sleep(0.01)

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
            self.com_timer = _TimerReset( interval=BOOT_COM_CONNECT_TIMEOUT_SEC, function=self.__com_timer_expire )
            self.com_timer.start()
        
        else:

            # Stop communication timeout timer
            self.com_timer.cancel()

            # Delete timer
            try:
                del self.com_timer
            except:
                pass

            # Reset input queue 
            self.bootProtocol.reset_rx_queue()

            # Reset progress bar
            self.progress_text["text"] = "%3d%%" % 0
            self.progress_bar.stop()

            # Update status
            self.status_text["fg"] = "yellow"
            self.status_text["text"] = "WARNING: Upgrade canceled!"

            # Allowing upgrade again
            self.update_btn.text( "Upgrade" )

            # Enable browse button back
            self.browse_btn.config(state=tk.NORMAL)

    # ===============================================================================
    # @brief:   Communication timeout event
    #
    # @return:      void
    # ===============================================================================
    def __com_timer_expire(self):

        # Are we in upgrade process
        if "Cancel" == self.update_btn.get_text():

            # Update status
            self.status_text["text"] = "ERROR: Communication with bootloader timeouted!"

            # Allowing upgrade again
            self.update_btn.text( "Upgrade" )

        # We are in connecting state
        else:

            # Update status
            self.status_text["text"] = "ERROR: Connecting with bootloader timeouted!"

        # Reset progress bar
        self.progress_text["text"] = "%3d%%" % 0
        self.progress_bar["mode"] = "determinate"
        self.progress_bar.stop()

        # Update status
        self.status_text["fg"] = "red"

        # Reset input queue on timeout
        self.bootProtocol.reset_rx_queue()

        # Enable browse button back
        self.browse_btn.config(state=tk.NORMAL)

        # Delete timer
        try:
            del self.com_timer
        except:
            pass

    # ===============================================================================
    # @brief:   Connect response message from bootlaoder receive callback
    #
    # @param[in]:   status  - Status of message
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __boot_connect_rx_cmpt_cb(self, status, payload):

        # At that point we are conected to bootloader
        self.waiting_for_connect_rsp = False

        # Bootloader connect success
        if BootProtocol.MSG_OK == status:

            self.update_btn.text( "Cancel" )

            # Store start time
            self.start_tick = time.time()

            # Get firmware info
            fw_size = self.fw_file.get_fw_size()
            sw_ver = self.fw_file.get_sw_ver()
            hw_ver = self.fw_file.get_hw_ver()

            # Send prepare message
            self.bootProtocol.send_prepare( fw_size, sw_ver, hw_ver )

            # Update status
            self.status_text["fg"] = GuiColor.sub_1_fg
            self.status_text["text"] = "Pre-validating and preparing flash..."

            # Restart communiction timeout timer
            self.com_timer.reset( BOOT_COM_PREPARE_TIMEOUT_SEC )

        else:
            self.status_text["fg"] = "red"
            self.status_text["text"] = "ERROR:" + self.bootProtocol.get_status_str( status )

            # Stop communication timeout timer
            self.com_timer.cancel()
            self.progress_bar.stop()
            self.update_btn.text( "Upgrade" )

    # ===============================================================================
    # @brief:   Prepare response message from bootlaoder receive callback
    #
    # @param[in]:   status  - Status of message
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __boot_prepare_rx_cmpt_cb(self, status, payload):

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
                self.status_text["text"] = "Flashing..."

                # Restart communiction timeout timer
                self.com_timer.reset( BOOT_COM_FLASH_TIMEOUT_SEC )

            else:
                self.status_text["fg"] = "red"
                self.status_text["text"] = "ERROR:" + self.bootProtocol.get_status_str( status )

                # Stop communication timeout timer
                self.com_timer.cancel()
                self.progress_bar.stop()
                self.update_btn.text( "Upgrade" )

    # ===============================================================================
    # @brief:   Flash data response message from bootlaoder receive callback
    #
    # @param[in]:   status  - Status of message
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __boot_flash_rx_cmpt_cb(self, status, payload):

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
                    self.com_timer.reset( BOOT_COM_FLASH_TIMEOUT_SEC )

                # No more bytes to flash
                else:
                    self.bootProtocol.send_exit()
                    self.status_text["text"] = "Post-validating..."

                    # Restart communiction timeout timer
                    self.com_timer.reset( BOOT_COM_EXIT_TIMEOUT_SEC )

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

    # ===============================================================================
    # @brief:   Exit response message from bootlaoder receive callback
    #
    # @param[in]:   status  - Status of message
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __boot_exit_rx_cmpt_cb(self, status, payload):

        # Are we in upgrade process
        if "Cancel" == self.update_btn.get_text():

            # Stop communiction timeout timer
            self.com_timer.cancel()

            # Bootloader exit success
            if BootProtocol.MSG_OK == status:

                # Calculate total firmware upgade duration
                total_time = time.time() - self.start_tick

                self.status_text["fg"] = GuiColor.btn_success_bg
                self.status_text["text"] = "Application successfully upgraded in %.2f sec!" % total_time
            
            # Bootloader exit error
            else:
                self.status_text["fg"] = "red"
                self.status_text["text"] = "ERROR: " + self.bootProtocol.get_status_str( status )

            # Final step -> change back to upgrade
            self.update_btn.text( "Upgrade" )

            # Enable browse button back
            self.browse_btn.config(state=tk.NORMAL)

            # Re-connection needed only for USB devices
            if True == self.usb_com_btn.state():
                self.__com_port_reconnect(BOOT_COM_RECONNECT_PAUSE);
        
    # ===============================================================================
    # @brief:   Info response message from bootlaoder receive callback
    #
    # @param[in]:   status  - Status of message
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __boot_info_rx_cmpt_cb(self, status, payload):

        # Bootloader info msg success
        if BootProtocol.MSG_OK == status:
            
            # Get bootloader version
            boot_ver = payload

            # Show bootloader version
            self.boot_ver_text["text"] = "V%d.%d.%d.%d" % ( boot_ver[3], boot_ver[2], boot_ver[1], boot_ver[0] )

    # ===============================================================================
    # @brief:   Disconnect from COM port
    #
    # @return:      void
    # ===============================================================================    
    def __com_port_disconnect(self):
        msg = IpcMsg()

        # Send disconnection reqeust to serial thread
        msg.type = IpcMsgType.IpcMsgType_ComDisconnect

        # Send command
        self.__ipc_msg_send(msg)        

    # ===============================================================================
    # @brief:   Connect to COM port with last configure settings
    #
    # @return:      void
    # ===============================================================================    
    def __com_port_connect(self):
        msg = IpcMsg()

        # Connect with pre-exsisting COM port settings
        msg.type    = IpcMsgType.IpcMsgType_ComConnect
        msg.payload = None

        # Send command
        self.__ipc_msg_send(msg)         

    # ===============================================================================
    # @brief:   Re-connect to COM port with the same settings
    #
    # @param[in]:   reconnect_pause - Time pause between connect-reconnect cmd
    # @return:      void
    # ===============================================================================    
    def __com_port_reconnect(self, reconnect_pause=2):
        self.__com_port_disconnect()
        time.sleep(reconnect_pause)
        self.__com_port_connect()

    # ===============================================================================
    # @brief:   Get state of upgrade button regardless of COM port actions
    #
    # @return:      upgrade_btn_active - Upgrade button active state
    # ===============================================================================    
    def upgrade_btn_is_active(self):
        return self.upgrade_btn_active

#################################################################################################
##  END OF FILE
#################################################################################################  





