#!/usr/bin/env python

import sys
import urllib2
import datetime as dt
import argparse
from math import radians, cos, sin, asin, sqrt

weather_keys = {
    '':'',
    '':'',
    '':'',
    '':'',
    '':'',
    '':'',
    '':'',
    '':'',
    }

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km * 0.621371

def date_action():
    class DateArgsAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            nmin, nmax = 1, 2
            if not nmin<=len(values)<=nmax:
                msg='argument "date" requires 1 arg (single date) or 2 args (inclusive start and end dates)'
                raise argparse.ArgumentTypeError(msg)
            elif any(len(val) != 8 for val in values):
                msg='"date" arguments must be 8 digit strings in YYYYMMDD format'
                raise argparse.ArgumentTypeError(msg)
            elif len(values) == 2:
                if values[1] <= values[0]:
                    msg='argument "date": end date must be after start date if two dates are passed'
            else:
                try:
                    ds = [dt.date(*map(int, [val[:4], val[4:6], val[6:]])) for val in values]
                except:
                    msg='"date" arguments must form valid dates'
                    raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return DateArgsAction

def zips_action():
    class ZipArgsAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if any(len(val) != 5 or not val.isdigit() for val in values):
                msg= '"zips" arguments must be one or more 5 digit zip codes'
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return ZipArgsAction

def lats_action():
    class LatArgsAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            try:
                tmp = map(float, values)
            except:
                msg = '"lats" arguments must be coercible to floats'
                raise argparse.ArgumentTypeError(msg)
            if any(val < -90. or val > 90. for val in tmp):
                msg = '"lats" latitude floats must be in range [-90., 90.]'
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return LatArgsAction

def lons_action():
    class LonArgsAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            try:
                tmp = map(float, values)
            except:
                msg = '"lons" arguments must be coercible to floats'
                raise argparse.ArgumentTypeError(msg)
            if any(val < -180. or val > 180. for val in tmp):
                msg = '"lons" longitude floats must be in range [-180., 180.]'
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return LonArgsAction

def datestr_to_dt(datestr):
    return dt.date(*map(int, [datestr[:4], datestr[4:6], datestr[6:8]]))

def main(args):
    if args.lats or args.lons:
        assert len(args.lats) == len(args.lons), "number of latitude args must equal number of longitude args"
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='PROG')
    parser.add_argument('-d', '--date', nargs='+', action=date_action(), type=str,
                        help='a date OR a start and end date (format: YYYYMMDD)')
    parser.add_argument('-z', '--zips', nargs='+', action=zips_action(), type=str,
                        help='one or more zip codes in the US')
    parser.add_argument('--lats', nargs='+', action=lats_action(), type=float,
                        help='one or more latitudes')
    parser.add_argument('--lons', nargs='+', action=lons_action(), type=float,
                        help='one or more longitudes (in same order as latitudes if multiple)')
    parser.add_argument('-v', '--val', nargs='+',
                        help='keys for weather values to return (see weather_keys dict in noaahist.py)')
    parser.add_argument('-n', '--no-stn-data', action='store_true', 
                        help='exclude station metadata for returned values')
    parser.add_argument('-p', '--ret-py-objs', action='store_true', 
                        help='return tuples instead of a string of pipe-delimeted time-series lines')
    parser.add_argument('-o', '--out-file', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='direct output to a file')
    args = parser.parse_args()
    print "VIEWING ARGS"
    print args
    main(args)
