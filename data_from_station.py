#!/usr/bin/env python

import datetime as dt
import argparse
from subprocess import Popen, PIPE
import re

# offsets for NOAA's fixed width format
NOAA_fields = {'HR_TIME':  [13,23], # YYYYMMDDHH
               'HR':[21,23],'MN':[23,25],'DIR':[26,29],'SPD':[30,33],'GUS':[34,37],
               'CLG':[38,41],'SKC':[42,45],'L':[46,47],'M':[48,49],'H':[50,51],
               'VSB':[52,56],'MW1':[57,59],'MW2':[60,62],'MW3':[63,65],'MW4':[66,68],
               'AW1':[69,71],'AW2':[72,74],'AW3':[75,77],'AW4':[78,80],'W':[81,82],
               'TEMP':[83,87],'DEWP':[88,92],'SLP':[93,99],'ALT':[100,105],'STP':[106,112],
               'MAX':[113,116],'MIN':[117,120],'PCP01':[121,126],'PCP06':[127,132],'PCP24':[133,138],
               'PCPXX':[139,144],'SD':[145,147],}

def datestr_to_dt(s):
    return dt.date(*map(int, [s[:4], s[4:6], s[6:8]]))

def main(args):
    sd = datestr_to_dt(args.startdate)
    ed = datestr_to_dt(args.enddate)
    yrs = range(sd.year, ed.year+1)
    lines = [",".join(['NAME', 'HR_TIME'] + args.flds)]
    url_fmt = 'ftp://ftp.ncdc.noaa.gov/pub/data/noaa/{0}/{1}-{0}.gz'
    for yr in yrs:
        url = url_fmt.format(yr, args.stn_id)
        p1 = Popen(["curl", url], stdout=PIPE)
        p2 = Popen(["gunzip"], stdin=p1.stdout, stdout=PIPE)
        p3 = Popen(['java', '-classpath', 'static', 'ishJava'], stdin=p2.stdout, stdout=PIPE)
        data = p3.communicate()[0].split("\n")[1:-1]
        for obs in data:
            hr_time = obs[NOAA_fields['HR_TIME'][0] : NOAA_fields['HR_TIME'][1]]
            if args.startdate < hr_time < args.enddate:
                lines += [",".join([args.queryname, hr_time] + [re.sub("\*+", "*", obs[NOAA_fields[fld][0] : NOAA_fields[fld][1]].strip()) for fld in args.flds])]
    print "\n".join(lines) + "\n"
                
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='./data_from_station.py')
    parser.add_argument('-n', '--queryname', type=str, required=True)
    parser.add_argument('-i', '--stn_id', type=str, required=True)
    parser.add_argument('-f', '--flds', type=str, nargs='+', required=True)
    parser.add_argument('-s', '--startdate', type=str, required=True)
    parser.add_argument('-e', '--enddate', type=str, required=True)
    args = parser.parse_args()
    main(args)
