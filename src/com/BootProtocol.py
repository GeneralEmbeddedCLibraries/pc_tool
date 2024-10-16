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

    PREAMBLE = [ 0xB0, 0x07 ]

    # Command type
    CMD_CONNECT_RSP     = 0x11
    CMD_PREPARE_RSP     = 0x21
    CMD_FLASH_RSP       = 0x31
    CMD_EXIT_RSP        = 0x41
    CMD_INFO_RSP        = 0xA1

    # Message status
    MSG_OK                  = 0x00
    MSG_ERROR_VALIDATION    = 0x01
    MSG_ERROR_INV_REQUEST   = 0x02
    MSG_ERROR_FLASH_WRITE   = 0x04
    MSG_ERROR_FLASH_ERASE   = 0x08
    MSG_ERROR_FW_SIZE       = 0x10
    MSG_ERROR_FW_VER        = 0x20
    MSG_ERROR_HW_VER        = 0x40
    MSG_ERROR_SIGNATURE     = 0x80
    
    MSG_ERROR_STR = {   
                        MSG_OK                  : "OK",
                        MSG_ERROR_VALIDATION    : "Validation error",
                        MSG_ERROR_INV_REQUEST   : "Invalid request (wrong sequence)",
                        MSG_ERROR_FLASH_WRITE   : "Error during flash write",
                        MSG_ERROR_FLASH_ERASE   : "Error during flash erase",
                        MSG_ERROR_FW_SIZE       : "Firmware image size error",
                        MSG_ERROR_FW_VER        : "Firmware version compatibility error",
                        MSG_ERROR_HW_VER        : "Hardware version compatibility error",
                        MSG_ERROR_SIGNATURE     : "Firmware image signature invalid error",
                    }


    # ===============================================================================
    # @brief:   Construct BootProtocol
    #
    # @param[in]:   rx_queue    - Reception queue
    # @param[in]:   send_fn     - Send function def send(binary)
    # @return:      void
    # ===============================================================================
    def __init__(self, send_fn, cb=None):

        # Send function
        self.send = send_fn

        # Reception queue
        self.rx_q = []

        # Supported bootloader commands
        self.cmd_type = [ BootProtocol.CMD_CONNECT_RSP, BootProtocol.CMD_PREPARE_RSP, BootProtocol.CMD_FLASH_RSP, BootProtocol.CMD_EXIT_RSP, BootProtocol.CMD_INFO_RSP  ]

        # Receive command callbacks
        self.cb = cb

    # ===============================================================================
    # @brief  Parse bootloader messages
    #
    # @param[in]    payload - Received pyload
    # @return       void
    # ===============================================================================
    def parser(self, payload):
        
        # Accumulate queue
        for byte in payload:
            self.rx_q.append( byte )

        # Data received
        if len( self.rx_q ) >= 8:

            # Header valid
            if BootProtocol.PREAMBLE == self.rx_q[0:2]:

                # Get fields
                lenght  = self.rx_q[2:4]
                source  = self.rx_q[4]
                command = self.rx_q[5]
                status  = self.rx_q[6]

                # Convert to value
                lenght_val = int((( lenght[1] << 8 ) | lenght[0] & 0xFF ) & 0xFFFF )
                
                # All data received
                if ( len( self.rx_q ) - 8 ) >= lenght_val:

                    # Calculate crc
                    calc_crc = self.__calc_crc8( lenght )       # Lenght
                    calc_crc ^= self.__calc_crc8( [source] )    # Source
                    calc_crc ^= self.__calc_crc8( [command] )   # Command
                    calc_crc ^= self.__calc_crc8( [status] )    # Status

                    # Is payload in message
                    if lenght_val > 0:

                        # Get payload
                        payload = self.rx_q[8:] 

                        # Apply payload to CRC
                        calc_crc ^= self.__calc_crc8( payload ) # Payload
                    else:
                        payload = []

                    # CRC OK
                    if calc_crc == self.rx_q[7]:
                        
                        # Go thru all commands
                        for n, cmd in enumerate( self.cmd_type ):
                            
                            # Find command
                            if cmd == command:

                                # Raise callback
                                self.cb[n]( status, payload )

                    # CRC error
                    else:
                        pass

                    # Reset queue
                    self.reset_rx_queue()

            # Frame received in between -> reset rx queue
            else:
                self.reset_rx_queue()         
            
    # ===============================================================================
    # @brief  Reset reception queue
    #
    # @return       void
    # ===============================================================================
    def reset_rx_queue(self):
        self.rx_q = []

    # ===============================================================================
    # @brief  Send connect command
    #
    # @return       void
    # ===============================================================================
    def send_connect(self):

        # Assemble connect comand
        cmd = [ 0xB0, 0x07, 0x00, 0x00, 0x2B, 0x10, 0x00, 0x9B ]

        # Send
        self.send( cmd )

    # ===============================================================================
    # @brief  Send prepare command
    #
    # @param[in]    image_header - Image (application) header
    # @return       void
    # ===============================================================================
    def send_prepare(self, image_header):

        # Get size of image header
        size = len(image_header)

        # Assemble prepare command
        prepare_cmd = [ 0xB0, 0x07, ( size & 0xFF ), (( size >> 8 ) & 0xFF ), 0x2B, 0x20, 0x00, 0x00 ]

        # Add payload
        for byte in image_header:
            prepare_cmd.append( byte )            

        # Calculate crc
        prepare_cmd[7] = self.__calc_crc8( prepare_cmd[2:4] )  # Lenght
        prepare_cmd[7] ^= self.__calc_crc8( [0x2B] )  # Source
        prepare_cmd[7] ^= self.__calc_crc8( [0x20] )  # Command
        prepare_cmd[7] ^= self.__calc_crc8( [0x00] )  # Status
        prepare_cmd[7] ^= self.__calc_crc8( prepare_cmd[8:]) # Payload

        # Send prepare command
        self.send( prepare_cmd )  

    # ===============================================================================
    # @brief  Send flash data command
    #
    # @param[in]    data    - Binary data to flash
    # @param[in]    size    - Size of binary data
    # @return       void
    # ===============================================================================
    def send_flash_data(self, data, size):

        # Assemble flash data command
        flash_cmd = [ 0xB0, 0x07, ( size & 0xFF ), (( size >> 8 ) & 0xFF ), 0x2B, 0x30, 0x00, 0x00 ]

        # Calculate CRC
        flash_cmd[7] = self.__calc_crc8( [flash_cmd[2], flash_cmd[3]] )  # Lenght
        flash_cmd[7] ^= self.__calc_crc8( [0x2B] )  # Source
        flash_cmd[7] ^= self.__calc_crc8( [0x30] )  # Command
        flash_cmd[7] ^= self.__calc_crc8( [0x00] )  # Status

        # Add payload
        for byte in data:
            flash_cmd.append( byte )
            
        # Calcualte payload CRC
        flash_cmd[7] ^= self.__calc_crc8( data ) 

        # Send prepare command
        self.send( flash_cmd )  

    # ===============================================================================
    # @brief  Send exit bootloader command
    #
    # @return       void
    # ===============================================================================
    def send_exit(self):

        # Assemble exit comand
        cmd = [ 0xB0, 0x07, 0x00, 0x00, 0x2B, 0x40, 0x00, 0x2C ]

        # Send
        self.send( cmd )   

    # ===============================================================================
    # @brief  Send information command
    #
    # @return       void
    # ===============================================================================
    def send_info(self):

        # Assemble info comand
        cmd = [ 0xB0, 0x07, 0x00, 0x00, 0x2B, 0xA0, 0x00, 0x82 ]

        # Send
        self.send( cmd )      

    # ===============================================================================
    # @brief  Get stringed status
    #
    # @param[in]    status  - Message status
    # @return       stringed status format
    # ===============================================================================
    def get_status_str(self, status):
        return BootProtocol.MSG_ERROR_STR[status]

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
