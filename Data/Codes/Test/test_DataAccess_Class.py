# todo :  unittesting -- 1. reads known file correctly;  also check some bad file calls (names, channels etc.)
# todo :  unittesting -- 2. test access handles
# todo :  unittesting -- 3. test processing data
# todo :  unittesting -- 4. test low pass filter; Padding;
# todo :  unittesting -- 5. test interfacing with controller
# todo: Unittests: Padding; Data_array Length; downsample value; correct values of lowpass filter
import numpy as np
import pytest
import DataAccess_Class as Da_C
import os
THIS_PATH=os.path.dirname(os.path.abspath(__file__))
file_to_test = 'test_data.dig'

dt = 'some server name'

class TestLoadFromFile:

    # def test_bad_channel(self, dig_file=file_to_test):
    #     """
    #     Try loading a file without a channel number
    #
    #     """
    #
    #     with pytest.raises(TypeError):
    #         Da_C.DataAccess(file_name=dig_file, file_path=THIS_PATH)
    #
    # def test_bad_filename(self, bad_file='bad_file'):
    #     """
    #     Try loading a file that does not exist
    #
    #     """
    #     with pytest.raises(IOError):
    #         Da_C.DataAccess(file_name=bad_file, file_path=THIS_PATH, chn=0, cutoff_frequency=-3)

    def test_bad_frequency(self, dig_file=file_to_test):
        """
        Try loading a file with an unreasonable cutoff frequency
        :return:
        """
        with pytest.raises(ValueError):
            Da_C.DataAccess(file_name=dig_file, file_path=THIS_PATH, chn=0, cutoff_frequency=-3)

    def test_no_data_specified(self):
        """
        Try creating class with neither _doc_id or file name

        """
        with pytest.raises(ValueError):
            Da_C.DataAccess(chn=0)

    def test_two_types_of_data_specified(self, dig_file=file_to_test, doc_test=dt):
        """
        ask for both a file and a _doc_id

        """
        with pytest.raises(ValueError):
            Da_C.DataAccess(file_name=dig_file, file_path=THIS_PATH, chn=0, doc_id=doc_test)

    def test_load_from_file(self, dig_file=file_to_test):
        """
        Try to load a valid .dig file

        """

        test_file = Da_C.DataAccess(file_name=dig_file, file_path=THIS_PATH, chn=0)
        assert isinstance(test_file, Da_C.DataAccess)


class TestData:
    """
    Compare read in data to a sample loaded by hand

    using file 2016-06-05 00-14-18.694128-0.dig
    and look at channel 0 to check the start of the file
    and channel 9 to check the end of the file
    """
    chn0_start_raw_file_data = ['\xfc\xfe\xfe\xff', '\x20\xfe\xfe\xff', '\xdb\x01\xff\xff']
    chn9_end_raw_file_data = ['\xd1\xf7\xff\xff', '\xdb\xf7\xff\xff']
    # Note, last byte of .dig file is a '\x0a' or ASCII new line
    # converted from hex to decimal by hand:
    # largest byte is rightmost of the 4 bytes but within a byte it reads left to right
    # highest value position flips to being largest negative number at 8 and then counts up from there to -1 ...
    # for 32 bit encoding: '\x00\x00\x00\x80 is largest negative number (-8*16^7) and '\xff\xff\xff\xff' is -1
    # '\xff\xff\xff\x7f' is largest possible positive number (8*16^7 - 1)
    chn0_start_decimal_file_data = np.array([-65796, -66016, -65061])
    chn9_end_decimal_file_data = np.array([-2095, -2085])

    def test_start_data_values(self, dig_file=file_to_test):
        """
        Look at channel values converted from hex binary to integers from the beginning of the file
        For this use channel 0

        """

        test_file = Da_C.DataAccess(file_name=dig_file, file_path=THIS_PATH, chn=0)
        assert test_file.data_array[:3].all() == self.chn0_start_decimal_file_data.all()

    def test_end_data_values(self, dig_file=file_to_test):
        """
        Look at channel values converted from hex binary to integers from the end of the file
        For this use channel 9

        """

        test_file = Da_C.DataAccess(file_name=dig_file, file_path=THIS_PATH, chn=9)
        assert test_file.data_array[-2:].all() == self.chn9_end_decimal_file_data.all()



