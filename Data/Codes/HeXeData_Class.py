# todo: unittest that sample frequency and time steps match
# todo: Move plotting to another class/function
# todo: subclass with chunked data
# todo: downsample on file loading

import scipy
import os
import numpy as np
import json
import pynedm
import struct

import matplotlib.pyplot as plt

__author__ = 'William'
"""
Class containing data from HeXe experiment
This class also handles data manipulation (downsampling, filtering, fft)
and as of Dec. 2015, visualisation, which should be moved

"""

# region File and network paths
ALL_OFF_FILE = "2015-10-05 13-45-38.031713_downsample.dig"
ALL_ON_FILE = "2015-10-05 14-35-42.713321_downsample.dig"

HELIUM_FREQUENCY = 40.79
XENON_FREQUENCY = 14.81

SQUID_CHANNELS = {'x1': 0, 'y1': 1, 'z1': 2, 'x2': 3, 'y2': 4, 'z2': 5}

_datapath = "/Users/William/Desktop/EDM/Data/DataRuns/"

_username = "nedm_user"
_password = "pw"
# _server = "http://raid.nedm1"
# or (preferred)
_server = "http://10.155.59.88:5984"
_db = "nedm%2Fmeasurements"


# endregion



class HeXeData:
    """
    Class containing data from HeXe experiment

    """
    # todo: handle case where file_name is not given!
    def __init__(self, file_name=None, name='unnamed'):
        """
        :param file_name: name of the .dig file containing the data to be used
        :return:
        """
        self._name = name
        self._data_dict = {}
        # Volt conversion factor from Flo's code :
        # {ADC Range in voltage}/{24 bit ADC} = 20/(2**24)volts/bit
        self._conversion_factors = {'Volts': 1.1920929e-6}
        self._units = "Volts"
        self._channels = SQUID_CHANNELS  # dictionary allowing the user to rename the DAQ channels
        self._data_path = "/Users/William/Desktop/EDM/Data/DataRuns/"
        self._file_name = file_name
        self._file_path = self._data_path + file_name
        self._sampled_dict = {}
        self._poly_fit_dict = {}
        self.load_file()
        self.re_key(self._data_dict, self._channels)
        self.set_scale()
        self._import_down_sampling = self.hdr['downsample']
        self._down_sample = self._import_down_sampling
        self._daq_frequency = self.hdr['freq_hz']  # DAQ sampling frequency
        self._sample_frequency = self._daq_frequency / self._import_down_sampling
        self._number_of_data_samples = self._data_dict.values()[0].size
        self._run_duration = self._import_down_sampling * self._number_of_data_samples * (1 / self._daq_frequency)
        self._data_dict["time"] = np.linspace(0, self._run_duration, self._number_of_data_samples)

    def load_file(self):
        """
        for getting .dig files and putting them in the class.

        This exists as a method for future options of file_downsampling or selecting only certain channels on import

        :return:
        """

        self._data_dict = self.interpret_file()

    def set_scale(self):
        for chan in self.channels:
            self._data_dict[chan] = self._data_dict[chan] * self._conversion_factors['Volts']

    # todo: allow downsampling file on input
    # todo: cleanup whether downsample applies to currently accessed data, or daq file data

    def down_sample(self, factor):
        """
        downsample the data in _internal_data_dict by factor and store result in sampled dict
        :param factor: down sampling factor
        :return:
        """
        data_samples = self._number_of_data_samples
        for k, v in self._data_dict.iteritems():
            padding = factor - (data_samples % factor)
            padded_data = np.append(v, np.zeros(padding) * np.NaN)
            data_reshape = padded_data.reshape(-1, factor)
            self._sampled_dict[k] = scipy.nanmean(data_reshape, 1)
        self._down_sample = self._import_down_sampling * factor
        self._sample_frequency /= factor
        return

    def cutoff_frequency(self, frequency=200):
        """
        downsample the data in _internal_data_dict so that the sample frequency in _sampled_dict
        is frequency

        :param frequency: sample frequency for the new _sampled_dict
        :return:
        """
        import_frequency = self._daq_frequency / self._import_down_sampling
        factor = np.floor(import_frequency / frequency)
        self.down_sample(factor)
        return

    ####
    #    Direct access to useful dictionary elements
    #    channel is the safest way to ask for a channel
    ####

    def channel(self, name):
        """
        If we have down-sampled after importing, returning down-sampled data i.e. _sampled_dict

        :param name: channel to be returned
        :return: array of channel data.  If there is a _sampled_dict use that
        """
        if self._sampled_dict:
            d = self._sampled_dict
        else:
            d = self._data_dict
        try:
            return d[name]
        except KeyError:
            print('channel "{0}" not found'.format(name))
            return {}

    @property
    def frequency(self):
        """
        :return: frequency of data being looked at (in sample dict)
        """
        return self._daq_frequency / self._down_sample

    @property
    def rate(self):
        return self.time[1] - self.time[0]  # ensures there wasn't anything weird with time changing

    @property
    def time(self):
        return self.channel('time')

    @property
    def x1(self):
        return self.channel('x1')

    @property
    def y1(self):
        return self.channel('y1')

    @property
    def z1(self):
        return self.channel('z1')

    @property
    def x2(self):
        return self.channel('x2')

    @property
    def y2(self):
        return self.channel('y2')

    @property
    def z2(self):
        return self.channel('z2')

    @property
    def channels(self):
        """
        :return: Channels recorded in file
        """
        return self._channels.keys()

    @property
    def data_keys(self):
        """
        Typically self.channels + 'time'

        :return: All data streams in the data dict.
        """
        return self._data_dict.keys()

    #########
    #         Data analysis and manipulation
    #########
    # todo:  Separate analysis class
    # todo: make channels batch by channel try/except
    def poly_fit(self, chn, order_to_fit):
        """
        fit a polynomial to the data. Add a new dictionary of poly1d elements
        :param chn:
        :
        :param order_to_fit:
        :return: dictionary of poly1d classes added to data class
        """
        # for chan in self.channels:
        #    c = np.polyfit(self.time, self.channel(chan), order_to_fit)
        #    self._poly_fit_dict[chan] = np.poly1d(c)
        c = np.polyfit(self.time, self.channel(chn), order_to_fit)
        self._poly_fit_dict[chn] = np.poly1d(c)
        return

    def remove_drift(self, chn, order_to_remove=0):
        """
        remove drift from channel

        :rtype : drift subtracted data
        :param order_to_remove: order of the polynomial subtracted from the data
        :return: array of the channel with the drift removed
        """
        self.poly_fit(chn, order_to_remove)
        fitpoints = self._poly_fit_dict[chn](self.time)
        return self.channel(chn) - fitpoints

    def fft(self, chn, order_to_remove=2):
        """
        returns frequencies and absolute value of fft for a given channel.
        FFT is normalized to length of data so amplitude of peak height
        matches amplitude of sine/cosine fit

        Currently uses hamming window

        :return: frequencies and absolute value of fft
        """
        # todo: make fft average of user inputed blocks
        # todo: make window user adjustable
        data = self.remove_drift(chn, order_to_remove)
        window = np.hamming(data.size)
        # d1 = data[:data.size/2]
        # d2 = data[data.size/2:-1]
        # df1 = (2./d1.size)*np.fft.rfft(d1)
        # df2 = (2./d2.size)*np.fft.rfft(d2)
        # # data_fft = (2./self.time.size)*np.fft.rfft(data)
        data_fft = (2. / data.size) * np.fft.rfft(data * window)
        abs_fft = np.abs(data_fft)
        fs = np.fft.rfftfreq(data.size, self.rate)  # creates axis of frequencies
        return fs, abs_fft

    # todo fit data segment

    #########
    #         Display and Presentation
    #########

    def plot_fft(self, chn,
                 order_to_remove=2, figure=False):
        """
        Plots the requested channel

        :param chn: Digitizer channel to be plotted
        :param order_to_remove: order of drift to remove
        # :param offset: offset the plot from being centered around 0
        :param figure: figure object for further adjustment of the plot
        :return:
        """
        # todo: improve plot limits
        fs, abs_fft = self.fft(chn, order_to_remove)
        if not figure:
            figure = plt.subplot()
        figure.plot(fs, abs_fft, label=self._name + ' ' + chn + ' FFT')
        figure.set_xbound(fs[0], fs[-1])
        figure.set_xlabel('freq [Hz]')
        figure.set_ylabel('{0} [{1}]'.format(chn, self._units))
        figure.legend()
        plt.show()
        return figure

    def plot_data(self, chn, remove_drift=True,
                  order_to_remove=1, scale=1, offset=0, figure=False):
        """
        Plots the requested channel

        :param chn: Digitizer channel to be plotted
        :param remove_drift: subtract polynomial drift
        :param order_to_remove: order of drift to remove
        :param scale: multiply the data by a scaling factor
        :param offset: offset the data from being centered around 0
        :param figure: figure object for further adjustment of the plot
        :return:
        """
        if not figure:
            figure = plt.subplot()
        if remove_drift:
            data = self.remove_drift(chn, order_to_remove)
        else:
            data = self.channel(chn)
        figure.plot(self.time, (scale * data) + offset, label=self._name + ' ' + chn)
        figure.set_xbound(self.time[0], self.time[-1])
        figure.set_xlabel('time [s]')
        figure.set_ylabel('{0} [{1}]'.format(chn, self._units))
        figure.legend()
        plt.show()
        return figure

    #########
    ######### DATA I/O handling
    #########

    def interpret_file(self, doc_id=None):
        """
        File structure is:
           bytes 0..3: length of json header N (excluding header word)
           bytes 4..4+N: json header (ASCII data)
           bytes 4+N+1..EOF: binary data of channels
        The binary data format depends on what's in the json header:
          header["channel_list"] ---> ordered list of channels
          header["byte_depth"]    ---> size of binary word
          header["bit_shift"]    ---> amount to shift right
        Every channel is listed one after another for each time point (fully
        interlaced)
        """
        ll = lambda: open(self._file_path)
        # retrieve file from server
        if doc_id is not None:
            po = pynedm.ProcessObject(uri=_server, username=_username, password=_password, adb=_db)
            ll = lambda: po.open_file(doc_id, self._file_name)

        with ll() as o:
            header_length = struct.unpack("<L", o.read(4))[0]
            o.seek(4)
            hdr = json.loads(o.read(header_length))
            self.hdr = hdr
            try:
                bit_depth = hdr["bit_depth"]
            except:
                bit_depth = hdr["byte_depth"]
            bit_shift = hdr["bit_shift"]
            dt = None
            if bit_depth == 2:
                dt = np.int16
            elif bit_depth == 4:
                dt = np.int32
            elif bit_depth == 8:
                dt = np.float64
            else:
                raise Exception("unknown bit_depth")

            def channel_dict(dat):
                x = dat
                if bit_shift != 0:
                    x = np.right_shift(dat, bit_shift)

                cl = hdr["channel_list"]
                total_ch = len(cl)

                # Now create a dictionary of the channels
                return dict([(cl[i], x[i::total_ch]) for i in range(len(cl))])

            # Reads from position 4 + header_length
            data_start = 4 + header_length
            o.seek(data_start)

            # We should always read by a factor of this chunk_size
            chunk_size = bit_depth * len(hdr["channel_list"])

            o.seek(0, os.SEEK_END)
            data_end = o.tell()
            o.seek(data_start)
            return channel_dict(np.fromstring(o.read(2000000 * chunk_size), dtype=dt))

            # # We can iterate over everything...
            # print("Iterating")
            # try:
            #     # Only works for files online
            #     for x in o.iterate(1024*chunk_size):
            #         chunk_data = channel_dict(np.fromstring(x, dtype=dt))
            #         processData(chunk_data)
            #         #break # comment this out to *really* iterate over everything
            # except: pass

            # # Or we can explicitly seek to a particular place (should be aligned
            # # with the chunk_size!
            # # In this case, we read out beginning with the 2000th point
            # o.seek(4 + header_length + 2000*chunk_size)
            #
            # # Read out 2000 points
            # print("Seeking")
            # print(channel_dict(np.fromstring(o.read(2000*chunk_size), dtype=dt)))


        ####
        ####  Helper functions

    def re_key(self, dictionary, keymap):
        """
        Change the keys in dictionary from keymap.keys to keymap.values

        :param dictionary: dictionary to be re-keyed
        :param keymap: dictionary with new keys as keys and old keys as values
        :return: dictionary that has been re-keyed
        """
        for k, v in keymap.iteritems():
            try:
                dictionary[k] = dictionary.pop(v)
            except KeyError:
                print("key {0} is not in dictionary {1}".format(k, dictionary))
        return dictionary


####
#### Testing Code

#### To check things in Console

hex = HeXeData(ALL_OFF_FILE, 'HeXe')


def setup():
    """
    for testing out new features and debugging
    :return:
    """
    return

    #### Unit tests
