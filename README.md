##### OVERVIEW 
Python API to get historical data from the NOAA weather station nearest a zip code or latitude and longitude coordinates. 

##### DEPENDENCIES 
curl, gunzip, Java Runtime Environment / compiler, pyzipcode (if you pass zip codes instead of latitude,longitude)

##### DATA SOURCE 
ftp://ftp.ncdc.noaa.gov/pub/data/noaa/  

##### FIELDS
* 'DIR':   wind direction in compass degrees, 990 = variable, reported as '***' when air is calm (spd will then be 000)
* 'SPD':   wind speed in miles per hour 
* 'GUS':   gust in miles per hour 
* 'CLG':   cloud ceiling--lowest opaque layer with 5/8 or greater coverage, in hundreds of feet, 722 = unlimited 
* 'SKC':   sky cover -- clr-clear, sct-scattered-1/8 to 4/8, bkn-broken-5/8 to 7/8, ovc-overcast, obs-obscured, pob-partial obscuration
* 'L':     medium cloud type
* 'H':     high cloud type
* 'VSB':   visibility in statute miles to nearest tenth
* 'MW1':   manually observed present weather (see ftp://ftp.ncdc.noaa.gov/pub/data/noaa/ish-abbreviated.txt for detail)
* 'MW2': 
* 'MW3': 
* 'MW4': 
* 'AW1':   auto-observed present weather (see ftp://ftp.ncdc.noaa.gov/pub/data/noaa/ish-abbreviated.txt for detail)
* 'AW2': 
* 'AW3': 
* 'AW4': 
* 'W':     past weather indicator
* 'TEMP':  temperature in Farenheit
* 'DEWP':  dewpoint in Farenheit
* 'SLP':   sea level pressure in millibars to nearest tenth
* 'ALT':   altimeter setting in inches to nearest hundredth
* 'STP':   station pressure in millibars to nearest tenth
* 'MAX':   maximum temperature in Fahrenheit (time period varies)
* 'MIN':   minimum temperature in Fahrenheit (time period varies)
* 'PCP01': 1-hour liquid precip report in inches and hundredths -- that is, the precip for the preceding 1 hour period
* 'PCP06': 6-hour liquid precip report in inches and hundredths -- that is, the precip for the preceding 6 hour period
* 'PCP24': 24-hour liquid precip report in inches and hundredths -- that is, the precip for the preceding 24 hour period
* 'PCPXX': liquid precip report in inches and hundredths, for a period other than 1, 6, or 24 hours (usually for 12 hour period for stations outside the u.s., and for 3 hour period for the u.s.) t = trace for any precip field
* 'SD':    snow depth in inches

##### REFORMATTING 
NOAA's raw files have some fixed fields and a richer set of fields with complicated, variable formatting.  NOAA provides a reformatting routine which has been modified (static/ishJava.java) to work in a UNIX pipeline within noaahist.py.

##### USAGE
Before using this tool, you must compile static/ishJava.java.  The Java binary file you create, ishJava.class, must be in the 'static/' directory for noaahist.py to find it, so 'cd' into static/ first.

```
$ cd static
$ javac ishJava.java
```

For simple calls, pass command line arguments:

* -d, --date: a single date or a start date and end date in YYYYMMDD format
* -z, --zips: one or more zip codes
* --lats: latitudes
* --lons: longitudes (length and order must agree with --lats args)
* -f, --flds: keys for the data you would like (see NOAA fields below)
* -p: automatically detect number of available processors, N, and run requests in parallel on N-1 processors
* --nprocs: explicitly set how many processors to use (ignored if -p is passed)
* -i, --infile: to run many requests at once, pass in a formatted text file with one request specified per line 
* -o, --outfile: redirect comma-separated output lines (defaults to stdout)
* -m, --metadata: feeback on which stations data was pulled from; if outfile is specified, written to outfilename_metadata.txt, else printed to STDOUT

Example:
```
$ ./noaahist.py -d 19710321 19710323 -z 89109 --lats 34.05 34.893 --lons -118.25 -117.019 -f SPD TEMP -p --outfile fllv.csv -m
```

This call will create fllv.csv with the requested NOAA weather data, as well as fllv_metadata.txt with information about the stations data was pulled from.

For more complicated calls or for requests with different date ranges or many different locations, pass a pipe-delimited, formatted text file that specifies one request per line. 

location name | date OR start_date,end_date | zip or latitude,longitude | comma-separated weather fields

Example:
```
$ echo 'LasVegas|19710321,19710323|89109|SKC,TEMP' > reqs.txt
$ echo 'WoodyCreek|20050220|39.270833,-106.886111|SPD,SD' >> reqs.txt
$ ./noaahist.py --infile reqs.txt -p -m
```

This example *does* use a zipcode, so it will fail if the pyzipcode module is not available.  Substitute a latitude and longitude for "89109" to work around that dependency. The location names, 'LasVegas' and 'WoodyCreek', are just for convenient grouping of the returned csv-formatted data.  They do not affect what data is pulled from NOAA.  There is currently no way to set a location name for calls that don't use the --infile option.

##### OTHER TOOLS
In many cases, NOAA's weather data coverage is sparse, and noaahist.py may not find data for a weather category near a location.  To dig further interactively, explore_stations.py contains functions that list the active stations closest to a location in a given year.

```python
>>> from explore_stations import *
>>> stns_with_fld("TEMP", 38.9, -77.0, 2013)
```

To pull data from a given station and date range, call data_from_station.py from the command line.  All the command line args are required.

* -n, --queryname: for convenient grouping of returned data
* -i, --stn_id: the USAF ID of the station from which to pull data
* -f, --flds: one or more field names
* -s, --startdate: date in YYYYMMDD format
* -e, --enddate: date in YYYYMMDD format

```
$ ./data_from_station.py -n DC_weather -i 724050-13743 -f TEMP SPD -s 20131107 -e 20131110
```