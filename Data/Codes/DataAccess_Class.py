import json
import numpy as np
import pynedm
import struct
import scipy
import os
import sys

__author__ = 'William'

THIS_PATH=os.path.dirname(os.path.abspath(__file__))

# todo: Unittests: Padding; Data_array Length; downsample value; correct values of lowpass filter
print('hi')
class DataAccess:
    """
    Class handling access to nedm DAQ data.

    """

    def __init__(self, file_name=None, file_path=THIS_PATH, chn=None, cutoff_frequency=None, doc_id=None):
        """

        :param file_name: file to be accessed
        :param chn: Digitizer channel requested
        :param cutoff_frequency: low-pass filter cutoff [Hz]
        :return:
        """

        # if file_name is not None and _doc_id is not None:
        #     raise ValueError('Only one file (file_name {}) or database id (_doc_id {}) can be specified.'
        #                      .format(file_name, _doc_id))
        if file_name is None and doc_id is None:
            raise ValueError('file (file_name) or database id (_doc_id) must be specified')
        self._doc_id = doc_id
        self._server_dict = dict(_db="nedm%2Fmeasurements",
                                 #_server="http://10.155.59.88:5984",
                                _server = "http://10.155.59.15",
                                 _server2="http://db.nedm1",
                                 _password="clu$terXz",
                                 _username="nedm_user")
        self._cutoff_frequency = cutoff_frequency
        self._chn = chn
        self._data_dict = {'header': {}, chn: np.array([])}
        self._temp_dict = {}
        self._file_path = file_path
        self._file_name = file_name
        self._dt = None
        self._bit_shift = None
        self._bit_depth = None
        self._header_length = None
        self._file_handle = self.get_file_handle()
        self.get_file_header()
        # self.compression_factor = self.set_compression_factor()
        self.compression_factor = 1
        self.reads_per_segment = 8192 * self.compression_factor  # set the number of samples per read of the file
        self.load_file()

    def get_file_handle(self):
        """
        Open file object for reading

        """
        # open file from local disk
        ll = lambda: open(self._file_address)
        # retrieve file from server
        if self._doc_id is not None:
            po = pynedm.ProcessObject(uri=self.sd['_server2'],
                                      username=self.sd['_username'],
                                      password=self.sd['_password'],
                                      adb=self.sd['_db'])
            ll = lambda: po.open_file(self._doc_id, self._file_name)
        return ll

    def get_file_header(self):
        """
        Read file header and set needed values

        :return:
        """

        with self._file_handle() as o:
            header_length = struct.unpack("<L", o.read(4))[0]
            o.seek(4)
            hdr = json.loads(o.read(header_length))
            self._file_header = hdr
            try:
                self._bit_depth = hdr["bit_depth"]
            except KeyError:
                self._bit_depth = hdr["byte_depth"]
            self._bit_shift = hdr["bit_shift"]
            if self._bit_depth == 2:
                dt = np.int16
            elif self._bit_depth == 4:
                dt = np.int32
            elif self._bit_depth == 8:
                dt = np.float64
            else:
                raise Exception("unknown bit_depth")
            print(self._bit_depth)
            self.load_header_info(dt, header_length)

    def set_compression_factor(self):
        """
        find downsampling factor needed for the requested cutoff frequency

        :return: integer compression factor.
        """
        if self._cutoff_frequency is None:
            return 1
        try:
            cf = int(np.floor(self.file_frequency / self._cutoff_frequency))
        except TypeError:
            print("Invalid type for cutoff_frequency")
            raise
        else:
            if cf > 0:
                return cf
            else:
                raise ValueError("cutoff_frequency is out of range, should be between 0 and {}, or None".
                                 format(self.file_frequency))

    ###
    # Convenience access handles
    ###
    @property
    def _file_address(self):
        try:
            file_address = os.path.join(self._file_path, self._file_name)
        except TypeError:
            print("File path invalid format")
            return
        return file_address

    @property
    def channel(self):
        if self._chn in self._file_header["channel_list"]:
            return self._chn
        else:
            raise TypeError("Invalid channel: {}  " \
                   "Channels available for" \
                   " this file are {}"
                            .format(self._chn, str(self._file_header["channel_names"])))


    @property
    def sd(self):
        return self._server_dict

    @property
    def data_array(self):
        return self._data_dict[self.channel]

    # @data_array.setter
    # def data_array(self, new_data_array):
    #     self._data_dict[self.channel] = new_data_array

    @property
    def output_header(self):
        return self._data_dict['header']

    @property
    def downsampling(self):
        return self.output_header['downsample']

    @downsampling.setter
    def downsampling(self, value):
        self.output_header['downsample'] = value

    @property
    def sample_frequency(self):
        return self.output_header['sample_frequency[Hz]']

    # @sample_frequency.setter
    # def sample_frequency(self, value):
    #     self.header['sample_frequency[Hz]'] = value

    @property
    def file_downsampling(self):
        return self._file_header['downsample']

    @property
    def file_frequency(self):
        return self._file_header['freq_hz'] / self.file_downsampling

    ###
    # Interfacing with the data file
    ###

    def load_file(self):

        """
        for getting .dig files and putting them in the class.

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
        :return:
        """

        self._data_dict = self._load_segment()

    # todo: reorganize into more OO concise style
    # todo: check validity of file locale
    # todo: parse with matrix instead of dictionary and reassign at the end
    # @profile
    def _load_segment(self):
        """

        """

        with self._file_handle() as o:

            def channel_dict(dat):
                """
                Helper function that makes dictionary from the data in memory

                :rtype : Dictionary
                """
                x = dat
                if self._bit_shift != 0:
                    x = np.right_shift(dat, self._bit_shift)

                cl = self._file_header["channel_list"]
                total_ch = len(cl)

                # Now create a dictionary of the channels
                return dict([(cl[i], x[i::total_ch]) for i in range(len(cl))])

            # Reads from position 4 + self._header_length
            data_start = 4 + self._header_length
            o.seek(data_start)

            # We should always read by a factor of this chunk_size
            chunk_size = self._bit_depth * len(self._file_header["channel_list"])

            # o.seek(0, os.SEEK_END)
            # data_end = o.tell()

            def file_iterator():
                """
                Make a generator of file data, broken into multiples of the chunk_length

                :rtype : generator
                """
                while True:
                    data_segment = o.read(self.reads_per_segment * chunk_size)
                    if not data_segment:
                        break
                    yield data_segment
            i = 0
            for segment in file_iterator():
                print('in iterator {}'.format(i))
                self._temp_dict = channel_dict(np.fromstring(segment, dtype=self._dt))
                self.process_incoming_data()
                i+=1
                if i == 20000: break

    def load_header_info(self, dt, header_length):
        """
        set up internal header with needed parameters from file header
        """
        self.downsampling = self._file_header['downsample']
        self.sample_frequency = self._file_header['freq_hz']
        self._dt = dt
        self._header_length = header_length
        return

    # @profile
    def process_incoming_data(self):
        """
        Extract relevant channel, downsample and add it to data array

        """
        data = self._temp_dict[self.channel]
        filtered_data = self.low_pass_filter(data)
        self.data_array = np.concatenate((self.data_array, filtered_data))
        return

    # @profile
    def low_pass_filter(self, input_data):
        """
        Apply a crude down-sample the incoming data in order to give it
        a more reasonable sample frequency.

        :param input_data: input_data array to be low-pass filtered
        :return:
        """
        self.downsampling = self.file_downsampling * self.compression_factor
        self.sample_frequency = self.file_frequency / self.compression_factor
        number_of_samples = input_data.size
        padding = self.compression_factor - (number_of_samples % self.compression_factor)
        if padding == self.compression_factor:
            padding = 0
        padded_data = np.append(input_data, np.zeros(padding) * np.NaN)
        data_reshape = padded_data.reshape(-1, self.compression_factor)
        sampled_data = scipy.nanmean(data_reshape, 1)
        return sampled_data

    ###
    # Interfacing with the controller
    ###

    def get_channel(self, chn):
        """
        Returns array with data from channel chn, along with relevant header info

        :param chn:  Digitizer channel to be delivered
        :return: Dictionary with header info and sensor data array
        """
        pass


# WILL_MAC_DATAPATH = "/Users/William/Desktop/EDM/Data/DataRuns/"
# ALL_OFF_FILE = "2015-10-05 13-45-38.031713_downsample.dig"
# DEC_HE3_SPIN_FILE = "2015-12-17 09-21-07.377783_downsample.dig"
# # dac = DataAccess(ALL_OFF_FILE, WILL_MAC_DATAPATH, 0, 200)
# lsp = DataAccess(DEC_HE3_SPIN_FILE, WILL_MAC_DATAPATH, 0, 200)


# todo :  unittesting -- 1. reads known file correctly
# todo :  unittesting -- 2. test access handles
# todo :  unittesting -- 3. test processing data
# todo :  unittesting -- 4. test low pass filter; Padding;
# todo :  unittesting -- 5. test interfacing with controller


NET_TEST = dict(filename="2016-06-05 00-14-18.694128-0.dig",
                doc_id="2e32e3448b57ee446ce8edb9a3449e0e")

netload = DataAccess(NET_TEST['filename'], chn=0, doc_id=NET_TEST['doc_id'])
print(netload.data_array[:3])

TEST_DATA = DataAccess(file_name='test_data.dig', file_path=THIS_PATH+'/Test', chn=0)
# print(TEST_DATA._raw_dict)