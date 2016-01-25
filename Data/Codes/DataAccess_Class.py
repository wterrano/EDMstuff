import json
import numpy as np
import pynedm
import struct
import scipy

__author__ = 'William'


# todo: Unittests: Padding; Data_array Length; downsample value; correct values of lowpass filter

class DataAccess:
    """
    Class handling access to nedm DAQ data.

    """

    def __init__(self, file_name=None, file_path=None, chn=None, frequency=200):
        """

        :param file_name: file to be accessed
        :param chn: Digitizer channel requested
        :param frequency: low-pass filter cutoff [Hz]
        :return:
        """

        self.server_dict = dict(_db="nedm%2Fmeasurements",
                                _server="http://10.155.59.88:5984",
                                _server2="http://raid.nedm1",
                                _password="pw",
                                _username="nedm_user")
        self.READ_SIZE = 1024  # used to set the number of samples per file read
        self.cutoff_frequency = frequency
        self.channel = chn
        self._file_header = {}
        self._data_dict = {'header': {}, chn: np.array([])}
        self._temp_dict = {}
        self._data_path = file_path
        self._file_name = file_name
        self._file_address = self._data_path + self._file_name
        self.load_file()

    ###
    # Convenience access handles
    ###
    @property
    def data_array(self):
        return self._data_dict[self.channel]

    @data_array.setter
    def data_array(self, new_data_array):
        self._data_dict[self.channel] = new_data_array

    @property
    def header(self):
        return self._data_dict['header']

    @header.setter
    def header(self, value):
        self._data_dict['header'] = value

    @property
    def factor(self):
        return int(np.floor(self.file_frequency / self.cutoff_frequency))

    @property
    def reads_per_segment(self):
        return self.factor * self.READ_SIZE

    @property
    def downsampling(self):
        return self.header['downsample']

    @downsampling.setter
    def downsampling(self, value):
        self.header['downsample'] = value

    @property
    def sample_frequency(self):
        return self.header['sample_frequency[Hz]']

    @sample_frequency.setter
    def sample_frequency(self, value):
        self.header['sample_frequency[Hz]'] = value

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

        :return:
        """

        self._data_dict = self._load_segment()

    # todo: reorganize into more OO concise style
    # todo: check validity of file locale
    def _load_segment(self, doc_id=None):
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
        ll = lambda: open(self._file_address)
        # retrieve file from server
        if doc_id is not None:
            po = pynedm.ProcessObject(uri=_server, username=_username, password=_password, adb=_db)
            ll = lambda: po.open_file(doc_id, self._file_name)

        with ll() as o:
            header_length = struct.unpack("<L", o.read(4))[0]
            o.seek(4)
            hdr = json.loads(o.read(header_length))
            self._file_header = hdr
            try:
                bit_depth = hdr["bit_depth"]
            except KeyError:
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

            self.initialize_header()

            def channel_dict(dat):
                """
                Helper function that makes dictionary from the data in memory

                :rtype : Dictionary
                """
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

            # o.seek(0, os.SEEK_END)
            # data_end = o.tell()
            o.seek(data_start)

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
                print("read #{}".format(i))
                self._temp_dict = channel_dict(np.fromstring(segment, dtype=dt))
                self.process_incoming_data()
                i += 1

    def initialize_header(self):
        """
        set up internal header with needed parameters from file header
        """
        self.downsampling = self._file_header['downsample']
        self.sample_frequency = self._file_header['freq_hz']
        return

    def process_incoming_data(self):
        """
        Extract relevant channel, downsample and add it to data array

        """
        data = self._temp_dict[self.channel]
        filtered_data = self.low_pass_filter(data)
        self.data_array = np.concatenate((self.data_array, filtered_data))
        return

    def low_pass_filter(self, input_data):
        """
        Apply a crude down-sample the incoming data in order to give it
        a more reasonable sample frequency.

        :param input_data: input_data array to be low-pass filtered
        :return:
        """
        self.downsampling = self.file_downsampling * self.factor
        self.sample_frequency = self.file_frequency / self.factor
        number_of_samples = input_data.size
        padding = self.factor - (number_of_samples % self.factor)
        if padding == self.factor:
            padding = 0
        padded_data = np.append(input_data, np.zeros(padding) * np.NaN)
        data_reshape = padded_data.reshape(-1, self.factor)
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


WILL_MAC_DATAPATH = "/Users/William/Desktop/EDM/Data/DataRuns/"
ALL_OFF_FILE = "2015-10-05 13-45-38.031713_downsample.dig"
DEC_HE3_SPIN_FILE = "2015-12-17 09-21-07.377783_downsample.dig"
# dac = DataAccess(ALL_OFF_FILE, WILL_MAC_DATAPATH, 0, 200)
lsp = DataAccess(DEC_HE3_SPIN_FILE, WILL_MAC_DATAPATH, 0, 200)
