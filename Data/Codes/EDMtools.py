__author__ = 'William'
###
#
# Tools for EDM analysis and workflow
#
###
import os
import sys
import numpy
import json
import struct
import pynedm

import scipy as sp
import matplotlib.pyplot as plt

squidchannels = {'0':'x1','1':'y1','2':'z1','3':'x2','4':'y2','5':'z2'}

def slice(data,start,stop=0):
    """
    Return a section of data between time start and stop.  stop = 0 corresponds to the end of the run

    :param data: digitizer data
    :param start:
    :param stop:
    :return:
    """



def re_key(dictionary, keymap):
    """
    Change the keys in dictionary from keymap.keys to keymap.values

    :param dictionary: dictionary to be re-keyed
    :param keymap: dictionary with new keys as values old keys as keys
    :return: dictionary that has been re-keyed
    """
    for k,v in keymap.iteritems():
        try:
            dictionary[v] = dictionary.pop(k)
        except KeyError:
            print("key {0} is not in dictionary {1}".format(k,dictionary))
    return dictionary

def channel_plot(run, chn,figure=False):
    if not figure:
        figure = plt.subplot()
    figure.plot(run['time'],run[chn])
    #figure.show()
    return figure


##############
##############
##############




_username = "nedm_user"
_password = "pw"
_server = "http://raid.nedm1"
# or (preferred)
_server = "http://10.155.59.88:5984"
_db = "nedm%2Fmeasurements"

def pp(obj):
    print("\n{}".format(json.dumps(obj, indent=4)))

def interpret_file(file_name, doc_id=None):
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
    ll = lambda : open(file_name)
    if doc_id is not None:
        po = pynedm.ProcessObject(uri=_server, username=_username, password=_password, adb=_db)
        ll = lambda : po.open_file(doc_id, file_name)

    with ll() as o:
        header_length = struct.unpack("<L", o.read(4))[0]
        o.seek(4)
        hdr = json.loads(o.read(header_length))
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


        ## print out the data
        #pp(hdr)

        # Reads from position 4 + header_length
        data_start = 4 + header_length
        o.seek(data_start)

        # We should always read by a factor of this chunk_size
        chunk_size = bit_depth * len(hdr["channel_list"])

        o.seek(0,os.SEEK_END)
        data_end = o.tell()
        o.seek(data_start)

        return channel_dict(numpy.fromstring(o.read(2000*chunk_size), dtype=dt))

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


# if __name__ == '__main__':
#     """
#     Call like:
#       python interpret_data.py 2015-09-16\ 16-27-13.392973.dig 3ae0269567420a2f5269aea9d0a858b7
#       or
#       python interpret_data.py /local/path/to/file/2015-09-16\ 16-27-13.392973.dig
#     """
#     doc_id = None
#     if len(sys.argv) > 2:
#         doc_id = sys.argv[2]
#     interpret_file(sys.argv[1], doc_id)