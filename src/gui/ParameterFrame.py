## Copyright (c) 2022 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       ParameterFrame.py
## @brief:      Device parameters
## @date:		30.06.2022
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

#################################################################################################
##  DEFINITIONS
#################################################################################################

#
#    Device response signal duration
#
#   It highlights table row with green in success or red 
#   after failed to received message
#
# Unit: ms
PAR_FRAME_DEV_RESP_SIGNAL_DUR   = 500


#################################################################################################
##  FUNCTIONS
#################################################################################################


#################################################################################################
##  CLASSES
#################################################################################################   

@dataclass
class Parameter():
    id: int = 0
    name: str = ""
    type: str = ""
    val: str = ""
    max: str = ""
    min: str = ""
    unit: str = ""
    access: str = ""
    nvm: str = ""
    comment: str = ""

@dataclass
class ParameterTable():
    par: Parameter
    row: int = 0


@dataclass
class ParCmd():
    Idle:   int = 0
    Status: str = "par_print"
    Write:  str = "par_set"
    Read:   str = "par_get"
    Store:  str = "par_save"

# ===============================================================================
#
# @brief:   Parameter frame
#
# ===============================================================================
class ParameterFrame(tk.Frame):

    def __init__(self, parent, btn_callbacks, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.main_bg)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Init widgets
        self.__init_widgets()

        # Store button callbacks
        self.btn_callbacks=btn_callbacks

        # Parameter command type
        self.__cmd = ParCmd.Idle
        self.__cmd_par_id = 0
        self.__table_row = 0
        self.__parameters = []

    # ===============================================================================
    # @brief:   Initialize widgets
    #
    # @return:      void
    # ===============================================================================
    def __init_widgets(self):

        # Create info label
        self.frame_label = tk.Label(self, text="Device Parameters", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)

        # Parameter table
        self.par_table = ttk.Treeview(self, style="mystyle.Treeview", selectmode="browse")

        # Define columns
        #self.par_table["columns"] = ("ID", "Name", "Val", "Max", "Min", "Unit", "Type", "Access", "NVM", "Comment" )
        self.par_table["columns"] = ("ID", "Name", "Val", "Max", "Min", "Comment" )
        self.par_table.column("#0",                                 width=0,                        stretch=tk.NO       )
        self.par_table.column("ID",             anchor=tk.W,        width=80,       minwidth=80,    stretch=tk.NO       )
        self.par_table.column("Name",           anchor=tk.W,        width=400,      minwidth=400,   stretch=tk.NO     )
        #self.par_table.column("Type",           anchor=tk.CENTER,   width=75,       minwidth=75,    stretch=tk.NO       )
        self.par_table.column("Val",            anchor=tk.W,        width=100,      minwidth=100,    stretch=tk.NO       )
        self.par_table.column("Max",            anchor=tk.W,        width=100,       minwidth=100,    stretch=tk.NO       )
        self.par_table.column("Min",            anchor=tk.W,        width=100,       minwidth=100,    stretch=tk.NO       )
        #self.par_table.column("Unit",           anchor=tk.CENTER,   width=80,       minwidth=80,    stretch=tk.NO       )
        #self.par_table.column("Access",         anchor=tk.CENTER,   width=110,      minwidth=110,   stretch=tk.NO       )
        #self.par_table.column("NVM",            anchor=tk.CENTER,   width=100,      minwidth=100,   stretch=tk.NO       )
        self.par_table.column("Comment",        anchor=tk.W,        width=200,      minwidth=200,   stretch=tk.YES       )

        self.par_table.heading("#0",            text="",            anchor=tk.CENTER    )
        self.par_table.heading("ID",            text="ID",          anchor=tk.W         )
        self.par_table.heading("Name",          text="Name",        anchor=tk.W         )
        #self.par_table.heading("Type",          text="Type",        anchor=tk.CENTER    )
        self.par_table.heading("Val",           text="Val",         anchor=tk.W         )
        self.par_table.heading("Max",           text="Max",         anchor=tk.W         )
        self.par_table.heading("Min",           text="Min",         anchor=tk.W         )
        #self.par_table.heading("Unit",          text="Unit",        anchor=tk.CENTER    )
        #self.par_table.heading("Access",        text="Access",      anchor=tk.CENTER    )
        #self.par_table.heading("NVM",           text="NVM",         anchor=tk.CENTER    )
        self.par_table.heading("Comment",       text="Comment",     anchor=tk.W         )

        # Left mouse click bindings
        self.par_table.bind("<Button-1>", self.__right_m_click_table)
        self.par_table.bind("<Double-Button-1>", self.__double_right_m_click_table)

        # Buttons
        self.read_btn       = NormalButton(self, text="Read", command=self.__read_btn_click)    
        self.write_btn      = NormalButton(self, text="Write", command=self.__write_btn_click)
        self.read_all_btn   = NormalButton(self, text="Read All", command=self.__read_all_btn_click)    
        self.store_all_btn  = NormalButton(self, text="Store All", command=self.__store_all_btn_click)

        # Parameter value
        self.value_label = tk.Label(self, text="Parameter Value", font=GuiFont.heading_2_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.value_entry = tk.Entry(self, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, font=GuiFont.normal, borderwidth=0, disabledbackground=GuiColor.main_bg, disabledforeground=GuiColor.main_fg)

        # Entry validation
        vcmd = (self.register(self.__value_entry_validate), '%P')
        self.value_entry.config(validate='key', validatecommand=vcmd)

        # Bind entry actions
        self.value_entry.bind("<Return>", self.__value_entry_enter)

        # Self frame layout
        self.frame_label.grid(      column=0, row=0,                    sticky=tk.W,                    padx=20, pady=10    )
        self.par_table.grid(        column=0, row=1, columnspan=4,      sticky=tk.W+tk.E+tk.N+tk.S,     padx=10, pady=10    )

        self.read_btn.grid(         column=0, row=2,                    sticky=tk.W+tk.N+tk.S,          padx=10, pady=10    )
        self.read_all_btn.grid(     column=0, row=3,                    sticky=tk.W+tk.N+tk.S,          padx=10, pady=10    )

        self.value_label.grid(      column=1, row=2,                    sticky=tk.E+tk.N+tk.S,          padx=0, pady=10    )
        self.value_entry.grid(      column=2, row=2,                    sticky=tk.W+tk.E+tk.N+tk.S,     padx=10, pady=10    )

        self.write_btn.grid(        column=3, row=2,                    sticky=tk.W+tk.E+tk.S,          padx=10, pady=10    )
        self.store_all_btn.grid(    column=3, row=3,                    sticky=tk.W+tk.E+tk.N,          padx=10, pady=10    )
        
    # ===============================================================================
    # @brief:   Insert parameter to table
    #
    # @param[in]:   idx     - Table row 
    # @param[in]:   par     - Device parameter
    # @return:      void
    # ===============================================================================
    def __par_table_insert(self, idx, par):

        if ( idx % 2 == 0 ):
            self.par_table.insert(parent='',index='end',iid=idx,text='', values=(str(par.id), str(par.name), str(par.val), str(par.max), str(par.min), str(par.comment)), tags=('even', 'simple'))
        else:
            self.par_table.insert(parent='',index='end',iid=idx,text='', values=(str(par.id), str(par.name), str(par.val), str(par.max), str(par.min), str(par.comment)), tags=('odd', 'simple'))

        self.par_table.tag_configure('even', background=GuiColor.table_fg, foreground=GuiColor.table_bg)
        
        self.par_table.tag_configure('odd', background=GuiColor.table_fg_even, foreground=GuiColor.table_bg)

    # ===============================================================================
    # @brief:   Insert delimiter to parameter table
    #
    # @param[in]:   idx     - Table row 
    # @param[in]:   name    - Description of deliiter
    # @return:      void
    # ===============================================================================
    def __par_table_insert_delimiter(self, idx, name):
        self.par_table.insert(parent='',index='end',iid=idx,text='', values=("",name), tags=('delimiter', 'simple'))
        self.par_table.tag_configure('delimiter', background=GuiColor.table_bg_delimiter, foreground=GuiColor.table_fg_delimiter, font=GuiFont.heading_2_bold)

    # ===============================================================================
    # @brief:   Clear parameter table
    #
    # @return:      void
    # ===============================================================================   
    def __par_table_clear(self):
        for i in self.par_table.get_children():
            self.par_table.delete(i)

    # ===============================================================================
    # @brief:   Change parameter data in GUI table
    #
    # @param[in]:   row - Table row
    # @param[in]:   par - Parameter values
    # @return:      void
    # ===============================================================================   
    def __par_table_change_par_data(self, row, par):
        self.par_table.item(row, values=(str(par.id), str(par.name), str(par.val), str(par.max), str(par.min), str(par.comment)))

    # ===============================================================================
    # @brief:   Get table row from parameter ID
    #
    # @param[in]:   row - Table row
    # @return:      id  - Parameter id or None if parameter is not in that row
    # ===============================================================================   
    def __par_table_get_id_by_row(self, row):        
        for p in self.__parameters:
            if int(row) == int(p.row):
                return p.par.id

    # ===============================================================================
    # @brief:   Get parameter by ID
    #
    # @param[in]:   id  - Parameter ID
    # @return:      par - Parameter object
    # ===============================================================================   
    def __par_table_get_par_by_id(self, id):
        for p in self.__parameters:
            if id == p.par.id:
                return p.par

    # ===============================================================================
    # @brief:   Get current value of parameter by ID
    #
    # @param[in]:   id  - Parameter ID
    # @return:      val - Current parameter value
    # ===============================================================================   
    def __param_get_value(self, id):
        for p in self.__parameters:
            if id == p.par.id:
                return float(p.par.val)

    # ===============================================================================
    # @brief:   Get current value of parameter by ID
    #
    # @param[in]:   id  - Parameter ID
    # @return:      max_val - Current parameter value
    # ===============================================================================   
    def __param_get_max_value(self, id):
        for p in self.__parameters:
            if id == p.par.id:
                return float(p.par.max)

    # ===============================================================================
    # @brief:   Get current value of parameter by ID
    #
    # @param[in]:   id  - Parameter ID
    # @return:      max_val - Current parameter value
    # ===============================================================================   
    def __param_get_min_value(self, id):
        for p in self.__parameters:
            if id == p.par.id:
                return float(p.par.min)

    # ===============================================================================
    # @brief:   Set current value of parameter by ID
    #
    # @param[in]:   id  - Parameter ID
    # @param[in]:   val - New parameter value
    # @return:      void
    # ===============================================================================       
    def __param_set_value(self, id, val):
        for p in self.__parameters:
            if id == p.par.id:
                p.par.val = val

    # ===============================================================================
    # @brief:   Set number of parameters
    #
    # @return:      number of device parameters
    # ===============================================================================   
    def param_get_num_of(self):
        return len(self.__parameters)

    # ===============================================================================
    # @brief:   Entry validation for parameter value write. This function is triggered
    #           on any keyboard press.
    #
    # @param[in]:   value - Value of key pressed
    # @return:      void
    # ===============================================================================  
    def __value_entry_validate(self, value):
        if value == "" or value == "-":
            return True
        else:
            if len(value) < 10:
                try:
                    float(value)
                    return True
                except:
                    return False
            else:
                return False

    # ===============================================================================
    # @brief:   Read button press
    #
    # @return:      void
    # ===============================================================================
    def __read_btn_click(self):

        # Get selected table row
        if self.par_table.selection():
            table_row = self.par_table.selection()[0]
        else:
            table_row = None

        # Check if any selected
        if table_row:
            
            # Search for parameter ID
            self.__cmd_par_id = self.__par_table_get_id_by_row(table_row)

            # Par ID founded
            if self.__cmd_par_id is not None:

                # Read parameter
                self.__cmd = ParCmd.Read

                # Raise callback for command send
                self.btn_callbacks[0](self.__cmd + " " + str(self.__cmd_par_id))

    # ===============================================================================
    # @brief:   Read all button press
    #
    # @return:      void
    # ===============================================================================
    def __read_all_btn_click(self):
    
        # Read status of all parameters
        self.__cmd = ParCmd.Status

        # Raise callback for command send
        self.btn_callbacks[0](self.__cmd)

    # ===============================================================================
    # @brief:   Write button press
    #
    # @return:      void
    # ===============================================================================
    def __write_btn_click(self):

        # Get selected table row
        if self.par_table.selection():
            table_row = self.par_table.selection()[0]
        else:
            table_row = None

        # Check if any selected
        if table_row:
            
            # Search for parameter ID
            self.__cmd_par_id = self.__par_table_get_id_by_row(table_row)

            # Par ID founded
            if self.__cmd_par_id is not None:

                # Get inputed value
                val_str = str(self.value_entry.get()).replace(",", ".") 
                val = float(val_str)
                
                # Get parameter limit
                val_max = self.__param_get_max_value( self.__cmd_par_id )
                val_min = self.__param_get_min_value( self.__cmd_par_id )

                # Check if within boundaries
                if val <= val_max and val >= val_min: 

                    # Write parameter
                    self.__cmd = ParCmd.Write

                    # Assemble command
                    
                    dev_cmd = self.__cmd + " " + str(self.__cmd_par_id) + "," + val_str

                    # Raise callback for command send
                    self.btn_callbacks[0](dev_cmd)

                # Invalid parameter value
                else:
                    self.__par_table_signal_warning()

    # ===============================================================================
    # @brief:   Store all button press
    #
    # @return:      void
    # ===============================================================================
    def __store_all_btn_click(self):
        #TODO: 
        pass

    # ===============================================================================
    # @brief:   Single right click on table action
    #
    #       Has the same actions as if clicking on reading button!
    #
    # @param[in]:   e   - Event
    # @return: void
    # ===============================================================================  
    def __right_m_click_table(self, e):
        
        iid = self.par_table.identify_row(e.y)
        if iid:
            
            val = self.__param_get_value(self.__par_table_get_id_by_row(iid))
        
            # Update value entry
            self.value_entry.focus()
            self.value_entry.delete(0, tk.END)
            self.value_entry.insert(0, val)
    
    # ===============================================================================
    # @brief:   Double right click on table action
    #
    #       Has the same actions as if clicking on reading button!
    #
    # @param[in]:   e   - Event
    # @return: void
    # ===============================================================================  
    def __double_right_m_click_table(self, e):
        self.__read_btn_click()

    # ===============================================================================
    # @brief:   Value enter to write to device event
    #
    #       Has the same actions as if clicking on write button!
    #
    # @param[in]:   e   - Event
    # @return: void
    # ===============================================================================  
    def __value_entry_enter(self, e):
        self.__write_btn_click()

    # ===============================================================================
    # @brief:   Signal device read/write parameter operation as success
    #
    # @return: void
    # ===============================================================================  
    def __par_table_signal_ok(self):
        style = ttk.Style()
        style.map("mystyle.Treeview", background=[("selected", GuiColor.table_ok_bg)], foreground=[("selected", GuiColor.table_bg)])

        # Start clear-up event
        self.after(PAR_FRAME_DEV_RESP_SIGNAL_DUR, self.__par_table_signal_clear) 

    # ===============================================================================
    # @brief:   Signal device read/write parameter operation as error
    #
    # @return: void
    # ===============================================================================  
    def __par_table_signal_error(self):
        style = ttk.Style()
        style.map("mystyle.Treeview", background=[("selected", GuiColor.table_fail_bg)], foreground=[("selected", GuiColor.table_bg)])

        # Start clear-up event
        self.after(PAR_FRAME_DEV_RESP_SIGNAL_DUR, self.__par_table_signal_clear) 

    # ===============================================================================
    # @brief:   Signal device read/write parameter operation as warning
    #
    # @return: void
    # ===============================================================================  
    def __par_table_signal_warning(self):
        style = ttk.Style()
        style.map("mystyle.Treeview", background=[("selected", GuiColor.table_warn_bg)], foreground=[("selected", GuiColor.table_bg)])

        # Start clear-up event
        self.after(PAR_FRAME_DEV_RESP_SIGNAL_DUR, self.__par_table_signal_clear) 

    # ===============================================================================
    # @brief:   Clear signal device read/write parameter operation status
    #
    # @return: void
    # ===============================================================================  
    def __par_table_signal_clear(self):
        style = ttk.Style()
        style.map("mystyle.Treeview", background=[("selected", GuiColor.table_sel_bg)], foreground=[("selected", GuiColor.table_fg)])

    # ===============================================================================
    # @brief:   Device parameter parser
    #
    #   This function is being called after received termination string!
    #
    #   At that stage initial command must be known in order to get contex
    #   of the device answer. Therefore initiated command must be stored
    #   and wait for response here.
    #
    # @param[in]    dev_msg - Parsed response from device
    # @return:      void
    # ===============================================================================      
    def dev_msg_parser(self, dev_msg):
        
        if ParCmd.Idle == self.__cmd:
            pass

        # Response for status command
        elif ParCmd.Status == self.__cmd:

            # Error reponse
            if "ERR" in dev_msg:

                # Init command
                self.__cmd = ParCmd.Idle
                self.__table_row = 0

            else:
                # After all characters are read set cmd to idle
                if ";END" == dev_msg:
                    self.__cmd = ParCmd.Idle
                    self.__table_row = 0

                # Header
                elif ";" == dev_msg[0]:
                    
                    # Clear table
                    self.__par_table_clear()
                    self.__parameters = []

                # Delimiter
                elif ":" == dev_msg[0]:
                    self.__par_table_insert_delimiter(self.__table_row, dev_msg[1:])

                    # Increment table row
                    self.__table_row += 1

                # Parameter info
                else:
                    
                    # Parse parameter info
                    p_id, p_name, p_val, p_def, p_min, p_max, p_comment, p_type, _ = dev_msg.split(",")

                    # Remove space in values
                    p_val = p_val.replace(" ", "")
                    p_def = p_def.replace(" ", "")
                    p_max = p_max.replace(" ", "")
                    p_min = p_min.replace(" ", "")

                    # Create parameter
                    p = Parameter(id=p_id, name=p_name, type=p_type, val=p_val, max=p_max, min=p_min, unit="", comment=p_comment, nvm="")

                    # Put paramter to table
                    self.__par_table_insert(self.__table_row, p)

                    par_to_table = ParameterTable(par=p, row=self.__table_row)
                    self.__parameters.append(par_to_table)

                    # Increment table row
                    self.__table_row += 1

        # Response for write command
        elif ParCmd.Write == self.__cmd:
            self.__cmd = ParCmd.Idle

            # Device response with error
            if "ERR" in dev_msg:
                self.__par_table_signal_error()

            # Device response with success
            elif "OK" in dev_msg:

                style = ttk.Style()
                style.map("mystyle.Treeview", background=[("selected", GuiColor.table_ok_bg)])
                
                # Parse value
                val = dev_msg.split("=")[1]
                
                # Change value in internal paramters data table
                self.__param_set_value(self.__cmd_par_id, val)

                # Update table
                self.__par_table_change_par_data(self.par_table.selection()[0], self.__par_table_get_par_by_id(self.__cmd_par_id))

                # Signal OK
                self.__par_table_signal_ok()
        
        # Reponse for read command
        elif ParCmd.Read == self.__cmd:
            self.__cmd = ParCmd.Idle
            
            # Device response with error
            if "ERR" in dev_msg:
                self.__par_table_signal_error()
            
            # Device response with success
            elif "OK" in dev_msg:

                # Parse value
                val = dev_msg.split("=")[1]
                
                # Change value in internal paramters data table
                self.__param_set_value(self.__cmd_par_id, val)

                # Update table
                self.__par_table_change_par_data(self.par_table.selection()[0], self.__par_table_get_par_by_id(self.__cmd_par_id))

                # Signal OK
                self.__par_table_signal_ok()


        # Reponse for saving command
        elif ParCmd.Store == self.__cmd:
            self.__cmd = ParCmd.Idle

            # TODO: Further actions here...


#################################################################################################
##  END OF FILE
#################################################################################################  





