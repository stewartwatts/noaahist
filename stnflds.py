#!/usr/bin/env python  

"""
Log which weather fields stations have
"""

import os
import re
import sys
import random
import datetime as dt
import traceback
from collections import OrderedDict
from multiprocessing import Pool, cpu_count
from subprocess import Popen, PIPE

STN_LOG = "static/stn_flds.txt"
header = ",".join(['ID','HR','MN','DIR','SPD','GUS','CLG','SKC','L','M','H','VSB','MW1','MW2','MW3','MW4','AW1','AW2','AW3','AW4','W',
          'TEMP','DEWP','SLP','ALT','STP','MAX','MIN','PCP01','PCP06','PCP24','PCPXX','SD']) + "\n"
if not os.path.exists(STN_LOG):
    with open(STN_LOG, 'w') as f:
        f.write(header)

# US stations
def datestr_to_dt(datestr):
    return dt.date(*map(int, [datestr[:4], datestr[4:6], datestr[6:8]]))

def parse_stn_line(line):
    try:
        return dict(usafid_wban='-'.join([line[0:6], line[7:12]]), name=line[13:43], state=line[49:51], lat=float(line[58:64])/1000.,
                    lon=float(line[65:72])/1000., sd=datestr_to_dt(line[83:91]), ed=datestr_to_dt(line[92:100]),)
    except:
        return None

def stn_covg(path='static/ISH-HISTORY.TXT'):
    stns = {'-'.join([line[0:6], line[7:12]]): parse_stn_line(line) for line in map(lambda x: x.strip(), open(path).readlines())}
    return {key: stns[key] for key in stns if stns[key]}

def get_stn_year(_id, us_stns):
    sd = us_stns[_id]['sd']
    ed = us_stns[_id]['ed']
    yrs = range(sd.year, ed.year + 1)
    try:
        return yrs[-3]              # likely to be representative, if exists
    except:
        return random.choice(yrs)   # faliing that, random choice

def log_station((_id, log_stns, us_stns)):
    # only continue if we have not logged this station already
    if _id in log_stns:
        return ''
    try:
        yr = get_stn_year(_id, us_stns)
        url = 'ftp://ftp.ncdc.noaa.gov/pub/data/noaa/{0}/{1}-{0}.gz'.format(yr, _id)
        print '\nretrieving stn=%s  yr=%s ... \n' % (_id, str(yr))
        p1 = Popen(["curl", url], stdout=PIPE)
        p2 = Popen(["gunzip"], stdin=p1.stdout, stdout=PIPE)
        p3 = Popen(['java', '-classpath', 'static', 'ishJava'], stdin=p2.stdout, stdout=PIPE)
        data = p3.communicate()[0].split("\n")[1:-1]

        flds = (
            ['HR',      [21,23]], ['MN',      [23,25]], ['DIR',     [26,29]], ['SPD',     [30,33]], ['GUS',   [34,37]], 
            ['CLG',     [38,41]], ['SKC',     [42,45]], ['L',       [46,47]], ['M',       [48,49]], ['H',     [50,51]], 
            ['VSB',     [52,56]], ['MW1',     [57,59]], ['MW2',     [60,62]], ['MW3',     [63,65]], ['MW4',   [66,68]], 
            ['AW1',     [69,71]], ['AW2',     [72,74]], ['AW3',     [75,77]], ['AW4',     [78,80]], ['W',     [81,82]], 
            ['TEMP',    [83,87]], ['DEWP',    [88,92]], ['SLP',     [93,99]], ['ALT',   [100,105]], ['STP', [106,112]], 
            ['MAX',   [113,116]], ['MIN',   [117,120]], ['PCP01', [121,126]], ['PCP06', [127,132]], 
            ['PCP24', [133,138]], ['PCPXX', [139,144]], ['SD',    [145,147]], 
            )

        def get_col(data, fld):
            return [dataline[fld[1][0]:fld[1][1]] for dataline in data]
    
        def fld_test(col):
            return any(['*' not in x for x in col])
    
        line = ",".join([_id] + map(str, [1 if fld_test(get_col(data, fld)) else 0 for fld in flds])) + "\n"
        return line
    except:
        traceback.print_exc()
        return ''
    
def main(n):
    # all stns in the US
    us_stns = stn_covg()
    # stns already tested, mapped by USAFID_WBAN
    log_stns = {line.split(",")[0]: line for line in open(STN_LOG).readlines()[1:]}   # skip header
    # station ids not logged yet
    unk_stns = [stn for stn in us_stns if stn not in log_stns]
    print "\nlen(unk_stns):", len(unk_stns), '\n'
    
    # stns we will log (randomly selected)
    t = range(len(unk_stns))
    random.shuffle(t) 
    stn_ids = [unk_stns[t[i]] for i in range(min(n, len(unk_stns)))]
    
    # make requests in parallel
    nprocs = max(1, cpu_count() - 1)
    print "making requests in parallel on < %s > processors" % str(nprocs)
    pool = Pool(processes=nprocs)
    result = pool.map_async(log_station, [(_id, log_stns, us_stns) for _id in stn_ids])
    log_lines = result.get()

    # write log_lines to STN_LOG
    with open(STN_LOG, "a") as f:
        f.writelines(log_lines)
    
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

