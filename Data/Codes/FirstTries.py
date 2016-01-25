__author__ = 'William'

# import pynedm
import fit_freq_domain_chunks as flo
import EDMtools as tools
import matplotlib.pyplot as plt
import HeXeData_Class as HXD
import ChunkedData_Class as ChD


_server = "http://10.155.59.88:5984/"
_un = "nedm_user"
_pa = "clu$terXz"
_db = "nedm%2Fmeasurements"

#o = pynedm.ProcessObject(_server,_un,_pa,_db)
#acct = o.acct

adoff = HXD.HeXeData(HXD.ALL_OFF_FILE, 'ds')
aoff = HXD.HeXeData(HXD.ALL_OFF_FILE, 'off')
aon = HXD.HeXeData(HXD.ALL_ON_FILE, 'on')
# adoff.down_sample(25)
aoff.down_sample(10)
aon.cutoff_frequency(200)
# aoff.plot_fft('y2')
# aon.plot_fft('y2')
# adoff.plot_fft('y2')
aon.plot_data('y2', order_to_remove=1)
# aoff.plot_data('y2', order_to_remove=1, offset=.01)
# adoff.plot_data('y2', order_to_remove=1, offset=.01)

ALL_OFF_FILE = "2015-10-05 13-45-38.031713_downsample.dig"
def testch(fname = ALL_OFF_FILE):
    chunked = ChD.ChunkedData(fname)
    chunked.plot_data('x2')
    return chunked

#testch()