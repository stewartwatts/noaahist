#!/usr/bin/env python  

import os
import sys
import time
import datetime as dt
from copy import copy
from collections import defaultdict
from calendar import monthrange
import argparse
from multiprocessing import Pool, cpu_count
from subprocess import Popen, PIPE
from math import radians, cos, sin, asin, sqrt

## Logic for handling data requests and outputting a response

# multiprocessing PickleError workaround
def run_req(req):
    req.get_response()
    return req.response

class WeatherDataRequest(object):
    
    def __init__(self, start_date, end_date, lat, lon, flds, freq, stns, name=None):
        ndays = (end_date-start_date).days
        # self.dates --> map each date to --> map each fld to a station _id
        self.dates = {date: {} for date in [end_date - dt.timedelta(days=n) for n in range(ndays,-1,-1)]}
        self.lat = float(lat)
        self.lon = float(lon)
        self.flds = flds
        self.freq = freq
        self.name = name
        # NOAA field explanations: ftp://ftp.ncdc.noaa.gov/pub/data/noaa/ish-abbreviated.txt
        # Note: *'s IN FIELD INDICATES ELEMENT NOT REPORTED
        self.NOAA_fields = {
            'HR':    [21,23], # GREENWICH MEAN TIME HOUR
            'MN':    [23,25], # GREENWICH MEAN TIME MINUTES 
            'DIR':   [26,29], # WIND DIRECTION IN COMPASS DEGREES, 990 = VARIABLE, REPORTED AS '***' WHEN AIR IS CALM (SPD WILL THEN BE 000)
            'SPD':   [30,33], # WIND SPEED IN MILES PER HOUR 
            'GUS':   [34,37], # GUST IN MILES PER HOUR 
            'CLG':   [38,41], # CLOUD CEILING--LOWEST OPAQUE LAYER WITH 5/8 OR GREATER COVERAGE, IN HUNDREDS OF FEET, 722 = UNLIMITED 
            'SKC':   [42,45], # SKY COVER -- CLR-CLEAR, SCT-SCATTERED-1/8 TO 4/8, BKN-BROKEN-5/8 TO 7/8, OVC-OVERCAST, OBS-OBSCURED, POB-PARTIAL OBSCURATION
            'L':     [46,47], # LOW CLOUD TYPE
            'M':     [48,49], # MEDIUM CLOUD TYPE
            'H':     [50,51], # HIGH CLOUD TYPE
            'VSB':   [52,56], # VISIBILITY IN STATUTE MILES TO NEAREST TENTH
            'MW1':   [57,59], # MANUALLY OBSERVED PRESENT WEATHER (see table on website listed above for detail)
            'MW2':   [60,62], #
            'MW3':   [63,65], #
            'MW4':   [66,68], #
            'AW1':   [69,71], # AUTO-OBSERVED PRESENT WEATHER (see table on website listed above for detail)
            'AW2':   [72,74], #
            'AW3':   [75,77], #
            'AW4':   [78,80], #
            'W':     [81,82], # PAST WEATHER INDICATOR
            'TEMP':  [83,87], # TEMPERATURE IN FARENHEIT
            'DEWP':  [88,92], # DEWPOINT IN FARENHEIT
            'SLP':   [93,99], # SEA LEVEL PRESSURE IN MILLIBARS TO NEAREST TENTH
            'ALT':   [100,105], # ALTIMETER SETTING IN INCHES TO NEAREST HUNDREDTH
            'STP':   [106,112], # STATION PRESSURE IN MILLIBARS TO NEAREST TENTH
            'MAX':   [113,116], # MAXIMUM TEMPERATURE IN FAHRENHEIT (TIME PERIOD VARIES)
            'MIN':   [117,120], # MINIMUM TEMPERATURE IN FAHRENHEIT (TIME PERIOD VARIES)
            'PCP01': [121,126], # 1-HOUR LIQUID PRECIP REPORT IN INCHES AND HUNDREDTHS -- THAT IS, THE PRECIP FOR THE PRECEDING 1 HOUR PERIOD
            'PCP06': [127,132], # 6-HOUR LIQUID PRECIP REPORT IN INCHES AND HUNDREDTHS -- THAT IS, THE PRECIP FOR THE PRECEDING 6 HOUR PERIOD
            'PCP24': [133,138], # 24-HOUR LIQUID PRECIP REPORT IN INCHES AND HUNDREDTHS -- THAT IS, THE PRECIP FOR THE PRECEDING 24 HOUR PERIOD
            'PCPXX': [139,144], # LIQUID PRECIP REPORT IN INCHES AND HUNDREDTHS, FOR A PERIOD OTHER THAN 1, 6, OR 24 HOURS (USUALLY FOR 12 HOUR PERIOD FOR STATIONS OUTSIDE THE U.S., AND FOR 3 HOUR PERIOD FOR THE U.S.) T = TRACE FOR ANY PRECIP FIELD
            'SD':    [145,147], # SNOW DEPTH IN INCHES
            }
        self.stns = stns
        # station _id maps to -->  names / dists in miles from location
        self.stns_metadata = defaultdict(dict)

        # get mapping of date to closest station with data, by month
        yr, mo, cands, usafid, actual_ids = None, None, [], None, []
        for d in self.dates:
            if d.year != yr or d.month != mo:
                # some stations have gaps in data.  find stations that acutally exist for this year on NOAA's site
                if d.year != yr:
                    yr = d.year
                    print "\nretrieving list of stations for year: %s ... \n" % str(yr)
                    p1 = Popen(['curl','ftp://ftp.ncdc.noaa.gov/pub/data/noaa/%s/' % str(yr)], stdout=PIPE)
                    p2 = Popen(['grep','-o','[0-9]\{6\}-[0-9]\{5\}'], stdin=p1.stdout, stdout=PIPE)
                    actual_ids = p2.communicate()[0].split("\n")[:-1]
                mo = d.month
                cands = [_id for _id in self.stns if self.stns[_id]['sd'] < dt.date(yr,mo,1) and self.stns[_id]['ed'] > dt.date(yr,mo,monthrange(yr,mo)[1]) and _id in actual_ids]
                # get closest station with each field for this date
                # first sort candidate _ids by distance to the location
                dist_sorted_cands = sorted(cands, key=lambda cand: haversine(self.lat, self.lon, stns[cand]['lat'], stns[cand]['lon']))
                for fld in self.flds:
                    found = False
                    for cand in dist_sorted_cands: 
                        if fld in self.stns[cand]['flds']:
                            _id = cand
                            found = True
                            break
                    if found:

                        # store the station _id from which to pull data for this date * field combination
                        self.dates[d][fld] = _id
                        
                        if _id not in self.stns_metadata:
                            self.stns_metadata[_id]['dist'] = haversine(self.lat, self.lon, self.stns[_id]['lat'], self.stns[_id]['lon'])
                            self.stns_metadata[_id]['name'] = self.stns[_id]['name']
                    else:
                        print "\n\nWARNING: no data found for fld=< {0} > for date=< {1} >\n".format(fld, "{:%Y-%m-%d}".format(d))
                        keep_going = raw_input("Proceed anyhow? [y/n]\n")
                        if keep_going and keep_going[0].lower() == 'y':
                            pass
                        else:
                            sys.exit("noaahist.py process has been terminated.")

        # self.dates maps:   date -> fld -> stn _id
        # when pulling the data, getting a year of each station is the bottleneck
        # want to map:  stn -> date -> flds   for convenient data parsing.
        self.stn_date_flds = {}
        for date in self.dates:
            for field in self.dates[date]:
                if date not in self.stn_date_flds:
                    self.stn_date_flds[date] = []
                self.stn_date_flds[date].append(field)
    # __init__() ENDS
        
        
    def to_float(self, x):
        try:
            return float(x)
        except:
            return x if '*' not in x else ''
            
    def get_response(self):
        self.response = []
        yrs = set([d.year for d in self.dates])
        for yr in yrs:
            # all dates from this year
            yrdates = [d for d in self.dates if d.year == yr]
            # _id of all stations for all these dates
            stns = set([self.dates[yrd][fld] for fld in self.flds for yrd in yrdates])
            for stn in stns:
                # (date,field) pairs for this particular station
                stn_dateflds = [(yrd,fld) for fld in self.dates[yrd] for yrd in yrdates if self.dates[yrd][fld] == stn]

                # fetch, uncompress, reformat, and read data file from NOAA
                url = 'ftp://ftp.ncdc.noaa.gov/pub/data/noaa/{0}/{1}-{0}.gz'.format(yr, stn)
                print '\nretrieving url: %s ... \n' % url 
                p1 = Popen(["curl", url], stdout=PIPE)
                p2 = Popen(["gunzip"], stdin=p1.stdout, stdout=PIPE)
                p3 = Popen(['java', '-classpath', 'static', 'ishJava'], stdin=p2.stdout, stdout=PIPE)
                data = p3.communicate()[0].split("\n")[1:-1]
                print '\n'
                # filter out lines for dates/times outside the query period
                data = [x for x in data if datestr_to_dt(x[13:21]) in [stn_dateflds[i][0] for i in range(len(stn_dateflds))]]

                # df -> tuple of form (dt.date, field)
                for df in stn_dateflds:
                    # subset to individual day of data
                    day_data = [x for x in data if datestr_to_dt(x[13:21]) == df[0]]
                    # static data
                    line = dict(DATE=''.join(map(lambda x: str(x).zfill(2), [df[0].year, df[0].month, df[0].day])),
                                LAT=self.lat, LON=self.lon, USAFID_WBAN=stn, DIST=self.stns_metadata[stn]['dist'])
                    if self.name:
                        line['NAME'] = self.name
                    # hrly: separate line for each observation
                    if self.freq == 'h':
                        for obs in day_data:
                            hrline = copy(line)
                            for fld in ['HR','MN'] + self.flds:
                                try:
                                    hrline[fld] = self.to_float(obs[self.NOAA_fields[fld][0]:self.NOAA_fields[fld][1]])
                                except:
                                    hrline[fld] = None
                            self.response.append(hrline)
                    # daily: average observations or extract non-'***' data
                    else:
                        tmp = defaultdict(list)
                        for obs in day_data:
                            for fld in self.flds:
                                try:
                                    tmp[fld].append(self.to_float(obs[self.NOAA_fields[fld][0]:self.NOAA_fields[fld][1]]))
                                except:
                                    pass
                        for fld in tmp:
                            try:
                                line[fld] = sum(tmp[fld])/len(tmp[fld])
                            except:
                                line[fld] = None
                        self.response.append(line)
        self.response = sorted(self.response, key=lambda r: r['DATE'])
                    
    def run(self):
        self.get_response()
        return self.response
    
class AllWeatherResponses(object):
    def __init__(self, resp_dicts_list):
        # response: dict(req_lat:lat_tuple, req_lon:lon_tuple, stn_dist:dist_tuple, dates:date_tuple, fld1:fld1_tuple, ...)
        self.responses = resp_dicts_list
        self.all_flds = set([key for resp in self.responses for key in resp[0].keys()])
        # make order of fields sensible
        self.fld_names = [fld for fld in ['NAME','DATE','HR','MN','LAT','LON','USAFID_WBAN','DIST',  # metadata
                                          'TEMP','MIN','MAX','DEWP',                                 # temperature
                                          'DIR','SPD','GUS',                                         # wind
                                          'PCP01','PCPXX','PCP06','PCP24','SD',                      # precipitation
                                          'SKC','CLG','L','M','H',                                   # sky conditions
                                          'AW1','AW2','AW3','AW4','MW1','MW2','MW3','MW4',           # see table
                                          'SLP','STP',                                               # pressure
                                          'ALT','VSB', 'W',] if fld in self.all_flds]
        self.lines = [','.join(self.fld_names) + "\n"]
        
    def format_line(self, obs_dict):
        return ",".join(map(lambda x: str(round(x,2)) if type(x)==float else str(x), [obs_dict[fld] if obs_dict.get(fld) is not None else '' for fld in self.fld_names])) + "\n"
    
    def write(self, dest):
        for resp in self.responses:
            self.lines += map(self.format_line, resp)
        dest.writelines(self.lines)

## Command line argument validation
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

def flds_action():
    class FldsArgsAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            good_flds = ['AW3', 'AW4', 'W', 'MIN', 'HR', 'H', 'PCP24', 'CLG', 'M', 'L', 'AW1', 'AW2',
                         'GUS', 'STP', 'SKC', 'ALT', 'DIR', 'MW3', 'MW2', 'MW1', 'TEMP', 'MW4', 'MAX',
                         'MN', 'PCP06', 'DEWP', 'VSB', 'PCP01', 'PCPXX', 'SLP', 'SPD', 'SD']
            if any(val not in good_flds for val in values):
                wrong_keys = [val for val in values if val not in good_flds]
                msg = 'weather keys not recognized:', wrong_keys
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return FldsArgsAction

## General helper functions 
def datestr_to_dt(datestr):
    return dt.date(*map(int, [datestr[:4], datestr[4:6], datestr[6:8]]))

def haversine(lat1, lon1, lat2, lon2):
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

def req_from_infile_line(line, stns):
    try:
        [name, dates, loc, flds, freq] = map(lambda x: x.strip(), line.strip().split("|"))
    except:
        sys.exit("Error parsing infile\nExample infile:\n\nLasVegas|19710321,19710323|89109|WSPD,TEMP|d\nWoodyCreek_CO|20050220|39.270833,-106.886111|BARP,VISD|h\n\n")
    try:
        [sd, ed] = map(datestr_to_dt, dates.split(','))
    except ValueError:
        sd = ed = datestr_to_dt(dates)
    try:
        [lat, lon] = loc.split(',')
    except ValueError:
        lat, lon = coords_from_zip(loc)
    flds = flds.split(',')
    return WeatherDataRequest(sd, ed, lat, lon, flds, 'h' if freq[0].lower()=='h' else 'd', stns, name)

def parse_stn_line(line):
    usafid_wban = '-'.join([line[0:6], line[7:12]])
    name = line[13:43].strip()
    state = line[49:51].strip()
    lat = float(line[58:64])/1000. if line[58:64].strip() else None
    lon = float(line[65:72])/1000. if line[65:72].strip() else None
    sd = datestr_to_dt(line[83:91]) if line[83:91].strip() else None
    ed = datestr_to_dt(line[92:100]) if line[92:100].strip() else None
    flds = []
    if usafid_wban and lat and lon and sd and ed:
        return dict(usafid_wban=usafid_wban, name=name, state=state, lat=lat, lon=lon, sd=sd, ed=ed, flds=flds)
        
def stn_covg(path='static/ISH-HISTORY.TXT'):
    stns = {'-'.join([line[0:6], line[7:12]]): parse_stn_line(line) for line in map(lambda x: x.strip(), open(path).readlines())}
    return {key: stns[key] for key in stns if stns[key]}

def stn_flds(path='static/stn_flds.txt'):
    lines = map(lambda x: x.strip(), open(path).readlines())
    flds = lines[0].split(',')[1:]
    out = {}
    for line in lines[1:]:
        data = map(int, line.split(',')[1:])
        _id = line.split(',')[0]
        out[_id] = {}
        for i in range(len(flds)):
            out[_id][flds[i]] = data[i]
    return out

def coords_from_zip(zipcode):
    from pyzipcode import ZipCodeDatabase
    zcdb = ZipCodeDatabase()
    zc = zcdb[int(zipcode)]
    return zc.latitude, zc.longitude

def main(args, update_stations=False):
    """
    - optionally refresh NOAA stations coverage metadata
    - if locations and fields were passed on the command line, create WeatherDataRequests from them
    - if infile specifying requests was passed on the command line, create a WeatherDataRequest from each line
    - run all WeatherDataRequests and dump output of resulting AllWeatherResponses
    """
    reqs, resps = [], []
    stns_path = 'static/ISH-HISTORY.TXT'
    # update if arg is True, or file doesn't exist, or over 180 days stale
    if update_stations or not os.path.exists(stns_path) or (time.time() - os.path.getmtime(stns_path)) > 180 * 24 * 60 * 60:
        stns_url = 'ftp://ftp.ncdc.noaa.gov/pub/data/inventories/ISH-HISTORY.TXT'
        print "Downloading NOAA stations list to %s ..." % stns_path
        with open(stns_path, "w") as f:
            p1 = Popen(["curl", stns_url], stdout=PIPE)
            # US stations only
            p2 = Popen(["grep", "US US"], stdin=p1.stdout, stdout=PIPE)
            p1.stdout.close()
            # kill lines with no lat/long or no WBAN code
            p3 = Popen(["grep", "-ve", "NO DATA"], stdin=p2.stdout, stdout=PIPE)
            p2.stdout.close()
            f.write(p3.communicate()[0])

    # Process command line args
    # get longitude and latitude of all requested locations
    lons, lats = [], []
    if args.lats or args.lons:
        assert len(args.lats) == len(args.lons), "number of latitude args must equal number of longitude args"
        lats += args.lats
        lons += args.lons
    if args.zips:
        for _zip in args.zips:
            lat, lon = coords_from_zip(_zip)
            lats.append(lat)
            lons.append(lon)

    # start_date and end_date
    if args.date and len(args.date) == 2:
        sd, ed = map(datestr_to_dt, args.date)
    elif args.date:
        sd = ed = datestr_to_dt(args.date[0])

    # fields (args.flds from command line is a list, not a single comma-separated string)
    flds = args.flds 
        
    # frequency: daily or hourly
    freq = 'h' if args.hrly else 'd'

    # Get station coverage data and flds coverage
    stns = stn_covg()
    flds_by_stn = stn_flds()
    # annotate 'stns' with lists of fields each station contains
    for _id in flds_by_stn:
        for fld in flds_by_stn[_id]:
            if flds_by_stn[_id][fld]:
                stns[_id]['flds'].append(fld)
    
    # make WeatherDataRequests (no 'name' attribute will be specified for these objects)
    for i in range(len(lats)):
        reqs.append(WeatherDataRequest(sd, ed, lats[i], lons[i], flds, freq, stns))
    
    # Get requests from --infile arg
    if args.infile:
        for line in map(lambda x: x.strip(), args.infile.readlines()):
            reqs.append(req_from_infile_line(line, stns))

    # Make requests
    nprocs = None
    if args.parallel:
        nprocs = max(1, cpu_count() - 1)
    elif args.nprocs:
        nprocs = args.nprocs
    if nprocs:
        # make requests in parallel
        print "making requests in parallel on < %s > processors" % str(nprocs)
        pool = Pool(processes=nprocs)
        result = pool.map_async(run_req, reqs)
        resps = result.get()
    else:
        # make requests in series
        for req in reqs:
            resps.append(req.run())

    # Combine and write output
    all_resp = AllWeatherResponses(resps)
    all_resp.write(args.outfile)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='./noaahist.py')
    parser.add_argument('-d', '--date', nargs='+', action=date_action(), type=str,
                        help='a date OR a start and end date (format: YYYYMMDD)')
    parser.add_argument('-z', '--zips', nargs='+', action=zips_action(), type=str,
                        help='one or more zip codes in the US')
    parser.add_argument('--lats', nargs='+', action=lats_action(), type=float,
                        help='one or more latitudes')
    parser.add_argument('--lons', nargs='+', action=lons_action(), type=float,
                        help='one or more longitudes (in same order as latitudes if multiple)')
    parser.add_argument('-f', '--flds', nargs='+', action=flds_action(),
                        help='weather data field names (see README.md or NOAA_fields in WeatherDataRequest definition)')
    parser.add_argument('--hrly', action='store_true',
                        help='return data with hourly frequency instead of daily')
    parser.add_argument('-p', '--parallel', action='store_true',
                        help='detect # of processors N, run data requests on N-1 procs')
    parser.add_argument('--nprocs', nargs=1, type=int,
                        help='explicitly set how many processors to use for requesting data')
    parser.add_argument('-i', '--infile', nargs='?', type=argparse.FileType('r'),
                        help='pipe-delimited file with fmt: zip OR lat,lon | date OR startdate,enddate | field1,field2,...')
    parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='direct output to a file')
    args = parser.parse_args()
    
    main(args)
