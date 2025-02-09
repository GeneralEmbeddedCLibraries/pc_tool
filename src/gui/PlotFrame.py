## Copyright (c) 2025 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       PlotFrame.py
## @brief:      Real-time plotting of device parameters
## @date:		08.12.2022
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
import csv

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.animation as animation

#################################################################################################
##  DEFINITIONS
#################################################################################################

# Default timestamp in miliseconds
LOG_FILE_FIXED_TIMESTAMP_MS     = 10000

# File delimiter
LOG_FILE_DELIMITER              = ";"


#################################################################################################
##  FUNCTIONS
#################################################################################################

#################################################################################################
##  CLASSES
#################################################################################################   

# ===============================================================================
#
# @brief:   Plot frame
#
# ===============================================================================
class PlotFrame(tk.Frame):

    def __init__(self, parent, import_callback, *args, **kwargs):
        
        # Import callback
        self.import_callback = import_callback

        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.main_bg)

        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=100)
        self.columnconfigure(1, weight=1)

        # Init widgets
        self.__init_widgets()

    # ===============================================================================
    # @brief:   Initialize widgets
    #
    # @return:      void
    # ===============================================================================
    def __init_widgets(self):

        # File to visualize
        self.meas_file = None

        # Measured data
        self.timestamp = []
        self.meas_signals = []

        # Create info label
        self.frame_label = tk.Label(self, text="Plot Measured Data", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)

        # =============================================================================================
        ## PLOT CONFIGURATIONS
        # =============================================================================================
        plt.style.use(['dark_background'])
        self.PLOT_MAIN_TITLE_SIZE    = 18
        self.PLOT_TITLE_SIZE         = 16
        self.PLOT_AXIS_LABEL_SIZE    = 12

        PLOT_ADJUST_LEFT        = 0.05
        PLOT_ADJUST_BOTTOM      = 0.048
        PLOT_ADJUST_RIGHT       = 0.99
        PLOT_ADJUST_TOP         = 0.99
        PLOT_ADJUST_WSPACE		= 0.2
        PLOT_ADJUST_HSPACE		= 0.08

        # Plot marker
        self.marker = None            

        # Plot frame
        self.plot_frame = tk.Frame(self, bg=GuiColor.main_bg)

        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.fig.tight_layout()

        # Customize layout
        plt.subplots_adjust(left=PLOT_ADJUST_LEFT, right=PLOT_ADJUST_RIGHT, top=PLOT_ADJUST_TOP, bottom=PLOT_ADJUST_BOTTOM, wspace=PLOT_ADJUST_WSPACE, hspace=PLOT_ADJUST_HSPACE)	

        canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                
        # Buttons
        self.import_btn     = NormalButton(self, text="Import", command=self.__import_btn_click,    width=30) 
        self.refresh_btn    = NormalButton(self, text="Refresh", command=self.__refresh_btn_callback,     width=14) 
        self.clear_all_btn  = NormalButton(self, text="Clean All", command=self.__clean_all_btn_callback,    width=14) 

        # Create table
        self.par_plot_table = ttk.Treeview(self, style="mystyle.Treeview", selectmode="browse")
        self.par_plot_table.bind("<Button-3>", self.__left_m_click_table)

        self.par_table_menu = tk.Menu(self.frame_label, tearoff=False, font=GuiFont.normal_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.par_table_menu.add_command(label="Add to plot 1",      command=self.__add_to_plot_1, state="normal")
        self.par_table_menu.add_command(label="Add to plot 2",      command=self.__add_to_plot_2, state="disabled")
        self.par_table_menu.add_command(label="Add to plot 3",      command=self.__add_to_plot_3, state="disabled")
        self.par_table_menu.add_command(label="Add to plot 4",      command=self.__add_to_plot_4, state="disabled")
        self.par_table_menu.add_command(label="Remove from plot",   command=self.__remove_selected_line_from_plot, state="normal")

        # Number of plots
        self.plot_num_label = tk.Label(self, text="Number of plots:", font=GuiFont.normal_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.plot_num_combo = GuiCombobox(self, options=["1","2","3","4"], font=GuiFont.normal_bold, state="disable", width=2, justify="left")
        self.plot_num_combo.set("1")
        self.num_of_plot = 1

        # Timestamp option
        self.timestamp_label = tk.Label(self, text="Timestamp [us]:", font=GuiFont.normal_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.timestamp_entry = tk.Entry(self, font=GuiFont.normal, bg=GuiColor.sub_1_fg, fg=GuiColor.sub_1_bg, borderwidth=0, width=8)
        self.timestamp_entry.insert(0,LOG_FILE_FIXED_TIMESTAMP_MS)

        timestamp_vcmd = (self.register(self.__timestamp_entry_validate), '%P')
        self.timestamp_entry.config(validate='key', validatecommand=timestamp_vcmd)

        # Sample points show
        self.samp_points = ConfigSwitch( self, initial_state=False, text="Show sampled points", command=self.__sample_points_btn_press )
        self.samp_points.config( state="disable" )

        # Bind to change        
        self.plot_num_combo.bind("<<ComboboxSelected>>", self.__plot_num_change)

        # Define columns
        self.par_plot_table["columns"] = ("Par", "Plot")
        self.par_plot_table.column("#0",                    width=0,                    stretch=tk.NO      )
        self.par_plot_table.column("Par",   anchor=tk.W,    width=150,  minwidth=150,   stretch=tk.YES     )
        self.par_plot_table.column("Plot",  anchor=tk.W,    width=50,   minwidth=50,    stretch=tk.NO      )

        self.par_plot_table.heading("#0",   text="",        anchor=tk.CENTER    )
        self.par_plot_table.heading("Par",  text="Par",     anchor=tk.W         )
        self.par_plot_table.heading("Plot", text="Plot",    anchor=tk.CENTER    )

        # Self frame layout
        self.frame_label.grid(      column=0, row=0,                sticky=tk.W,                   padx=20, pady=10 )
        self.plot_frame.grid(       column=0, row=1, rowspan=6,     sticky=tk.W+tk.N+tk.E+tk.S,    padx=0,  pady=0 )
        self.plot_num_label.grid(   column=1, row=1,                sticky=tk.S+tk.E+tk.N,         padx=0,  pady=10 )
        self.plot_num_combo.grid(   column=2, row=1,                sticky=tk.W+tk.S+tk.E+tk.N,    padx=10, pady=10 )
        self.timestamp_label.grid(  column=1, row=2,                sticky=tk.S+tk.E+tk.N,         padx=0,  pady=10 )
        self.timestamp_entry.grid(  column=2, row=2,                sticky=tk.W+tk.S+tk.E+tk.N,    padx=10, pady=10 )        
        self.samp_points.grid(      column=1, row=3, columnspan=2,  sticky=tk.E+tk.W+tk.N+tk.S,    padx=10, pady=10 )

        self.par_plot_table.grid(   column=1, row=4, columnspan=2,  sticky=tk.W+tk.S+tk.E+tk.N,    padx=10, pady=10 )
        self.refresh_btn.grid(      column=1, row=5, columnspan=1,  sticky=tk.W+tk.S+tk.E,         padx=5,  pady=5 )
        self.clear_all_btn.grid(    column=2, row=5, columnspan=1,  sticky=tk.W+tk.S+tk.E,         padx=5,  pady=5 )
        self.import_btn.grid(       column=1, row=6, columnspan=2,  sticky=tk.W+tk.S+tk.E,         padx=5,  pady=10 )

        # Refresh plot configs
        self.__refresh_plot_configs()

    # ===============================================================================
    # @brief:   Import button click callback
    #
    # @return:      void
    # ===============================================================================
    def __import_btn_click(self):

        # Select file to visualize
        self.meas_file =  tk.filedialog.askopenfilename(initialdir = self.meas_file,title = "Select file",filetypes = (("text file","*.txt"),("all files","*.*")))
        
        # File selected
        if self.meas_file:

            # Parse data
            self.__parse_meas_file()

            # Update table of parameters
            self.__table_update()

            # Setup open file name to status line
            self.import_callback( "%s" % self.meas_file )

            # Remove all plots from graphs
            self.__clean_all_btn_callback()
            self.__refresh_btn_callback()

            # Enable multiplot selection
            self.plot_num_combo.configure(state="readonly")

            # Enable sample point showing
            self.samp_points.config( state="normal" )

    # ===============================================================================
    # @brief:   Parse imported file
    #
    # @return:      void
    # ===============================================================================
    def __parse_meas_file(self):

        # Get fixed timestamp in seconds
        fixed_timestamp_sec = ( int(self.timestamp_entry.get()) / 1e6 )

        # Open file for reading
        with open(self.meas_file, "r") as csvfile: 

            # Read row
            spamreader = csv.reader(csvfile, delimiter=LOG_FILE_DELIMITER)

            # Init timestamp
            self.timestamp = []
            self.meas_signals = []

            # Go thru file
            for idx, row in enumerate(spamreader):

                # Read header
                if 0 == idx:
                    for h in row:
                        self.meas_signals.append( { "name": h, "data": [], "plot": None, "line": None } )

                # Read data
                else:
                
                    if idx == 1:
                        self.timestamp.append( 0 )
                    else:
                        self.timestamp.append( self.timestamp[-1] + fixed_timestamp_sec )
                

                    # Get signal data
                    for num, signal in enumerate( self.meas_signals ):
                        signal["data"].append( float( row[num] ))

    # ===============================================================================
    # @brief:   Update parameter table
    #
    # @return:      void
    # ===============================================================================   
    def __table_update(self):

        # Clean table
        self.__table_clear()

        # List all signals defined in header
        for idx, signal in enumerate( self.meas_signals ):
            self.par_plot_table.insert(parent='',index='end',iid=idx,text="", values=(signal["name"],"x") )


    # ===============================================================================
    # @brief:   Clear parameter table
    #
    # @return:      void
    # ===============================================================================   
    def __table_clear(self):
        for i in self.par_plot_table.get_children():
            self.par_plot_table.delete(i)

    # ===============================================================================
    # @brief:   Update all subplots
    #
    # @return:      void
    # ===============================================================================   
    def __update_all_plots(self):

        # Clean plot
        plt.cla()

        # Go thru all measured signal
        for idx, signal in enumerate( self.meas_signals ):
            
            # Get signal name, assigned plot and data
            name = signal["name"]
            plot = signal["plot"]
            data = signal["data"]

            # Plot if signal is already ploted
            if None != plot:

                # Single plot
                if 1 == self.num_of_plot:

                    # Plot only signals that are assign to 0 plot
                    if 0 == plot:
                        signal["line"]  = self.ax.plot( self.timestamp, data, marker=self.marker, label=name )
                        self.ax.legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)

                # Multi plot
                else:
                    
                    # Draw only if plot is available
                    if plot < self.num_of_plot:
                        signal["line"] = self.ax[plot].plot( self.timestamp, data, marker=self.marker, label=name )
                        self.ax[plot].legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)

        # Refresh plot configs
        self.__refresh_plot_configs()

        # Refresh matplotlib library
        plt.draw()

    # ===============================================================================
    # @brief:   Number of plots change callback
    #
    # @param[in]:   event - Change combobox event
    # @return:      void
    # =============================================================================== 
    def __plot_num_change(self, event):

        if 1 == self.num_of_plot:
            self.ax.remove()
        else:
            for n in range( self.num_of_plot ):
                self.ax[n].remove()

        # Refesh number of plots
        self.num_of_plot = int( self.plot_num_combo.get() )

        # Create subplots
        self.ax = self.fig.subplots( nrows=self.num_of_plot, ncols=1, sharex=True, sharey=False)

        # Refresh all plots
        self.__update_all_plots()

        # Disable menu for adding/removing plots
        if 1 == self.num_of_plot:
            self.par_table_menu.entryconfig("Add to plot 1", state="normal")
            self.par_table_menu.entryconfig("Add to plot 2", state="disabled")
            self.par_table_menu.entryconfig("Add to plot 3", state="disabled")
            self.par_table_menu.entryconfig("Add to plot 4", state="disabled")

        elif 2 == self.num_of_plot:
            self.par_table_menu.entryconfig("Add to plot 1", state="normal")
            self.par_table_menu.entryconfig("Add to plot 2", state="normal")
            self.par_table_menu.entryconfig("Add to plot 3", state="disabled")
            self.par_table_menu.entryconfig("Add to plot 4", state="disabled")

        elif 3 == self.num_of_plot:
            self.par_table_menu.entryconfig("Add to plot 1", state="normal")
            self.par_table_menu.entryconfig("Add to plot 2", state="normal")
            self.par_table_menu.entryconfig("Add to plot 3", state="normal")
            self.par_table_menu.entryconfig("Add to plot 4", state="disabled")

        elif 4 == self.num_of_plot:
            self.par_table_menu.entryconfig("Add to plot 1", state="normal")
            self.par_table_menu.entryconfig("Add to plot 2", state="normal")
            self.par_table_menu.entryconfig("Add to plot 3", state="normal")
            self.par_table_menu.entryconfig("Add to plot 4", state="normal")

    # ===============================================================================
    # @brief:   Refresh plot configurations
    #
    # @return:      void
    # ===============================================================================
    def __refresh_plot_configs(self):

        if 1 == self.num_of_plot:
            self.ax.grid(True, alpha=0.25)
            self.ax.set_xlabel("Time [sec]")
        else:
            for n in range( self.num_of_plot ):
                self.ax[n].grid(True, alpha=0.25)
            
            self.ax[self.num_of_plot-1].set_xlabel("Time [sec]")

    # ===============================================================================
    # @brief:   Left mouse click on table callback
    #
    # @param[in]:   e - Event
    # @return:      void
    # ===============================================================================
    def __left_m_click_table(self, e):

        iid = self.par_plot_table.identify_row(e.y)

        if iid:
            self.par_plot_table.selection_set(iid)    

            # Store selected parameter
            self.par_selected = int(self.par_plot_table.selection()[0])

            # Popup menu
            self.par_table_menu.tk_popup(e.x_root, e.y_root)  

        else:
            # mouse pointer not over item
            # occurs when items do not fill frame
            # no action required
            pass

    # ===============================================================================
    # @brief:   Add to plot 1 option pressed callback
    #
    # @return:      void
    # ===============================================================================
    def __add_to_plot_1(self):

        # Remove if already ploted
        self.__remove_selected_line_from_plot()

        # Signal not jet ploted on plot 0
        if 0 != self.meas_signals[self.par_selected]["plot"]:

            # Assign signal plot number
            self.meas_signals[self.par_selected]["plot"] = 0

            # Get signal data and name
            data = self.meas_signals[self.par_selected]["data"]
            name = self.meas_signals[self.par_selected]["name"]

            # Update table plot number
            self.par_plot_table.item(self.par_selected, values=(name,"1" ))

            # Plot data
            if 1 == self.num_of_plot:
                lines = self.ax.plot( self.timestamp, data, marker=self.marker, label=name )
                self.ax.legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)
            else:
                lines = self.ax[0].plot( self.timestamp, data, marker=self.marker, label=name )
                self.ax[0].legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)

            # Assign plot line
            self.meas_signals[self.par_selected]["line"] = lines

            # Refresh matplotlib library
            plt.draw()


    # ===============================================================================
    # @brief:   Add to plot 2 option pressed callback
    #
    # @return:      void
    # ===============================================================================
    def __add_to_plot_2(self):

        # Remove if already ploted
        self.__remove_selected_line_from_plot()
        
        # Signal not jet ploted on plot 1
        if 1 != self.meas_signals[self.par_selected]["plot"]:

            # Assign signal plot number
            self.meas_signals[self.par_selected]["plot"] = 1

            # Get signal data and name
            data = self.meas_signals[self.par_selected]["data"]
            name = self.meas_signals[self.par_selected]["name"]

            # Update table plot number
            self.par_plot_table.item(self.par_selected, values=(name,"2" ))

            # Plot data
            if self.num_of_plot > 1:
                line = self.ax[1].plot( self.timestamp, data, marker=self.marker, label=name)
                self.ax[1].legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)

                # Assign plot line
                self.meas_signals[self.par_selected]["line"] = line

                # Refresh matplotlib library
                plt.draw()

    # ===============================================================================
    # @brief:   Add to plot 3 option pressed callback
    #
    # @return:      void
    # ===============================================================================
    def __add_to_plot_3(self):

        # Remove if already ploted
        self.__remove_selected_line_from_plot()

        # Signal not jet ploted on plot 1
        if 2 != self.meas_signals[self.par_selected]["plot"]:

            # Assign signal plot number
            self.meas_signals[self.par_selected]["plot"] = 2

            # Get signal data and name
            data = self.meas_signals[self.par_selected]["data"]
            name = self.meas_signals[self.par_selected]["name"]

            # Update table plot number
            self.par_plot_table.item(self.par_selected, values=(name,"3" ))

            # Plot data
            if self.num_of_plot > 2:
                line = self.ax[2].plot( self.timestamp, data, marker=self.marker, label=name)
                self.ax[2].legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)

                # Assign plot line
                self.meas_signals[self.par_selected]["line"] = line

                # Refresh matplotlib library
                plt.draw()

    # ===============================================================================
    # @brief:   Add to plot 4 option pressed callback
    #
    # @return:      void
    # ===============================================================================
    def __add_to_plot_4(self):

        # Remove if already ploted
        self.__remove_selected_line_from_plot()
    
        # Signal not jet ploted on plot 1
        if 3 != self.meas_signals[self.par_selected]["plot"]:

            # Assign signal plot number
            self.meas_signals[self.par_selected]["plot"] = 3

            # Get signal data and name
            data = self.meas_signals[self.par_selected]["data"]
            name = self.meas_signals[self.par_selected]["name"]

            # Update table plot number
            self.par_plot_table.item(self.par_selected, values=(name,"4" ))

            # Plot data
            if self.num_of_plot > 3:
                line = self.ax[3].plot( self.timestamp, data, marker=self.marker, label=name)
                self.ax[3].legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)

                # Assign plot line
                self.meas_signals[self.par_selected]["line"] = line

                # Refresh matplotlib library
                plt.draw()
        
    # ===============================================================================
    # @brief:   Remove plot line that is selected from plot
    #
    # @return:      void
    # ===============================================================================
    def __remove_selected_line_from_plot(self):

        # Is even signal plot
        if None != self.meas_signals[self.par_selected]["plot"]:

            # Update table plot number
            self.par_plot_table.item(self.par_selected, values=(self.meas_signals[self.par_selected]["name"],"x" ))

            # Get plot and line
            plot = self.meas_signals[self.par_selected]["plot"]
            line = self.meas_signals[self.par_selected]["line"]

            # Signle plot
            if 1 == self.num_of_plot:

                # Remove only from that first plot 
                if 0 == plot:
                    self.ax.lines.remove( line[0] )
                    self.ax.legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)
            
            # Multiplot
            else:

                # If plot exists
                if plot < self.num_of_plot:
                    self.ax[plot].lines.remove( line[0] )
                    self.ax[plot].legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)

            # Refresh matplotlib library
            plt.draw()

            # Clear global signals data
            self.meas_signals[self.par_selected]["plot"] = None
            self.meas_signals[self.par_selected]["line"] = None

    # ===============================================================================
    # @brief:   Refresh button pressed callback
    #
    # @return:      void
    # ===============================================================================
    def __refresh_btn_callback(self):
        self.__plot_num_change(None)

    # ===============================================================================
    # @brief:   Clean all button pressed callback
    #
    # @return:      void
    # ===============================================================================
    def __clean_all_btn_callback(self):
        for idx, _ in enumerate( self.meas_signals ):
            self.par_selected = idx
            self.__remove_selected_line_from_plot()

    # ===============================================================================
    # @brief:   Entry validation for baudrate selection. This function is triggered
    #           on any keyboard press.
    #
    # @param[in]:   value - Value of key pressed
    # @return:      void
    # ===============================================================================  
    def __timestamp_entry_validate(self, value):
        if value.isdigit() or value == "":
            if len(value) < 9:
                return True
            else:
                return False
        else:
            return False

    # ===============================================================================
    # @brief:   Callback on enabling/disabling sample points show
    #
    # @param[in]:   state - Current state of show points state
    # @return:      void
    # ===============================================================================  
    def __sample_points_btn_press(self, state):

        # Toggle marker
        if state:
            self.marker = "o"
        else:
            self.marker = None   

#################################################################################################
##  END OF FILE
#################################################################################################  





