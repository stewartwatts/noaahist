OVERVIEW: API to get historical NOAA weather data from the NOAA station nearest a zip code or latitude and longitude coordinates. 

DEPENDS: *NIX curl, pyzipcode (if you pass zip codes instead of longitude and latitude)

DATA: ftp://ftp.ncdc.noaa.gov/pub/data/noaa/     (OLD: NOAA Quality Controlled Local Climatological Data)

COVERAGE: July 1996 - present

FIELDS: 

SPEED: The NOAA files this script downloads are large even when compressed.  Each API call will take a long time, particularly for long date ranges.  It is recommended to pass all the locations needed for a given month in one call to avoid redownloading large files multiple times.  