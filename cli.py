#!/usr/bin/env python3

import argparse
import sys
from operator import itemgetter

from pyWL.realtime import Departures
from pyWL.database import Station, Line
from pyWL.textformat import *

parser = argparse.ArgumentParser(description='WienerLinien test commandline client')
parser.add_argument(metavar='station name', dest='name')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-s', '--search', action='store_true',
                   help='search station by name', dest='search')
group.add_argument('-d', '--departures', action='store_true',
                   help='show departures', dest='deps')
group.add_argument('-l', '--line', action='store_true',
                   help='show stations', dest='line')

args = parser.parse_args()

stations = Station.search_by_name(args.name, weight='line_count')

if args.search:
    for station in map(lambda x: x['name'], stations):
        print(station)

if args.line:
    name = args.name.upper()
    l = Line.get_by_name(name)

    if l is None:
        s = Line.search_by_name(name)
        print('Line not found')
        if s:
            print('Did you mean:')
            for line in s:
                print(line['name'])
        sys.exit(1)
    else:
        i = 1
        for direction in l.get_stations():
            print()
            print('-'*12)
            print(inred('Direction:'), i)
            print('-'*12)
            print()
            i += 1
            for station in direction:
                print(station['name'])

if args.deps:
    rbl = []
    for st in stations:
        rbl += list(st.get_stops())

    deps = Departures.get_by_stops(rbl)

    for station in sorted(deps.values(), key=itemgetter('name')):
        print()
        print('='*len(station['name']))
        print(ingreen(station['name']))
        print('='*len(station['name']))

        for departure in sorted(station['departures'], key=itemgetter('countdown')):
            dep_text = departure['line']['name'].ljust(6)
            dep_text += departure['line']['towards'].ljust(20)
            if departure['line']['barrierFree']:
                dep_text += inblue(str(departure['countdown']).rjust(4))
            else:
                dep_text += inred(str(departure['countdown']).rjust(4))

            print(dep_text)
