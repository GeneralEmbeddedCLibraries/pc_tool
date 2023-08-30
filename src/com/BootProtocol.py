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
import struct


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
    # @param[in]:   send_fn     - Send function def send(binary)
    # @return:      void
    # ===============================================================================
    def __init__(self, send_fn, cb=None):

        self.send = send_fn


    def parser(self, rx_queue):
        pass


    def send_connect(self):

        # Assemble connect comand
        cmd = [ 0xB0, 0x07, 0x00, 0x00, 0x2B, 0x10, 0x00, 0x9B ]

        # Send
        self.send( cmd )


    def send_prepare(self, fw_size, fw_ver, hw_ver):

        # Assemble prepare command
        prepare_cmd = [ 0xB0, 0x07, 0x0C, 0x00, 0x2B, 0x20, 0x00, 0x00 ]

        # Assemble FW size
        for byte in struct.pack('I', int(fw_size)):
            prepare_cmd.append( byte )

        # Assemble FW version
        for byte in struct.pack('I', int(fw_ver)):
            prepare_cmd.append( byte )

        # Assemble HW version
        for byte in struct.pack('I', int(hw_ver)):
            prepare_cmd.append( byte )

        # Calculate crc
        prepare_cmd[7] = self.__calc_crc8( [0x0C, 0x00] )  # Lenght
        prepare_cmd[7] ^= self.__calc_crc8( [0x2B] )  # Source
        prepare_cmd[7] ^= self.__calc_crc8( [0x20] )  # Command
        prepare_cmd[7] ^= self.__calc_crc8( [0x00] )  # Status
        prepare_cmd[7] ^= self.__calc_crc8( [fw_size, fw_ver, hw_ver] )

        # Send prepare command
        self.send( prepare_cmd )  


    # ===============================================================================
    # @brief  Calculate CRC-8
    #
    # @param[in]    data    - Inputed data
    # @return       crc8    - Calculated CRC8
    # ===============================================================================
    def __calc_crc8(self, data):
        poly = 0x07
        seed = 0xB6
        crc8 = seed

        for byte in data:
            crc8 = (( crc8 ^ byte ) & 0xFF )

            for n in range( 8 ):
                if 0x80 == ( crc8 & 0x80 ):
                    crc8 = (( crc8 << 1 ) ^ poly )
                else:
                    crc8 = ( crc8 << 1 );

        return crc8 & 0xFF


        

#################################################################################################
##  END OF FILE
#################################################################################################  
