import cloudant
import json
import urllib3.request as p
import requests
import struct
import os
from clint.textui.progress import Bar as ProgressBar
import logging
import pynedm


# Authentication
o = pynedm.ProcessObject(uri="http://10.155.59.88:5984",
  username="nedm_user",
  password="""pw"""
  )
acct = o.acct

# Grab the correct database
db = acct["nedm%2Fmeasurements"]

# Get a list of measurements
# The query here is important, measure_name can be the initial stem of a set of
# measurements.  (Note: regular expressions are *not* supported by couch) This
# is used to define the endkey and startkey in the following query.
measure_name = "Monopole_1MHz"
query_dic = dict(descending=True,
                 endkey=[measure_name, 2015, 5, 16], # Gets on a particular day (16 June 2016)
                 startkey=[measure_name + "\ufff0", 2015, 5, 16, {}],
                 #endkey=[measure_name], # Gets *all* measurements with this stem
                 #startkey=[measure_name + "\ufff0", {}],
                 include_docs=True,
                 reduce=False
                 )

res = db.design('measurements').view('measurements').get(
                    params=query_dic)


# Get ids of documents
all_docs = [d["doc"] for d in res.json()["rows"]]
print("Found {} measurements\n".format(len(all_docs)))

# Grab a particular document (you can grab the id via a view call)

for res in all_docs:
   print res["_id"]
   for f in res["external_docs"]:
      print "   " + f
      x = o.download_file(res["_id"], f)
      bar = ProgressBar(expected_size=x.next(), filled_char='=')
      with open(f, "wb") as t:
          total = 0
          for ch in x:
              total += len(ch)
              bar.show(total)
              t.write(ch)
              t.flush()

