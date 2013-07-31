#!/usr/bin/env python  

"""
Log which weather fields a given station has
"""

import os
import re
import sys
import random
import datetime as dt
from multiprocessing import Pool, cpu_count
from subprocess import Popen, PIPE

STN_LOG = 

# US stations
def stn_covg(path='static/ISH-HISTORY.TXT'):
    stns = {'-'.join([line[0:6], line[7:12]]): parse_stn_line(line) for line in map(lambda x: x.strip(), open(path).readlines())}
    return {key: stns[key] for key in stns if stns[key]}
stns = stn_covg()

# Stations that have already been tested


unk_stns = None #TODO!

def log_station(_id):
    pass

def main(n):
    t = random.shuffle(range(len(unk_stns)))
    for i in range(n):
        log_station(unk_stns[t[i]])

if __name__ == "__main__":
    if sys.argv[1:]:
        if re.search("^\d{6}-\d{5}$", sys.argv[1]):
            log_station(re.search("^\d{6}-\d{5}$", sys.argv[1]).group(0))
        else:
            # coerce first arg to an int, and randomly check that many unknown stations
            main(int(sys.argv[1]))
    else:
        # by default, log 10 random US stations
        main(10)
