## Copyright (c) 2022 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       CliFrame.py
## @brief:      Command Line Inteface frame
## @note:       Input/Output message streams for communication with the device
## @date:		27.06.2022
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from dataclasses import dataclass
import datetime
import tkinter as tk
from tkinter import scrolledtext

from gui.GuiCommon import GuiFont, GuiColor, NormalButton, SwitchButton, AddRemoveButton

#################################################################################################
##  DEFINITIONS
#################################################################################################

# Maximum number of allowed shortcuts
CLI_MAX_NUM_OF_SHORTCUTS = 10


#################################################################################################
##  FUNCTIONS
#################################################################################################


#################################################################################################
##  CLASSES
#################################################################################################   

# ===============================================================================
#
# @brief:   Cli frame
#
# ===============================================================================
class CliFrame(tk.Frame):

    def __init__(self, parent, btn_callbacks, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.main_bg)

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # Init widgets
        self.__init_widgets()

        # Store button callbacks
        self.btn_callbacks=btn_callbacks

        # Last commands
        self.__cmd_trace = []
        self.__cmd_trace_ptr = 0


    # ===============================================================================
    # @brief:   Initialize widgets
    #
    # @return:      void
    # ===============================================================================
    def __init_widgets(self):

        # Create info label
        self.frame_label = tk.Label(self, text="Command Line Interface", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)

        # Create the textbox
        self.console_text = scrolledtext.ScrolledText(self, width=40, height=10, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, font=GuiFont.cli, relief=tk.FLAT, state=tk.DISABLED)

        # Change text color based on source
        self.console_text.tag_config("pc",      background=GuiColor.sub_1_bg,   foreground=GuiColor.console_pc_fg,   font=GuiFont.cli_bold   )
        self.console_text.tag_raise("sel")
        self.console_text.tag_config("device",  background=GuiColor.sub_1_bg,   foreground=GuiColor.console_dev_fg,  font=GuiFont.cli        )
        self.console_text.tag_raise("sel")
        self.console_text.tag_config("err",     background=GuiColor.sub_1_bg,   foreground=GuiColor.console_err_fg,  font=GuiFont.cli        )
        self.console_text.tag_raise("sel")
        self.console_text.tag_config("war",     background=GuiColor.sub_1_bg,   foreground=GuiColor.console_war_fg,  font=GuiFont.cli        )
        self.console_text.tag_raise("sel")

        # Command entry
        self.cmd_entry = tk.Entry(self, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg, font=GuiFont.normal, borderwidth=0, disabledbackground=GuiColor.main_bg, disabledforeground=GuiColor.main_fg)

        # Bind entry actions
        self.cmd_entry.bind("<Return>", self.__entry_send)
        self.cmd_entry.bind("<Up>", self.__entry_up_arrow)
        self.cmd_entry.bind("<Down>", self.__entry_down_arrow)
        self.cmd_entry.bind("<FocusIn>", self.__entry_focus_in)
        self.cmd_entry.bind("<FocusOut>", self.__entry_focus_out)
        self.console_text.bind("<Button-1>", self.cmd_entry_focus)
        self.bind("<Button-1>", self.cmd_entry_focus)

        # Buttons
        self.clear_btn = NormalButton(self, text="Clear", command=self.__clear_btn_click)

        # Cli settings
        self.cfg = CliConfig(self)
        self.cfg.add_switch(id=CliCfgOpt.Timestamp,     text="Show message timestamp",      initial_state=False)
        self.cfg.add_switch(id=CliCfgOpt.MsgSrc,        text="Show message source",         initial_state=False)
        self.cfg.add_switch(id=CliCfgOpt.Freeze,        text="Freeze console print",        initial_state=False)
        self.cfg.add_switch(id=CliCfgOpt.RawTraffic,    text="Show raw message traffic",    initial_state=False)
        #self.cfg.add_switch(id=CliCfgOpt.LogToFile,     text="Log to file",                 initial_state=False)

        # Cli shortcuts
        self.shortcut = CliShortcut(self, self.cmd_entry, self.__entry_send)

        # Add deafult shortcuts
        self.shortcut.add("Help", "help")
        self.shortcut.add("Reset", "reset")
        self.shortcut.add("Show parameters", "par_print")

        # TODO: Remove only tesing
        self.shortcut.add("Streaming ON", "status_start")
        self.shortcut.add("Streaming OFF", "status_stop")
        # TODO END: 

        # Self frame layout
        self.frame_label.grid(  column=0, row=0,                sticky=tk.W,                   padx=20, pady=10     )
        self.console_text.grid( column=0, row=1, rowspan=3,     sticky=tk.E+tk.W+tk.N+tk.S,    padx=10, pady=0      )
        self.cmd_entry.grid(    column=0, row=4,                sticky=tk.E+tk.W+tk.S+tk.N,    padx=10, pady=10     )
        self.clear_btn.grid(    column=1, row=4,                sticky=tk.E+tk.W+tk.S,         padx=10, pady=10     )
        
        self.cfg.grid(          column=1, row=1, rowspan=1,     sticky=tk.E+tk.W+tk.N+tk.S,    padx=0, pady=0       )
        self.shortcut.grid(     column=1, row=2, rowspan=1,     sticky=tk.E+tk.W+tk.N+tk.S,    padx=5, pady=27       )

      
    # ===============================================================================
    # @brief:   Clear console button press
    #
    # @return:      void
    # ===============================================================================
    def __clear_btn_click(self):
        self.console_text.configure(state=tk.NORMAL)
        self.console_text.delete(1.0, 'end')
        self.console_text.configure(state=tk.DISABLED)

    # ===============================================================================
    # @brief:   Send command entry
    #
    # @note:    This function is bind to Enter press!
    #
    # @return: void
    # ===============================================================================  
    def __entry_send(self, e):
 
        # Entry is enabled
        if tk.NORMAL == self.cmd_entry["state"]:

            # Assemble command
            cmd = str(self.cmd_entry.get())

            # Print PC command
            self.print_pc_cmd(cmd)

            # Raise callback
            self.btn_callbacks[0](cmd)

            # Clear entry
            self.cmd_entry.delete(0, 'end')

            # Remove command if already in trace
            if cmd in self.__cmd_trace:
                self.__cmd_trace.remove(cmd)
            
            # Add command at the end of line
            self.__cmd_trace.append(cmd)

            # Reset trace pointer
            self.__cmd_trace_ptr = 0

    # ===============================================================================
    # @brief:   Arrow down pressed on entry focus
    #
    #       Gets oldest command from command trace
    #
    # @param[in]:   e - Event
    # @return:      void
    # ===============================================================================     
    def __entry_up_arrow(self, e):

        # Is there any command in trace
        if len(self.__cmd_trace) > 0:

            if self.__cmd_trace_ptr < len(self.__cmd_trace):
                self.__cmd_trace_ptr += 1
            
            # Clear entry
            self.cmd_entry.delete(0, tk.END)

            # Display lastest command send
            self.cmd_entry.insert(0, self.__cmd_trace[-self.__cmd_trace_ptr])

    # ===============================================================================
    # @brief:   Arrow down pressed on entry focus
    #
    #       Gets oldest command from command trace
    #
    # @param[in]:   e - Event
    # @return:      void
    # ===============================================================================              
    def __entry_down_arrow(self, e):

        # Is there any command in trace
        if len(self.__cmd_trace) > 0:
            
            if self.__cmd_trace_ptr > 1:
                self.__cmd_trace_ptr -= 1

            # Clear entry
            self.cmd_entry.delete(0, tk.END)

            # Display oldest command send
            self.cmd_entry.insert(0, self.__cmd_trace[-self.__cmd_trace_ptr])

    # ===============================================================================
    # @brief:   Command entry focus out event
    #
    # @param[in]:   e - Event
    # @return:      void
    # ===============================================================================       
    def __entry_focus_out(self, e):
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, "Put command here...")

    # ===============================================================================
    # @brief:   Command entry focus in event
    #
    # @param[in]:   e - Event
    # @return:      void
    # ===============================================================================    
    def __entry_focus_in(self, e):
        self.cmd_entry.delete(0, tk.END)

    # ===============================================================================
    # @brief:   Focus on command entry
    #
    # @param[in]:   e - Event
    # @return:      void
    # ===============================================================================  
    def cmd_entry_focus(self, e):
        self.cmd_entry.focus()

    # ===============================================================================
    # @brief:   Print string with specific tag on console
    #
    # @param[in]:   text    - String to be printed
    # @param[in]:   tag     - Tag
    # @return:      void
    # ===============================================================================  
    def __print_to_console(self, text, tag):

        # Freeze console
        if not self.cfg.get_state(CliCfgOpt.Freeze):

            # Raw message check
            if not self.__get_raw_msg(text) or self.cfg.get_state(CliCfgOpt.RawTraffic):

                # Unlock text box
                self.console_text.configure(state=tk.NORMAL)

                # Append timestamp
                if self.cfg.get_state(CliCfgOpt.Timestamp):
                    _datetime = datetime.datetime.now()
                    datetime_text = "(%02d.%02d.%04d  %02d:%02d:%02d.%03d)" % (_datetime.day, _datetime.month, _datetime.year, _datetime.hour, _datetime.minute, _datetime.second, round(_datetime.microsecond/1000)) + "    "

                    # Insert send char and command
                    self.console_text.insert(tk.END, datetime_text, tag)

                # Add message source
                if self.cfg.get_state(CliCfgOpt.MsgSrc):
                    if tag == "pc":
                        self.console_text.insert(tk.END, "(TX <---)    ", tag)
                    else:
                        self.console_text.insert(tk.END, "(RX --->)    ", tag)  

                # Insert send char and command
                self.console_text.insert(tk.END, text + "\n", tag)
                
                # Lock text box back
                self.console_text.configure(state=tk.DISABLED)
                
                # Scrool with latest text
                self.console_text.see(tk.END)

    # ===============================================================================
    # @brief:   Print PC command
    #
    # @param[in]:   cmd     - PC command string
    # @return:      void
    # ===============================================================================  
    def print_pc_cmd(self, cmd):
        self.__print_to_console(str(cmd), "pc")

    # ===============================================================================
    # @brief:   Print device normal response
    #
    # @param[in]:   text    - Device response
    # @return:      void
    # ===============================================================================   
    def print_normal(self, text):
        self.__print_to_console(str(text), "dev")

    # ===============================================================================
    # @brief:   Print device error response
    #
    # @param[in]:   text    - Device response
    # @return:      void
    # ===============================================================================   
    def print_err(self, text):
        self.__print_to_console(str(text), "err")

    # ===============================================================================
    # @brief:   Print device warning response
    #
    # @param[in]:   text    - Device response
    # @return:      void
    # ===============================================================================   
    def print_war(self, text):
        self.__print_to_console(str(text), "war")

    # ===============================================================================
    # @brief:   Check if device message is raw traffic
    #
    # @note     Raw msg is being determinate based on first char. If number that
    #           msg is potencially raw. If futhermore no alphabetic is found inside
    #           msg then it is actually raw! 
    #
    # @param[in]:   dev_msg     - Message from embedded device
    # @return:      raw         - Raw message flag
    # ===============================================================================
    def __get_raw_msg(self, dev_msg):

        if dev_msg[0].isdigit():
            for ch in dev_msg:
                if ch.isalpha():
                    return False
            return True
        else:
            return False



# ===============================================================================
#
#  @brief:   CLI Configurations Options
#
# ===============================================================================  
@dataclass
class CliCfgOpt:
    Timestamp:  int = 0
    RawTraffic: int = 1
    LogToFile:  int = 2
    MsgSrc:     int = 3
    Freeze:     int = 4


# ===============================================================================
#
#  @brief:   CLI Configurations
#
# ===============================================================================  
class CliConfig():

    # ===============================================================================
    # @brief:   Create CLI configuration frame
    #
    # @param[in]:   root    - Parent window
    # @return:      void
    # ===============================================================================   
    def __init__(self, root):

        # Create frame
        self.frame = tk.Frame(root, bg=GuiColor.main_bg, padx=0, pady=0)

        # List of switches
        self.switches = []

    # ===============================================================================
    # @brief:   Add configuration switch
    #
    # @param[in]:   id              - Switch ID
    # @param[in]:   text            - Text to describe the option switch
    # @param[in]:   initial_state   - Startup state
    # @return:      void
    # ===============================================================================   
    def add_switch(self, id, text, initial_state=False):

        # Create switch    
        sw = CliConfigSwitch(self.frame, initial_state=initial_state, text=text)
    
        # Add to grid
        sw.grid(column=0, row=len(self.switches)+1, sticky=tk.E+tk.W+tk.N+tk.S, padx=5, pady=5)

        # Create dictionary
        sw_dict = { "id": id, "sw": sw }

        # Add to global space
        self.switches.append( sw_dict )

    # ===============================================================================
    # @brief:   Get state from configuration switch
    #
    # @param[in]:   id      - Switch ID
    # @return:      void
    # ===============================================================================   
    def get_state(self, id):

        for sw in self.switches:
            if sw["id"] == id:
                return sw["sw"].state()

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)


# ===============================================================================
#
#  @brief:   Boolean (ON/OFF) option for CLI configuration
#
# ===============================================================================  
class CliConfigSwitch():

    # ===============================================================================
    # @brief:   Boolean CLI configuration option
    #
    # @param[in]:   root            - Root window
    # @param[in]:   text            - Name of configuration
    # @param[in]:   initial_state   - Initial state of configuration
    # @return:      void
    # ===============================================================================  
    def __init__(self, root, text, initial_state):
        
        # Settings selection
        self.frame = tk.Frame(root, bg=GuiColor.sub_1_bg, padx=0, pady=0)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        # Setting button & label
        self.btn = SwitchButton(root=self.frame, initial_state=initial_state)
        self.label = tk.Label(self.frame, text=text, font=GuiFont.normal_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.sub_1_fg)

        # Settings frame layout
        self.label.grid(    column=0, row=0, sticky=tk.W, padx=10, pady=0    )
        self.btn.grid(      column=1, row=0, sticky=tk.E, padx=0, pady=0     )

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)

    # ===============================================================================
    # @brief:   Get swtich button state
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================   
    def state(self):
        return self.btn.state


# ===============================================================================
#
#  @brief:   CLI Shortcuts
#
# ===============================================================================  
class CliShortcut():

    # ===============================================================================
    # @brief:   Shortcut constructor
    #
    # @param[in]:   root                - Parent window 
    # @param[in]:   cmd_entry           - Command entry from parent window
    # @param[in]:   cmd_entry_send      - Send command function 
    # @return:      void
    # ===============================================================================  
    def __init__(self, root, cmd_entry, cmd_entry_send):

        # Create frame
        self.frame = tk.Frame(root, bg=GuiColor.sub_1_bg, padx=0, pady=0)
        self.frame.rowconfigure(100, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.label = tk.Label(self.frame, text="Shortcuts", font=GuiFont.heading_2_bold, bg=GuiColor.sub_1_bg, fg=GuiColor.main_fg)
        self.label.grid(column=0, row=0, sticky=tk.W+tk.N, padx=5, pady=10 )

        self.add_btn = AddRemoveButton(self.frame, text="+", command=self.__add_btn_pressed)
        self.add_btn.grid(column=1, row=0, sticky=tk.W+tk.N, padx=0, pady=0,)

        # Shortcuts
        self.shortcut = []
        self.btn_cnt = 0

        # Store command entry information 
        self.cmd_entry = cmd_entry
        self.cmd_entry_send = cmd_entry_send

    # ===============================================================================
    # @brief:   Add shortcut
    #
    # @param[in]:   name        - Name of shortcut
    # @param[in]:   cmd_string  - String command to be sended to embedded device
    # @return:      void
    # ===============================================================================  
    def add(self, name, cmd_string):

        if len(self.shortcut) < CLI_MAX_NUM_OF_SHORTCUTS:

            # Get lowest button row
            btn_row = len(self.shortcut) + 1

            bnt_id = int(self.btn_cnt)
            
            # Create switch    
            btn = NormalButton(self.frame, text=name, command=lambda: self.__shortcut_pressed(bnt_id))
            del_btn = AddRemoveButton(self.frame, text="-", command=lambda: self.__remove(bnt_id))

            # Put to grid
            btn.grid(column=0, row=btn_row, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=5 )
            del_btn.grid(column=1, row=btn_row, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=5 )

            # Create shortcut data
            shortcut = { "id": bnt_id, "cmd": cmd_string, "btn": btn, "del_btn": del_btn, "row": btn_row }

            # Append to list
            self.shortcut.append( shortcut )
            self.btn_cnt += 1

            if len(self.shortcut) >= CLI_MAX_NUM_OF_SHORTCUTS:
                self.add_btn.config(state=tk.DISABLED)

    # ===============================================================================
    # @brief:   Remove shortcut
    #
    # @param[in]:   btn_id  - Button ID 
    # @return:      void
    # ===============================================================================  
    def __remove(self, btn_id):

        deleted_row = 0

        for s in self.shortcut:
            if s["id"] == btn_id:
                
                # Remove buttons
                s["btn"].destroy()
                s["del_btn"].destroy()

                # Remove short from shortlist
                self.shortcut.remove(s)

                # If one shortcut was destroyed that must be place for another one
                self.add_btn.config(state=tk.NORMAL)

                # Store deleted row
                deleted_row = s["row"]

                break

        # Shift all buttons below that row for one up
        for s in self.shortcut:
            if s["row"] > deleted_row:
                
                # Move shortcut one up
                new_row = int(s["row"]-1)

                # Store new row
                s["row"] = new_row

                # Move shortcut one up
                s["btn"].grid(      column=0, row=new_row, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=5 )
                s["del_btn"].grid(  column=1, row=new_row, sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=5 )

    # ===============================================================================
    # @brief:   Shortcut button pressed actions
    #
    # @param[in]:   btn_id  - Button ID 
    # @return:      void
    # ===============================================================================  
    def __shortcut_pressed(self, btn_id):

        for s in self.shortcut:
            if s["id"] == btn_id:
                self.cmd_entry.delete(0, 'end')
                self.cmd_entry.insert(0, s["cmd"])
                self.cmd_entry_send(None)

    # ===============================================================================
    # @brief:   Put button on grid
    #
    # @param[in]:   args, kwargs - Arguments
    # @return:      void
    # ===============================================================================  
    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)

    # ===============================================================================
    # @brief:   Shortcut button add pressed action
    #
    # @return:      void
    # ===============================================================================  
    def __add_btn_pressed(self):
        
        # Disable add button
        self.add_btn.config(state=tk.DISABLED)

        # Pop shortcut configuration menu
        name, cmd_string = ShortcutConfig()

        # Check that shortcut has some value
        if "" == name.get() or "" == cmd_string.get():
            pass
        else:
            self.add(name.get(), cmd_string.get())

        # Enable add button back
        if len(self.shortcut) < CLI_MAX_NUM_OF_SHORTCUTS:
            self.add_btn.config(state=tk.NORMAL)

# ===============================================================================
# @brief:   TopWindow for Shortcut Add 
#
# @return:      name    - Command name in form of tk.StringVar
# @return:      cmd     - Command value in form of tk.StringVar
# ===============================================================================  
def ShortcutConfig():

    # Create top level window
    top_win = tk.Toplevel()
    top_win.config(bg=GuiColor.main_bg)
    top_win.rowconfigure(2, weight=1)
    top_win.columnconfigure(1, weight=1)
    top_win.resizable(False, False)

    # Center popup window in the middle of the screen
    screen_width = top_win.winfo_screenwidth()
    screen_height = top_win.winfo_screenheight()
    x = screen_width/2 - 200
    y = screen_height/2 - 200
    top_win.geometry("+%d+%d" % (x, y))

    # Title and description
    title_label = tk.Label(top_win, text="Add New Shortcut", font=GuiFont.heading_2_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
    desc_label  = tk.Label(top_win, text="Create button shortcut in order to save time\ntyping the same command to CLI again and again.      ", font=GuiFont.normal_italic_small, bg=GuiColor.main_bg, fg=GuiColor.main_fg, justify=tk.LEFT)

    # Entry values
    name = tk.StringVar()
    cmd = tk.StringVar()
    bind = tk.StringVar()

    # Shortcut option frame
    opt_frame = tk.Frame(top_win, bg=GuiColor.sub_1_bg)
    opt_frame.columnconfigure(1,weight=1)

    # Labels
    name_label = tk.Label(opt_frame, text="Name:",      font=GuiFont.normal, bg=GuiColor.sub_1_bg, fg=GuiColor.main_fg)
    cmd_label = tk.Label(opt_frame, text="  Command:",  font=GuiFont.normal, bg=GuiColor.sub_1_bg, fg=GuiColor.main_fg)

    # Entries
    name_entry = tk.Entry(opt_frame, textvariable=name, bg=GuiColor.sub_1_fg, fg=GuiColor.sub_1_bg, font=GuiFont.normal, borderwidth=0, disabledbackground=GuiColor.main_bg, disabledforeground=GuiColor.main_fg)
    cmd_entry = tk.Entry(opt_frame, textvariable=cmd,   bg=GuiColor.sub_1_fg, fg=GuiColor.sub_1_bg, font=GuiFont.normal, borderwidth=0, disabledbackground=GuiColor.main_bg, disabledforeground=GuiColor.main_fg)

    cmd_entry.bind("<Return>", lambda event: top_win.destroy())

    # Layout
    name_label.grid(    column=0, row=0, sticky=tk.E+tk.N+tk.S,         padx=0, pady=5)
    name_entry.grid(    column=1, row=0, sticky=tk.E+tk.W+tk.N+tk.S,    padx=5, pady=5)
    cmd_label.grid(     column=0, row=1, sticky=tk.E+tk.N+tk.S,         padx=0, pady=5)
    cmd_entry.grid(     column=1, row=1, sticky=tk.E+tk.W+tk.N+tk.S,    padx=5, pady=5)

    # Apply button
    apply_btn = NormalButton(top_win, text="Apply", command=top_win.destroy, width=10)

    # Top level window layout
    title_label.grid(   column=0, row=0,                sticky=tk.W+tk.N+tk.S,      padx=5, pady=5)
    desc_label.grid(    column=0, row=1,                sticky=tk.W+tk.N+tk.S,      padx=5, pady=0)
    opt_frame.grid(     column=0, row=2, columnspan=2,  sticky=tk.E+tk.W+tk.N+tk.S, padx=0, pady=10)
    apply_btn.grid(     column=0, row=3,                sticky=tk.E+tk.N+tk.S,      padx=10, pady=10)

    # Focus on name entry
    name_entry.focus()

    # Wait until destruction of the top window
    top_win.wait_window()

    return (name, cmd)



#################################################################################################
##  END OF FILE
#################################################################################################  





