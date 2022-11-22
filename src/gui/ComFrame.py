## Copyright (c) 2022 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       ComFrame.py
## @brief:      Communication frame window 
## @note:       Display virtual COM ports.        
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

from gui.GuiCommon import GuiFont, GuiColor, NormalButton
from com.IpcProtocol import IpcMsg, IpcMsgType

#################################################################################################
##  DEFINITIONS
#################################################################################################


#################################################################################################
##  FUNCTIONS
#################################################################################################


#################################################################################################
##  CLASSES
#################################################################################################   
 


class ComFrame(tk.Frame):

    def __init__(self, parent, btn_callbacks, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.main_bg)

        # List of COM/baudrates
        self.com_port_list = [""]
        self.baudrate_list = ["9600", "115200", "1M", "Custom"]

        # Init widgets
        self.__init_widgets()

        #self.rowconfigure(1, weight=1)
        self.rowconfigure(5, weight=2)
        self.rowconfigure(6, weight=5)
        self.columnconfigure(0, weight=1)

        # Store button callbacks
        self.btn_callbacks=btn_callbacks


    # ===============================================================================
    # @brief:   Initialize widgets
    #
    # @return:      void
    # ===============================================================================
    def __init_widgets(self):

        # Create info label
        self.frame_label = tk.Label(self, text="Communication Settings", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)

        # Settings selection
        self.settings_frame = tk.Frame(self, bg=GuiColor.sub_1_bg, padx=20, pady=20)

        self.com_port_sel_label = tk.Label(self.settings_frame, text="COM port", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.baudrate_sel_label = tk.Label(self.settings_frame, text="Baudrate", font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)
        self.com_port_sel = tk.Entry(self.settings_frame, font=GuiFont.normal, bg=GuiColor.sub_1_fg, fg=GuiColor.sub_1_bg, borderwidth=0, width=8)
        self.baudrate_sel = tk.Entry(self.settings_frame, font=GuiFont.normal, bg=GuiColor.sub_1_fg, fg=GuiColor.sub_1_bg, borderwidth=0, width=8)
        
        # Default values
        self.baudrate_sel.insert(0, "115200")

        # Entry validation
        port_vcmd = (self.register(self.__com_port_entry_validate), '%P')
        self.com_port_sel.config(validate='key', validatecommand=port_vcmd)
        baudrate_vcmd = (self.register(self.__baudrate_entry_validate), '%P')
        self.baudrate_sel.config(validate='key', validatecommand=baudrate_vcmd)

        # Buttons
        self.connect_btn = NormalButton(self.settings_frame, text="Connect", command=self.__connect_btn_click)

        # Create a table
        self.com_port_title = tk.Label(self, text="List of available COM ports", font=GuiFont.heading_2_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.main_fg)
        
        # Create table
        self.com_port_table = ttk.Treeview(self, style="mystyle.Treeview", selectmode="none")

        # Left mouse click bindings
        self.com_port_table.bind("<Button-1>", self.__left_m_click_table)
        self.com_port_table.bind("<Double-Button-1>", self.__left_m_double_click_table)

        # Define columns
        self.com_port_table["columns"] = ("#", "Name", "Desc")
        self.com_port_table.column("#0",                    width=0,                     stretch=tk.NO  )
        self.com_port_table.column("#",     anchor=tk.W,    width=50,   minwidth=50,     stretch=tk.NO  )
        self.com_port_table.column("Name",  anchor=tk.W,    width=120,  minwidth=120,    stretch=tk.NO  )
        self.com_port_table.column("Desc",  anchor=tk.W                                                 )

        self.com_port_table.heading("#0",text="",anchor=tk.CENTER)
        self.com_port_table.heading("#",text="#",anchor=tk.W)
        self.com_port_table.heading("Name",text="Name",anchor=tk.W)
        self.com_port_table.heading("Desc",text="Description",anchor=tk.W)

        # Self frame layout
        self.frame_label.grid(              column=0, row=0,                sticky=tk.W,                padx=20, pady=10    )
        self.settings_frame.grid(           column=0, row=1, columnspan=2,  sticky=tk.E+tk.W+tk.N+tk.S, padx=10, pady=0    )
        self.com_port_title.grid(           column=0, row=5, columnspan=2,  sticky=tk.E+tk.W+tk.S,      padx=10, pady=0     )
        self.com_port_table.grid(           column=0, row=6, columnspan=2,  sticky=tk.E+tk.W+tk.N+tk.S, padx=10, pady=10    )
        
        # Settings frame layout
        self.com_port_sel_label.grid(       column=0, row=0, sticky=tk.E,   padx=5, pady=5  )
        self.com_port_sel.grid(             column=1, row=0,                padx=5, pady=5  )
        self.baudrate_sel_label.grid(       column=0, row=1, sticky=tk.E,   padx=5, pady=5  )
        self.baudrate_sel.grid(             column=1, row=1,                padx=5, pady=5  )
        self.connect_btn.grid(              column=2, row=1, sticky=tk.W,   padx=30, pady=5 )


    # ===============================================================================
    # @brief:   Connect button press
    #
    # @return:      void
    # ===============================================================================
    def __connect_btn_click(self):
        
        # Get selected COM and baudrate
        com = self.com_port_sel.get()
        baud = self.baudrate_sel.get()

        # Raise callback
        self.btn_callbacks[0](com, baud)

    # ===============================================================================
    # @brief:   Insert COM and baudrate to table
    #
    # @param[in]:   idx     - Table row 
    # @param[in]:   name    - Name of COM port
    # @param[in]:   desc    - Description of COM port
    # @return:      void
    # ===============================================================================      
    def __com_port_table_insert(self, idx, name, desc):
        if ( idx % 2 == 0 ):
            self.com_port_table.insert(parent='',index='end',iid=idx,text='',values=(str(idx), str(name), str(desc)), tags=('even', 'simple'))
        else:
            self.com_port_table.insert(parent='',index='end',iid=idx,text='',values=(str(idx), str(name), str(desc)), tags=('odd', 'simple'))

        self.com_port_table.tag_configure('even', background=GuiColor.table_fg, foreground=GuiColor.table_bg)
        
        # TODO: Check why discrepancie between computers
        #self.com_port_table.tag_configure('odd', background=GuiColor.table_fg_even, foreground=GuiColor.table_bg_even)
        self.com_port_table.tag_configure('odd', background=GuiColor.table_fg_even, foreground=GuiColor.table_bg)

    # ===============================================================================
    # @brief:   Set COM port table
    #
    # @param[in]:   names   - List of COM port names
    # @param[in]:   desc    - List of COM port description
    # @return:      void
    # ===============================================================================     
    def com_port_table_set(self, names, desc):
        for idx, name in enumerate(names):
            self.__com_port_table_insert(idx, str(name), str(desc[idx]))

    # ===============================================================================
    # @brief:   Clear COM port table
    #
    # @return:      void
    # ===============================================================================   
    def com_port_table_clear(self):
        for i in self.com_port_table.get_children():
            self.com_port_table.delete(i)

    # ===============================================================================
    # @brief:   Copy COM value to entry label
    #
    # @param[in]:   e   - Bind event
    # @return:      void
    # ===============================================================================   
    def __left_m_click_table(self, e):
        
        # Get clicked table row
        table_row = self.com_port_table.identify_row(e.y)

        if table_row:

            # Get COM port name
            com_name = self.com_port_table.item(table_row)["values"][1]

            # Set to label
            self.com_port_sel.delete(0, tk.END)
            self.com_port_sel.insert(0, com_name)

    # ===============================================================================
    # @brief:   Connect to selected com port
    #
    # @param[in]:   e   - Bind event
    # @return:      void
    # ===============================================================================  
    def __left_m_double_click_table(self, e):

        # Copy com port info
        self.__left_m_click_table(e)

        # Connect
        self.__connect_btn_click()

    # ===============================================================================
    # @brief:   Entry validation for COM port selection. This function is triggered
    #           on any keyboard press.
    #
    # @param[in]:   value - Value of key pressed
    # @return:      void
    # ===============================================================================  
    def __com_port_entry_validate(self, value):
        pass

    # ===============================================================================
    # @brief:   Entry validation for baudrate selection. This function is triggered
    #           on any keyboard press.
    #
    # @param[in]:   value - Value of key pressed
    # @return:      void
    # ===============================================================================  
    def __baudrate_entry_validate(self, value):
        if value.isdigit() or value == "":
            if len(value) < 9:
                return True
            else:
                return False
        else:
            return False


#################################################################################################
##  END OF FILE
#################################################################################################  




