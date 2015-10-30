__author__ = 'William'
"""
Class containing data from HeXe experiment

"""


import os
import sys
import numpy
import json
import struct
import pynedm

import scipy as sp
import matplotlib.pyplot as plt
from matplotlib import rc


alloff_file = "2015-10-05 13-45-38.031713_downsample.dig"
allon_file = "2015-10-05 14-35-42.713321_downsample.dig"

squidchannels = {'x1':0,'y1':1,'z1':2,'x2':3,'y2':4,'z2':5}

import EDMtools as tools

_datapath = "/Users/William/Desktop/EDM/Data/DataRuns/"

_username = "nedm_user"
_password = "pw"
_server = "http://raid.nedm1"
# or (preferred)
_server = "http://10.155.59.88:5984"
_db = "nedm%2Fmeasurements"


class HeXeData():
    """
    Class containing data from HeXe experiment

    """

    def __init__(self,filename=None):
        """
        :param filename: name of the .dig file containing the data to be used
        :return:
        """

        self.conversion_factors = {'Volts': 1.1920929e-6 }
        self.units = "Volts"
        self.channeldict = squidchannels # dictionary allowing the user to rename the channels
        self._datapath = "/Users/William/Desktop/EDM/Data/DataRuns/"
        self._filename = filename
        self._filepath = self._datapath+filename
        self.load_file()

    def load_file(self):
        """
        for getting .dig files and putting them in the class.

        This method also converts the data based on self.conversion_factor
        and sets up some additional useful attributes.

        :return:
        """

        self.interpret_file()
        self.set_scale()
        self.sample_rate = self.hdr['freq_hz'] # DAQ sampling rate
        self.length_of_data = self.datadict.values()[0].size
        self.run_duration = self.downsampling*self.length_of_data*(1/self.sample_rate)
        self.time = numpy.linspace(0,self.run_duration,self.length_of_data)
        self.re_key(self.datadict,self.channeldict)


    # Volt conversion factor from Flo's code = {ADC Range in voltage}/{24 bit ADC} = 20/(2**24)
    # volts/bit

    def set_scale(self):
        for k,v in self.datadict.iteritems():
            self.datadict[k]=v*self.conversion_factors['Volts']


    def low_pass(self,f):

####
#### Direct access to useful dictionary elements
#### channel is the safest way to ask for a channel
####



    def channel(self,name):
        if name is 'time':
            return self.time
        try:
            return self.datadict[name]
        except KeyError:
            print('channel "{0}" not loaded'.format(name))
            return {}

    @property
    def downsampling(self):
        return self.hdr['downsample']

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


#########
######### Data analysis and manipulation
#########

    def poly_fit(self, order_to_fit):
        """
        fit a polynomial to the data. Add a new dictionary of poly1d elements
        :
        :param order_to_fit:
        :return: dictionary of poly1d classes added to data class
        """
        self.driftdict = {}
        for k,v in self.datadict.iteritems():
            c = numpy.polyfit(self.time,v,order_to_fit)
            self.driftdict[k] = numpy.poly1d(c)
        return

    def remove_drift(self,chn,order_to_remove=0):
        """
        remove drift from channel

        :param order_to_remove: order of the polynomial subtracted from the data
        :return: array of the channel with the drift removed
        """
        self.poly_fit(order_to_remove)
        fitpoints = self.driftdict[chn](self.time)
        return self.channel(chn) - fitpoints


#########
######### Display and Presentation
#########

    def plot_channel(self,chn,remove_drift = True,
        order_to_remove = 1, scale=1, offset = 0, figure=False):
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
            data = self.remove_drift(chn,order_to_remove)
        else:
            data = self.channel(chn)
        figure.plot(self.time,(scale*data)+offset,label=chn)
        figure.set_xbound(self.time[0],self.time[-1])
        figure.set_xlabel('time [s]')
        figure.set_ylabel('{0} [{1}]'.format(chn,self.units))
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
        ll = lambda : open(self._filepath)
        # retrieve file from server
        if doc_id is not None:
            po = pynedm.ProcessObject(uri=_server, username=_username, password=_password, adb=_db)
            ll = lambda : po.open_file(doc_id, self._file_name)

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
            if bit_depth == 2: dt = numpy.int16
            elif bit_depth ==4: dt = numpy.int32
            elif bit_depth == 8: dt = numpy.float64
            else: raise Exception("unknown bit_depth")

            def channel_dict(dat):
                x = dat
                if bit_shift != 0:
                    x = numpy.right_shift(dat, bit_shift)

                cl = hdr["channel_list"]
                total_ch = len(cl)

                # Now create a dictionary of the channels
                return dict([(cl[i],x[i::total_ch]) for i in range(len(cl))])


            # Reads from position 4 + header_length
            data_start = 4 + header_length
            o.seek(data_start)

            # We should always read by a factor of this chunk_size
            chunk_size = bit_depth * len(hdr["channel_list"])

            o.seek(0,os.SEEK_END)
            data_end = o.tell()
            o.seek(data_start)
            self.datadict = channel_dict(numpy.fromstring(o.read(2000000*chunk_size), dtype=dt))

            # # We can iterate over everything...
            # print("Iterating")
            # try:
            #     # Only works for files online
            #     for x in o.iterate(1024*chunk_size):
            #         chunk_data = channel_dict(numpy.fromstring(x, dtype=dt))
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
            # print(channel_dict(numpy.fromstring(o.read(2000*chunk_size), dtype=dt)))


####
####  Helper functions

    def re_key(self, dictionary, keymap):
        """
        Change the keys in dictionary from keymap.keys to keymap.values

        :param dictionary: dictionary to be re-keyed
        :param keymap: dictionary with new keys as keys and old keys as values
        :return: dictionary that has been re-keyed
        """
        for k,v in keymap.iteritems():
            try:
                dictionary[k] = dictionary.pop(v)
            except KeyError:
                print("key {0} is not in dictionary {1}".format(k,dictionary))
        return dictionary