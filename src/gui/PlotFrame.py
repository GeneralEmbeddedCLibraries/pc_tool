## Copyright (c) 2022 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       PlotFrame.py
## @brief:      Real-time plotting of device parameters
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

# Streaming period in secodns
LOG_FILE_FIXED_TIMESTAMP        = 0.1

# File delimiter
LOG_FILE_DELIMITER              = ";"


#################################################################################################
##  FUNCTIONS
#################################################################################################



#################################################################################################
##  CLASSES
#################################################################################################   



class PlotFrame(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        
        # Create frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(bg=GuiColor.main_bg)

        self.rowconfigure(2, weight=1)
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
        self.meas_file_header = []

        # Create info label
        self.frame_label = tk.Label(self, text="Plot Measured Data", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)


        # =============================================================================================
        ## PLOT CONFIGURATIONS
        # =============================================================================================
        plt.style.use(['dark_background'])
        self.PLOT_MAIN_TITLE_SIZE    = 18
        self.PLOT_TITLE_SIZE         = 16
        self.PLOT_AXIS_LABEL_SIZE    = 12

        PLOT_ADJUST_LEFT        = 0.038
        PLOT_ADJUST_BOTTOM      = 0.083
        PLOT_ADJUST_RIGHT       = 0.99
        PLOT_ADJUST_TOP         = 0.94
        PLOT_ADJUST_WSPACE		= 0.2
        PLOT_ADJUST_HSPACE		= 0.2
            
        # Plot frame
        self.plot_frame = tk.Frame(self, bg=GuiColor.main_bg)

        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        
        # Customize layout
        plt.subplots_adjust(left=PLOT_ADJUST_LEFT, right=PLOT_ADJUST_RIGHT, top=PLOT_ADJUST_TOP, bottom=PLOT_ADJUST_BOTTOM, wspace=PLOT_ADJUST_WSPACE, hspace=PLOT_ADJUST_HSPACE)	

        canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                
        # Buttons
        self.import_btn = NormalButton(self, text="Import", command=self.__import_btn_click, width=30) 

        # Create table
        self.par_plot_table = ttk.Treeview(self, style="mystyle.Treeview", selectmode="browse")
        self.par_plot_table.bind("<Button-3>", self.__left_m_click_table)
        self.par_plot_table.bind("<Button-1>", self.__right_m_click_table)

        self.par_table_menu = tk.Menu(self.frame_label, tearoff=False, font=GuiFont.normal_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.par_table_menu.add_command(label="Add to plot 1",      command=self.__add_to_plot_1)
        self.par_table_menu.add_command(label="Add to plot 2",      command=self.__add_to_plot_2)
        self.par_table_menu.add_command(label="Add to plot 3",      command=self.__add_to_plot_3)
        self.par_table_menu.add_command(label="Add to plot 4",      command=self.__add_to_plot_4)
        self.par_table_menu.add_command(label="Remove from plot",   command=self.__remove_from_plot)

        # Number of plots
        self.plot_num_label = tk.Label(self, text="Number of plots", font=GuiFont.normal_bold, bg=GuiColor.main_bg, fg=GuiColor.main_fg)
        self.plot_num_combo = GuiCombobox(self, options=["1","2","3","4"], font=GuiFont.normal_bold, state="readonly", width=2, justify="left")
        self.plot_num_combo.set("1")
        self.num_of_plot = 1

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
        self.plot_frame.grid(       column=0, row=1, rowspan=4,     sticky=tk.W+tk.N+tk.E+tk.S,    padx=10, pady=10 )
        self.plot_num_label.grid(   column=1, row=1,                sticky=tk.S+tk.E+tk.N,         padx=10, pady=10 )
        self.plot_num_combo.grid(   column=2, row=1,                sticky=tk.W+tk.S+tk.E+tk.N,    padx=10, pady=10 )
        self.par_plot_table.grid(   column=1, row=2, columnspan=2,  sticky=tk.W+tk.S+tk.E+tk.N,    padx=10, pady=10 )
        self.import_btn.grid(       column=1, row=3, columnspan=2,  sticky=tk.W+tk.S+tk.E,         padx=10, pady=10 )

        # Refresh plot configs
        self.__refresh_plot_configs()


    def __import_btn_click(self):

        # Select file to visualize
        self.meas_file =  tk.filedialog.askopenfilename(initialdir = self.meas_file,title = "Select file",filetypes = (("text file","*.txt"),("all files","*.*")))
        
        # File selected
        if self.meas_file:

            # Parse data
            self.__parse_meas_file()

            # Update table of parameters
            self.__table_update()

            # Update plot
            self.__plot_update()



    def __parse_meas_file(self):

        # Open file for reading
        with open(self.meas_file, "r") as csvfile: 

            # Read row
            spamreader = csv.reader(csvfile, delimiter=LOG_FILE_DELIMITER)

            # Init timestamp
            self.timestamp = []
            self.data = []              # TODO: Omit this
            self.meas_file_header = []  # TODO: Omit this

            self.meas_signals = []

            # Go thru file
            for idx, row in enumerate(spamreader):

                # Read header
                if 0 == idx:
                    for h in row:
                        self.meas_file_header.append( h )

                        # Prepare dictionary of measured data
                        self.meas_signals.append( { "name": h, "data": [], "plot": None, "line": None } )

                # Read data
                else:
                
                    if idx == 1:
                        self.timestamp.append( 0 )

                        for pos, signal in enumerate( self.meas_file_header ):
                            self.data.append( [ ( float( row[pos] )) ])

                    else:
                        self.timestamp.append( self.timestamp[-1] + LOG_FILE_FIXED_TIMESTAMP )
                
                        # Accumulate data
                        for pos, signal in enumerate( self.meas_file_header ):
                            self.data[pos].append( float( row[pos] ))   # TODO: Omit self.data...

                            self.meas_signals[pos]["data"].append( float( row[pos] ))


    def __table_update(self):

        # Clean table
        self.__table_clear()

        # List all signals defined in header
        for idx, signal in enumerate( self.meas_file_header ):
            self.par_plot_table.insert(parent='',index='end',iid=idx,text="", values=(signal,"x") )


    # ===============================================================================
    # @brief:   Clear parameter table
    #
    # @return:      void
    # ===============================================================================   
    def __table_clear(self):
        for i in self.par_plot_table.get_children():
            self.par_plot_table.delete(i)


    def __plot_update(self):
        
        # Setup file
        self.fig.suptitle( "File: \"%s\"" % self.meas_file.split("/")[-1]  , fontsize=self.PLOT_MAIN_TITLE_SIZE )

        # Clean plot
        plt.cla()

        # Plot data
        #for idx, signal in enumerate(self.data):
        #    self.ax.plot( self.timestamp, self.data[idx], label=self.meas_file_header[idx])

        # Refresh plot configs
        self.__refresh_plot_configs()

        # Refresh matplotlib library
        #plt.draw()


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

        # Refresh plot configs
        self.__refresh_plot_configs()

        # Refresh matplotlib library
        plt.draw()



    def __refresh_plot_configs(self):

        if 1 == self.num_of_plot:
            self.ax.grid(True, alpha=0.25)
            self.ax.legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)
            self.ax.set_xlabel("Time [sec]")
        else:
            for n in range( self.num_of_plot ):
                self.ax[n].grid(True, alpha=0.25)
                self.ax[n].legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)
            
            self.ax[self.num_of_plot-1].set_xlabel("Time [sec]")




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

    def __right_m_click_table(self, e):
        pass


    def __add_to_plot_1(self):


        print("Selected parameter: %s" % self.meas_signals[self.par_selected]["name"] )
        
        # Signal not jet ploted on plot 0
        if 0 != self.meas_signals[self.par_selected]["plot"]:

            # Update table plot number
            self.par_plot_table.item(self.par_selected, values=(self.meas_file_header[self.par_selected],"1" ))

            # Assign signal plot number
            self.meas_signals[self.par_selected]["plot"] = 0

            # Get signal data and name
            data = self.meas_signals[self.par_selected]["data"]
            name = self.meas_signals[self.par_selected]["name"]

            # Plot data
            if 1 == self.num_of_plot:
                #plot_line = self.ax.plot( self.timestamp, self.data[self.par_selected], label=self.meas_file_header[self.par_selected])
                lines = self.ax.plot( self.timestamp, self.data[self.par_selected], label=name )
            else:
                #plot_line = self.ax[0].plot( self.timestamp, self.data[self.par_selected], label=self.meas_file_header[self.par_selected])
                lines = self.ax[0].plot( self.timestamp, self.data[self.par_selected], label=name )

            # Assign plot line
            self.meas_signals[self.par_selected]["line"] = lines

            # Refresh matplotlib library
            plt.draw()

            print("Parameter added to plot: %s, plot:%s, line: %s" % ( self.meas_signals[self.par_selected]["name"], self.meas_signals[self.par_selected]["plot"], self.meas_signals[self.par_selected]["line"] ))




    def __add_to_plot_2(self):
        
        # Signal not jet ploted on plot 1
        if 1 != self.meas_signals[self.par_selected]["plot"]:

            # Update table plot number
            self.par_plot_table.item(self.par_selected, values=(self.meas_file_header[self.par_selected],"2" ))

            # Assign signal plot number
            self.meas_signals[self.par_selected]["plot"] = 1

            # Get signal data and name
            data = self.meas_signals[self.par_selected]["data"]
            name = self.meas_signals[self.par_selected]["name"]

            # Plot data
            if self.num_of_plot > 1:
                lines = self.ax[1].plot( self.timestamp, self.data[self.par_selected], label=name)

            # Assign plot line
            self.meas_signals[self.par_selected]["line"] = lines

            # Refresh matplotlib library
            plt.draw()




    def __add_to_plot_3(self):

        # Update table plot number
        self.par_plot_table.item(self.par_selected, values=(self.meas_file_header[self.par_selected],"3" ))


        # Plot data
        if self.num_of_plot > 2:
            self.ax[2].plot( self.timestamp, self.data[self.par_selected], label=self.meas_file_header[self.par_selected])

            # Refresh matplotlib library
            plt.draw()
        

    def __add_to_plot_4(self):
    
        # Update table plot number
        self.par_plot_table.item(self.par_selected, values=(self.meas_file_header[self.par_selected],"4" ))


        # Plot data
        if self.num_of_plot > 3:
            self.ax[3].plot( self.timestamp, self.data[self.par_selected], label=self.meas_file_header[self.par_selected])

            # Refresh matplotlib library
            plt.draw()
        

    def __remove_from_plot(self):

        # Is even signal plot
        if None != self.meas_signals[self.par_selected]["plot"]:

            # Update table plot number
            self.par_plot_table.item(self.par_selected, values=(self.meas_signals[self.par_selected]["name"],"x" ))

            # Get plot and line
            plot = self.meas_signals[self.par_selected]["plot"]
            line = self.meas_signals[self.par_selected]["line"]

            # Signle plot
            if 1 == self.num_of_plot:
                self.ax.lines.remove( line[0] )
            
            # Multiplot
            else:
                self.ax[plot].lines.remove( line[0] )

            # Refresh matplotlib library
            plt.draw()

            # Clear global signals data
            self.meas_signals[self.par_selected]["plot"] = None
            self.meas_signals[self.par_selected]["line"] = None
        



#################################################################################################
##  END OF FILE
#################################################################################################  





