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
            'VDC': {0.03: 'R-2', 0.3: 'R-1', 3.0: 'R0', 30.0: 'R1', 300.0: 'R2'},
            'VAC': {0.3: 'R-1', 3.0: 'R0', 30.0: 'R1', 300.0: 'R2'},
            'ADC': {0.3: 'R-1', 3.0: 'R0'},
            'AAC': {0.3: 'R-1', 3.0: 'R0'},
            'OHMS': {30: 'R1', 300: 'R1', 3E3: 'R3',
                     3E4: 'R4', 3e5: 'R5', 3E6: 'R6', 3E7: 'R7'}
        }
        return None

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
            self.instrument.write(self.valid_modes[mode])
        else:
            raise ValueError("Invalid mode option")
        return None

    def measure(self):

        return float(self.instrument.read())
