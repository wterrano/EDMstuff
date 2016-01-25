__author__ = 'William'
self._conversion_factors = {'Volts': 1.1920929e-6}
        self._units = "Volts"
        self._channels = SQUID_CHANNELS  # dictionary allowing the user to rename the DAQ channels
self.re_key(self._data_dict, self._channels)
self.set_scale()
self._down_sample = self_import_down_sampling
        self._import_down_sampling = self.hdr['downsample']
        self._daq_frequency = self.hdr['freq_hz']  # DAQ sampling frequency
        self._sample_frequency = self._daq_frequency / self._import_down_sampling
        self._number_of_data_samples = self._data_dict.values()[0].size
        self._run_duration = self._import_down_sampling * self._number_of_data_samples * (1 / self._daq_frequency)
self._data_dict["time"] = np.linspace(0, self._run_duration, self._number_of_data_samples)

    def set_scale(self):
        for chan in self.channels:
            self._data_dict[chan] = self._data_dict[chan] * self._conversion_factors['Volts']

