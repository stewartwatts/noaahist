OVERVIEW: API to get historical data from the NOAA weather station nearest a zip code or latitude and longitude coordinates. 

DEPENDS: *NIX curl, pyzipcode (if you pass zip codes instead of longitude and latitude)

DATA SOURCE: ftp://ftp.ncdc.noaa.gov/pub/data/noaa/

FIELDS: 

USAGE: For simple calls, pass command line arguments:

-d, --date: a single date or a start date and end date in YYYYMMDD format
-z, --zips: one or more zip codes
--lats: latitudes
--lons: longitudes (length and order must agree with --lats args)
-f, --flds: keys for the data you would like (see NOAA fields below)
--hrly: return hourly data instead of daily (note: hourly data is not always complete)
-p: automatically detect number of available processors, N, and run requests in parallel on N-1 processors
--nprocs: explicitly set how many processors to use (ignored if -p is passed)
-i, --infile: to run many requests at once, can pass in a formatted text file with one request specified per line 
-o, --outfile: redirect comma-separated output lines (defaults to stdout)

Example:
$ ./noaahist.py -d 19710321 19710323 -z 89109 --lats 34.05 34.893 --lons -118.25 -117.019 -f MINT MAXT -p --outfile fllv.txt

For more complicated calls or for requests with different date ranges or many different locations, pass a pipe-delimited, formatted text file that specifies one request per line.  If the frequency is not 'h' or 'H', observation frequency will default to daily.  

location name | date OR start_date,end_date | zip or latitude,longitude | comma-separated weather fields | daily ('d') OR hourly ('h')

Example:
$ echo 'LasVegas|19710321,19710323|89109|MAXT,MINT|d' > noaa_requests.txt
$ echo 'WoodyCreek_CO|20050220|39.270833,-106.886111|MAXT,MINT|h' >> noaa_requests.txt
$ ./noaahist.py --infile noaa_requests.txt

Note: location name is just for convenient grouping of results when responses are dumped together in .csv format.  It does not affect what data is pulled from NOAA.