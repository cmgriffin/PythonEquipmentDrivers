from . import HP_34401A


class Fluke_8845A(HP_34401A):
    """
    Fluke_8845A(address, factor=1)

    address: str, address of the connected multimeter

    factor: float, multiplicitive scale for all measurements defaults to 1.

    object for accessing basic functionallity of the FLUKE_8845A multimeter.
    The factor term allows for measurements to be multiplied by some number
    before being returned. For example, in the case of measuring the voltage
    across a current shunt this factor can represent the conductance of the
    shunt. This factor defaults to 1 (no effect on measurement).
    """

    def __init__(self, address, **kwargs):
        super().__init__(address, **kwargs)

    def disable_cmd_emulation_mode(self):
        """
        disable_cmd_emulation_mode()

        Disable the Fluke 45 command set emulation mode
        """
        self.instrument.write("L1")

    def arm_trigger(self):
        """
        arm_trigger()

        Arm the meter trigger function
        """
        self.instrument.write("INIT")

    def fetch_measurement(self):
        """
        fetch_measurement()

        Fetch the measurement after a bus trigger
        """
        response = self.instrument.query("FETC?")
        return self.factor*float(response)

    def set_trigger_source(self, source):
        """
        set_trigger_source(source)

        Configure the meter trigger source

        source (str): { BUS | IMMediate | EXTernal }
        """
        self.instrument.write(f"TRIG:SOURCE {source.strip()}")

    def set_mode_adv(self, mode, range_, nplc):
        """
        set_mode_adv(mode, range_, nplc)

        Access more detailed meter configuration options

        Args:
            mode (str): type of measurement to be done
                valid modes are: 'VDC', 'VAC', 'ADC', 'AAC', 'FREQ', 'OHMS',
                                 'DIOD', 'CONT', 'PER'
                which correspond to DC voltage, AC voltage, DC current, AC current,
                frequency, resistence, diode voltage, continuity, and period
                respectively (not case sensitive)

            range_ (float): Maximum expected measurement value, the meter 
                will choose from available ranges accordingly
            nplc (float): Set the meter's integration time based on the number
                of power line cycles (0.02, 0.2, 1, 10, and 100)

        Raises:
            ValueError: [description]
        """
        mode = mode.upper()
        if mode in self.valid_modes:
            self.instrument.write(
                f"CONFIGURE {self.valid_modes[mode]} {range_}")
        else:
            raise ValueError("Invalid mode option")
        self.instrument.write(f"VOLT:DC:NPLC {nplc}")
