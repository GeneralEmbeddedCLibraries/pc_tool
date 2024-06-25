## Copyright (c) 2024 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       main.py
## @brief:      Main entry for PC tool
## @date:		09.12.2022
## @author:		Ziga Miklosic
## @version:    V0.4.0
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from gui.MainWindow import MainWindow
from com.SerialComPort import SerialComunication
import multiprocessing


#################################################################################################
##  DEFINITIONS
#################################################################################################

# Script version
MAIN_SCRIPT_VER     = "V0.4.1"

#################################################################################################
##  FUNCTIONS
#################################################################################################


# ===============================================================================
# @brief:  Main 
#
# @return: void
# ===============================================================================
def main():
    
    # Fix issue with reopening of window over and over
    multiprocessing.freeze_support()

    # Create and run communication process
    q_gui_to_serial = multiprocessing.Queue()
    q_serial_to_gui = multiprocessing.Queue()

    # Run communication engine
    serial_com = SerialComunication(q_gui_to_serial, q_serial_to_gui)

    # Create and run main window
    mainWin = MainWindow(MAIN_SCRIPT_VER, q_serial_to_gui, q_gui_to_serial)

#################################################################################################
##  MAIN ENTRY
#################################################################################################   
if __name__ == "__main__":
    main()


#################################################################################################
##  END OF FILE
#################################################################################################  

