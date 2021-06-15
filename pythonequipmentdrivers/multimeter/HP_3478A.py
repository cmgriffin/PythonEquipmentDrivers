from pythonequipmentdrivers import Scpi_Instrument as _Scpi_Instrument


class HP_3478A(_Scpi_Instrument):
    def __init__(self, address, **kwargs):
        super().__init__(address, **kwargs)
        self.factor = kwargs.get('factor', 1.0)
        self.valid_modes = {'VDC': "F1",
                            'VAC': "F2",
                            'ADC': "F5",
                            'AAC': "F6",
                            'OHMS': "F3"}
        self.ranges = {
            'VDC': {0.03: 'R-2', 0.3: 'R-1', 3.0: 'R0', 30.0: 'R1',
                    300.0: 'R2'},
            'VAC': {0.3: 'R-1', 3.0: 'R0', 30.0: 'R1', 300.0: 'R2'},
            'ADC': {0.3: 'R-1', 3.0: 'R0'},
            'AAC': {0.3: 'R-1', 3.0: 'R0'},
            'OHMS': {30: 'R1', 300: 'R1', 3E3: 'R3',
                     3E4: 'R4', 3e5: 'R5', 3E6: 'R6', 3E7: 'R7'}
        }
        self.triggers = {'INTERNAL': 'T1', 'EXTERNAL': 'T2', 'SINGLE': 'T3'}
        self._current_mode = None
        self.set_mode('VDC')

    def set_mode(self, mode):
        """
        set_mode(mode)

        mode: str, type of measurement to be done
            valid modes are: 'VDC', 'VAC', 'ADC', 'AAC', 'OHMS'
            which correspond to DC voltage, AC voltage, DC current, AC current,
            frequency, resistence respectively (not case sensitive)

        Configures the multimeter to perform the specified measurement
        """
        mode = mode.upper()
        if mode in self.valid_modes:
            self._current_mode = mode
            self.instrument.write(self.valid_modes[mode])
        else:
            raise ValueError("Invalid mode option")
        return None

    def set_resolution(self, digits):
        """
        set_resolution(digits)

        Sets the resolution of the DMM in digits + 0.5

        Args:
            digits (int): Number of digits displayed: 3, 4, 5. 
            Corresponds to 0.1, 1, and 10 NPLC
        """
        if digits in range(3, 5+1):
            self.instrument.write(f'N{digits}')
        else:
            raise ValueError('Invalid resolution setting')

    def set_trigger(self, trigger):
        """
        set_trigger(trigger)

        Args:
            trigger (str): 'INTERNAL', 'EXTERNAL', or 'SINGLE'
            Note both external and single respond to GET. 
            SINGLE creates an immediate one shot measurement.
        """
        trigger = trigger.upper()
        if trigger in self.triggers:
            self.instrument.write(self.triggers[trigger])
        else:
            raise ValueError('Invalid trigger setting')

    def get_mode(self):
        """
        get_mode()

        retrives type of measurement the multimeter is current configured to
        perform.

        returns: str
        """
        return self._current_mode

    def set_range(self, max_value):
        """
        set_range(max_value)

        Args:
            max_value (float): Maximum measurement value expected
        """
        for range_, command in self.ranges[self._current_mode].items():
            if max_value < range_:
                self.instrument.write(command)
                return
        raise ValueError(f'{max_value=} is greater than highest range')

    def set_autozero(self, enabled=True):
        """
        Enable/disable internal autozero function. 
        Disabling will reduce measurement time.

        Args:
            enabled (bool, optional): Defaults to True.
        """
        cmd = 'Z1' if enabled else 'Z0'
        self.instrument.write(cmd)

    def set_display(self, msg='', disable_display_udpates=False):
        """
        Print a message on the display and optionally pause display updating.

        Args:
            msg (str, optional): Message, up to 12 chars. No message resets the
            display back to normal mode Defaults to ''.
            disable_display_udpates (bool, optional): Pause display updates to
            speed up measurements. Defaults to False.
        """
        if len(msg) > 0:
            if disable_display_udpates:
                self.instrument.write('D3'+msg)
            else:
                self.instrument.write('D2'+msg)
        else:
            self.instrument.write('D1')

    def get_status(self, print_verbose=True):
        """
        Query the DMM status register

        Args:
            print_verbose (bool, optional): Print out a verbose description of 
            the status. Defaults to True.

        Returns:
            tuple: Values of the status bytes
        """
        self.instrument.write('B')
        raw = tuple(self.instrument.read_bytes(5))

        return raw

    def _measure_signal(self):
        """
        _measure_signal()

        returns the value of the current measurement selected on the
        multimeter display

        returns: float
        """
        return float(self.instrument.read())

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
            return self._measure_signal()

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
            return self._measure_signal()

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
            return self._measure_signal()

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
            return self._measure_signal()

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
            return self._measure_signal()
