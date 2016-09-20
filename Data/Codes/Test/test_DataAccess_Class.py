# todo : only test network reading optionally
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
from DataAccess.DigRead_Class import DigReadSettingError
THIS_PATH = os.path.dirname(os.path.abspath(__file__))
FILE_LOCAL_TEST = 'test_data.dig'
FILE_TEST_NAME = "2016-06-05 00-14-18.694128-0.dig"
FILE_TEST_ID = "2e32e3448b57ee446ce8edb9a3449e0e"

dt = 'some server name'


# noinspection PyClassHasNoInit
class TestInputParameters(object):

    def test_bad_filename(self, bad_file='bad_file'):
        """
        Try loading a file that does not exist

        """
        with pytest.raises(IOError):
            Da_C.DigAccess(file_name=bad_file, file_path=THIS_PATH)

    def test_no_data_specified(self):
        """
        Try creating class with neither _doc_id or file name

        """
        with pytest.raises(TypeError):
            Da_C.DigAccess()

    def test_two_types_of_data_specified(self, dig_file=FILE_LOCAL_TEST, doc_test=dt):
        """
        ask for both a file and a _doc_id

        """

    def test_load_from_file(self, dig_file=FILE_LOCAL_TEST):
        """
        Try to load a valid .dig file

        """

        test_file = Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH)
        assert isinstance(test_file, Da_C.DigAccess)

    def test_invalid_downsample_values(self, dig_file=FILE_LOCAL_TEST):
        """
        downsample must be an integer

        :param dig_file:
        :return:
        """
        settings = {'downsample': 2*np.pi}
        with pytest.raises(TypeError):
            Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH, user_settings=settings)

    def test_invalid_channel_request_list(self, dig_file=FILE_LOCAL_TEST):
        """
        channels must exist in file
        :param dig_file:
        :return:
        """
        settings = {'channels_to_read': [17,18] }
        with pytest.raises(TypeError):
            Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH, user_settings=settings)

    def test_invalid_channel_request(self, dig_file=FILE_LOCAL_TEST):
        """
        channel must exist in file
        :param dig_file:
        :return:
        """
        settings = {'channels_to_read': 2*np.pi}
        with pytest.raises(TypeError):
            Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH, user_settings=settings)

    def test_invalid_setting_request(self, dig_file=FILE_LOCAL_TEST):
        """
        settings must be vaild
        :param dig_file:
        :return:
        """
        settings = {'animal': 'horse'}
        with pytest.raises(TypeError):
            Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH, user_settings=settings)

    def test_invalid_setting_format(self, dig_file=FILE_LOCAL_TEST):
        """
        settings must be a dict
        :param dig_file:
        :return:
        """
        settings = {'filter?'}
        with pytest.raises(TypeError):
            Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH, user_settings=settings)

    def test_invalid_read_settings_start(self, dig_file=FILE_LOCAL_TEST):
        """
        start must lie with in file

        :param dig_file:
        :return:
        """
        settings = {'start_read' : -7}
        with pytest.raises(DigReadSettingError):
            Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH, user_settings=settings)


class TestData(object):
    """
    Compare read in data to a sample loaded by hand

    using file 2016-06-05 00-14-18.694128-0.dig
    and look at channel 0 to check the start_byte of the file
    and channel 9 to check the end_byte of the file
    """
    # Note, last byte of .dig file is a '\x0a' or ASCII new line
    # converted from hex to decimal by hand:
    # largest byte is rightmost of the 4 bytes but within a byte it reads left to right
    # highest value position flips to being largest negative number at 8 and then counts up from there to -1 ...
    # for 32 bit encoding: '\x00\x00\x00\x80 is largest negative number (-8*16^7) and '\xff\xff\xff\xff' is -1
    # '\xff\xff\xff\x7f' is largest possible positive number (8*16^7 - 1)
    file_start_raw_chn0 = ['\xfc\xfe\xfe\xff', '\x20\xfe\xfe\xff', '\xdb\x01\xff\xff']
    file_end_raw_chn9 = ['\xd1\xf7\xff\xff', '\xdb\xf7\xff\xff']
    file_start_decimal_chn0 = np.array([-65796, -66016, -65061])
    file_end_decimal_chn9 = np.array([-2095., -2085.])

    def test_start_data_values(self, dig_file=FILE_LOCAL_TEST):
        """
        Look at channel values converted from hex binary to integers from the beginning of the file
        For this use channel 0

        """

        test_file = Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH)
        assert test_file.channel(0)[:3].all() == self.file_start_decimal_chn0.all()

    def test_end_data_values(self, dig_file=FILE_LOCAL_TEST):
        """
        Look at channel values converted from hex binary to integers from the end_byte of the file
        For this use channel 9

        """

        test_file = Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH)
        channel9 = test_file.channel(9)
        print(len(channel9), len(self.file_end_decimal_chn9))
        assert channel9[-2:].all() == self.file_end_decimal_chn9.all()

    def test_only_read_some_channels(self, dig_file=FILE_LOCAL_TEST):
        """
        See whether it works to only load some channels

        :param dig_file:
        :return:
        """

        chn = [0, 9]
        settings = {'channels_to_read': chn}
        test_load = Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH, user_settings=settings)
        chn9 = test_load.channel(9)[-2:]
        chn0 = test_load.channel(0)[:3]
        assert chn9.all() == self.file_end_decimal_chn9.all() and chn0.all() == self.file_start_decimal_chn0.all()

    def test_do_not_read_some_channels(self, dig_file=FILE_LOCAL_TEST):
        """
        Check that channels that have not been requested are not read in

        :param dig_file:
        """

        chn = [3]
        settings = {'channels_to_read': chn}
        test_load = Da_C.DigAccess(file_name=dig_file, file_path=THIS_PATH, user_settings=settings)
        with pytest.raises(KeyError):
            test_load.channel(0)

# noinspection PyClassHasNoInit
class TestDownSampleFromServer(object):

    # def __init__(self):
        # self._server = 'http://db.nedm1'
        # self.acct = cloudant.Account(self._server)
        # self.acct.login('nedm_user', 'clu$terXz')
        # self.cookies = '; '.join(['='.join(x) for x in self.acct._session.cookies.items()])
        # self.submit = {
        #   "db" : "nedm%2Fmeasurements",
        #   "id" : FILE_TEST_ID,
        #   "att_name" : os.path.basename(FILE_TEST_NAME)
        # }
        # self.serverpath = '/_attachments/{db}/{id}/{att_name}'.format(**self.submit)

    def testdownloading(self, file_name=FILE_TEST_NAME, doc_id=FILE_TEST_ID):
        test_file = Da_C.DigAccess(file_name=file_name, doc_id=doc_id)
        assert isinstance(test_file, Da_C.DigAccess)

    def testdownsampling(self, file_name=FILE_TEST_NAME, doc_id=FILE_TEST_ID, downsample=50):
        test_file = Da_C.DigAccess(file_name=file_name, doc_id=doc_id, downsample=downsample)
        assert test_file.header.downsample == 50

