## Copyright (c) 2022 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       IpcProtocol.py
## @brief:      Inter-Process protocol
## @date:		04.07.2022
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from dataclasses import dataclass


#################################################################################################
##  DEFINITIONS
#################################################################################################


#################################################################################################
##  FUNCTIONS
#################################################################################################


#################################################################################################
##  CLASSES
#################################################################################################   


@dataclass
class IpcMsgType():

    IpcMsgType_None: int                = 0     # No operations
    
    IpcMsgType_ComRefresh : int         = 10    # Get informations about connected devices to PC
    IpcMsgType_ComConnect : int         = 11    # Connect to device
    IpcMsgType_ComDisconnect : int      = 12    # Disconnect from device
    IpcMsgType_ComRxFrame : int         = 13    # Received frame from embedded device
    IpcMsgType_ComTxFrame : int         = 14    # Transmit frame to embedded device


@dataclass
class IpcMsg():

    # Type of message
    type: int = IpcMsgType.IpcMsgType_None

    # Payload
    payload: str = None


#################################################################################################
##  END OF FILE
#################################################################################################  





