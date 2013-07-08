import os
import sys
import urllib2
import datetime as dt
import argparse



if __name__ == "__main__":
    main()

parser = argparse.ArgumentParser(description='inputs:\n1. date || (start date && end date) in YYYYMMDD format\n2. zip code || (latitude and longitude)\n3.keys for weather values you wish to extract.')
parser.add_argument('integers', metavar='N', type=str, nargs='+',
                   help='an integer for the accumulator')
parser.add_argument('--sum', dest='accumulate', action='store_const',
                   const=sum, default=max,
                   help='sum the integers (default: find the max)')
parser.add_arguemtn('--')

args = parser.parse_args()
print(args.accumulate(args.integers))
