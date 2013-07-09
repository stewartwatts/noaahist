#!/usr/bin/env python  

import sys
import urllib2
import datetime as dt
import argparse
from subprocess import Popen, PIPE
from math import radians, cos, sin, asin, sqrt

class WeatherDataRequest(object):
    def __init__(self, dates, lat, lon, flds, freq):
        self.dates = {date: None for date in dates}
        self.lat = lat
        self.lon = lon
        self.flds = flds
        self.freq = freq
        self.get_stns_by_date()

    def get_stns_by_date(self, stn_months):
        pass

class WeatherDataResponse(object):
    def __init__(self, req_list):
        self.req_list = req_list
        self.fields = set(map(+, []))

NOAA_fields = {
    'STN':   [0, 6],         # Station number (WMO/DATSAV3 number)
    'WBAN':  [7, 12],        # WBAN number
    'YEAR':  [14, 18],       # year
    'MODA':  [18, 22],       # month and day
    'TEMP':  [24, 30],       # mean temperature in degrees F. Missing: 9999.9
    'DEWP':  [35, 41],       # Mean dew point
    'SLP':   [46, 52],       # Mean sea level pressure, millibars
    'STP':   [57, 63],       # Mean station pressure
    'VISIB': [68, 73],       # Mean visibility in miles. Missing = 999.9
    'WDSP':  [78, 83],       # Mean wind speed in knots. Missing = 999.9
    'MXSPD': [88, 93],       # Max sustained wind speed in knots.
    'GUST':  [85, 100],      # Max wind gust in knots.
    'MAX':   [102, 108],     # Max temp in F
    'MIN':   [110, 116],     # Min temp in F
    'PRCP':  [118, 123],     # Total precipitation in inches
    'SNDP':  [125, 130],     # Snow depth in inches
    'FRSHTT': [132, 138],    # Codes, 1=yes, 0=no:
                             # Fog ('F' - 1st digit).
                             # Rain or Drizzle ('R' - 2nd digit).
                             # Snow or Ice Pellets ('S' - 3rd digit).
                             # Hail ('H' - 4th digit).
                             # Thunder ('T' - 5th digit).
                             # Tornado or Funnel Cloud ('T' - 6th digit).
}

NOAA_fields = {
    '':'',
    '':'',
    '':'',
    '':'',
    '':'',
    '':'',
    '':'',
    '':'',    
}

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

def wkey_action(weather_keys):
    class WkeyArgsAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if any(val not in weather_keys for val in values):
                msg = '"lons" longitude floats must be in range [-180., 180.]'
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return WkeyArgsAction

def datestr_to_dt(datestr):
    return dt.date(*map(int, [datestr[:4], datestr[4:6], datestr[6:8]]))

def haversine(lon1, lat1, lon2, lat2):
    """
    author: Michael Dunn
    link: http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points

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

def coords_from_zip(zipcode):
    pass

def parse_infile_line(line):
    [loc, dates, flds] = line.strip().split("|")
    try:
        [lat, lon] = loc.split(',')
    except ValueError:
        lat, lon = coords_from_zip(loc)
    try:
        [sd, ed] = map(datestr_to_dt, dates.split(','))
    except ValueError:
        sd = ed = datestr_to_dt(dates)
    flds = flds.split(',')
    return [sd, ed, lat, lon] + map(lambda x: NOAA_fields[x], flds)


def main(args, update_stations=True):
    if update_stations:
        stns_url = 'ftp://ftp.ncdc.noaa.gov/pub/data/inventories/ISH-HISTORY.TXT'
        stns_path = 'static/ISH-HISTORY.TXT'
        if not os.path.exists(stns_path):
            print "Downloading NOAA stations list to %s ..." % stns_path
            with open(stns_path, "w") as f:
                p1 = Popen(["curl", stns_url], stdout=PIPE)
                # US stations only
                p2 = Popen(["grep", "US US"], stdin=p1.stdout, stdout=PIPE)
                # kill lines with no lat/long or no WBAN code
                p3 = Popen(["grep", "-ve", "99999"], stdin=p2.stdout, stdout=PIPE)
                f.write(p3.communicate()[0])
    
    # get longitude and latitude of all requested locations
    lons, lats = [], []
    if args.lats or args.lons:
        assert len(args.lats) == len(args.lons), "number of latitude args must equal number of longitude args"
        lats += args.lats
        lons += args.lons

    if args.zips:
        from pyzipcode import ZipCodeDatabase
        zcdb = ZipCodeDatabase()
        for _zip in args.zips:
            zc = zcdb[int(_zip)]
            lats.append(zc.latitude)
            lons.append(zc.longitude)

    # quality controlled local climatological data
    qcd_url = 'http://cdo.ncdc.noaa.gov/qclcd_ascii/'

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
    parser.add_argument('-f', '--flds', nargs='+',
                        help='weather value keys for desired data (see weather_keys dict in noaahist.py)')
    parser.add_argument('--hrly', action='store_true',
                        help='return data with hourly frequency instead of daily')
    parser.add_argument('-n', '--no-stn-data', action='store_true', 
                        help='exclude station metadata for returned values')
    parser.add_argument('-i', '--infile', nargs'?', type=argparse.FileType('r'),
                        help='pipe-delimited file with fmt: zip OR lat,lon | date OR startdate,enddate | field1,field2,...')
    parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='direct output to a file')
    args = parser.parse_args()
    #print "VIEWING ARGS"
    #print args

    main(args)


