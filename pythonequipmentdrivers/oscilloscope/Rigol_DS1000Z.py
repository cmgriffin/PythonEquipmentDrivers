from pathlib import Path
from pythonequipmentdrivers import Scpi_Instrument


class Rigol_DS1000Z(Scpi_Instrument):
    """    
    Rigol_DS1000Z(address)

    address : str, address of the connected oscilloscope

    object for accessing basic functionallity of the Rigol_DS1054Z Oscilloscope
    """

    def autoscale(self) -> None:
        """
        autoscale()

        Run device autoscaling routine. The oscilloscope will automatically
        adjust the vertical scale, horizontal timebase, and trigger mode 
        according to the input signal to realize optimum waveform display.
        """
        self.instrument.write(":AUToscale")

    def trigger_run(self) -> None:
        """
        trigger_run()

        Set oscilliscope aquisition mode to Run
        """
        self.instrument.write(":RUN")

    def trigger_stop(self) -> None:
        """
        trigger_stop()

        Set oscilliscope aquisition mode to Stop
        """
        self.instrument.write(":STOP")

    def clear(self) -> None:
        """
        clear()

        Clear all the waveforms on the screen. 
        If the oscilloscope is in the RUN state, waveform will still be
        displayed. This command is equivalent to pressing the CLEAR key
        on the front panel.
        """
        self.instrument.write(":CLEar")

    def trigger_single(self) -> None:
        """
        trigger_single()

        arms the oscilloscope to capture a single trigger event.
        """
        self.instrument.write(":SINGle")

    def trigger_force(self) -> None:
        """
        trigger_force()

        forces a trigger event to occur
        """
        self.instrument.write(":TFORce")

    def set_horizontal_scale(self, scale: float) -> None:
        """
        set_horizontal_scale(scale)

        sets the scale of horizontal divisons (for all channels) to the
        specified value in seconds.

        Args:
            scale (float): time scale across one horizontal division on the
                display in seconds.
        """
        self.instrument.write(f":TIMebase:SCALe {scale}")

    def get_horizontal_scale(self) -> float:
        """
        get_horizontal_scale()

        Retrieves the horizontal scale used to accquire waveform data.

        Returns:
            float: horizontal scale in seconds per division.
        """
        return float(self.instrument.query(f":TIMebase:SCALe?").strip())

    def set_channel_scale(self, channel: int, scale: float) -> None:
        """
        set_channel_scale(channel, scale)

        sets the scale of vertical divisons for the specified channel

        Args:
            channel (int): channel number to query information on
            scale (float): scale of the channel amplitude across one
                vertical division on the display.
        """
        self.instrument.write(f":CHANnel{channel:d}:SCALe {scale}")

    def get_channel_scale(self, channel: int) -> float:
        """
        get_channel_scale(channel)

        Retrives the scale for vertical divisons for the specified channel

        Args:
            channel (int): channel number to query information on

        Returns:
            (float): scale of the channel amplitude across one
                vertical division on the display.
        """
        return float(
            self.instrument.query(f":CHANnel{channel:d}:SCALe?").strip()
        )

    def set_channel_enable(self, channel_number, enable):
        self.instrument.write(f"CHANnel{channel_number:d}:DISPlay {enable}")

    def get_channel_enable(self, channel_number):
        return self.instrument.query(f"CHANnel{channel_number:d}:DISPlay?")

    def set_channel_offset(self, channel: int, off: float) -> None:
        """
        set_channel_offset(channel, off)

        Sets the vertical offset for the display of the specified channel.

        Args:
            channel (int): Channel number to query
            off (float): vertical/amplitude offset
        """
        self.instrument.write(f"CHANnel{channel:d}:OFFSet {off}")

    def get_channel_offset(self, channel: int) -> float:
        """
        get_channel_offset(channel)

        Retrives the vertical offset for the display of the specified channel.

        Args:
            channel (int): Channel number to query

        Returns:
            float: vertical/amplitude offset
        """
        return float(
            self.instrument.query(f"CHANnel{channel:d}:OFFSet?").strip()
        )

    def get_measure_data(self, *meas_param: tuple[int, str]) -> Union[float, tuple]:
        """
        get_measure_data(*meas_idx)

        Returns the current value of the requesed measurement(s) reference by
        the provided index(s).

        Args:
            meas_param (tuple[int, str]): pair(s) of channel number and
            measurement name

        Returns:
            float: Current value of the requested measurement. If no value as
                been assigned to the measurement yet the returned value is nan.
        """

        data = []
        for channel, measurement in meas_param:

            query_cmd = (f":MEASure:ITEM? {measurement},",
                         f"CHANnel{channel:d}")
            response = self.instrument.query(query_cmd)

            try:
                data.append(float(response))
            except ValueError:
                data.append(float('nan'))

        if len(data) == 1:
            return data[0]
        return tuple(data)

    def get_waveform_data(self, channel_number):
        raise NotImplementedError

    def get_image(self, image_title, color="ON", invert="OFF") -> None:
        """Save the current image on the display

        Args:
            filename (str): this is the image filename and optional path excluding the
            extension, which is appending automatically
            color (str, optional): {ON, OFF}. Defaults to 'ON'.
            invert (str, optional): {ON, OFF}. Defaults to 'OFF'.
            format_ (str, optional): {BMP24, BMP8, PNG, JPEG, TIFF}. Defaults to 'BMP24'.
        """

        extension_loopup = {
            "BMP24": ".bmp",
            "BMP8": ".bmp",
            "PNG": ".png",
            "JPEG": ".jpg",
            "TIFF": ".tif",
        }

        # add file extension
        if isinstance(image_title, Path):
            file_path = image_title.parent.joinpath(image_title.name + '.png')
        elif isinstance(image_title, str):
            file_path = f"{image_title}.png"
        else:
            raise ValueError('image_title must be a str or path-like object')

        self.instrument.write(f":DISPlay:DATA? {color},{invert},PNG")
        data = self.instrument.read_raw()
        header_length = int(chr(data[1])) + 2
        image_data = data[header_length:-1]
        with open(file_path, "wb") as f:
            f.write(image_data)
