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
# @brief:   Boot frame
#
# ===============================================================================
class BootFrame(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.main_bg)

        #self.rowconfigure(2, weight=1)
        #self.columnconfigure(0, weight=100)
        #self.columnconfigure(1, weight=1)

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


        # Self frame layout
        self.frame_label.grid(      column=0, row=0,                sticky=tk.W,                   padx=20, pady=10 )


#################################################################################################
##  END OF FILE
#################################################################################################  





