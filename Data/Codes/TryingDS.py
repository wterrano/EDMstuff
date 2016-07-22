import cloudant
import os
import pycurl
from StringIO import StringIO
import json
from clint.textui.progress import Bar as ProgressBar

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

download_file('test.dig', _server + '/_attachments/{db}/{id}/{att_name}'
              .format(**submit))

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