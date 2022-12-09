## Copyright (c) 2022 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       GuiCommon.py
## @brief:      Common GUI syles and appearance
## @date:		01.07.2022
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

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
#  @brief:   List of GUI colors
#
# ===============================================================================  
@dataclass
class GuiColor():

    # Main frame
    main_bg: str = "#1e1e1e"
    main_fg: str = "#d4d4d4"

    # Sub frames
    sub_1_bg: str = "#303031"
    sub_1_fg: str = "#cccccc"

    # Normal button
    btn_bg: str = "#0e639c"
    btn_fg: str = "#ffffff"
    btn_hoover_bg: str = "#1177bb"

    # Navigation button
    nav_btn_bg: str = "#16825d"
    nav_btn_fg: str = "#ffffff"
    nav_btn_hoover_bg: str = "#1a996c"

    # Swich button
    sw_on_btn_bg:           str = "#00e600"
    sw_on_btn_fg:           str = "#000000"
    sw_on_btn_hoover_bg:    str = "#4dff4d"
    sw_off_btn_bg:          str = "#e60000"
    sw_off_btn_fg:          str = "#000000"
    sw_off_btn_hoover_bg:   str = "#ff4d4d"

    # Table
    table_bg: str = "#303031"
    table_fg: str = "#cccccc"
    table_sel_bg: str = "#404040"
    table_ok_bg: str = "#4dff4d"
    table_fail_bg: str = "#ff4d4d"
    table_warn_bg: str = "#e6b800"

    table_bg_even: str = "#d8d8d9"
    table_fg_even: str = "#e8f4fd"

    table_bg_delimiter: str = "#2ca0ed"
    table_fg_delimiter: str = "#ffffff"

    # Status line
    status_bg: str = "#2691d9"
    status_fg: str = "#ffffff"
    status_bg_connected: str = "#53c653"

    # Console colors
    console_pc_fg: str = "#7dbde8"
    console_dev_fg: str = "#16825d"
    console_err_fg: str = "red"
    console_war_fg: str = "yellow"

    # Add button
    add_btn_hoover_bg:    str = "#4c4c4d"

# ===============================================================================
#
#  @brief:   List of GUI fonts
#
# ===============================================================================  
@dataclass
class GuiFont():

    # Title
    title: list = ("Calibri", 26)

    # Headings
    heading_1: list = ("Calibri", 18)
    heading_1_bold: list = ("Calibri", 18, "bold")
    heading_2: list = ("Calibri", 16)
    heading_2_bold: list = ("Calibri", 16, "bold")

    # Normal text
    normal: list = ("Calibri", 14)
    normal_bold: list = ("Calibri", 14, "bold")
    normal_italic: list = ("Calibri", 14, "italic")

    # Normal Small text
    normal_small: list = ("Calibri", 12)
    normal_bold_small: list = ("Calibri", 12, "bold")
    normal_italic_small: list = ("Calibri", 12, "italic")

    # Button
    btn: list = ("Calibri", 14, "bold")

    # Navigation button
    nav_btn: list = ("Calibri", 16, "bold")

    # Status
    status: list = ("Calibri", 11, "normal")

    # Command line text
    cli: list = ("Consolas", 14)
    cli_bold: list = ("Consolas", 14, "bold")
    cli_italic: list = ("Consolas", 14, "italic")


# ===============================================================================
#
#  @brief:   Custom implementation of NORMAL button
#
# ===============================================================================  
class NormalButton():

    # ===============================================================================
    # @brief:   MyButton constructor
    #
    # @param[in]:   root        - Root window
    # @param[in]:   text        - Button text
    # @param[in]:   command     - Callback function registration on press event
    # @return:      void
    # ===============================================================================  
    def __init__(self, root, text=None, command=None, width=20):

        # Create tkinter button
        self.btn = tk.Button(root, text=text, font=GuiFont.btn, bg=GuiColor.btn_bg, fg=GuiColor.btn_fg, activebackground=GuiColor.btn_bg, activeforeground=GuiColor.btn_fg, relief=tk.FLAT, borderwidth=0, width=width, command=command)

        # Bind button actions
        self.btn.bind("<Enter>", self.__btn_enter)
        self.btn.bind("<Leave>", self.__btn_leave)

    # ===============================================================================
    # @brief:   Get current button label
    #
    # @return:      text of button
    # ===============================================================================  
    def text(self):
        return str(self.btn["text"])

    # ===============================================================================
    # @brief:   Change button text
    #
    # @param[in]:   text    - New text for button
    # @return:      void
    # ===============================================================================  
    def text(self, text):
        self.btn["text"] = str(text)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid(self, *args, **kwargs):
        self.btn.grid(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid_forget(self, *args, **kwargs):
        self.btn.grid_forget(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def pack(self, *args, **kwargs):
        self.btn.pack(*args, **kwargs)

    # ===============================================================================
    # @brief:   Destroy widget
    #
    # @return:      void
    # ===============================================================================  
    def destroy(self):
        self.btn.destroy()

    # ===============================================================================
    # @brief:   Post-init configurations
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def config(self, *args, **kwargs):
        self.btn.config(*args, **kwargs)

    # ===============================================================================
    # @brief:   Connect button callback on mouse entry
    #
    # @param[in]:   e   - Event
    # @return:      void
    # ===============================================================================  
    def __btn_enter(self, e):
        self.btn["bg"] = GuiColor.btn_hoover_bg

    # ===============================================================================
    # @brief:   Connect button callback on mouse exit
    #
    # @param[in]:   e   - Event
    # @return: void
    # ===============================================================================  
    def __btn_leave(self, e):
        self.btn["bg"] = GuiColor.btn_bg


# ===============================================================================
#
#  @brief:   Custom implementation of NAVIGATION button
#
# ===============================================================================  
class NavigationButton():

    # ===============================================================================
    # @brief:   MyButton constructor
    #
    # @param[in]:   root        - Root window
    # @param[in]:   text        - Button text
    # @param[in]:   command     - Callback function registration on press event
    # @return:      void
    # ===============================================================================  
    def __init__(self, root, text=None, command=None):

        # Create tkinter button
        self.btn = tk.Button(root, text=text, font=GuiFont.nav_btn, bg=GuiColor.nav_btn_bg, fg=GuiColor.nav_btn_fg, activebackground=GuiColor.nav_btn_bg, activeforeground=GuiColor.nav_btn_fg, borderwidth=0, relief=tk.FLAT, width=5, command=command)
        
        # Bind button actions
        self.btn.bind("<Enter>", self.__btn_enter)
        self.btn.bind("<Leave>", self.__btn_leave)

    # ===============================================================================
    # @brief:   Get current button label
    #
    # @return:      text of button
    # ===============================================================================  
    def text(self):
        return str(self.btn["text"])

    # ===============================================================================
    # @brief:   Change button text
    #
    # @param[in]:   text    - New text for button
    # @return:      void
    # ===============================================================================  
    def text(self, text):
        self.btn["text"] = str(text)

    # ===============================================================================
    # @brief:   Post-init configurations
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def config(self, *args, **kwargs):
        self.btn.config(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid(self, *args, **kwargs):
        self.btn.grid(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def pack(self, *args, **kwargs):
        self.btn.pack(*args, **kwargs)

    # ===============================================================================
    # @brief:   Destroy widget
    #
    # @return:      void
    # ===============================================================================  
    def destroy(self):
        self.btn.destroy()

    # ===============================================================================
    # @brief:   Connect button callback on mouse entry
    #
    # @param[in]:   e   - Event
    # @return:      void
    # ===============================================================================  
    def __btn_enter(self, e):
        self.btn["bg"] = GuiColor.nav_btn_hoover_bg

    # ===============================================================================
    # @brief:   Connect button callback on mouse exit
    #
    # @param[in]:   e   - Event
    # @return: void
    # ===============================================================================  
    def __btn_leave(self, e):
        self.btn["bg"] = GuiColor.nav_btn_bg


# ===============================================================================
#
#  @brief:   Custom implementation of SWITCH button
#
# ===============================================================================  
class SwitchButton():

    # ===============================================================================
    # @brief:   MyButton constructor
    #
    # @param[in]:   root        - Root window
    # @param[in]:   text        - Button text
    # @param[in]:   command     - Callback function registration on press event
    # @return:      void
    # ===============================================================================  
    def __init__(self, root, initial_state=False):

        # Switch button state
        self.state = initial_state

        # Create tkinter button
        self.btn = tk.Button(root, text="", font=GuiFont.btn, borderwidth=0, relief=tk.FLAT, width=5, command=self.__btn_pressed)
        
        # Update appearance
        self.__update_appear(self.state)

        # Bind button actions
        self.btn.bind("<Enter>", self.__btn_enter)
        self.btn.bind("<Leave>", self.__btn_leave)

    # ===============================================================================
    # @brief:   Get current button label
    #
    # @return:      text of button
    # ===============================================================================  
    def text(self):
        return str(self.btn["text"])

    # ===============================================================================
    # @brief:   Change button text
    #
    # @param[in]:   text    - New text for button
    # @return:      void
    # ===============================================================================  
    def text(self, text):
        self.btn["text"] = str(text)

    # ===============================================================================
    # @brief:   Post-init configurations
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def config(self, *args, **kwargs):
        self.btn.config(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid(self, *args, **kwargs):
        self.btn.grid(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid_forget(self, *args, **kwargs):
        self.btn.grid_forget(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def pack(self, *args, **kwargs):
        self.btn.pack(*args, **kwargs)

    # ===============================================================================
    # @brief:   Override switch to OFF state
    #
    # @return:      void
    # ===============================================================================  
    def turn_off(self):
        self.state = False
        self.__update_appear(self.state)

    # ===============================================================================
    # @brief:   Override switch to ON state
    #
    # @return:      void
    # ===============================================================================  
    def turn_on(self):
        self.state = True
        self.__update_appear(self.state)

    # ===============================================================================
    # @brief:   Refresh appearance
    #
    # @param[in]:   state   - State of toggle switch
    # @return:      void
    # ===============================================================================  
    def __update_appear(self, state):
        if state:
            self.text("ON")
            self.btn["bg"]=GuiColor.sw_on_btn_bg
            self.btn["fg"]=GuiColor.sw_on_btn_fg
            self.btn["activebackground"]=GuiColor.sw_on_btn_bg
            self.btn["activeforeground"]=GuiColor.sw_on_btn_fg
        else:
            self.text("OFF")
            self.btn["bg"]=GuiColor.sw_off_btn_bg
            self.btn["fg"]=GuiColor.sw_off_btn_fg
            self.btn["activebackground"]=GuiColor.sw_off_btn_bg
            self.btn["activeforeground"]=GuiColor.sw_off_btn_fg

    # ===============================================================================
    # @brief:   Button pressed event
    #
    # @return:      void
    # ===============================================================================  
    def __btn_pressed(self):

        # Toggle state
        self.state = not self.state

        # Update appearance
        self.__update_appear(self.state)

    # ===============================================================================
    # @brief:   Connect button callback on mouse entry
    #
    # @param[in]:   e   - Event
    # @return:      void
    # ===============================================================================  
    def __btn_enter(self, e):
        if self.state:
            self.btn["bg"] = GuiColor.sw_on_btn_hoover_bg
        else:
            self.btn["bg"] = GuiColor.sw_off_btn_hoover_bg

    # ===============================================================================
    # @brief:   Connect button callback on mouse exit
    #
    # @param[in]:   e   - Event
    # @return: void
    # ===============================================================================  
    def __btn_leave(self, e):
        if self.state:
            self.btn["bg"] = GuiColor.sw_on_btn_bg
        else:
            self.btn["bg"] = GuiColor.sw_off_btn_bg


# ===============================================================================
#
#  @brief:   Custom implementation of AddRemove button
#
# ===============================================================================  
class AddRemoveButton():

    # ===============================================================================
    # @brief:   AddRemove Button constructor
    #
    # @param[in]:   root        - Root window
    # @param[in]:   text        - Button text
    # @param[in]:   command     - Callback function registration on press event
    # @return:      void
    # ===============================================================================  
    def __init__(self, root, text, command=None):

        # Create tkinter button
        self.btn = tk.Button(root, text=text, font=GuiFont.heading_2_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.main_fg, activebackground=GuiColor.sub_1_bg, activeforeground=GuiColor.main_fg, relief=tk.FLAT, borderwidth=0, width=3, command=command)

        # Bind button actions
        self.btn.bind("<Enter>", self.__btn_enter)
        self.btn.bind("<Leave>", self.__btn_leave)   

    # ===============================================================================
    # @brief:   Connect button callback on mouse entry
    #
    # @param[in]:   e   - Event
    # @return:      void
    # ===============================================================================  
    def __btn_enter(self, e):
        self.btn["bg"] = GuiColor.add_btn_hoover_bg

    # ===============================================================================
    # @brief:   Connect button callback on mouse exit
    #
    # @param[in]:   e   - Event
    # @return: void
    # ===============================================================================  
    def __btn_leave(self, e):
        self.btn["bg"] = GuiColor.sub_1_bg

    # ===============================================================================
    # @brief:   Post-init configurations
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def config(self, *args, **kwargs):
        self.btn.config(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid(self, *args, **kwargs):
        self.btn.grid(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid_forget(self, *args, **kwargs):
        self.btn.grid_forget(*args, **kwargs)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def pack(self, *args, **kwargs):
        self.btn.pack(*args, **kwargs)

    # ===============================================================================
    # @brief:   Destroy widget
    #
    # @return:      void
    # ===============================================================================  
    def destroy(self):
        self.btn.destroy()

# ===============================================================================
#
#  @brief:   Custom implementation of Combobox button
#
# ===============================================================================  
class GuiCombobox():

    # ===============================================================================
    # @brief:   Combobox constructor
    #
    # @param[in]:   root        - Root window
    # @param[in]:   options     - Options to show on dropdown of widget
    # @param[in]:   command     - Callback function registration on change event
    # @return:      void
    # ===============================================================================  
    def __init__(self, root, options, command=None, *args, **kwargs):

        """
        # Setup custom style
        style = ttk.Style()
        #style.theme_use('clam')
        style.map('custom.TCombobox', fieldbackground=[("readonly",GuiColor.sub_1_bg)] )
        style.map('custom.TCombobox', foreground=[("readonly",GuiColor.sub_1_fg)] )
        style.map('custom.TCombobox', background =[("readonly",GuiColor.sub_1_bg)] )
        style.map('custom.TCombobox', selectbackground=[("readonly",GuiColor.sub_1_bg)])
        style.map('custom.TCombobox', selectforeground=[("readonly",GuiColor.sub_1_fg)])
        style.map('custom.TCombobox', bordercolor =[("readonly",GuiColor.sub_1_bg)])
        style.map('custom.TCombobox', arrowcolor  =[("readonly",GuiColor.sub_1_fg)])
        style.map('custom.TCombobox', arrowsize   =[("readonly",14)])
        style.map('custom.TCombobox', insertwidth = [("readonly", 0)] )
        style.map('custom.TCombobox', insertcolor  = [("readonly", GuiColor.sub_1_bg)] )
        style.map('custom.TCombobox', lightcolor   = [("readonly", GuiColor.sub_1_bg)] )
        style.map('custom.TCombobox', placeholderforeground    = [("readonly", GuiColor.sub_1_bg)] )
        style.map('custom.TCombobox', postoffset     = [("readonly", 0)] )
        style.map('custom.TCombobox', darkcolor      = [("readonly", GuiColor.sub_1_bg)] )

        # Create widget
        self.combo = ttk.Combobox(root, values=options, style='custom.TCombobox', *args, **kwargs)

        """

        # Create widget
        self.combo = ttk.Combobox(root, values=options, *args, **kwargs)

    # ===============================================================================
    # @brief:   Put combobox on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid(self, *args, **kwargs):
        self.combo.grid(*args, **kwargs)

    # ===============================================================================
    # @brief:   Remove cobobox from grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid_forget(self, *args, **kwargs):
        self.combo.grid_forget(*args, **kwargs)

    # ===============================================================================
    # @brief:   Set combobox selected value
    #
    # @param[in]:   val - Value to select field
    # @return:      void
    # ===============================================================================  
    def set(self, val):
        self.combo.set(val)

    # ===============================================================================
    # @brief:   Set combobox option value
    #
    # @param[in]:   list_of_options - List of options
    # @return:      void
    # =============================================================================== 
    def set_options(self, list_of_options):
        self.combo["values"] = list_of_options

    # ===============================================================================
    # @brief:   Get combobox selected value
    #
    # @return:      currently selected value
    # ===============================================================================  
    def get(self):
        return self.combo.get()

    # ===============================================================================
    # @brief:   Bind combo comand
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def bind(self, *args, **kwargs):
        self.combo.bind(*args, **kwargs)

    # ===============================================================================
    # @brief:   Post-init configurations
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def configure(self, *args, **kwargs):
        self.combo.configure(*args, **kwargs)




#################################################################################################
##  END OF FILE
#################################################################################################  





