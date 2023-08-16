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

        # Firmware image
        self.fw_file = None

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

        # Progress bar
        self.progress_bar   = ttk.Progressbar( self.boot_frame, orient='horizontal', mode='indeterminate', length=300, style='text.Horizontal.TProgressbar' )
        self.progress_text  = tk.Label(self.boot_frame, text="0%", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.file_text      = tk.Label(self.boot_frame, text="", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.browse_btn     = NormalButton( self.boot_frame, "Browse", command=self.__browse_btn_press)
        self.update_btn     = NormalButton( self.boot_frame, "Update", command=self.__update_btn_press)

        self.update_btn.config(state=tk.DISABLED)

        # Start moving progress bar
        # TODO: Remove when not needed...
        #self.progress_bar.start()

        # Self frame layout
        self.frame_label.grid(      column=0, row=0,                sticky=tk.W,                   padx=20, pady=10 )
        self.boot_frame.grid(       column=0, row=1,                sticky=tk.W,                   padx=20, pady=10 )

        # Boot frame layout
        self.progress_bar.grid(     column=0, row=0,                sticky=tk.W,                   padx=20, pady=10    )
        self.progress_text.grid(    column=1, row=0,                sticky=tk.W,                   padx=20, pady=10    )
        self.browse_btn.grid(       column=2, row=0,                sticky=tk.W,                   padx=20, pady=10    )
        self.update_btn.grid(       column=2, row=1,                sticky=tk.W,                   padx=20, pady=10    )
        
        self.file_text.grid(      column=0, row=2,                sticky=tk.W,                   padx=20, pady=10    )
        tk.Label(self.boot_frame, text="File path:", font=GuiFont.normal_italic, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg).grid( column=0, row=1, sticky=tk.W, padx=20, pady=10    )


    def __browse_btn_press(self):

        # Select file to visualize
        self.fw_file =  tk.filedialog.askopenfilename(initialdir=self.fw_file, title = "Select firmware image",filetypes = (("Binary files","*.bin"),("all files","*.*")))
        
        # File selected
        if self.fw_file:

            print("Selected FW image: %s" % self.fw_file )

            self.update_btn.config(state=tk.NORMAL)
            self.file_text["text"] = self.fw_file[:20]



    def __update_btn_press(self):  

        self.update_btn.text( "Cancel" )



#################################################################################################
##  END OF FILE
#################################################################################################  





