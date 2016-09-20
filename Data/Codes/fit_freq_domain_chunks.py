import json
import struct
import os
#import log

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
#import allantools as al

def interpret_file(url):
    """
    File structure is:
       bytes 0..3: length of json header N (excluding header word)
       bytes 4..4+N: json header (ASCII data)
       bytes 4+N+1..EOF: binary data of channels

    The binary data format depends on what's in the json header:
      header["channel_list"]      ---> ordered list of channels
      header["channel_names"]     ---> dictionary relating channel numbers and names
      header["byte_depth"]        ---> size of binary word
      header["bit_shift"]         ---> amount to shift right
      header["freq_hz"]           ---> sampling rate
      header["conversion_factor"] ---> V to T
      header["full_scale"]        ---> total range in V
      header["current_gains"]     ---> dictionary of gain numbers for channel numbers
      header["gain_conversion"]   ---> translate gain numbers to actual gain factors

    Every channel is listed one after another for each time point (fully
    interlaced)

    """
    pass

def Read_dig2(file_path, unit="volt"):
    '''Reads data from data file. Code made by Flo'''
    data_file = open(file_path, "rb")
    header_length = struct.unpack("<L", data_file.read(4))[0]
    data_file.seek(4)
    hdr = json.loads(data_file.read(header_length))
    #to interpret the numbers
    byte_depth = hdr["byte_depth"]
    bit_shift = hdr["bit_shift"]
    #extract header information to scale the numbers
    number_of_channels = len(hdr["channel_list"])
    if "current_gains" in hdr:
        channel_gains_dict = hdr["current_gains"]["1"]
        gain_conversion_table = hdr["gain_conversion"]
        gains_dict = {}
        for i in channel_gains_dict:
            #lookup the gain table
            gain = gain_conversion_table[str(channel_gains_dict[str(i)])]
            #convert to float for scaling
            gains_dict[str(i)] = float(gain.lstrip("x"))
    else:
        gains_dict = {}
        for i in range(number_of_channels):
            gains_dict[str(i)]=1.0

    if "full_scale" in hdr: full_scale = hdr["full_scale"]
    else: full_scale = 20

    if unit == "tesla":
        conversion_factor = hdr["conversion_factor"]
    else:
        conversion_factor = 1

    sample_rate = hdr["freq_hz"]
    if "channel_names" in hdr: channel_names = hdr["channel_names"]
    else: channel_names = False
    measurement_name = hdr["measurement_name"]

    #convert the data
    dt = None
    if byte_depth == 2: dt = np.int16
    elif byte_depth ==4: dt = np.int32
    else: raise Exception("unknown bit_depth")

    # Reads from position 4 + header_length
    data_file.seek(4+header_length)
    interlaced_array = np.fromfile(data_file, dtype=dt)
    # Do a right shift if necessary
    if bit_shift != 0:
        interlaced_array = np.right_shift(interlaced_array, bit_shift)

    # Scaling of the raw data
    scaled_data_dict={}
    for i in range(number_of_channels):
        single_ch = interlaced_array[i::number_of_channels]
        single_ch_scaled = single_ch*full_scale*conversion_factor/(gains_dict[str(i)]*2**(24))
        #create a dictionary of the channels
        if channel_names:
            scaled_data_dict.update(dict([(channel_names[str(i)], single_ch_scaled)]))
        else: scaled_data_dict.update(dict([(str(i), single_ch_scaled)]))
    time_axis = np.array([i/sample_rate for i in range(len(single_ch))])
    scaled_data_dict.update(dict(time=time_axis))
    #print scaled_data_dict
    #print "Scaled data ({}) incl. time axis:\n".format(len(single_ch))
    ##print scaled_data_dict['time']
    data_file.close()
    return (scaled_data_dict, sample_rate, channel_names, measurement_name, hdr)

def make_channels_list(hdr,data):
    '''Makes list of channels from input data and another list with their names

    works by using a list of channel names and if there exists each different
    desired channel in names then uses same channel to put into channels list
    to be used later'''

    cn = hdr[u'channel_names']
    channel_names_list = []
    channels = []
    channel_names = []
    for key, value in cn.iteritems():
        temp = [key,value]
        channel_names_list.append(temp)
    for ch in channel_names_list: #Assumes there exists each squid channel
        if ch[1] == u'SQUID_X1':
            x1 = data[ch[0]]
            channels.append(x1)
            channel_names.append('x1')
        elif ch[1] == u'SQUID_X2':
            x2 = data[ch[0]]
            channels.append(x2)
            channel_names.append('x2')
        elif ch[1] == u'SQUID_Y1':
            y1 = data[ch[0]]
            channels.append(y1)
            channel_names.append('y1')
        elif ch[1] == u'SQUID_Y2':
            y2 = data[ch[0]]
            channels.append(y2)
            channel_names.append('y2')
        elif ch[1] == u'SQUID_Z1':
            z1 = data[ch[0]]
            channels.append(z1)
            channel_names.append('z1')
        elif ch[1] == u'SQUID_Z2':
            z2 = data[ch[0]]
            channels.append(z2)
            channel_names.append('z2')
        if len(data) > 7: #sometimes data doesn't have all the channels that channel names does
            if ch[1].lower() == u'lockin_he':
                lockin_he = data[ch[0]]
                channels.append(lockin_he)
                channel_names.append('lockin he')
            if ch[1].lower() == u'lockin_xe':
                lockin_xe = data[ch[0]]
                channels.append(lockin_xe)
                channel_names.append('lockin xe')
    return (channels, channel_names)

def downsample_to_2n(data, sample_rate, location = 'end_byte'):
    '''Downsamples a dataset to be of length that is equal of 2^n. Used for
    Making fft quicker. if location == end_byte then takes data off of end_byte of
    dataset. If location == start_byte then takes data off of beginning of dataset'''
    closest_lower = 2
    while closest_lower < len(data):
        closest_lower *= 2
    closest_lower /= 2
    if location == 'end_byte':
        return data[:closest_lower]
    elif location == 'start_read':
        return data[len(data) - closest_lower:]

def find_he_xe_freqs(x_data, y_data):
    '''Finds frequency of peak for xenon and helium. Does by finding peak of
    fft of data where peak is around 14 for xe and 39 for he. Can make better by applying a fit around
    the guess area and finding peak of fit.'''

    fourier = np.fft.rfft(y_data)
    x_n = x_data.size
    rate = x_data[1] - x_data[0] #ensures there wasn't anything weird with time changing
    freqs = np.fft.rfftfreq(x_n,rate) #creates axis of frequencies corresponding to fft peaks
    he = [i for i in freqs if 36 < i < 42] #regions to search for he
    he_loc = np.where(freqs == he[0])[0][0] #index of beginning of he region
    he_loc_end = np.where(freqs == he[-1])[0][0] #index of end_byte of he region
    xe = [i for i in freqs if 12 < i < 16] #same as he
    xe_loc = np.where(freqs == xe[0])[0][0]
    xe_loc_end = np.where(freqs == xe[-1])[0][0]
    he_max = np.amax(fourier[he_loc:he_loc_end]) #finds peak in he region
    xe_max = np.amax(fourier[xe_loc:xe_loc_end]) #same
    he_max_loc = np.where(fourier == he_max)[0][0] #index of peak
    xe_max_loc = np.where(fourier == xe_max)[0][0] #same
    he_freq = freqs[he_max_loc] #actual frequency of peak found
    xe_freq = freqs[xe_max_loc] #same
    return (he_freq, xe_freq, freqs, fourier)

#Read_dig2("2015-07-27%2019-10-20.729984.dig")

#argparse
#have x1, y1, z1, x2, y2, z2, evtl. lockins, extra...
#make grads x, y, z
#make mags x, y, z? (x1-x2/2 ...)
#choose times from gradZ
#(sample down to 2^n)?
#choose time interval
#(sample down to 2^n)?
#perform fft (window?)
#fit peaks
#make allan dev.

#plot(time,zgrad)
                #title('Z gradiometer')
                #xlabel('time (s)')
                #ylabel('Volts')
                #ylim(bounds(zgrad))
                #show()

                #start_byte =  float(raw_input('Enter beginning of pulse in seconds: '))
                #end_byte = float(raw_input('Enter end_byte of pulse in seconds: '))

                #print '...'
                #time_loc_start = min(range(len(time)), key=lambda i: abs(time[i]-start_byte))
                #time_loc_end = min(range(len(time)), key=lambda i: abs(time[i]-end_byte))
