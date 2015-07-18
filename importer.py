#!/usr/bin/python

import re
import csv
from datetime import datetime

from pyWL.database import *

line_file = 'wienerlinien-ogd-linien.csv'
stop_file = 'wienerlinien-ogd-steige.csv'
station_file = 'wienerlinien-ogd-haltestellen.csv'

dt_format = "%Y-%m-%d %H:%M:%S"

# importer use first matching colour
COLOURS = (
    (re.compile('S.+'), 0x2d1d8f), ('U1', 0xe4121d), ('U2', 0xa349a4),
    ('U3', 0xff7f27), ('U4', 0x22b14c), ('U5', 0x00bfbf), ('U6', 0xa76745)
)



def get_last_changed(info):
    if info['STAND']:
        return datetime.strptime(info['STAND'], dt_format)
    return None


def import_commune(cid, name, commit=False):
    c = Commune(cid, name)
    c.save(commit)


def import_stop(info, commit=False):
    rbl = info['RBL_NUMMER']
    last_changed = get_last_changed(info)
    s = Stop(info['RBL_NUMMER'], info['STEIG'], info['STEIG_WGS84_LAT'],
             info['STEIG_WGS84_LON'], int(info['FK_HALTESTELLEN_ID']),
             info['BEREICH'], last_changed)
    if rbl.isdigit():
        s.save(commit)
    elif rbl:
        print('Skip RBL: {}'.format(rbl))


def import_stop_line(info, commit=False):
    rbl = info['RBL_NUMMER']
    s = Stop.get(rbl)
    if s:
        s.connect_line(info['FK_LINIEN_ID'], info['RICHTUNG'],
                       info['REIHENFOLGE'], commit)
    elif rbl:
        print('Stop not found:', rbl)


def import_station(info, commit=False):
    last_changed = get_last_changed(info)
    import_commune(info['GEMEINDE_ID'], info['GEMEINDE'])
    s = Station((info['HALTESTELLEN_ID']), info['NAME'], info['TYP'],
                info['GEMEINDE_ID'], float(info['WGS84_LAT'] or '0'),
                float(info['WGS84_LON'] or '0'), last_changed)
    s.save(commit)


def import_line(info, commit=False):
    last_changed = get_last_changed(info)

    name = info['BEZEICHNUNG']
    line_colour = None
    for colour_check, colour in COLOURS:
        if hasattr(colour_check, 'match') and colour_check.match(name) or\
              colour_check == name:
            line_colour = colour
            break

    l = Line(info['LINIEN_ID'], info['BEZEICHNUNG'], info['ECHTZEIT'] == '1',
             info['VERKEHRSMITTEL'], last_changed, line_colour)
    l.save(commit)


with open(line_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for line in reader:
        import_line(line, commit=False)

conn.commit()

with open(station_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for station in reader:
        import_station(station, commit=False)

conn.commit()

with open(stop_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for stop in reader:
        import_stop(stop, commit=False)

    conn.commit()

with open(stop_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for stop in reader:
        import_stop_line(stop, commit=False)

conn.commit()
