import csv
from datetime import datetime

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

import stations
from database import *

line_file = 'wienerlinien-ogd-linien.csv'
point_file = 'wienerlinien-ogd-steige.csv'
station_file = 'wienerlinien-ogd-haltestellen.csv'

engine = create_engine('sqlite:///wl.db', echo=False)

metadata = Base.metadata
metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
session.autocommit = True

dt_format = "%Y-%m-%d %H:%M:%S"


def import_commune(cid, name):
    c2 = session.query(Commune).get(cid)

    if c2:
        c = c2
    else:
        c = Commune()

    if c:
        c.id = cid
        c.name = name
        session.add(c)


def import_station(info):
    s = None
    s2 = session.query(Station).get(info['\ufeff"HALTESTELLEN_ID"'])
    last_changed = datetime.strptime(info['STAND'], dt_format)

    if s2: 
        if s2.last_changed < last_changed:
            s = s2
    else:
        s = Station()
        s.id = info['\ufeff"HALTESTELLEN_ID"']

    if s:
        s.name = info['NAME']
        s.lat = float(info['WGS84_LAT'])
        s.lon = float(info['WGS84_LON'])
        s.last_changed = last_changed
        s.commune_id = info['GEMEINDE_ID']
        import_commune(info['GEMEINDE_ID'], info['GEMEINDE'])
        session.add(s)


def import_line(info):
    l = None
    l2 = session.query(Line).get(int(line['LINIEN_ID']))
    last_changed = datetime.strptime(info['STAND'], dt_format)

    if l2:
        if l2.last_changed < last_changed:
            l = l2
    else:
        l = Line()

    if l:
        l.id = int(info['LINIEN_ID'])
        l.name = info['BEZEICHNUNG']
        l.realtime = True if info['ECHTZEIT'] == '1' else False
        l.type = info['VERKEHRSMITTEL']
        l.last_changed = last_changed
        session.add(l)


with open(line_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for line in reader:
        import_line(line)


with open(station_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for station in reader:
        import_station(station)


session.commit()
session.flush()
