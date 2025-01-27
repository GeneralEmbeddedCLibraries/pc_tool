## Copyright (c) 2025 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       NavigationFrame.py
## @brief:      Navigation frame for changing PC tool contex 
## @date:		27.06.2022
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from dataclasses import dataclass
import tkinter as tk

from gui.GuiCommon import GuiFont, GuiColor, NavigationButton


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
# @brief:   Navigation Frame
#
# ===============================================================================
class NavigationFrame(tk.Frame):

    def __init__(self, parent, btn_callbacks, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.sub_1_bg)

        # Store button callbacks
        self.btn_callbacks=btn_callbacks

        # Init widgets
        self.__init_widgets()

    # ===============================================================================
    # @brief:   Initialize widgets
    #
    # @return:      void
    # ===============================================================================
    def __init_widgets(self):

        # Create buttons
        self.btn_com    = NavigationButton(self, text="COM", command=self.btn_callbacks[0])
        self.btn_cli    = NavigationButton(self, text="CLI", command=self.btn_callbacks[1])
        self.btn_par    = NavigationButton(self, text="PAR", command=self.btn_callbacks[2])
        self.btn_plot   = NavigationButton(self, text="PLOT", command=self.btn_callbacks[3])
        self.btn_boot   = NavigationButton(self, text="BOOT", command=self.btn_callbacks[4])
        
        # Setup layout
        self.btn_com.pack(padx=0, pady=10, fill="x")
        self.btn_cli.pack(padx=0, pady=10, fill="x")
        self.btn_par.pack(padx=0, pady=10, fill="x")
        self.btn_plot.pack(padx=0, pady=10, fill="x")
        self.btn_boot.pack(padx=0, pady=10, fill="x")


#################################################################################################
##  END OF FILE
#################################################################################################  




