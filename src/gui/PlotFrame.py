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

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

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

        # Define columns
        self.par_plot_table["columns"] = ("Par", "Plot")
        self.par_plot_table.column("#0",                    width=0,                    stretch=tk.NO      )
        self.par_plot_table.column("Par",   anchor=tk.W,    width=150,  minwidth=150,   stretch=tk.YES     )
        self.par_plot_table.column("Plot",  anchor=tk.W,    width=50,   minwidth=50,    stretch=tk.NO      )

        self.par_plot_table.heading("#0",   text="",        anchor=tk.CENTER    )
        self.par_plot_table.heading("Par",  text="Par",     anchor=tk.W         )
        self.par_plot_table.heading("Plot", text="Plot",    anchor=tk.W         )


        # Self frame layout
        self.frame_label.grid(      column=0, row=0,            sticky=tk.W,                   padx=20, pady=10 )
        self.plot_frame.grid(       column=0, row=1, rowspan=4, sticky=tk.W+tk.N+tk.E+tk.S,    padx=10, pady=10 )
        self.par_plot_table.grid(   column=1, row=1,            sticky=tk.W+tk.S+tk.E+tk.N,    padx=10, pady=10 )
        self.import_btn.grid(       column=1, row=2,            sticky=tk.W+tk.S+tk.E,         padx=10, pady=10 )



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

            # Go thru file
            for idx, row in enumerate(spamreader):

                # Read header
                if 0 == idx:
                    for h in row:
                        self.meas_file_header.append( h )

                # Read data
                else:
                
                    if idx == 1:
                        self.timestamp.append( 0 );
                    else:
                        self.timestamp.append( self.timestamp[-1] + LOG_FILE_FIXED_TIMESTAMP )
                
                    """
                    # Accumulate data
                    Tint.append( float( row[ LOG_FILE_INT_TEMP_COL ] ))
                    Tint_filt.append( float( row[ LOG_FILE_INT_TEMP_FILT_COL ] ))
                    Taux.append( float( row[ LOG_FILE_AUX_TEMP_COL ] ))
                    Taux_filt.append( float( row[ LOG_FILE_AUX_TEMP_FILT_COL ] ))
                    Tcomp.append( float( row[ LOG_FILE_COMP_TEMP_COL ] ))
                    Tcomp_filt.append( float( row[ LOG_FILE_COMP_TEMP_FILT_COL ] ))
                    Trelay.append( float( row[ LOG_FILE_RELAY_TEMP_COL ] ))
                    Trelay_filt.append( float( row[ LOG_FILE_RELAY_TEMP_FILT_COL ] ))

                    """

    def __table_update(self):

        # Clean table
        self.__table_clear()

        # List all signals defined in header
        for idx, signal in enumerate( self.meas_file_header ):

            signal = signal.replace(" ", "_")
            self.par_plot_table.insert(parent='',index='end',iid=idx,text="", values=( signal ) )


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
        

        
        # Configure plot
        self.ax.set_xlabel("Time [sec]")
        self.ax.grid(True, alpha=0.25)
        self.ax.legend(fancybox=True, shadow=True, loc="upper right", fontsize=12)

        # Refresh matplotlib library
        plt.draw()







#################################################################################################
##  END OF FILE
#################################################################################################  





