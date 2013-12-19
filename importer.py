#!/usr/bin/python

import csv
from datetime import datetime

import stations
from database import *

line_file = 'wienerlinien-ogd-linien.csv'
point_file = 'wienerlinien-ogd-steige.csv'
station_file = 'wienerlinien-ogd-haltestellen.csv'

dt_format = "%Y-%m-%d %H:%M:%S"


def import_commune(cid, name, commit=False):
    c = Commune(cid, name)
    c.save(commit)


def import_point(info):
    pass


def import_station(info, commit=False):
    last_changed = datetime.strptime(info['STAND'], dt_format)
    import_commune(info['GEMEINDE_ID'], info['GEMEINDE'])
    s = Station((info['\ufeff"HALTESTELLEN_ID"']), info['NAME'], info['TYP'],
                info['GEMEINDE_ID'], float(info['WGS84_LAT']),
                float(info['WGS84_LON']), last_changed)
    s.save(commit)


def import_line(info, commit=False):
    last_changed = datetime.strptime(info['STAND'], dt_format)
    l = Line(info['LINIEN_ID'],info['BEZEICHNUNG'], info['ECHTZEIT']=='1',
             info['VERKEHRSMITTEL'], last_changed)
    l.save(commit)


with open(line_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for line in reader:
        import_line(line, commit=False)

conn.commit()

with open(station_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for station in reader:
        import_station(station)

conn.commit()

#with open(point_file, 'r') as f:
#    reader = csv.DictReader(f, delimiter=';')
#    for point in reader:
#        import_point(point)
