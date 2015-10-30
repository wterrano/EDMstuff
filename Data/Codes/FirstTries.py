__author__ = 'William'

#import pynedm
import fit_freq_domain_chunks as flo
import EDMtools as tools
import matplotlib.pyplot as plt
import HeXeData as hx


_server = "http://10.155.59.88:5984/"
_un = "nedm_user"
_pa = "clu$terXz"
_db = "nedm%2Fmeasurements"

#o = pynedm.ProcessObject(_server,_un,_pa,_db)
#acct = o.acct

aoff = hx.HeXeData(hx.alloff_file)
aon = hx.HeXeData(hx.allon_file)
aon.plot_channel('y1',order_to_remove= 1)
aoff.plot_channel('y1',order_to_remove = 1,offset=.01)