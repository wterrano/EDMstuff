import cloudant
import os
import pycurl
from StringIO import StringIO
import json
from clint.textui.progress import Bar as ProgressBar
'''
 URL to request downsampled data

/_attachments/[db_name]/[doc_id]/[attachment].dig/downsample/50

 http://db.nedm1/_attachments/nedm%2Fmeasurements/2e32e3448b57ee446ce8edb9a3449e0e/2016-06-05
00-14-18.694128-0.dig/downsample/50 '''

# _server = "http://127.0.0.1"
_server = 'http://db.nedm1'
acct = cloudant.Account(_server)
acct.login('nedm_user', 'clu$terXz')
cookies = '; '.join(['='.join(x) for x in acct._session.cookies.items()])
submit = {
  "db" : "nedm%2Fmeasurements",
  "id" : "91658d165b1e7603942a628edf7af557",
  "att_name" : os.path.basename('2016-07-18 15-02-50.343916-0.dig')
}
serverpath = '/_attachments/{db}/{id}/{att_name}'.format(**submit)
submit = {
  "db" : "nedm%2Fmeasurements",
  "id" : "2e32e3448b57ee446ce8edb9a3449e0e",
  "att_name" : os.path.basename('2016-07-18 15-02-50.343916-0.dig')
}
serverpath = '/_attachments/{db}/{id}/{att_name}'.format(**submit)


def download_file(file_name, get_from_path):
    r = acct.get(get_from_path, stream = True)
    # print(r.status)
    print(r.headers)
    total_size = int(r.headers['content-length'])
    bar = ProgressBar(expected_size=total_size, filled_char='=')
    with open(file_name, 'wb') as f:
        total = 0
        for chunk in r.iter_content(chunk_size=100*10240):
            if chunk:
                total += len(chunk)
                bar.show(total)
                f.write(chunk)
                f.flush()

#download_file('test.dig', _server + '/_attachments/{db}/{id}/{att_name}'
#              .format(**submit))

s = _server + serverpath
sd = s + '/downsample/50'
print(sd)
rd = acct.get(sd)
print(rd)
'''
s = _server + serverpath
>>> s
'http://db.nedm1/_attachments/nedm%2Fmeasurements/91658d165b1e7603942a628edf7af557/2016-07-18 15-02-50.343916-0.dig'
>>> sd = s + '/downsample/50'
>>> sd
'http://db.nedm1/_attachments/nedm%2Fmeasurements/91658d165b1e7603942a628edf7af557/2016-07-18 15-02-50.343916-0.dig/downsample/50'
>>> rd = t.acct.get(sd)
>>> rd.headers
{'Content-Length': '1445671', 'Content-Disposition': 'attachment; filename="2016-07-18 15-02-50.343916-0_downsample.dig"', 'Server': 'nginx/1.9.3', 'Connection': 'keep-alive', 'Date': 'Thu, 21 Jul 2016 14:42:50 GMT', 'Content-Type': 'application/octet-stream'}
>>> rd
<Response [200]>
>>> type(rd)
<class 'requests.models.Response'>
>>> len(rd.content)
1445671
np.fromstring(rd.content[0:4],np.int32)
array([987], dtype=int32)
>>> rd.content[987:1020]
'nt"}\x00\x00\x80\xff\x00\x00\x80\xff\xff\xff\x7f\x00\xff\xff\x7f\x00\xff\xff\x7f\x00\xff\xff\x7f\x0001\n\x00\x1d'
'''

############
##
## Potentially useful stuff from DataAccess refactor
##
#############
#
# def set_compression_factor(self):
#     """
#     find downsampling factor needed for the requested cutoff frequency
#
#     :return: integer compression factor.
#     """
#     if self._cutoff_frequency is None:
#         return 1
#     try:
#         cf = int(np.floor(self.file_frequency / self._cutoff_frequency))
#     except TypeError:
#         print("Invalid type for cutoff_frequency")
#         raise
#     else:
#         if cf > 0:
#             return cf
#         else:
#             raise ValueError("cutoff_frequency is out of range, should be between 0 and {}, or None".
#                              f
# ###
# # Interfacing with the data file
# ###
#
# def load_header_info(self, header_length):
#     """
#     set up internal header with needed parameters from file header
#     """
#
#     return
#
# # @profile
# def process_incoming_data(self):
#     """
#     Extract relevant channel, downsample and add it to data array
#
#     """
#     data = self._temp_dict[self.channel]
#     filtered_data = self.low_pass_filter(data)
#     self.data_array = np.concatenate((self.data_array, filtered_data))
#     return
#
# # @profile
# def low_pass_filter(self, input_data):
#     """
#     Apply a crude down-sample the incoming data in order to give it
#     a more reasonable sample frequency.
#
#     :param input_data: input_data array to be low-pass filtered
#     :return:
#     """
#     self.downsampling = self.file_downsampling * self.compression_factor
#     self.sample_frequency = self.file_frequency / self.compression_factor
#     number_of_samples = input_data.size
#     padding = self.compression_factor - (number_of_samples % self.compression_factor)
#     if padding == self.compression_factor:
#         padding = 0
#     padded_data = np.append(input_data, np.zeros(padding) * np.NaN)
#     data_reshape = padded_data.reshape(-1, self.compression_factor)
#     sampled_data = scipy.nanmean(data_reshape, 1)
#     return sampled_data
#     format(self.file_frequency))
