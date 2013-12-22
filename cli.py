#!/usr/bin/env python3

import argparse
import sys

from database import Station
from realtime import Departures

rbl = []
for st in Station.search_by_name(sys.argv[1]):
    rbl += list(st.get_stops())

print(Departures.get_by_stops(rbl))
