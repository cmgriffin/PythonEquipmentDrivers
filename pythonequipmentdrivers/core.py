import pyvisa
from pyvisa import VisaIOError

# Globals
rm = pyvisa.ResourceManager()


# Utility Functions
def get_devices_addresses():
    """
    returns a list of the addresses of peripherals connected to the computer
    """
    return rm.list_resources()


def identify_devices(verbose=False):
    """
    identify_connections(verbose=False)

    verbose (optional): bool, if True address and identicaion information is
    printed to the screen in addition to return the data in a structure,
    default behavior is to print the information.

    Queries devices connected for IDN response
    appends addresses with valid responses to a tuple with its response

    returns:
        ((address_1, idn_response_1),
         (address_2, idn_response_2),
         ...
         (address_n, idn_response_n))
    """
    scpi_devices = []
    for address in rm.list_resources():
        try:
            device = rm.open_resource(address)
            response = device.query("*IDN?")
            scpi_devices.append((address, response))
            device.close()

            if verbose:
                print(f"{len(scpi_devices)-1}:")
                print(f"\taddress: {address}")
                print(f"\tresponse: {response}\n")

        except pyvisa.Error:
            if verbose:
                print(f"Invalid IDN query reponse from address {address}\n")
            device.close()
            continue

    return scpi_devices


class Scpi_Instrument():

    _serial_instruments = []

    def __init__(self, address, **kwargs):
        self.address = address
        self.instrument = self.open_instrument(address)
        self.timeout = kwargs.get('timeout', 1000)

    def open_instrument(self, address):
        """
        open_instrument(address)

        Replaces the normal rm.open_resource so that serial devices can be
        handled specially. A least with the pyvisa-py libarary, opening the
        same serial device multiple times results in a SerialException being
        raised. A class attribute list of already opened serial ports is 
        maintained. If a Serial Exception is raised, the list will be searched
        for a matching already opened port

        Args:
            address (str): Visa style resource string

        Returns:
            pyvisa.Resource: Same resource instance as returned by
            the pyvisa ResourceManager
        """

        if "ASRL" in address.upper():
            # only necessary for serial devices
            for addr, inst in self._serial_instruments:
                if addr in address.upper():
                    print(f'matched {address} with {addr}')
                    return inst
            # if no matching address was found then we need to open it
            instrument = rm.open_resource(address)
            # append the short form ASRLn to the list
            address_short = address.split("::")[0]
            type(self)._serial_instruments.append((address_short, instrument))
            return instrument
        else:
            # any other type of device, just open it normally
            return rm.open_resource(address)

    def write(self, message: str, **kwargs):
        """
        write(write_str, **kwargs)

        Pass-through function which forwards the contents of 'write_str' to
        the device. 

        The is to allow subclass modifications where further processing might
        need to to performed

        Args:
            message: string, scpi query to be passed through to the device.
            **kwargs: passed to pyvisa.resource respective method

        """
        return self.instrument.write(message, **kwargs)

    def read(self, **kwargs):
        """
        read(**kwargs)

        Pass-through function which reads the device, returning the response
        without any processing.

        The is to allow subclass modifications where further processing might
        need to to performed

        Args:
            **kwargs: passed to pyvisa.resource respective method

        """
        return self.instrument.read(**kwargs)

    def query(self, message: str, **kwargs):
        """
        query(query_str, **kwargs)

        Pass-through function which forwards the contents of 'query_str' to
        the device and returns the response without further processing.

        The is to allow subclass modifications where further processing might
        need to to performed

        Args:
            message: string, scpi query to be passed through to the device.
            **kwargs: passed to pyvisa.resource respective method

        """
        return self.instrument.query(message, **kwargs)

    @property
    def idn(self):
        """
        idn

        Identify Query

        Returns a string that uniquely identifies the instrument. The IDN query
        sent to the instrument is one of the IEEE 488.2 Common Commands and
        should be supported by all SCPI compatible instruments.

        Returns:
            str: uniquely identifies the instrument
        """
        return self.query('*IDN?')

    def cls(self, **kwargs) -> None:
        """
        cls(**kwargs)

        Clear Status Command

        Clears the instrument status byte by emptying the error queue and
        clearing all event registers. Also cancels any preceding *OPC command
        or query. The CLS command sent to the instrument is one of the
        IEEE 488.2 Common Commands and should be supported by all SCPI
        compatible instruments.

        Returns:
            None
        """

        self.write('*CLS', **kwargs)

    def rst(self, **kwargs) -> None:
        """
        rst()

        Reset Command

        Executes a device reset and cancels any pending *OPC command or query.
        The RST command sent to the instrument is one of the IEEE 488.2 Common
        Commands and should be supported by all SCPI compatible instruments.
        """

        self.write('*RST', **kwargs)

    def set_local(self):
        """
        set_local()

        Set the instument to local mode

        Attempts to send the go to local command if the device has a ren function.
        Should be overriden to customize for a particular instument
        """
        try:
            # generic set local method for GPIB, USB, TCIP
            self.instrument.control_ren(
                pyvisa.constants.RENLineOperation.address_gtl)
        except (AttributeError, VisaIOError):
            # not a device that has a ren function
            pass

    @property
    def timeout(self):
        return self.instrument.timeout

    @timeout.setter
    def timeout(self, timeout):
        self.instrument.timeout = timeout
        return None

    def __repr__(self):

        def_str = f"{self.__class__.__name__}"
        def_str += f"({self.address}, timeout={self.timeout})"

        return def_str

    def __str__(self):
        return f'Instrument ID: {self.idn}\nAddress: {self.address}'

    def __eq__(self, obj):
        """
        __eq__(obj)

        Args:
            obj (object): object to compare

        Returns:
            bool: True if the objects are both instances of Scpi_Instrument
                (or any class that inherits from Scpi_Instrument) and have the
                same address and class name. Otherwise False.
        """

        if not isinstance(obj, Scpi_Instrument):
            return False

        if not (self.address == obj.address):
            return False

        if not (self.__class__.__name__ == obj.__class__.__name__):
            return False

        return True

    def __ne__(self, obj):
        """
        __ne__(obj)

        Args:
            obj (object): object to compare

        Returns:
            bool: whether or not to object are not equal. Defined as the
                inverse of the result from __eq__
        """

        return not self.__eq__(obj)

    def send_raw_scpi(self, command_str: str, **kwargs) -> None:
        """
        send_raw_scpi(command_str, **kwargs)

        Pass-through function which forwards the contents of 'command_str' to
        the device. This function is intended to be used for API calls for
        functionally that is not currently supported. Can only be used for
        commands, will not return queries.

        Args:
            command_str: string, scpi command to be passed through to the
                device.

        Returns:
            None
        """

        self.write(command_str, **kwargs)

    def query_raw_scpi(self, query_str: str, **kwargs) -> str:
        """
        query_raw_scpi(query, **kwargs)

        Pass-through function which forwards the contents of 'query_str' to
        the device, returning the response without any processing. This
        function is intended to be used for API calls for functionally that is
        not currently supported. Only to be used for queries.

        Args:
            query_str: string, scpi query to be passed through to the device.

        """

        return self.query(query_str, **kwargs)

    def read_raw_scpi(self, **kwargs) -> str:
        """
        read_raw_scpi(**kwargs)

        Pass-through function which reads the device, returning the response
        without any processing. This function is intended to be used for API
        calls for functionally that is not currently supported.
        Only to be used for read.
        """

        return self.read(**kwargs)


class Gpib_Interface:
    """
    Class for instantiation of the GPIB interface device (typically plugs into
    the computer's USB port). Since GPIB is a bus based interface layer,
    all instruments that utilize the bus can be accessed with group commands,
    if supported, to perform syncronized tasks.
    """

    def __init__(self, address, **kwargs) -> None:
        self.address = address
        self.instrument = rm.open_resource(self.address)

    def group_execute_trigger(self, *trigger_devices):
        """
        Sends the group execture trigger (GET) command to the devices specified

        *trigger_devices: Device instances to trigger
        """
        visa_handles = [n.instrument for n in trigger_devices]
        self.instrument.group_execute_trigger(*visa_handles)


if __name__ == "__main__":
    pass
