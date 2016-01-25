import fractions
import more_itertools
from HeXeData_Class import *

__author__ = 'William'
"""
Subclass of HeXeData to handle chunking up the data
"""

# Set chunk length to have a roughly integer number of both He and Xe cycles
GYRO_RATIO = fractions.Fraction(2.754).limit_denominator(25)
HELIUM_FREQUENCY = 40.79
XENON_FREQUENCY = 14.81
CHUNK_LENGTH = GYRO_RATIO.numerator / HELIUM_FREQUENCY

class ChunkedData:
    def __init__(self, file_name=None, name='unnamed'):
        """


            :param name: internal name of data for labeling
            :return:
            """
        self.chunk_length = CHUNK_LENGTH
        self._run_data = HeXeData(file_name, name)
        self._chunked_data_dict = {}
        self.chunk_data(CHUNK_LENGTH)
        print("Data chunked into {} second long sections, corresponding to {} "
              "He-3 cycles and {} Xe-129 cycles"
              .format(self.chunk_length, GYRO_RATIO.numerator, GYRO_RATIO.denominator))

    def __getattr__(self, attr):
        """
            Overload unknown attributes into nested HeXeData attributes
             
        """
        return getattr(self._run_data, attr)

    def chunk_data(self, chunk_length):
        """
        split up data file into chunks of length chunk_length

        :type self: ChunkedData class
        :rtype : none
        """
        # todo: setup chunking
        for stream in self.data_keys:
            ch_it = more_itertools.chunked(
                self._run_data.channel(stream), self.points_per_chunk)
            ch_list = list(ch_it)
            ch_list.pop()
            # remove last data segment,
            # which is presumably not the same length as the others
            self._chunked_data_dict[stream] = np.array(ch_list)

    @property
    def points_per_chunk(self):
        return np.round(self.chunk_length / self.rate)

# todo: unit tests: check things ending _dict are dictionary objects
# todo: UT: check lengths of chunks and number of chunks are consistent

