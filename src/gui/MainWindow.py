## Copyright (c) 2025 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       MainWindow.py
## @brief:      Root window of application
## @date:		27.06.2022
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

from gui.CliFrame import CliFrame
from gui.ComFrame import ComFrame
from gui.NavigationFrame import NavigationFrame
from gui.StatusFrame import StatusFrame, GeneralInfoFrame
from gui.ParameterFrame import ParameterFrame
from gui.PlotFrame import PlotFrame
from gui.BootFrame import BootFrame
from gui.GuiCommon import GuiFont, GuiColor

from com.IpcProtocol import IpcMsg, IpcMsgType

from com.Scp import ScpCliMessage, ScpParser

import time

#################################################################################################
##  DEFINITIONS
#################################################################################################

# Fast timer period
#
# Unit: ms
MAIN_WIN_FAST_TIM_PERIOD    = 1

# Slow timer period
#
# Unit: ms
MAIN_WIN_SLOW_TIM_PERIOD    = 2500

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
# @brief:   Main Window 
#
# ===============================================================================
class MainWindow():

    def __init__(self, ver, rx_queue, tx_queue): 
        
        # Create master window
        self.master_win = tk.Tk()

        # Initialize frames
        self.__init_frames()

        # Init menu bar
        #self.__init_menu_bar()

        # Configure layout
        self.master_win.columnconfigure(1, weight=1)
        self.master_win.rowconfigure(1, weight=1)

        # Change icon & name
        self.master_win.title("Configuration tool")
        #self.master_win.iconbitmap("D:/Personal/C_embedded/utc/new/gui/logo/c_logo.ico")    # TODO: Make it relative!!!

        # Set general info
        self.gen_info_frame.sw_ver_label["text"] = "Software Version %s" % ver

        # Maximize window
        self.master_win.state('zoomed')
        
        # Change default style of widgets
        self.__change_table_style()

        # IPC queue
        self.__rx_q = rx_queue
        self.__tx_q = tx_queue
        self.com_rx_buf = ""

        # Connection status
        self.__connection_status = False
        self.__connection_port = None
        self.__connection_baud = None

        # =============================================================================================
        # IPC Command Function Table
        # Specified here actions for received messages via IPC mechanism
        # NOTE: Following functions will be executed within MAIN_WIN_FAST_PERIOD time! Make
        #       sure that function execution will not cosume more time!!!    
        self.__cmd_table = {    IpcMsgType.IpcMsgType_ComRefresh :      self.__ipc_refresh_cmd,
                                IpcMsgType.IpcMsgType_ComConnect :      self.__ipc_connect_cmd,  
                                IpcMsgType.IpcMsgType_ComDisconnect :   self.__ipc_disconnect_cmd,  
                                IpcMsgType.IpcMsgType_ComRxFrame :      self.__ipc_rx_frame_cmd,  
                                IpcMsgType.IpcMsgType_ComRxBinary :     self.__ipc_rx_binary_cmd,  
                                IpcMsgType.IpcMsgType_ComTxFrame :      self.__ipc_tx_frame_cmd,  
        }
        # =============================================================================================

        # Start fast & slow loop cyclic functions
        self.__fast_hndl()
        self.__slow_hndl()

        # De-activate connection related widgets
        self.__deactivate_widgets()

        self.scpParser = ScpParser()

        # Run GUI
        self.run()


    # ===============================================================================
    # @brief:   Initialize all frames
    #
    # @return: void
    # ===============================================================================    
    def __init_frames(self):

        # Create frames
        self.nav_frame      = NavigationFrame(self.master_win, btn_callbacks=[self.__nav_btn_com_action, self.__nav_btn_cli_action, self.__nav_btn_par_action, self.__nav_btn_plot_action, self.__nav_btn_boot_action])
        self.status_frame   = StatusFrame(self.master_win)
        self.gen_info_frame = GeneralInfoFrame(self.master_win)
        self.cli_frame      = CliFrame(self.master_win, btn_callbacks=[self.__cli_btn_enter])
        self.com_frame      = ComFrame(self.master_win, btn_callbacks=[self.__com_btn_connect])
        self.par_frame      = ParameterFrame(self.master_win, btn_callbacks=[self.__par_com_request])
        self.plot_frame     = PlotFrame(self.master_win, import_callback=self.__file_import_callback)
        self.boot_frame     = BootFrame(self.master_win, self.__ipc_send_msg)

        # Layout
        self.nav_frame.grid(        column=0, row=1, sticky=tk.E+tk.W+tk.N+tk.S, rowspan=2,     padx=0, pady=0    )
        self.status_frame.grid(     column=0, row=2, sticky=tk.E+tk.W+tk.N+tk.S, columnspan=2,  padx=0, pady=0    )
        self.gen_info_frame.grid(   column=0, row=0, sticky=tk.E+tk.W+tk.N+tk.S, columnspan=2,  padx=0, pady=0    )
        #self.cli_frame.grid(        column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S,                padx=0, pady=0    )    # Hide that frame
        #self.par_frame.grid(        column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S,                padx=0, pady=0    )    # Hide that frame
        #self.plot_frame.grid(       column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S,                padx=0, pady=0    )    # Hide that frame
        self.com_frame.grid(        column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S,                padx=0, pady=0    )
        
        self.nav_frame.btn_com.set_active(1)
        self.nav_frame.btn_cli.set_active(0)
        self.nav_frame.btn_par.set_active(0)
        self.nav_frame.btn_plot.set_active(0)
        self.nav_frame.btn_boot.set_active(0)

    # Leave for future improvements
    def __init_menu_bar(self):
        self.menu = tk.Menu(self.master_win)
        self.master_win.config(menu=self.menu)

        file_menu = tk.Menu(self.menu)
        self.menu.add_cascade( label="Project", menu=file_menu )
        
        file_menu.add_command( label="Save", command=None )
        file_menu.add_command( label="Load", command=None )

        self.menu.add_cascade( label="Terminal" )
        self.menu.add_cascade( label="Help" )


    # ===============================================================================
    # @brief:   Change main window to communication settings frame
    #
    # @return: void
    # ===============================================================================
    def __nav_btn_com_action(self):
        self.cli_frame.grid_forget()
        self.par_frame.grid_forget()
        self.plot_frame.grid_forget()
        self.boot_frame.grid_forget()
        self.com_frame.grid(column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=0)

        self.nav_frame.btn_com.set_active(1)
        self.nav_frame.btn_cli.set_active(0)
        self.nav_frame.btn_par.set_active(0)
        self.nav_frame.btn_plot.set_active(0)
        self.nav_frame.btn_boot.set_active(0)
  
    # ===============================================================================
    # @brief:   Change main window to command line interface frame
    #
    # @return: void
    # ===============================================================================
    def __nav_btn_cli_action(self):
        self.com_frame.grid_forget()
        self.par_frame.grid_forget()
        self.plot_frame.grid_forget()
        self.boot_frame.grid_forget()
        self.cli_frame.grid(column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=0)
        
        # Focus on command entry
        self.cli_frame.cmd_entry_focus(None)

        self.nav_frame.btn_com.set_active(0)
        self.nav_frame.btn_cli.set_active(1)
        self.nav_frame.btn_par.set_active(0)
        self.nav_frame.btn_plot.set_active(0)
        self.nav_frame.btn_boot.set_active(0)
      
    # ===============================================================================
    # @brief:   Change main window to device parameter frame
    #
    # @return: void
    # ===============================================================================
    def __nav_btn_par_action(self):
        self.com_frame.grid_forget()
        self.cli_frame.grid_forget()
        self.plot_frame.grid_forget()
        self.boot_frame.grid_forget()
        self.par_frame.grid(column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=0)     

        self.nav_frame.btn_com.set_active(0)
        self.nav_frame.btn_cli.set_active(0)
        self.nav_frame.btn_par.set_active(1)
        self.nav_frame.btn_plot.set_active(0) 
        self.nav_frame.btn_boot.set_active(0) 

    # ===============================================================================
    # @brief:   Change main window to plot frame
    #
    # @return: void
    # ===============================================================================
    def __nav_btn_plot_action(self):
        self.com_frame.grid_forget()
        self.cli_frame.grid_forget()
        self.par_frame.grid_forget()
        self.boot_frame.grid_forget()
        self.plot_frame.grid(column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=0)      

        self.nav_frame.btn_com.set_active(0)
        self.nav_frame.btn_cli.set_active(0)
        self.nav_frame.btn_par.set_active(0)
        self.nav_frame.btn_plot.set_active(1)
        self.nav_frame.btn_boot.set_active(0)

    # ===============================================================================
    # @brief:   Change main window to bootloader frame
    #
    # @return: void
    # ===============================================================================
    def __nav_btn_boot_action(self):
        self.com_frame.grid_forget()
        self.cli_frame.grid_forget()
        self.par_frame.grid_forget()
        self.par_frame.grid_forget()
        self.boot_frame.grid(column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=0)      

        self.nav_frame.btn_com.set_active(0)
        self.nav_frame.btn_cli.set_active(0)
        self.nav_frame.btn_par.set_active(0)
        self.nav_frame.btn_plot.set_active(0)
        self.nav_frame.btn_boot.set_active(1)

    # ===============================================================================
    # @brief:   Change default table style
    #
    # @return: void
    # ===============================================================================
    def __change_table_style(self):

        # Create a table syle
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0, rowheight=30, font=GuiFont.normal, background=GuiColor.table_bg, foreground=GuiColor.table_fg)
        style.map("mystyle.Treeview", background=[("selected", GuiColor.table_sel_bg)])

        # Heading style
        style.configure("mystyle.Treeview.Heading", font=GuiFont.heading_2_bold, background=GuiColor.sub_1_fg, foreground=GuiColor.sub_1_bg) 

        # Remove table borders
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])

    # ===============================================================================
    # @brief:   Connect button press callback
    #
    # @param[in]:   com     - Selected COM port
    # @param[in]:   baud    - Selected baudrate
    # @return:      void
    # ===============================================================================
    def __com_btn_connect(self, com, baud):
        
        msg = IpcMsg()

        # Connection is not jet established
        if False == self.__connection_status:
            msg.type = IpcMsgType.IpcMsgType_ComConnect
            msg.payload = "%s;%s" % (com, baud)

            # Save connection info (later use for automatic re-connection)
            self.__connection_port = com
            self.__connection_baud = baud

        # Connection is established
        else:

            # Send disconnection reqeust to serial thread
            msg.type = IpcMsgType.IpcMsgType_ComDisconnect

            # Turn off automatic connection
            self.com_frame.auto_con_btn.turn_off()

        # Send command
        self.__ipc_send_msg(msg)

    # ===============================================================================
    # @brief:   Parameter communication request
    #
    #   This callback is raised on parameter frame events that needs 
    #   information from embedded device such as button press.
    #
    # @param[in]:   cmd    - Command to read all parameters
    # @return:      void
    # ===============================================================================
    def __par_com_request(self, cmd):

        # Connected to device
        if True == self.__connection_status:

            # Write command on console
            self.cli_frame.print_pc_cmd(cmd)

            # Append end string termiantion 
            dev_cmd = str(cmd) + MAIN_WIN_COM_STRING_TERMINATION

            # Assemble and send command
            msg = IpcMsg(IpcMsgType.IpcMsgType_ComTxFrame, payload=dev_cmd)
            self.__ipc_send_msg(msg)

            # Update msg tx counter
            self.status_frame.set_tx_count(len(dev_cmd))

    # ===============================================================================
    # @brief:   CLI enter button press callback
    #
    # @param[in]:   cmd - User CLI command
    # @return:      void
    # ===============================================================================
    def __cli_btn_enter(self, cmd):

        # Connected to device
        if True == self.__connection_status:

            # Append end string termiantion 
            dev_cmd = str(cmd) + MAIN_WIN_COM_STRING_TERMINATION

            # Send cmd to serial process
            msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComTxFrame, payload=dev_cmd)
            self.__ipc_send_msg(msg)

            # Update msg tx counter
            self.status_frame.set_tx_count(len(dev_cmd))

    # ===============================================================================
    # @brief:   Send message via IPC
    #
    # @param[in]:   msg - Message to be sended
    # @return:      void
    # ===============================================================================
    def __ipc_send_msg(self, msg):
        self.__tx_q.put(msg)

    # ===============================================================================
    # @brief:   Receive message from IPC
    #  
    # @return:      msg - Received message
    # ===============================================================================
    def __ipc_receive_msg(self):
       return self.__rx_q.get(block=False, timeout=0)

    # ===============================================================================
    # @brief:   Send refresh command via IPC
    #  
    # @return:      void
    # ===============================================================================
    def __send_com_refresh_cmd(self):
        msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComRefresh)
        self.__ipc_send_msg(msg)

    # ===============================================================================
    # @brief:   Slow GUI handler
    # @note:    Period is set with MAIN_WIN_SLOW_TIM_PERIOD define.
    #
    # @return: void
    # ===============================================================================
    def __slow_hndl(self):

        # Reload timer
        self.master_win.after(MAIN_WIN_SLOW_TIM_PERIOD, self.__slow_hndl)

        # Refresh COM port list
        self.__send_com_refresh_cmd()

        # Refresh status frame
        self.status_frame.set_num_of_pars(self.par_frame.param_get_num_of())

    # ===============================================================================
    # @brief:   Fast GUI handler
    # @note:    Period is set with MAIN_WIN_FAST_TIM_PERIOD define.
    #
    # @return: void
    # ===============================================================================
    def __fast_hndl(self):

        # Reload timer
        self.master_win.after(MAIN_WIN_FAST_TIM_PERIOD, self.__fast_hndl) 

        # Take all messages from reception queue
        while self.__rx_q.empty() == False:

            # Get msg from queue (non-blocking)
            msg = self.__ipc_receive_msg()

            # Execute command if supported
            for key in self.__cmd_table.keys():
                if key == msg.type:
                    self.__cmd_table[key](msg.payload)              

    # ===============================================================================
    # @brief:   Response from refresh command to Serial Process via IPC
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_refresh_cmd(self, payload):

        com = []
        desc = []
        com_detected = False

        # Go thru IPC message
        for dev in payload:
            
            # Get com port and description
            com_port = dev["device"]
            com_desc = dev["description"]

            # Check if open port is still present
            if self.__connection_port == com_port:
                com_detected = True

            # Add to table list
            com.append(com_port)
            desc.append(com_desc)

        # Update table
        self.com_frame.com_port_table_clear()
        self.com_frame.com_port_table_set(com, desc)

        # Disconnect if connected port is no longer available
        if False == com_detected and True == self.__connection_status:

            # Send IPC to serial to disconnect
            msg = IpcMsg()
            msg.type = IpcMsgType.IpcMsgType_ComDisconnect
            self.__ipc_send_msg(msg)

        # Automatic re-connection if:
        #       1. Automatic Connection is turned ON
        #   AND 2. No active connection is present
        #   AND 3. Previously connected port is back 
        elif True == com_detected and False == self.__connection_status and True == self.com_frame.auto_con_btn.state:
            
            # Send IPC to serial to connect
            msg = IpcMsg()
            msg.type = IpcMsgType.IpcMsgType_ComConnect
            msg.payload = "%s;%s" % (self.__connection_port, self.__connection_baud)
            self.__ipc_send_msg(msg)

    # ===============================================================================
    # @brief:   Response from connecto command to (Serial Process) via IPC
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_connect_cmd(self, payload):
        
        # Connection is established
        if payload:
            self.__connection_status = True
            
            # Change btn label
            self.com_frame.connect_btn.text("Disconnect")

            # Update status line
            self.status_frame.change_bg_color(GuiColor.status_bg_connected)
            self.status_frame.set_com_status(True)
            self.status_frame.clear_rx_count()
            self.status_frame.clear_tx_count()
            self.status_frame.clear_num_of_pars()
            self.status_frame.clear_err_count()
            self.status_frame.clear_war_count()
            self.status_frame.set_port_baudrate(self.__connection_port, self.__connection_baud)

            # Activate connection related widgets
            self.__activate_widgets()

        # Connection failed
        else:
            pass

    # ===============================================================================
    # @brief:   Response from disconnect command to (Serial Process) via IPC
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_disconnect_cmd(self, payload):
        
        # Disconnection successfull
        if payload:
            self.__connection_status = False
            
            # Change btn label
            self.com_frame.connect_btn.text("Connect")

            # Update status line
            self.status_frame.change_bg_color(GuiColor.status_bg)
            self.status_frame.set_com_status(False)

            # De-activate connection related widgets
            self.__deactivate_widgets()

        # Disconnection failed
        else:
            pass


    # ===============================================================================
    # @brief:   Response from RX frame command to (Serial Process) via IPC
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_rx_frame_cmd(self, payload):
        
        # Is there any answer from embedded device?
        if payload:

            # Append received chars to buffer
            self.com_rx_buf += str(payload)
            
            # Check for termiantion char
            str_term = str(self.com_rx_buf).find(MAIN_WIN_COM_STRING_TERMINATION)

            # Termination char founded
            if str_term >= 0:

                # Parsed response from device
                dev_resp = self.com_rx_buf[:str_term]

                # Print till terminator
                if "ERR" in dev_resp:
                    self.cli_frame.print_err(dev_resp)
                    self.status_frame.set_err_count(1)
                elif "WAR" in dev_resp:
                    self.cli_frame.print_war(dev_resp)
                    self.status_frame.set_war_count(1)
                else:
                    self.cli_frame.print_normal(dev_resp)

                # Copy the rest of string for later process
                # Note: Copy without termiantor
                self.com_rx_buf = self.com_rx_buf[str_term+len(MAIN_WIN_COM_STRING_TERMINATION):]

                # Parameter parser
                # Note: Ignore raw traffic for parameter parser
                if not self.get_raw_msg(dev_resp):
                    self.par_frame.dev_msg_parser(dev_resp)
                
                # Raw trafic for plotting purposes
                else:
                    pass # TODO: Provide that data to plotter...

        # Update msg rx counter
        self.status_frame.set_rx_count(len(payload))

    # ===============================================================================
    # @brief:   Response from RX frame BINARY command to (Serial Process) via IPC
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_rx_binary_cmd(self, payload):

        # Handle received message
        self.boot_frame.msg_receive_cb(payload)

    # ===============================================================================
    # @brief:   Response from TX frame command (to Serial Process) via IPC
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_tx_frame_cmd(self, payload):
        pass

    # ===============================================================================
    # @brief:   Activate connection related widgets
    #
    # @return: void
    # ===============================================================================
    def __activate_widgets(self):
        
        # Cli frame
        self.cli_frame.cmd_entry.config(state=tk.NORMAL)
        self.cli_frame.clear_btn.config(state=tk.NORMAL)

        # Parameter frame
        self.par_frame.read_all_btn.config(state=tk.NORMAL)
        self.par_frame.store_all_btn.config(state=tk.NORMAL)

        # Boot frame
        self.boot_frame.browse_btn.config(state=tk.NORMAL)

        if self.boot_frame.upgrade_btn_is_active():
            self.boot_frame.update_btn.config(state=tk.NORMAL)

    # ===============================================================================
    # @brief:   Deactivate connection related widgets
    #
    # @return: void
    # ===============================================================================
    def __deactivate_widgets(self):
        
        # Cli frame
        self.cli_frame.cmd_entry.config(state=tk.DISABLED)
        self.cli_frame.clear_btn.config(state=tk.DISABLED)

        # Parameter frame
        self.par_frame.read_all_btn.config(state=tk.DISABLED)
        self.par_frame.store_all_btn.config(state=tk.DISABLED)

        # Boot frame
        self.boot_frame.browse_btn.config(state=tk.DISABLED)
        self.boot_frame.update_btn.config(state=tk.DISABLED)

    # ===============================================================================
    # @brief:   File imported callback
    #
    # @param[in]:   file_name   - Measurement data file name
    # @return:      void
    # ===============================================================================
    def __file_import_callback(self, file_name):
        self.status_frame.set_meas_file( file_name )

    # ===============================================================================
    # @brief:   Check if device message is raw traffic
    #
    # @note     Raw is being determinate based on latter. If any latter is inside
    #           expection string than this string is not raw traffic.
    #
    # @param[in]:   dev_msg     - Message from embedded device
    # @return:      raw         - Raw message flag
    # ===============================================================================
    def get_raw_msg(self, dev_msg):
        raw = True

        for ch in dev_msg:
            if ch.isalpha():
                raw = False
                break

        return raw

    # ===============================================================================
    # @brief:   Start GUI engine
    # @note:    This function is blocking until app is closed!
    #
    # @return: void
    # ===============================================================================
    def run(self):
        self.master_win.mainloop()

        # Send command to end serial thread
        msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComFinished)
        self.__ipc_send_msg(msg)


#################################################################################################
##  END OF FILE
#################################################################################################  





