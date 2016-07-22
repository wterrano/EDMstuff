import json
import numpy as np
import pynedm
import struct
import scipy
import os
import sys
__author__ = 'William'

THIS_PATH=os.path.dirname(os.path.abspath(__file__))
NET_TEST = dict(filename="2016-06-05 00-14-18.694128-0.dig/downsample/10",
                doc_id="2e32e3448b57ee446ce8edb9a3449e0e")


class FileHandle:
    # retrieve file from server
    def __init__(self, file_name=None, file_path=THIS_PATH, chn=None, cutoff_frequency=None, doc_id=None):
        self._file_name = file_name
        self._doc_id = doc_id
        self._server_dict = dict(_db="nedm%2Fmeasurements",
                            #_server="http://10.155.59.88:5984",
                           _server = "http://10.155.59.15",
                            _server2="http://db.nedm1",
                            _password="clu$terXz",
                            _username="nedm_user")
        self.ll = lambda: open(self._file_address)
        if self._doc_id is not None:
            po = pynedm.ProcessObject(uri=self.sd['_server2'],
                                  username=self.sd['_username'],
                                      password=self.sd['_password'],
                                      adb=self.sd['_db'])
        print(self._file_name)
        self.ll = lambda: po.open_file(self._doc_id, self._file_name)

    def report(self, n):
        for a in range(n):
            y = self.ll().read(4)
            print(np.fromstring(y, np.int32))

    @property
    def sd(self):
        return self._server_dict


tester = FileHandle(file_name=NET_TEST['filename'], doc_id=NET_TEST['doc_id'])
tester.report(10)
