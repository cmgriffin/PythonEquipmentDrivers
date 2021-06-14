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
