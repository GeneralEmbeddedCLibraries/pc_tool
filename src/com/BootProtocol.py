## Copyright (c) 2023 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       BootProtocol.py
## @brief:      Bootloader communication protocol
## @date:		30.08.2023
## @author:		Ziga Miklosic
## @version:    V0.1.0
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
import os


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
# @brief  Binary file Class
# ===============================================================================
class BinFile:

    # Access type
    READ_WRITE  = "r+b"      # Puts pointer to start of file 
    WRITE_ONLY  = "wb"       # Erase complete file
    READ_ONLY   = "rb"
    APPEND      = "a+b"      # This mode puts pointer to EOF. Access: Read & Write

    # ===============================================================================
    # @brief  Binary file constructor
    #
    # @param[in]    file    - File name
    # @param[in]    access  - Access level
    # @return       void
    # ===============================================================================
    def __init__(self, file, access=READ_ONLY):

        # Store file name
        self.file_name = file

        try:
            if os.path.isfile(file):
                self.file = open( file, access )
        except Exception as e:
            print(e)

    # ===============================================================================
    # @brief  Write to binary file
    #
    # @param[in]    addr    - Address to write to
    # @param[in]    val     - Value to write as list
    # @return       void
    # ===============================================================================
    def write(self, addr, val):
        self.__set_ptr(addr)
        self.file.write( bytearray( val ))

    # ===============================================================================
    # @brief  Read from binary file
    #
    # @param[in]    addr    - Address to read from
    # @param[in]    size    - Sizeof read in bytes
    # @return       data    - Readed data
    # ===============================================================================
    def read(self, addr, size):
        self.__set_ptr(addr)
        data = self.file.read(size)
        return data
    
    # ===============================================================================
    # @brief  Get size of binary file
    #
    # @return       data    - Readed data
    # ===============================================================================    
    def size(self):
        return len( self.read( 0, None ))

    # ===============================================================================
    # @brief  Set file pointer
    #
    # @note     Pointer is being evaluated based on binary file value
    #
    # @param[in]    offset  - Pointer offset
    # @return       void
    # ===============================================================================
    def __set_ptr(self, offset):
        self.file.seek(offset) 



class FwImage(BinFile):

    def __init__(self, file):
        self.file = BinFile(file=file, access=BinFile.READ_ONLY)




# ===============================================================================
# @brief:   Boot Protocol class
#
# @note     This class implementation is low level interface agnostics! 
#           
#           Communication with that class goes thru reception and transmission
#           queues. 
#
# @return:      void
# ===============================================================================
class BootProtocol:

    # ===============================================================================
    # @brief:   Construct BootProtocol
    #
    # @param[in]:   rx_queue    - Reception queue
    # @param[in]:   tx_queue    - Transmission queue
    # @return:      void
    # ===============================================================================
    def __init__(self, fw_file, rx_queue, tx_queue, cb=None):

        self.fw_file    = fw_file
        self.q_rx       = rx_queue
        self.q_tx       = tx_queue


    def parser(self):
        pass

    def send_connect(self):
        pass

    def send_prepare(self):
        pass



        

#################################################################################################
##  END OF FILE
#################################################################################################  
