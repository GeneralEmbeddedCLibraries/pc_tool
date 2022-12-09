## Copyright (c) 2022 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       StatusFrame.py
## @brief:      Overall application and device status
## @date:		27.06.2022
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
import tkinter as tk

from gui.GuiCommon import GuiFont, GuiColor

#################################################################################################
##  DEFINITIONS
#################################################################################################


#################################################################################################
##  FUNCTIONS
#################################################################################################


#################################################################################################
##  CLASSES
#################################################################################################   

# ===============================================================================
#
# @brief:   Status frame
#
# ===============================================================================
class StatusFrame(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.status_bg)

        # Init widgets
        self.__init_widgets()

        # Transmition statistics
        self.rx_count = 0
        self.tx_count = 0

        # Error/Warning statistics
        self.err_count = 0
        self.war_count = 0


    # ===============================================================================
    # @brief:   Initialize widgets
    #
    # @return:      void
    # ===============================================================================
    def __init_widgets(self):
        
        # Communication status
        self.com_status_label = tk.Label(self, text="Disconnected", font=GuiFont.status, bg=GuiColor.status_bg, fg=GuiColor.status_fg)
        self.port_baud_label = tk.Label(self, text="", font=GuiFont.status, bg=GuiColor.status_bg, fg=GuiColor.status_fg)

        # Communication counters
        self.rx_cnt_label = tk.Label(self, text="Rx 0", font=GuiFont.status, bg=GuiColor.status_bg, fg=GuiColor.status_fg)
        self.tx_cnt_label = tk.Label(self, text="Tx 0", font=GuiFont.status, bg=GuiColor.status_bg, fg=GuiColor.status_fg)
        self.err_cnt_label = tk.Label(self, text="Err 0", font=GuiFont.status, bg=GuiColor.status_bg, fg=GuiColor.status_fg)
        self.war_cnt_label = tk.Label(self, text="War 0", font=GuiFont.status, bg=GuiColor.status_bg, fg=GuiColor.status_fg)

        # Number of device parameters
        self.dev_par_num_label = tk.Label(self, text="#Par 0", font=GuiFont.status, bg=GuiColor.status_bg, fg=GuiColor.status_fg)

        # CPU load
        self.cpu_load_label = tk.Label(self, text="CPU 0%", font=GuiFont.status, bg=GuiColor.status_bg, fg=GuiColor.status_fg)

        # Self frame layout       
        self.rx_cnt_label.pack(         side="left",    padx=10, pady=0 )
        self.tx_cnt_label.pack(         side="left",    padx=10, pady=0 )
        self.err_cnt_label.pack(        side="left",    padx=10, pady=0 )
        self.war_cnt_label.pack(        side="left",    padx=10, pady=0 )
        self.dev_par_num_label.pack(    side="left",    padx=10, pady=0 )
        self.cpu_load_label.pack(       side="left",    padx=10, pady=0 )

        self.com_status_label.pack(     side="right",   padx=10, pady=0 )
        self.port_baud_label.pack(      side="right",   padx=10, pady=0 )
        

    def update(self):
        None

    # ===============================================================================
    # @brief:   Set number of received bytes
    #
    # @param[in]:   cnt     - Number of received bytes
    # @return:      void
    # ===============================================================================
    def set_rx_count(self, cnt):
        self.rx_count += cnt
        self.rx_cnt_label["text"] = "Rx " + str(self.rx_count)

    # ===============================================================================
    # @brief:   Clear number of received bytes
    #
    # @return:      void
    # ===============================================================================
    def clear_rx_count(self):
        self.rx_count = 0
        self.rx_cnt_label["text"] = "Rx " + str(self.rx_count)

    # ===============================================================================
    # @brief:   Set number of transmitted bytes
    #
    # @param[in]:   cnt     - Number of transmited bytes
    # @return:      void
    # ===============================================================================
    def set_tx_count(self, cnt):
        self.tx_count += cnt
        self.tx_cnt_label["text"] = "Tx " + str(self.tx_count)

    # ===============================================================================
    # @brief:   Clear number of transmitted bytes
    #
    # @return:      void
    # ===============================================================================
    def clear_tx_count(self):
        self.tx_count = 0
        self.tx_cnt_label["text"] = "Tx " + str(self.tx_count)

    # ===============================================================================
    # @brief:   Set number of received error messages
    #
    # @param[in]:   cnt     - Number of err msg
    # @return:      void
    # ===============================================================================
    def set_err_count(self, cnt):
        self.err_count += cnt
        self.err_cnt_label["text"] = "Err " + str(self.err_count)

    # ===============================================================================
    # @brief:   Clear number of error messages
    #
    # @return:      void
    # ===============================================================================
    def clear_err_count(self):
        self.err_count = 0
        self.err_cnt_label["text"] = "Err " + str(self.err_count)

    # ===============================================================================
    # @brief:   Set number of received warning messages
    #
    # @param[in]:   cnt     - Number of war msg
    # @return:      void
    # ===============================================================================
    def set_war_count(self, cnt):
        self.war_count += cnt
        self.war_cnt_label["text"] = "War " + str(self.war_count)

    # ===============================================================================
    # @brief:   Clear number of warning messages
    #
    # @return:      void
    # ===============================================================================
    def clear_war_count(self):
        self.war_count = 0
        self.war_cnt_label["text"] = "War " + str(self.war_count)

    # ===============================================================================
    # @brief:   Set communication status
    #
    # @param[in]:   status  - Either Connected or Disconnected
    # @return:      void
    # ===============================================================================
    def set_com_status(self, status):
        if status:
            self.com_status_label["text"] = "Connected"
        else:
            self.com_status_label["text"] = "Disconnected"
            self.set_port_baudrate(None, None)

    # ===============================================================================
    # @brief:   Set connected port name and baudrate
    #
    # @param[in]:   port    - Name of COM port
    # @param[in]:   baud    - Baudrate
    # @return:      void
    # ===============================================================================
    def set_port_baudrate(self, port, baud):
        if port == None or baud == None:
            self.port_baud_label["text"] = ""
        else:
            self.port_baud_label["text"] = "%s %s" % (str(port).upper(), str(baud).upper())

    # ===============================================================================
    # @brief:   Set number of device parameters
    #
    # @param[in]:   num_of_pars - Numer of device parameters
    # @return:      void
    # ===============================================================================
    def set_num_of_pars(self, num_of_pars):
        self.dev_par_num_label["text"] = "#Par %u" % int(num_of_pars)

    # ===============================================================================
    # @brief:   CLear number of device parameters
    #
    # @return:      void
    # ===============================================================================
    def clear_num_of_pars(self):
        self.set_num_of_pars(0)

    # ===============================================================================
    # @brief:   Set average CPU load 
    #
    # @param[in]:   load    - CPU load
    # @return:      void
    # ===============================================================================
    def set_cpu_load(self, load):
        self.cpu_load_label["text"] = "CPU %u%%" % int(load)

    # ===============================================================================
    # @brief:   Change widget background color
    #
    # @param[in]:   color - New color
    # @return:      void
    # ===============================================================================
    def change_bg_color(self, color):
        self.configure(bg=color)
        self.com_status_label["bg"] = color
        self.port_baud_label["bg"] = color
        self.rx_cnt_label["bg"] = color
        self.tx_cnt_label["bg"] = color
        self.err_cnt_label["bg"] = color
        self.war_cnt_label["bg"] = color
        self.dev_par_num_label["bg"] = color
        self.cpu_load_label["bg"] = color







class GeneralInfoFrame(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg="#4c4c4d")

        # Init widgets
        self.__init_widgets()



    def __init_widgets(self):

        # Picture
        #img = ImageTk.PhotoImage(Image.open("D:/Personal/C_embedded/utc/new/gui/logo/c_logo.png"), size=10)
        #img_label = tk.Label(self, image=img)
        
        # Software version label
        self.sw_ver_label = tk.Label(self, bg="#4c4c4d", fg="#d4d4d4", font=("TkHeading", 10, "bold"))
        
        # Set layout
        #img_label.pack(anchor="e")
        self.sw_ver_label.pack(anchor="e")



    def update(self):
        None




#################################################################################################
##  END OF FILE
#################################################################################################  





