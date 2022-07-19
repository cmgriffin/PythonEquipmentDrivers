import logging
from pyvisa.constants import BufferOperation
from pythonequipmentdrivers import Scpi_Instrument

logger = logging.getLogger(__name__)


class Fluke_45(Scpi_Instrument):
    """
    Fluke_45(address, factor=1)

    address : str, address of the connected multimeter

    factor: float, multiplicitive scale for all measurements defaults to 1.

    object for accessing basic functionallity of the Fluke 45 Multimeter.
    The factor term allows for measurements to be multiplied by some number
    before being returned. For example, in the case of measuring the voltage
    across a current shunt this factor can represent the conductance of the
    shunt. This factor defaults to 1 (no effect on measurement).

    For additional commands see programmers Manual:
    http://www.ece.ubc.ca/~eng-services/files/manuals/Man_DMM_fluke45.pdf
    """

    ranges = (
        ({'VDC', 'VAC'}, (
            ({'M', 'F'}, ((0.3, 1), (3, 2), (30, 3), (300, 4), (1000, 5))),
            ({'S'}, ((0.1, 1), (1, 2), (10, 3), (100, 4), (1000, 5)))
        )),
        ({'ADC', 'AAC'}, (
            ({'M', 'F'}, ((0.03, 1), (0.1, 2), (10, 3))),
            ({'S'}, ((0.01, 1), (0.1, 2), (10, 3)))
        )),
        ({'OHM'}, (
            ({'M', 'F'}, ((300, 1), (3E3, 2), (3E4, 3),
             (3E5, 4), (3E6, 5), (3E7, 6), (3E8, 7))),
            ({'S'}, ((100, 1), (1E3, 2), (1E4, 3),
             (1E5, 4), (1E6, 5), (1E7, 6), (1E8, 7)))
        )),
        ({'FREQ'}, (
            ({'S', 'M', 'F'}, ((1E3, 1), (1E4, 2), (1E5, 3),
                               (1E6, 4), (1E7, 5))),
        )),
    )

    def __init__(self, address, **kwargs):
        super().__init__(address, **kwargs)
        self.factor = kwargs.get('factor', 1.0)
        self.valid_modes = ('AAC', 'ADC', 'VAC', 'VDC',
                            'OHMS', 'FREQ', 'CONT', 'DIODE')
        # if fluke 45 is using rs232 special considerations need to be taken
        if "asrl" in address.lower():
            self._is_serial = True
            self.instrument.flush(BufferOperation.discard_receive_buffer)
            self.instrument.read_termination = '\r\n'
            self.instrument.write_termination = '\r\n'
        else:
            self._is_serial = False
        return None

    def write(self, message, **kwargs):
        """
        write(command_str)

        command_str: string, scpi command to be passed through to the device.

        Pass-through function which forwards the contents of 'command_str' to
        the device. This function is intended to be used for API calls for
        functionally that is not currently supported. Can only be used for
        commands, will not return queries.

        A special version of this command for the Fluke45 due to issues with
        pyvisa handling it natively
        """
        super().write(message, **kwargs)
        if self._is_serial:
            # serial version returns "=>" if the command is a success
            # otherwise "?>"
            # log this with an error so the user can see if something is wrong
            resp = self.read()
            if resp != "=>":
                logger.error(f' response to command was {resp}')

    def query(self, message, **kwargs):
        """
        query(query)

        query_str: string, scpi query to be passed through to the device.

        Pass-through function which forwards the contents of 'query_str' to
        the device, returning the response without any processing. This
        function is intended to be used for API calls for functionally that is
        not currently supported. Only to be used for queries.
        """
        ret = super().query(message, **kwargs)
        if self._is_serial:
            # serial version returns "=>" if the command is a success
            # otherwise "?>"
            # log this with an error so the user can see if something is wrong
            resp = self.read()
            if resp != "=>":
                logger.error(f'{self} response to command was {resp}')
        return ret

    def fetch_data(self):
        """
        _fetch_data()

        returns the value of the current measurement selected on the
        multimeter display

        returns: float
        """
        response = self.query("VAL?")
        return self.factor*float(response)

    def enable_cmd_emulation_mode(self):
        """
        enable_cmd_emulation_mode()

        For use with a Fluke 8845A. Enables the Fluke 45 command set emulation
        mode
        """
        self.write("L2")

    def set_local(self):
        """
        set_local()

        Set the DMM to local mode
        """
        if self._is_serial:
            # there is a specific serial command
            self.write('LOCS')
        else:
            # use the GPIB method
            super().set_local()

    def _get_range_number(self, value, reverse_lookup=False):
        mode = self.get_mode()
        rate = self.get_rate()
        for valid_modes, rates in self.ranges:
            if mode not in valid_modes:
                continue
            for valid_rates, max_values in rates:
                if rate not in valid_rates:
                    continue
                for range_, command in max_values:
                    if value < range_ and not reverse_lookup:
                        return command
                    elif command == value and reverse_lookup:
                        return range_
                raise ValueError(f"{value=} is greater than highest range")

    def set_range(self, signal_range=None, n=None, auto_range=False):
        """
        set_range(n, auto_range=False)

        n: int, range mode to set
        auto_range: bool, whether to enable autoranging (default is False)

        Set the current range setting used for measurements.
            valid settings are the integers 1 through 7, meaning of the index
            depends on which measurement is being performed.
        if the auto_range flag is set to True the device will automaticly
        determine which range to be in base on the signal level default is
        False.

        returns: int
        """

        if auto_range:
            self.write("AUTO")
        elif n is None:
            n = self._get_range_number(signal_range)
        if n in range(0, 7):
            self.write(f"RANGE {n}")
        else:
            raise ValueError("Invalid range option, should be 1-7")

    def get_range(self):
        """
        get_range()

        Retrieve the current range setting used for measurements.
        Return value is an index from 1 to 7, meaning of the index depends
        on which measurement is being performed.

        returns: int
        """

        n = int(self.query("RANGE1?"))
        return self._get_range_number(n, reverse_lookup=True)

    def set_rate(self, rate):
        """
        set_rate(rate)

        rate: str, speed of sampling
            valid options are 'S','M', or 'F' for slow, medium, and fast
            respectively (not case sensitive)

        adjusts the sampling rate for multimeter measurements
        """

        rate = rate.upper()
        if rate in ['S', 'M', 'F']:
            self.write(f"RATE {rate}")
        else:
            raise ValueError("Invalid rate option, should be 'S','M', or 'F'")
        return None

    def get_rate(self):
        """
        get_rate()

        Retrives the sampling rate setting for multimeter measurements
        returns: str
        """

        response = self.query("RATE?")
        return response.rstrip('\r\n')

    def set_mode(self, mode):
        """
        set_mode(mode)

        mode: str, type of measurement to be done
            valid modes are 'AAC', 'ADC','VAC', 'VDC','OHMS', 'FREQ', 'CONT'
            which correspond to AC current, DC current, AV voltage, DC voltage,
            resistence, frequency, and continuity respectively (not case
            sensitive)

        Configures the multimeter to perform the specified measurement
        """

        mode = mode.upper()
        if mode in self.valid_modes:
            self.write(f"{mode}")
        else:
            raise ValueError("Invalid mode option, valid options are: "
                             + f"{', '.join(self.valid_modes)}")
        return None

    def get_mode(self):
        """
        get_mode()

        retrives type of measurement the multimeter is current configured to
        perform.

        returns: str
        """

        response = self.query("FUNC1?")
        return response.rstrip('\r\n')

    def measure_voltage(self):
        """
        measure_voltage()

        returns float, measurement in Volts DC

        Measure the voltage present at the DC voltage measurement terminals.
        If the meter is not configured to measure DC voltage this will raise an
        exception. This can be remedied by setting the meaurement mode with the
        set_mode method.

        """
        if self.get_mode() != 'VDC':
            raise IOError("Multimeter is not configured to measure voltage")
        else:
            return self.fetch_data()

    def measure_voltage_rms(self):
        """
        measure_voltage_rms()

        returns float, measurement in Volts rms

        Measure the voltage present at the AC voltage measurement terminals.
        If the meter is not configured to measure AC voltage this will raise an
        exception. This can be remedied by setting the meaurement mode with the
        set_mode method.

        """
        if self.get_mode() != 'VAC':
            raise IOError("Multimeter is not configured to measure AC voltage")
        else:
            return self.fetch_data()

    def measure_current(self):
        """
        measure_current()

        returns float, measurement in Amperes DC

        Measure the current present through the DC current measurement
        terminals. If the meter is not configured to measure DC current this
        will raise an exception. This can be remedied by setting the meaurement
        mode with the set_mode method.

        """
        if self.get_mode() != 'ADC':
            raise IOError("Multimeter is not configured to measure current")
        else:
            return self.fetch_data()

    def measure_current_rms(self):
        """
        measure_current_rms()

        returns float, measurement in Amperes rms

        Measure the current present through the AC current measurement
        terminals. If the meter is not configured to measure AC current this
        will raise an exception. This can be remedied by setting the meaurement
        mode with the set_mode method.

        """
        if self.get_mode() != 'AAC':
            raise IOError("Multimeter is not configured to measure AC current")
        else:
            return self.fetch_data()

    def measure_resistance(self):
        """
        measure_resistance()

        returns float, measurement in Ohms

        Measure the resistance present at the resistance measurement terminals.
        If the meter is not configured to measure resistance this will raise an
        exception. This can be remedied by setting the meaurement mode with the
        set_mode method.

        """
        if self.get_mode() != 'OHMS':
            raise IOError("Multimeter is not configured to measure resistance")
        else:
            return self.fetch_data()

    def measure_frequency(self):
        """
        measure_frequency()

        returns float, measurement in Hertz

        Measure the frequency present at the frequency measurement terminals.
        If the meter is not configured to measure frequency this will raise an
        exception. This can be remedied by setting the meaurement mode with the
        set_mode method.

        """
        if self.get_mode() != 'FREQ':
            raise IOError("Multimeter is not configured to measure frequency")
        else:
            return self.fetch_data()

    def set_trigger_source(self, trigger):
        """
        set_trigger_source(source)

        Configure the meter trigger source

        source (str): { INTernal or EXTernal }
        """
        trigger_type_num = 2 if 'ext' in trigger.lower() else 1
        self.write(f"TRIGGER {trigger_type_num}")

    def trigger(self):
        """
        trigger()

        Send the trigger commmand
        """
        self.instrument.write('*TRG')

    def config(self, mode, rate, signal_range=None, range_n=None):
        """
        set_mode_adv(mode, range_n, rate)

        A one stop shop to configure the most common operating parameters

        Args:
            mode (str): type of measurement to be done
                valid modes are 'AAC', 'ADC','VAC', 'VDC','OHMS', 'FREQ', 'CONT'
                which correspond to AC current, DC current, AV voltage, DC voltage,
                resistence, frequency, and continuity respectively (not case
                sensitive)
            range_n (float, optional): Set the current range setting used for measurements.
                valid settings are the integers 1 through 7, meaning of the index
                depends on which measurement is being performed.
            signal_range (float, optional): measurement range. Defaults to 'auto'
            rate (str): speed of sampling
                valid options are 'S','M', or 'F' for slow, medium, and fast
                respectively (not case sensitive)
        """
        self.set_mode(mode)
        self.set_range(n=range_n, signal_range=signal_range)
        self.set_rate(rate)
