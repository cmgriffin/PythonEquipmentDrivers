from pythonequipmentdrivers import Scpi_Instrument as _Scpi_Instrument


class HP_3478A_AR488(_Scpi_Instrument):

    valid_modes = {'VDC': "F1",
                   'VAC': "F2",
                   'ADC': "F5",
                   'AAC': "F6",
                   'OHMS': "F3"}
    ranges = {
        'VDC': ((0.03, 'R-2'), (0.3, 'R-1'), (3.0, 'R0'), (30.0, 'R1'),
                (300.0, 'R2')),
        'VAC': ((0.3, 'R-1'), (3.0, 'R0'), (30.0, 'R1'), (300.0, 'R2')),
        'ADC': ((0.3, 'R-1'), (3.0, 'R0')),
        'AAC': ((0.3, 'R-1'), (3.0, 'R0')),
        'OHMS': ((30, 'R1'), (300, 'R2'), (3E3, 'R3'),
                 (3E4, 'R4'), (3e5, 'R5'), (3E6, 'R6'), (3E7, 'R7'))
    }
    triggers = {'INTERNAL': 'T1', 'EXTERNAL': 'T2', 'SINGLE': 'T3'}
    status_lookup = [
        ('Function Range and Number of Digits', [(0xE0, {1: 'VDC', 2: 'VAC', 3: 'OHMS',
                                                         4: 'OHMS', 5: 'ADC', 6: 'AAC', 7: 'OHMS'}),
                                                 (0x1C, {1: '30mV DC, 300mV AC, 30 ohm, 300mA AC or DC, ohms extended',
                                                         2: '300mV DC, 3V AC, 300 ohm, 3A AC or DC',
                                                         3: '3V DCM, 30V AC, 3K ohm',
                                                         4: '30V DC, 300V AC 30K ohm',
                                                         5: '300V DC, 300K ohm',
                                                         6: '3M ohm',
                                                         7: '30M ohm'}
                                                  ),
                                                 (0x03, {1: '5.5 Digit Mode', 2: '4.5 Digit Mode', 3: '3.5 Digit Mode'})]),
        ('Status Bits', ['Always 0', 'External Trigger Enabled', 'Cal RAM Enabled', 'Front/Rear SW in Front Pos',
                         '50Hz Line Freq Set', 'Auto-Zero Enabled', 'Internal Trigger Enabled']),
        ('Serial Poll Mask', ['PON SRQ switch on last POR or CLS Recv', 'Always 0', 'SRQ if CAL Procedure Failed',
                              'SRQ if SRQ key pressed', 'SRQ if HW error', 'SRQ if syntax error', 'Unused', 'SRQ as every reading avail']),
        ('Error Information', ['Always 0', 'Always 0', 'A/D link failure', 'A/D slope error',
                               'ROM selftest failed', 'RAM selftest failed', 'CAL RAM bad checksum']),
        ('DAC Value', 'RAW')
    ]

    def __init__(self, address, **kwargs):
        self.address = address
        self.gpib_address = kwargs.get('gpib_address')
        try:
            import ar488py
        except ImportError:
            raise NotImplementedError(
                "HP_3478A implementation is limited to use with the AR488/Prologix \
                 GPIB adapter"
            )
        self.intf = ar488py.Ar488(address)
        if self.gpib_address is not None:
            self.intf.target_addr = self.gpib_address
        self.factor = kwargs.get('factor', 1.0)

    def close(self):
        self.intf.close()

    def __del__(self):
        self.close()

    def idn(self):
        raise TypeError('Command Not Supported')

    def cls(self):
        return self.intf.send_clr()

    def get_mode(self):

        return self.get_status()[1][0]

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
            self.intf.write(self.valid_modes[mode])
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
            self.intf.write(f'N{digits}')
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
            self.intf.write(self.triggers[trigger])
        else:
            raise ValueError('Invalid trigger setting')

    def set_range(self, max_value):
        """
        set_range(max_value)

        Args:
            max_value (float): Maximum measurement value expected
        """
        for range_, command in self.ranges[self._current_mode]:
            if max_value < range_:
                self.intf.write(command)
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
        self.intf.write(cmd)

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
                self.intf.write('D3'+msg)
            else:
                self.intf.write('D2'+msg)
        else:
            self.intf.write('D1')

    @staticmethod
    def _shift_by_mask(mask, val):
        while not(mask & 0x1):
            mask >>= 1
            val >>= 1
        val &= mask
        return val

    def get_status(self):
        """
        Query the DMM status register

        Args:
            print_verbose (bool, optional): Print out a verbose description of 
            the status. Defaults to True.
            display_all_bits (bool, option): Display all the status/error bits,
            instead of just the ones that are set

        Returns:
            tuple: Values of the status bytes
        """

        self.intf.write('B')
        raw = list(self.intf.read()[:5])
        #raw = [ord(b) for b in raw]
        out_list = []
        for byte, (desc, lookup) in zip(raw, self.status_lookup):
            if isinstance(lookup, list):
                for index, item in enumerate(lookup):
                    if isinstance(item, tuple):
                        mask, d = item
                        val = self._shift_by_mask(mask, byte)
                        out_list.append(d[val])
                    elif isinstance(item, str):
                        bitval = byte & 2**(7-index)
                        if bitval:
                            out_list.append(item)
            elif lookup == 'RAW':
                out_list.append(byte)
        return raw, out_list

    def _measure_signal(self):
        """
        _measure_signal()

        returns the value of the current measurement selected on the
        multimeter display

        returns: float
        """
        return float(self.intf.read())

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
