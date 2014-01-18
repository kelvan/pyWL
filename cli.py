#!/usr/bin/env python3

import argparse
import sys

from database import Station
from realtime import Departures
import argparse

from textformat import *

parser = argparse.ArgumentParser(description='WienerLinien test commandline client')
parser.add_argument(metavar='station name', dest='name')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-s', '--search', action='store_true',
                    help='search station by name', dest='search')
group.add_argument('-d', '--departures', action='store_true',
                    help='show departures', dest='deps')

args = parser.parse_args()

stations = Station.search_by_name(args.name)

if args.search:
    for station in map(lambda x: x['name'], stations):
        print(station)

if args.deps:
    rbl = []
    for st in stations:
        rbl += list(st.get_stops())

    deps = Departures.get_by_stops(rbl)
    print(inred(args.name))
    for d in map(str, deps.values()):
        print(d)
        print(inblue('#'*79))
