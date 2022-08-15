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
import multiprocessing
import tkinter as tk
from tkinter import ttk
from gui.GuiCommon import GuiFont, GuiColor



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


#################################################################################################
##  FUNCTIONS
#################################################################################################



#################################################################################################
##  CLASSES
#################################################################################################   


"""
class Scope(multiprocessing.Process):
    def __init__(self, fig, ax, maxt=2, dt=0.02):
        self.ax = ax
        self.dt = dt
        self.maxt = maxt
        self.tdata = [0]
        self.ydata = [0]
        self.line = Line2D(self.tdata, self.ydata)
        self.ax.add_line(self.line)
        self.ax.set_ylim(-.1, 1.1)
        self.ax.set_xlim(0, self.maxt)

        # Create and start process
        self.process = multiprocessing.Process(name="Serial Communication", target=self.run)  
        self.process.start()

        #ani = animation.FuncAnimation(fig, self.plt_update, self.plt_emiter, interval=50, blit=True)
        ani = animation.FuncAnimation(fig, self.update, self.plt_emiter, interval=50, blit=True)
        #plt.show()


    def run(self):
        #plt.show()
        pass
        

    def update(self, y):
        lastt = self.tdata[-1]
        if lastt > self.tdata[0] + self.maxt:  # reset the arrays
            self.tdata = [self.tdata[-1]]
            self.ydata = [self.ydata[-1]]
            self.ax.set_xlim(self.tdata[0], self.tdata[0] + self.maxt)
            self.ax.figure.canvas.draw()

        t = self.tdata[-1] + self.dt
        self.tdata.append(t)
        self.ydata.append(y)
        self.line.set_data(self.tdata, self.ydata)
        return self.line,

    def plt_emiter(self):
        while True:
            v = np.random.rand(1)
            if v > 0.1:
                yield 0.
            else:
                yield np.random.rand(1)


"""




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

        # Create info label
        self.frame_label = tk.Label(self, text="Real-Time Ploting", font=GuiFont.title, bg=GuiColor.main_bg, fg=GuiColor.main_fg)

        # Plot frame
        self.plot_frame = tk.Frame(self, bg=GuiColor.main_bg)



        
        # Matplotlib figure
        self.fig = Figure(figsize=(5, 4), dpi=100)
        #fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        
    
        #t = np.arange(0, 100, .01)
        #self.ax = self.fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0,100)

        self.line, = self.ax.plot(0,0)

        canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        

        #scope = Scope(fig, ax)
        

        # Buttons
        self.run_stop_btn = tk.Button(self, text="Run", font=GuiFont.btn, bg=GuiColor.btn_bg, fg=GuiColor.btn_fg, activebackground=GuiColor.btn_bg, activeforeground=GuiColor.btn_fg, relief=tk.FLAT, borderwidth=0, width=20, command=self.__run_btn_click) 
        self.clear_btn = tk.Button(self, text="Clear", font=GuiFont.btn, bg=GuiColor.btn_bg, fg=GuiColor.btn_fg, activebackground=GuiColor.btn_bg, activeforeground=GuiColor.btn_fg, relief=tk.FLAT, borderwidth=0, width=20, command=None) 

        # Create table
        self.par_plot_table = ttk.Treeview(self, style="mystyle.Treeview", selectmode="browse")

        # Define columns
        self.par_plot_table["columns"] = ("Par", "Plot")
        self.par_plot_table.column("#0",                    width=0,                    stretch=tk.NO      )
        self.par_plot_table.column("Par",   anchor=tk.W,    width=50,   minwidth=50,    stretch=tk.YES     )
        self.par_plot_table.column("Plot",  anchor=tk.W,    width=50,   minwidth=50,    stretch=tk.NO      )

        self.par_plot_table.heading("#0",   text="",        anchor=tk.CENTER    )
        self.par_plot_table.heading("Par",  text="Par",     anchor=tk.W         )
        self.par_plot_table.heading("Plot", text="Plot",    anchor=tk.W         )


        # Self frame layout
        self.frame_label.grid(              column=0, row=0,            sticky=tk.W,                   padx=20, pady=10    )
        self.plot_frame.grid(               column=0, row=1, rowspan=4, sticky=tk.W+tk.N+tk.E+tk.S,    padx=10, pady=10    )
        
        self.par_plot_table.grid(           column=1, row=1,            sticky=tk.W+tk.S+tk.E+tk.N,    padx=10, pady=10   )
        self.run_stop_btn.grid(             column=1, row=2,            sticky=tk.W+tk.S+tk.E,         padx=10, pady=0    )
        self.clear_btn.grid(                column=1, row=3,            sticky=tk.W+tk.N+tk.E+tk.S,    padx=10, pady=10    )

        self.cnt = 0
        #self.__update()


    """
    def plt_emiter(self):
        while True:
            v = np.random.rand(1)
            if v > 0.1:
                yield 0.
            else:
                yield np.random.rand(1)
    """


    def __run_btn_click(self):

        print("RUN BTN PRESSED!")


    def __update(self):

        #print("PLOT TIMER EXPIRE...")


        # Reload timer
        self.plot_frame.after(1000, self.__update) 

        self.cnt += 1

        if self.cnt > 60:
            self.cnt = 0

        #self.ax.plot(self.cnt, self.cnt, "ro")
        t = np.arange(0, self.cnt, .01)
        data = 2 * np.cos(2 * np.pi * t) * np.sin(2 * np.pi * t)

        #self.ax.plot(t, 2 * np.cos(2 * np.pi * t))

        self.line.set_xdata(t)
        self.line.set_ydata(data)
        self.ax.set_xlim(0, self.cnt)
        self.fig.canvas.draw()
        #self.fig.canvas.flush_events()





#################################################################################################
##  END OF FILE
#################################################################################################  





