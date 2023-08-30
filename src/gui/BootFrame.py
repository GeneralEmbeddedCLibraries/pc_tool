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

from com.IpcProtocol import IpcMsg, IpcMsgType

#################################################################################################
##  DEFINITIONS
#################################################################################################

# Enter bootloader command (to application)
BOOT_ENTER_BOOT_CMD         = "enter_boot"

# Enter bootloader success command
BOOT_ENTER_BOOT_RSP_CMD     = "OK, Entering bootloader..."

# Serial command end symbol
MAIN_WIN_COM_STRING_TERMINATION = "\r\n"

#################################################################################################
##  FUNCTIONS
#################################################################################################

#################################################################################################
##  CLASSES
#################################################################################################   


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

        #self.boot_frame.rowconfigure(0, weight=1)
        #self.boot_frame.columnconfigure(0, weight=100)

        # Progress bar
        self.progress_bar   = ttk.Progressbar( self.boot_frame, orient='horizontal', mode='indeterminate', style='text.Horizontal.TProgressbar' )
        self.progress_text  = tk.Label(self.boot_frame, text="0%", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.file_text      = tk.Label(self.boot_frame, text="", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.browse_btn     = NormalButton( self.boot_frame, "Browse", command=self.__browse_btn_press)
        self.update_btn     = NormalButton( self.boot_frame, "Update", command=self.__update_btn_press)

        self.update_btn.config(state=tk.DISABLED)

        # Start moving progress bar
        # TODO: Remove when not needed...
        #self.progress_bar.start()

        # Self frame layout
        self.frame_label.grid(      column=0, row=0,                sticky=tk.W,                padx=20, pady=10 )
        self.boot_frame.grid(       column=0, row=1,                sticky=tk.W+tk.N+tk.S+tk.E, padx=20, pady=10 )

        # Boot frame layout
        self.browse_btn.grid(       column=0, row=0,                sticky=tk.W,                    padx=20, pady=10    )
        self.update_btn.grid(       column=0, row=1,                sticky=tk.W,                    padx=20, pady=10    )
        self.progress_bar.grid(     column=0, row=2, columnspan=2,  sticky=tk.W+tk.N+tk.S+tk.E,     padx=20, pady=10    )
        self.progress_text.grid(    column=2, row=2,                sticky=tk.W,                    padx=20, pady=10    )

        
        self.file_text.grid(      column=2, row=1,                sticky=tk.W,                   padx=20, pady=10    )
        tk.Label(self.boot_frame, text="File path:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg).grid( column=1, row=1, sticky=tk.W, padx=20, pady=10    )


    def __browse_btn_press(self):

        # Select file to visualize
        self.fw_file =  tk.filedialog.askopenfilename(initialdir=self.fw_file, title = "Select firmware image",filetypes = (("Binary files","*.bin"),("all files","*.*")))
        
        # File selected
        if self.fw_file:

            print("Selected FW image: %s" % self.fw_file )

            self.update_btn.config(state=tk.NORMAL)
            self.file_text["text"] = self.fw_file



    def __update_btn_press(self):  

        self.__send_connect_cmd()

        self.__send_prepare_cmd( 1, 1, 1 )

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


    def __send_connect_cmd(self):

        # Assmemble connect command
        connect_cmd = [ 0xB0, 0x07, 0x00, 0x00, 0x2B, 0x10, 0x00, 0x9B ]

        # Send connect command
        self.msg_send_bin( connect_cmd )


    def __send_prepare_cmd(self, fw_size, fw_ver, hw_ver):

        # Assmemble connect command
        prepare_cmd = [ 0xB0, 0x07, 0x0C, 0x00, 0x2B, 0x20, 0x00, 0x00 ]

        # Get FW size
        #prepare_cmd.append( fw_size )
        for byte in struct.pack('I', int(fw_size)):
            prepare_cmd.append( byte )

        # Get FW version
        for byte in struct.pack('I', int(fw_ver)):
            prepare_cmd.append( byte )

        # Get HW version
        for byte in struct.pack('I', int(hw_ver)):
            prepare_cmd.append( byte )

        # Calculate crc
        crc = self.__calc_crc8( [0x0C, 0x00] )  # Lenght
        crc ^= self.__calc_crc8( [0x2B] )  # Source
        crc ^= self.__calc_crc8( [0x20] )  # Command
        crc ^= self.__calc_crc8( [0x00] )  # Status
        crc ^= self.__calc_crc8( [fw_size, fw_ver, hw_ver] )

        # Set CRC
        prepare_cmd[7] = crc

        # Send connect command
        self.msg_send_bin( prepare_cmd )  

        print("Prepare cmd: %s" % prepare_cmd )

    # ===============================================================================
    # @brief:   Message received callback
    #
    # @note     Come here either ASCII or binary character is received!
    #
    # @return:      void
    # ===============================================================================
    def msg_receive_cb(self, payload):
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





#################################################################################################
##  END OF FILE
#################################################################################################  





