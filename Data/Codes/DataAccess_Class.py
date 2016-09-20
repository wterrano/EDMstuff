import os

import numpy as np
# todo : Improve MemoryError if matrix is too big: report which file caused problem; implement generator output

from DataAccess.DigHandle_Class import LocalHandle
from DataAccess.DigHeader_Class import DigHeader
from DataAccess.DigRead_Class import DigRead
from DataAccess.DigRead_Class import DigReadSettingError

__author__ = 'William'

THIS_PATH = os.path.dirname(os.path.abspath(__file__))
MAX_ARRAY_SIZE = 2 ** 62


class DigAccess(object):
    """
    Class handling access to nedm DAQ .dig files.

    """

    def __init__(self, file_name, file_path=THIS_PATH, doc_id=None, user_settings=dict()):
        """

        :param file_name: file to be accessed, doc_id on server or File_path on local disk
        :return:
        """
        self.user_settings = user_settings
        self.source = self.set_source(doc_id)
        self.file_name = file_name
        self._handle = LocalHandle(file_name=self.file_name, file_path=file_path)
        self.header = DigHeader(self._handle)
        self.default_settings = dict(
                downsample=1,
                channels_to_read=self.header.channel_list,
                start_read=0,
                end_read=self.header.data_length_reads)
        self.read_settings = self.define_read_settings()
        self.read = DigRead(self._handle, self.header, self.read_settings)
        self._internal_data_dict = dict()

    def define_read_settings(self):
        """
        define the settings for the Dig file reader based on the user settings and the header info
        the settings understood by the DigRead class itself are
                'downsample': factor to downsample the data by
                'channels_to_read': list of the channel numbers that you want back
                'start_read': First digitizer read number to include
                'end_read': Last digitizer read number to include

# todo :
        DataAccess can also handle
                'frequency_cut_off'
                'start_time' and 'end_time'


        default behaviour is to read the entire file
        :return:
        """
        default_settings = self.default_settings
        known_settings = default_settings.keys()
        try:
            user_keys = self.user_settings.keys()
        except AttributeError:
            raise DigReadSettingError('Requested settings must be as a dictionary')
        settings_dict = dict(default_settings)
        if not set(user_keys) < set(known_settings):
            raise DigReadSettingError('Available settings are {}'.format(known_settings))
        for key in default_settings.keys():
            if key in user_keys:
                    settings_dict[key] = self.user_settings[key]
        return settings_dict


    @property
    def data_dict(self):
        if not self._internal_data_dict:
            self.load_data_dict()
        return self._internal_data_dict

    def set_source(self, doc_id):
        if doc_id:
            return 'server'
        if not doc_id:
            return 'local'

    def load_data_dict(self):
        """
        Load the file in to a dictionary, if the whole thing fits in RAM memory

        :return:
        """

        self.allocate_data_dict()
        index = 0
        count = 0
        for segment in self.read.data_segments():
            for chn in segment:
                length = len(segment[chn])
                self._internal_data_dict[chn][index:index + length] = segment[chn]
            index += length
            count += 1

    def allocate_data_dict(self):
        number_of_reads = self.header.data_length_reads
        total_ch = self.header.total_ch
        downsample = self.read.downsample
        array_size = number_of_reads / (total_ch * downsample)
        read_channels = self.read.channels_to_read
        try:
            self._internal_data_dict = dict([(chn, np.zeros(array_size)) for chn in read_channels])
        except MemoryError:
            print("File too large for working memory try clearing space or using the .data_generator method")
            raise
        except ValueError:
            print("File larger than maximum allowed numpy array size try using the .data_generator method")

    #############
    ### Data Controller functions
    #############
    def channel(self, chn):
        if chn in self.read.channels_to_read:
            return self.data_dict[chn]
        else:
            raise KeyError("Invalid channel: {} has not been read "
                            "Channel numbers available for"
                            " this file are {} corresponding to channels {}"
                            .format(chn, self.header.channel_list, str(self.header.channel_names)))


# todo :  unittesting -- 1. reads known file correctly
# todo :  unittesting -- 2. test access handles
# todo :  unittesting -- 3. test processing data
# todo :  unittesting -- 4. test low pass filter; Padding;
# todo :  unittesting -- 5. test interfacing with controller


NET_TEST = dict(filename="2016-06-05 00-14-18.694128-0.dig",
                doc_id="2e32e3448b57ee446ce8edb9a3449e0e")

testfile = DigAccess('test_data.dig', './Test')

# netload = DataAccess(NET_TEST['filename']+'/downsample/1', chn=0, doc_id=NET_TEST['doc_id'])
# print(netload.data_array[:3])
