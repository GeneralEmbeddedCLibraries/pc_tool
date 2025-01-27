## Copyright (c) 2025 Ziga Miklosic
## All Rights Reserved
## This software is under MIT licence (https://opensource.org/licenses/MIT)
#################################################################################################
##
## @file:       SerialComPort.py
## @brief:      Serial COM port communication
## @date:		22.07.2022
## @author:		Ziga Miklosic
##
#################################################################################################

#################################################################################################
##  IMPORTS
#################################################################################################
from dataclasses import dataclass
from threading import Thread
import serial
import serial.tools.list_ports
from threading import Thread
from com.IpcProtocol import IpcMsg, IpcMsgType

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
#
#  @brief:   Serial Communication as process
#
# ===============================================================================  
class SerialComunication():

    # ===============================================================================
    # @brief:   Constructor
    #
    # @param[in]:   rx_queue    - Reception queue (to embedded device)
    # @param[in]:   tx_queue    - Transmition queue (to embedded device)
    # @return:      void
    # ===============================================================================
    def __init__(self, rx_queue, tx_queue):
        
        # Communication queues
        self.__rx_q = rx_queue
        self.__tx_q = tx_queue

        # Serial com port
        self.port = SerialComPort()

        # Create and start process
        self.process = Thread(name="Serial Communication", target=self.run)  
        self.__alive = True
        self.process.start()


    # ===============================================================================
    # @brief:   Desctructor
    #
    # @return:      void
    # ===============================================================================
    def __del__(self):
        self.__alive = False
        self.port.disconnect()

    # ===============================================================================
    # @brief:   Send message via IPC
    #
    # @param[in]:   msg - Message to be sended
    # @return:      void
    # ===============================================================================
    def __ipc_send_msg(self, msg):
        self.__tx_q.put(msg)

    # ===============================================================================
    # @brief:   Receive message from IPC
    #  
    # @return:      msg - Received message
    # ===============================================================================
    def __ipc_receive_msg(self):
       return self.__rx_q.get(block=False, timeout=0)

    # ===============================================================================
    # @brief:   Master GUI is requesing port list refresh
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_refresh_cmd(self, payload):

        # Get serial port list
        self.port.refresh()

        # Send refresh response
        msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComRefresh, payload=self.port._com_ports_list)
        self.__ipc_send_msg(msg)

    # ===============================================================================
    # @brief:   Master GUI is requesing connection
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_connect_cmd(self, payload):

        # Get COM and baudrate if specified
        if payload != None:
            self.port.port, self.port.baudrate = str(payload).split(";")

        # Connect to port
        status = self.port.connect()

        # Return message
        msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComConnect, payload=status)
        self.__ipc_send_msg(msg)

    # ===============================================================================
    # @brief:   Master GUI is requesing disconnection
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_disconnect_cmd(self, payload):
        
        # Disconnect from port
        status = self.port.disconnect()

        # Return message
        msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComDisconnect, payload=status)
        self.__ipc_send_msg(msg)

    # ===============================================================================
    # @brief:   Master GUI is receive data from embedded device
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_rx_frame_cmd(self, payload):

        # Read message from embedded device
        dev_msg = self.port.read()

        if dev_msg:
            msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComRxFrame, payload=dev_msg)
            self.__ipc_send_msg(msg)

    # ===============================================================================
    # @brief:   Master GUI is requesing to send data to embedded device
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_tx_frame_cmd(self, payload):
        
        # Send to device
        self.port.send(str(payload))

    # ===============================================================================
    # @brief:   Master GUI is requesing to send binary data to embedded device
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_tx_binary_cmd(self, payload):
        
        # Send to device
        self.port.send_binary( payload )

    # ===============================================================================
    # @brief:   Master GUI is requesting end of the thread
    #
    # @param[in]:   payload - Message payload
    # @return:      void
    # ===============================================================================
    def __ipc_kill_cmd(self, payload):
        self.__del__()

    # ===============================================================================
    # @brief:   Handle command from Master GUI via IPC
    #
    # @return:      void
    # ===============================================================================
    def __ipc_rx_hndl(self):

        # Take all messages from reception queue
        while self.__rx_q.empty() == False:

            # Get msg from queue (non-blocking)
            msg = self.__ipc_receive_msg()

            # Execute command if supported
            for key in self.__cmd_table.keys():
                if key == msg.type:
                    self.__cmd_table[key](msg.payload)  

    # ===============================================================================
    # @brief:   Handle received messages from embedded device
    #
    # @return:      void
    # ===============================================================================
    def __dev_rx_hndl(self):

        # Read message from embedded device
        dev_msg_bin = self.port.read()

        if len(dev_msg_bin) > 0:
            
            try:
                # Try to decode
                dev_msg = dev_msg_bin.decode( "utf-8" )
                
                # Send UTF-8 format string to Main Window process
                msg = IpcMsg(type=IpcMsgType.IpcMsgType_ComRxFrame, payload=dev_msg)
                self.__ipc_send_msg(msg)
            except:
                pass
            
            # Send binary message to MainWindow process
            msg_bin = IpcMsg(type=IpcMsgType.IpcMsgType_ComRxBinary, payload=dev_msg_bin)
            self.__ipc_send_msg(msg_bin)


    # ===============================================================================
    # @brief:   Main process loop
    #
    # @return:      void
    # ===============================================================================
    def run(self):

        # =============================================================================================
        # IPC Command Function Table
        # Specified here actions for received messages via IPC mechanism        
        self.__cmd_table = {    IpcMsgType.IpcMsgType_ComRefresh :      self.__ipc_refresh_cmd,
                                IpcMsgType.IpcMsgType_ComConnect :      self.__ipc_connect_cmd,  
                                IpcMsgType.IpcMsgType_ComDisconnect :   self.__ipc_disconnect_cmd,  
                                #IpcMsgType.IpcMsgType_ComRxFrame :      self.__ipc_rx_frame_cmd,  
                                IpcMsgType.IpcMsgType_ComTxFrame :      self.__ipc_tx_frame_cmd,  
                                IpcMsgType.IpcMsgType_ComTxBinary :      self.__ipc_tx_binary_cmd,  
                                IpcMsgType.IpcMsgType_ComFinished :      self.__ipc_kill_cmd,  
        }
        
        # =============================================================================================      

        # Run process until end
        while self.__alive:
        
            # Handle IPC commands from MasterGUI
            self.__ipc_rx_hndl()

            # Handle received msg from embedded device
            self.__dev_rx_hndl()


# ===============================================================================
#
#  @brief:   COM Port Description
#
# ===============================================================================  
class ComPortDesc():

    def new(self, device, desc, com_num):

        port_desc = {   "device"        : device, 
                        "description"   : desc,
                        "com_num"       : com_num
                    }   

        return port_desc

# ===============================================================================
#
#  @brief:   Serial COM Port 
#
# ===============================================================================  
class SerialComPort(ComPortDesc):
     
    def __init__(self):

        # Available com ports
        self._com_ports_list = []

        # Connect status
        self._is_connected = False

        self._com_port = serial.Serial()
        
        # List all available serial com ports
        #for port in serial.tools.list_ports.comports():
        #    new_port = self.new(port.device, port.description, int( port.device[3:] ))
        #    self._com_ports_list.append(new_port)
        self.refresh()

        # Com settings
        self._com_settings = {  "port"      : None,
                                "baudrate"  : 115200, 
                                "bytesize"  : serial.EIGHTBITS,
                                "parity"    : serial.PARITY_NONE,
                                "stopbits"   : serial.STOPBITS_ONE,
                                "r_timeout" : 0,                    # Read timeout [s] - NON-BLOCKING
                                "w_timeout" : 0,                    # Write timeout [s] - NON-BLOCKING
                                "xonxoff"   : False,                # Software flow control
                                "rtscts"    : False,                # Hardware flow control
                                "dsrdtr"    : False,                # Hardware flow control
                                "b_timeout" : None                  # Inter-Character timeout
                            }

    def connect(self):
        self._is_connected = False

        # Open port
        try:
            self._com_port = serial.Serial( port                = self._com_settings["port"],
                                            baudrate            = self._com_settings["baudrate"],
                                            bytesize            = self._com_settings["bytesize"],
                                            stopbits            = self._com_settings["stopbits"],
                                            timeout             = self._com_settings["r_timeout"],
                                            write_timeout       = self._com_settings["w_timeout"],   
                                            xonxoff             = self._com_settings["xonxoff"],
                                            rtscts              = self._com_settings["rtscts"],
                                            dsrdtr              = self._com_settings["dsrdtr"],
                                            inter_byte_timeout  = self._com_settings["b_timeout"]
                                         )
            # Return state
            self._is_connected = self._com_port.is_open
            return self._is_connected
    
        except ValueError:
            print("value error")

        except serial.SerialException:
            print("serial exception")

    def disconnect(self):
        self._com_port.close()
        self._is_connected = False
        return not self._com_port.is_open

    def info(self):
        return self._com_ports_list

    def refresh(self):
        self._com_ports_list = []

         # List all available serial com ports
        for idx, port in enumerate(serial.tools.list_ports.comports()):
            new_port = self.new(port.device, port.description, None)
            self._com_ports_list.append(new_port)    

    def settings(self):
        print("port: %s"        % self.port)
        print("baudrate: %s"    % self.baudrate)
        print("bytesize: %s"    % self.bytesize)
        print("parity: %s"      % self.parity)
        print("stopbits: %s"    % self.stopbits)
        print("r_timeout: %s"   % self.read_timeout)
        print("w_timeout: %s"   % self.write_timeout)

    @property
    def port(self):
        return self._com_settings["port"]

    @port.setter
    def port(self, port):
        self._com_settings["port"] = port
    
    @property
    def baudrate(self):
        return self._com_settings["baudrate"]

    @baudrate.setter
    def baudrate(self, baudrate):
        self._com_settings["baudrate"] = baudrate

    @property
    def bytesize(self):
        return self._com_settings["bytesize"]        

    @bytesize.setter
    def bytesize(self):
        self._com_settings["bytesize"] = bytesize

    @property
    def parity(self):
        return self._com_settings["parity"]     

    @parity.setter
    def parity(self, parity):
        self._com_settings["parity"] = parity

    @property
    def stopbits(self):
        return self._com_settings["stopbits"]    

    @stopbits.setter
    def stopbits(self, stopbits):
        self._com_settings["stopbits"] = stopbits

    @property
    def read_timeout(self):
        return self._com_settings["r_timeout"]         

    @read_timeout.setter
    def read_timeout(self, timeout):
        self._com_settings["r_timeout"] = timeout

    @property
    def write_timeout(self):
        return self._com_settings["w_timeout"]    

    @write_timeout.setter
    def write_timeout(self, timeout):
        self._com_settings["w_timeout"] = timeout  

    def is_connected(self):
        return self._is_connected

    def send(self, str):
        try:
            if self.is_connected():
                self._com_port.write(self.__unicode_str__(str))
        except:
            pass

    def send_binary(self, bin):
        try:
            if self.is_connected():
                self._com_port.write( bin )
        except:
            pass

    def write(self, str):
        # NOTE: Implicit termination with CR
        self._com_port.write(self.__unicode_str__(str + '\r'))

    def read(self):

        rx_data = []
        try:
            if self.is_connected():
                rx_data = self._com_port.read()
        except:
            pass

        return rx_data

    def __unicode_str__(self, str):
        return str.encode("utf-8")


#################################################################################################
##  END OF FILE
#################################################################################################  

