#!/usr/bin/env python3
# 
#
# A sample REST client for the face match application
#
import requests
import json
import time
import sys, os
import jsonpickle

def doUrl(addr, filename, debug=False):
    # prepare headers for http request
    headers = {'content-type': 'application/json'}
    # send http request with image and receive response
    image_url = addr + '/scan/url'
    data = jsonpickle.encode({ "url" : filename})
    response = requests.post(image_url, data=data, headers=headers)
    if debug:
        # decode response
        print("Response is", response)
        print(json.loads(response.text))

def doCheck(addr, hashval, debug=False):
    url = addr + "/check/" + hashval
    response = requests.get(url)
    if debug:
        # decode response
        print("Response is", response)
        print(json.loads(response.text))

host = sys.argv[1]
cmd = sys.argv[2]

addr = 'http://{}'.format(host)

if cmd == 'url':
    url = sys.argv[3]
    reps = int(sys.argv[4])
    start = time.time()
    for x in range(reps):
        doUrl(addr, url, True)
    delta = ((time.time() - start)/reps)*1000
    print("Took", delta, "ms per operation")
elif cmd == 'check':
    hashval = sys.argv[3]
    reps = int(sys.argv[4])
    start = time.time()
    for x in range(reps):
        doCheck(addr, hashval, True)
    delta = ((time.time() - start)/reps)*1000
    print("Took", delta, "ms per operation")
else:
    print("Unknown option", cmd)