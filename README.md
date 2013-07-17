#### OVERVIEW 
Python API to get historical data from the NOAA weather station nearest a zip code or latitude and longitude coordinates. 

#### DEPENDENCIES 
*NIX curl, gunzip, Java Runtime Environment / compiler, pyzipcode (if you pass zip codes instead of latitude,longitude)

#### DATA SOURCE 
ftp://ftp.ncdc.noaa.gov/pub/data/noaa/  

#### FIELDS
* 'DIR':   WIND DIRECTION IN COMPASS DEGREES, 990 = VARIABLE, REPORTED AS '***' WHEN AIR IS CALM (SPD WILL THEN BE 000)
* 'SPD':   WIND SPEED IN MILES PER HOUR 
* 'GUS':   GUST IN MILES PER HOUR 
* 'CLG':   CLOUD CEILING--LOWEST OPAQUE LAYER WITH 5/8 OR GREATER COVERAGE, IN HUNDREDS OF FEET, 722 = UNLIMITED 
* 'SKC':   SKY COVER -- CLR-CLEAR, SCT-SCATTERED-1/8 TO 4/8, BKN-BROKEN-5/8 TO 7/8, OVC-OVERCAST, OBS-OBSCURED, POB-PARTIAL OBSCURATION
* 'L':     MEDIUM CLOUD TYPE
* 'H':     HIGH CLOUD TYPE
* 'VSB':   VISIBILITY IN STATUTE MILES TO NEAREST TENTH
* 'MW1':   MANUALLY OBSERVED PRESENT WEATHER (see ftp://ftp.ncdc.noaa.gov/pub/data/noaa/ish-abbreviated.txt for detail)
* 'MW2': 
* 'MW3': 
* 'MW4': 
* 'AW1':   AUTO-OBSERVED PRESENT WEATHER (see ftp://ftp.ncdc.noaa.gov/pub/data/noaa/ish-abbreviated.txt for detail)
* 'AW2': 
* 'AW3': 
* 'AW4': 
* 'W':     PAST WEATHER INDICATOR
* 'TEMP':  TEMPERATURE IN FARENHEIT
* 'DEWP':  DEWPOINT IN FARENHEIT
* 'SLP':   SEA LEVEL PRESSURE IN MILLIBARS TO NEAREST TENTH
* 'ALT':   ALTIMETER SETTING IN INCHES TO NEAREST HUNDREDTH
* 'STP':   STATION PRESSURE IN MILLIBARS TO NEAREST TENTH
* 'MAX':   MAXIMUM TEMPERATURE IN FAHRENHEIT (TIME PERIOD VARIES)
* 'MIN':   MINIMUM TEMPERATURE IN FAHRENHEIT (TIME PERIOD VARIES)
* 'PCP01': 1-HOUR LIQUID PRECIP REPORT IN INCHES AND HUNDREDTHS -- THAT IS, THE PRECIP FOR THE PRECEDING 1 HOUR PERIOD
* 'PCP06': 6-HOUR LIQUID PRECIP REPORT IN INCHES AND HUNDREDTHS -- THAT IS, THE PRECIP FOR THE PRECEDING 6 HOUR PERIOD
* 'PCP24': 24-HOUR LIQUID PRECIP REPORT IN INCHES AND HUNDREDTHS -- THAT IS, THE PRECIP FOR THE PRECEDING 24 HOUR PERIOD
* 'PCPXX': LIQUID PRECIP REPORT IN INCHES AND HUNDREDTHS, FOR A PERIOD OTHER THAN 1, 6, OR 24 HOURS (USUALLY FOR 12 HOUR PERIOD FOR STATIONS OUTSIDE THE U.S., AND FOR 3 HOUR PERIOD FOR THE U.S.) T = TRACE FOR ANY PRECIP FIELD
* 'SD':    SNOW DEPTH IN INCHES
* NOTE: *'s IN OUTPUT INDICATES FIELD NOT REPORTED

#### REFORMATTING 
NOAA's raw files have some fixed fields and a richer set of fields with variable and complicated formatting.  NOAA provides a reformatting routine which has been modified (static/ishJava.java) to work in a pipeline.  This modified code is ready-compiled (static/ishJava.class), so this API depends on a Java Runtime Environment, but not necessarily a Java compiler.

#### USAGE
Before using this tool, you must compile static/ishJava.java to create static/ishJava.class.  Your ishJava.class compiled file must be in static/ for noaahist.py to find it, so 'cd' into static/ before compiling ishJava.java.

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
* --hrly: return hourly data instead of daily (note: hourly data is not always complete)
* -p: automatically detect number of available processors, N, and run requests in parallel on N-1 processors
* --nprocs: explicitly set how many processors to use (ignored if -p is passed)
* -i, --infile: to run many requests at once, can pass in a formatted text file with one request specified per line 
* -o, --outfile: redirect comma-separated output lines (defaults to stdout)

Example:
```
$ ./noaahist.py -d 19710321 19710323 -z 89109 --lats 34.05 34.893 --lons -118.25 -117.019 -f SPD TEMP -p --outfile fllv.txt
```

For more complicated calls or for requests with different date ranges or many different locations, pass a pipe-delimited, formatted text file that specifies one request per line.  If the frequency is not 'h' or 'H', observation frequency will default to daily.  

location name | date OR start_date,end_date | zip or latitude,longitude | comma-separated weather fields | daily ('d') OR hourly ('h')

Example:
```
$ echo 'LasVegas|19710321,19710323|89109|SKC,TEMP|d' > reqs.txt
$ echo 'WoodyCreek_CO|20050220|39.270833,-106.886111|SPD,SD|h' >> reqs.txt
$ ./noaahist.py --infile reqs.txt
```

Note: location name is just for convenient grouping of results when responses are dumped together in .csv format.  It does not affect what data is pulled from NOAA.