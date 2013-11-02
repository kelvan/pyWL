import os
import csv

line_file = 'wienerlinien-ogd-linien.csv'
point_file = 'wienerlinien-ogd-steige.csv'
station_file = 'wienerlinien-ogd-haltestellen.csv'


class Station:
    def __init__(self, info):
        self.id = int(info['\ufeff"HALTESTELLEN_ID"'])
        self.name = info['NAME']
        self.lat = float(info['WGS84_LAT'])
        self.lon = float(info['WGS84_LON'])

    def __repr__(self):
        return "%s - %d" % (self.name, self.id)


class Line:
    def __init__(self, info):
        self.name = info['BEZEICHNUNG']
        self.realtime = True if info['ECHTZEIT'] == '1' else False
        self.id = int(info['LINIEN_ID'])
        self.type = info['VERKEHRSMITTEL']
        self._stations = None
        self._points = None

    def __repr__(self):
        return "%s - %d" % (self.name, self.id)

    @property
    def stations(self):
        if self._stations is None:
            self._stations = {'H': [], 'R': []}
            stations_h = set()
            stations_r = set()
            for point in self.points:
                stid = point['FK_HALTESTELLEN_ID']
                if point['RICHTUNG'] == 'H':
                    stations_h.add(stid)
                elif point['RICHTUNG'] == 'R':
                    stations_r.add(stid)

            with open(station_file, 'r') as f:
                reader = csv.DictReader(f, delimiter=';')
                for station in reader:
                    if station['\ufeff"HALTESTELLEN_ID"'] in stations_h:
                        self._stations['H'].append(Station(station))
                    if station['\ufeff"HALTESTELLEN_ID"'] in stations_r:
                        self._stations['R'].append(Station(station))

        return self._stations

    @property
    def points(self):
        if self._points is None:
            self._points = []
            with open(point_file, 'r') as f:
                reader = csv.DictReader(f, delimiter=';')
                for point in reader:
                    if int(point['FK_LINIEN_ID']) == self.id:
                        self._points.append(point)

        return self._points


class Lines(dict):
    def __init__(self):
        with open(line_file, 'r') as f:
            reader = csv.DictReader(f, delimiter=';')
            for line in reader:
                self[line['BEZEICHNUNG']] = Line(line)
