## Copyright (c) 2025 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       scp.py
## @brief:      SCP
## @date:		19.01.2025
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from enum import Enum
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
class ScpCommand:
    READ = 0x00  # Read attributes command
    WRITE = 0x01  # Write attributes command
    READ_RSP = 0x02  # Read attributes response command
    WRITE_RSP = 0x03  # Write attributes response command
    SUBSCRIBE = 0x04  # Subscribe attributes command
    SUBSCRIBE_RSP = 0x05  # Subscribe attributes response command
    NOTIFY = 0x06  # Notify subscribed device about attribute change

@dataclass
class ScpStatus:
    OK = 0x00  # Normal operation
    ERROR = 0x01  # General error code
    ERROR_MALFORMED_CMD = 0x80  # Invalid command, either missing or invalid fields
    ERROR_UNSUPPORTED_ATTRIBUTE = 0x86  # Attribute does not exist in device cluster table
    ERROR_UNSUPPORTED_CLUSTER = 0xC3  # Cluster does not exist in device cluster table
    ERROR_INVALID_VALUE = 0x87  # Attribute set out of range error or set to a reserved value
    ERROR_INVALID_DATA_TYPE = 0x8D  # The data type given for an attribute is incorrect
    ERROR_NOT_AUTHORIZED = 0x7E  # Writing to read-only attribute error
    ERROR_UNSUBSCRIBABLE_ATTRIBUTE = 0x8C  # Attribute cannot be subscribed

@dataclass
class ScpAttrType:
    U8 = 0x20  # Unsigned 8-bit integer
    U16 = 0x21  # Unsigned 16-bit integer
    U32 = 0x23  # Unsigned 32-bit integer
    I8 = 0x28  # Signed 8-bit integer
    I16 = 0x29  # Signed 16-bit integer
    I32 = 0x2B  # Signed 32-bit integer
    F32 = 0x39  # Single precision floating point - 32bit
    STR = 0x42  # Character string or byte array

class ScpCliMessage():

    def __init__(self):
        self.scp_msg = []
    
    def assemle(self, data):

        ### Assmeble header
        # Frame control -> normal frame
        self.scp_msg.append( 0x00 )

        # Command type -> write
        self.scp_msg.append( ScpCommand.WRITE )

        # Cluster ID -> Command Line Interface (ID: 0xFC49)
        self.scp_msg.append( 0x49 )
        self.scp_msg.append( 0xFC )

        # TSN -> 0
        self.scp_msg.append( 0x00 )

        # Reserved
        self.scp_msg.append( 0x00 )
        self.scp_msg.append( 0x00 )
        self.scp_msg.append( 0x00 )

        ### Assemble payload
        # Attribute ID -> Receive end-point (ID: 0x0001)
        self.scp_msg.append( 0x01 )
        self.scp_msg.append( 0x00 )

        # Attribute data type
        self.scp_msg.append( ScpAttrType.STR )  

        # Attribute value 
        self.scp_msg.append( len(data) + 2 ) # Add 2 bytes for CR + LR
        for ch in data:
            self.scp_msg.append( ord(ch) )
        self.scp_msg.append( 0x0D ) # CR
        self.scp_msg.append( 0x0A ) # LR

        # Add STPS transport layer
        stps_msg = StpsMessage( self.scp_msg, 0x0000 ).get_msg()

        return ( stps_msg + self.scp_msg )


    
class ScpParser():

    def __init__(self):
        self.stpsParser = StpsParser()

    def parse(self, data):
        scp_payload = self.stpsParser.parse( data )

        if scp_payload:
            attr_size = scp_payload[11]

            scp_payload_str = ''.join(chr(b) for b in scp_payload[12:12+attr_size])

            return scp_payload_str
        else:
            return None



# ===============================================================================
#
#  @brief:   STPS Message
#
# ===============================================================================  
class StpsMessage():

    # ===============================================================================
    # @brief:   STPS constructor
    #
    # @param[in]:   scp_msg     - SCP message
    # @param[in]:   dev_id      - Device ID 
    # @return:      void
    # ===============================================================================  
    def __init__(self, scp_msg, dev_id):
        
        # Add header
        self.msg = []
        self.msg.append( 0xA9 )
        self.msg.append( 0x65 )

        # Calculate scp message lenght
        scp_msg_len = int( len( scp_msg ))

        _scp_msg_len_low = ( scp_msg_len & 0xFF )
        _scp_msg_len_high = (( scp_msg_len >> 8 ) & 0xFF )

        # Add lenght to msg
        self.msg.append( _scp_msg_len_low )
        self.msg.append( _scp_msg_len_high )

        # Add device id 
        _dev_id_low     = ( dev_id & 0xFF )
        _dev_id_high    = (( dev_id >> 8 ) & 0xFF )

        self.msg.append( _dev_id_low )
        self.msg.append( _dev_id_high )

        # Reserved
        self.msg.append( 0x00 )

        # Calcualate CRC
        _crc_8 = self.__calc_crc( scp_msg, scp_msg_len )
        _crc_8 ^= self.__calc_crc( [_scp_msg_len_low, _scp_msg_len_high], 2 )
        _crc_8 ^= self.__calc_crc( [_dev_id_low, _dev_id_high], 2 )

        # Add CRC
        self.msg.append( _crc_8 & 0xFF )

    # ===============================================================================
    # @brief:   Get STPS assembled message
    #
    # @return:      self.msg - STPS message
    # ===============================================================================  
    def get_msg(self):
        return self.msg

    # ===============================================================================
    # @brief:   Calculate CRC
    #
    # @param[in]:   data    - SCP payload data
    # @param[in]:   size    - Size of SCP payload data
    # @return:      void
    # ===============================================================================  
    def __calc_crc(self, data, size):

        poly = 0x07
        seed = 0x34
        crc8 = seed

        for i in range(size):
            crc8 = ( crc8 ^ data[i] )

            for j in range(8):
                if crc8 & 0x80:
                    crc8 = (( crc8 << 1 ) ^ poly )
                else:
                    crc8 = crc8 << 1

        return crc8 & 0xFF


import time

class StpsParser():

    Idle = 0
    Header = 1
    Payload = 2


    def __init__(self):
        self.buf = []
        self.last_time = time.time()
        self.mode = StpsParser.Idle

    def parse(self, data):

        if data:
            # convert to integers
            self.buf.append( int.from_bytes(data, byteorder='big') )
            self.last_time = time.time()         

        if self.mode == StpsParser.Idle:
            self.mode = StpsParser.Header
            rtn_status = None

        elif self.mode == StpsParser.Header:
            rtn_status = self.__parse_header()

        elif self.mode == StpsParser.Payload:   
            rtn_status = self.__parse_payload()

	    # Check for timeout only when parser is in the middle of work
	    # If there is no incoming data then timeout handling is not relevant!
        if self.mode != StpsParser.Idle:
            if ( time.time() - self.last_time ) > 0.1: # 100ms timeout
                self.mode = StpsParser.Idle
                self.buf = []

                return None


        # Return "None" if message is not complete
        return rtn_status


    def __parse_header(self):
        
        if len( self.buf ) >= 8:

            # Check for preamble
            if self.buf[0] == 0xA9 and self.buf[1] == 0x65:
                self.mode = StpsParser.Payload
                return None # Still not a complete message
            
            else:
                # Reset buffer
                self.buf = []
                self.mode = StpsParser.Idle
                return None
        else:
            return None
            
    def __parse_payload(self):

        payload_len = self.buf[2] + ( self.buf[3] << 8 )

        if len( self.buf ) >= ( payload_len + 8 ):  # 8 bytes for STPS
            payload = self.buf[8:payload_len+8]

            # Reset buffer
            self.buf = []
            self.mode = StpsParser.Idle

            return payload  # Message received

            # TODO: Check CRC here
            #crc_calc = self.__calc_crc( payload, payload_len )
            #crc_calc ^= self.__calc_crc( payload, payload_len )
            #crc_calc ^= self.__calc_crc( payload, payload_len )




    # ===============================================================================
    # @brief:   Calculate CRC
    #
    # @param[in]:   data    - SCP payload data
    # @param[in]:   size    - Size of SCP payload data
    # @return:      void
    # ===============================================================================  
    def __calc_crc(self, data, size):

        poly = 0x07
        seed = 0x34
        crc8 = seed

        for i in range(size):
            crc8 = ( crc8 ^ data[i] )

            for j in range(8):
                if crc8 & 0x80:
                    crc8 = (( crc8 << 1 ) ^ poly )
                else:
                    crc8 = crc8 << 1

        return crc8 & 0xFF



#################################################################################################
##  END OF FILE
#################################################################################################  
