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
from dataclasses import dataclass
import time

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
        # NOTE: DeviceID=2 for USB communication
        stps_msg = StpsMessage( self.scp_msg, 2 ).get_msg()

        return ( stps_msg + self.scp_msg )


# ===============================================================================
#
#  @brief:   SCP Message
#
# ===============================================================================  
class ScpParser():

    def __init__(self):
        self.stpsParser = StpsParser()

    # ===============================================================================
    # @brief:   Parse SCP message
    #
    # @param[in]:   data    - Data to parse
    # @return:      None    - If message is not complete
    #               str     - If message is complete
    # ===============================================================================
    def parse(self, data):

        # Parse STPS (it will return SCP msg if complete)
        scp_msg = self.stpsParser.parse( data )

        # Check if message is complete
        if scp_msg:

            # Parse SCP layer
            cluster_id = scp_msg[2] + ( scp_msg[3] << 8 )
            cmd_type = scp_msg[1]

            # Expectiong only CLI cluster and write command
            if cluster_id == 0xFC49 and cmd_type == ScpCommand.WRITE:

                # Get attribute info
                attr_id = scp_msg[8] + ( scp_msg[9] << 8 )
                attr_type = scp_msg[10]
                attr_size = scp_msg[11]

                # Check if attribute is Transmit-endpoint 
                # and if it is string type
                if attr_id == 0x0000 and attr_type == ScpAttrType.STR:
                    
                    # Convert to string
                    scp_payload_str = ''.join(chr(b) for b in scp_msg[12:12+attr_size])
                    return scp_payload_str
                
                # Invalid attribute
                else:
                    return None

            # Invalid message
            else:
                return None
            
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

# ===============================================================================
#
#  @brief:   STPS Parser
#
# ===============================================================================  
class StpsParser():

    # Parse engine modes
    Idle = 0
    Header = 1
    Payload = 2

    def __init__(self):
        self.buf = []
        self.last_time = time.time()
        self.mode = StpsParser.Idle

    # ===============================================================================
    # @brief:   Parse incoming data
    #
    #   If msg is comple and valid it return complete SCP message!
    #
    # @param[in]:   data    - Incoming data to parse
    # @return:      None    - If message is not complete or invalid
    #               scp_msg - If message is complete and valid
    # =============================================================================== 
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

    # ===============================================================================
    # @brief:   Parse header of the incoming data
    #
    # @return:      None    - If header is not complete or invalid
    #               None    - If header is complete but payload is not yet complete
    # ===============================================================================
    def __parse_header(self):
        
        # Header received
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
            
    # ===============================================================================
    # @brief:   Parse payload of the incoming data
    #
    # @return:      None    - If payload is not complete or invalid
    #               payload - If payload is complete and valid
    # =============================================================================== 
    def __parse_payload(self):

        # Get payload length
        payload_length = self.buf[2] + ( self.buf[3] << 8 )

        # All bytes received
        if len( self.buf ) >= ( payload_length + 8 ):  # 8 bytes for STPS
            
            # Get packet data
            payload = self.buf[8:payload_length+8]
            devid = self.buf[4] + ( self.buf[5] << 8 )
            crc = self.buf[7]

            # Calculate crc
            crc_calc = self.__calc_crc8( payload )
            crc_calc ^= self.__calc_crc8( [ payload_length & 0xFF, ( payload_length>>8 ) & 0xFF ] )            
            crc_calc ^= self.__calc_crc8( [ devid & 0xFF, ( devid>>8 ) & 0xFF ] )            

            # Reset buffer
            self.buf = []
            self.mode = StpsParser.Idle

            if crc_calc == crc:
                return payload  # Message received
            else:
                return None         


    # ===============================================================================
    # @brief:   Calculate CRC
    #
    # @param[in]:   data    - SCP payload data
    # @param[in]:   size    - Size of SCP payload data
    # @return:      void
    # ===============================================================================      
    def __calc_crc8(self, data):
        poly = 0x07
        seed = 0x34
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
