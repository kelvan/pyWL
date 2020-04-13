import sqlite3
from operator import attrgetter, itemgetter

import config

# XXX
conn = sqlite3.connect(config.database)
c = conn.cursor()


class Base(dict):
    __tablename__ = None

    def __init__(self):
        if self.__tablename__ is None:
            raise Exception("Don't use Base class directly")

        self['id'] = None
        self.connection = conn
        self.cursor = c

        if not self.table_exists:
            self.create_table()

    def create_table(self):
        c.execute(self.__table_definition__)

    @classmethod
    def get(cls, cid):
        """ fetch element by id, returns as dict-like object
        """
        r = c.execute(
            """SELECT * FROM %s WHERE id = ?""" % cls.__tablename__,
            (cid,))
        f = r.fetchone()
        if f:
            return cls(*f)

    @classmethod
    def all(cls):
        r = c.execute("""SELECT * FROM %s""" % cls.__tablename__).fetchall()
        if r:
            return map(lambda x: cls(*x), r)
        else:
            return []

    def delete(self, commit=True):
        self.cursor.execute(
            """DELETE FROM %s WHERE id=?""" % self.__tablename__,
            (self['id'],))
        if commit:
            self.connection.commit()

    @property
    def table_exists(self):
        r = c.execute("""SELECT COUNT(*)
                           FROM sqlite_master
                           WHERE type=? AND
                                 name=?""",
                      ('table', self.__tablename__))
        return r.fetchone()[0] > 0

    def save(self, commit=True):
        raise NotImplementedError()


class LocationMixIn:
    @classmethod
    def get_nearby(cls, lat, lon, distance=0.005):
        # TODO distance in meters
        d = distance
        s = c.execute(
            """SELECT * FROM %s WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?""" % cls.__tablename__,
            (lat - d, lat + d, lon - d, lon + d)).fetchall()
        if s:
            return map(lambda x: cls(*x), s)
        else:
            return []


def guess_line(lines):
    """ Extract best match from lines with same name
    e.g. tram and bus with name '1' extracts the tram

    :return: single Line
    """
    name = lines[0]['name']
    line_type = None

    static_mapping = {'VRT': 'ptTramVRT', 'WLB': 'ptTramWLB', 'O': 'ptTram', 'D': 'ptTram'}

    if name in static_mapping:
        line_type = static_mapping[name]
    elif name.endswith('A') or name.endswith('B'):
        line_type = 'ptBusCity'
    elif name.startswith('N'):
        line_type = 'ptBusNight'
    elif name.startswith('U'):
        line_type = 'ptMetro'
    elif name.startswith('S'):
        line_type = 'ptTrainS'
    elif name.isdigit():
        # no regional bus lines supported
        line_type = 'ptTram'

    for line in lines:
        if line['type'] == line_type:
            return line


class NameMixIn:

    @classmethod
    def get_by_name(cls, name):
        results = cls.search_by_name(name, exact=True)

        if len(results) == 1:
            return results[0]
        if len(results) > 1:
            return guess_line(results)

    @classmethod
    def search_by_name(cls, name, exact=False, weight=None):
        if exact:
            s = c.execute(
                """SELECT * FROM %s WHERE name == ? COLLATE NOCASE""" % cls.__tablename__,
                (name,)).fetchall()
        else:
            s = c.execute(
                """SELECT * FROM %s WHERE name LIKE ? COLLATE NOCASE""" % cls.__tablename__,
                ('%' + name + '%',)).fetchall()

        if s:
            result = [cls(*x) for x in s]
            if weight:
                if weight in result[0]:
                    result = sorted(result, key=itemgetter(weight), reverse=True)
                elif hasattr(result[0], weight):
                    result = sorted(result, key=attrgetter(weight), reverse=True)

            return result
        else:
            return []


class Commune(Base, NameMixIn):
    __tablename__ = 'communes'
    __table_definition__ = """CREATE TABLE communes (id INTEGER NOT NULL,
                                                     name VARCHAR(50),
                                                     PRIMARY KEY (id))"""

    def __init__(self, cid, name):
        super().__init__()
        self['id'] = cid
        self['name'] = name

    def save(self, commit=True):
        if self['id'] is None:
            c.execute(
                """INSERT INTO %s VALUES (?)""" % self.__tablename__,
                (self['name'],))
        else:
            c.execute(
                """INSERT OR REPLACE INTO %s VALUES (?, ?)""" % self.__tablename__,
                (self['id'], self['name']))

        if commit:
            conn.commit()

    # TODO
    def get_stations(self):
        if self['id'] is None:
            return False


class Line(Base, NameMixIn):
    __tablename__ = 'lines'
    __table_definition__ = """CREATE TABLE lines (id INTEGER NOT NULL,
                                                  name VARCHAR(10),
                                                  realtime BOOLEAN,
                                                  type VARCHAR(10),
                                                  last_changed DATETIME,
                                                  colour INT(12),
                                                  logo BLOB,
                                                  PRIMARY KEY (id),
                                                  CHECK (realtime IN (0, 1)))"""

    def __init__(self, lid, name, realtime, typ, last_changed, colour=None, logo=None):
        super().__init__()
        self['id'] = lid
        self['name'] = name
        self['realtime'] = realtime
        self['type'] = typ
        self['last_changed'] = last_changed
        self['colour'] = colour
        self['logo'] = logo

    def save(self, commit=True):
        if self['id'] is None:
            c.execute("""INSERT INTO %s VALUES (?,?,?,?,?,?)""" % self.__tablename__,
                      (self['name'], self['realtime'], self['typ'], self['last_changed'],
                       self['colour'], self['logo']))
        else:
            c.execute("""INSERT OR REPLACE INTO %s VALUES (?,?,?,?,?,?,?)""" % self.__tablename__,
                      (self['id'], self['name'], self['realtime'], self['type'],
                       self['last_changed'], self['colour'], self['logo']))

        if commit:
            conn.commit()

    @property
    def hex_colour(self):
        if self['colour']:
            return str(hex(self['colour'])).replace('0x', '#')

    def get_stations(self):
        if self['id'] is None:
            return False

        sql = '''SELECT {0}.*,direction FROM {0}
                 JOIN {1} ON {0}.id={1}.station_id
                 JOIN {2} ON {2}.stop_id={1}.id
                 WHERE {2}.line_id=?
                 ORDER BY direction, "order"
              '''

        r = c.execute(sql.format(Station.__tablename__, Stop.__tablename__, LineStop.__tablename__),
                      (self['id'],)).fetchall()
        if r:
            h = [Station(*x[:-1]) for x in filter(lambda x: x[-1] == 'H', r)]
            r = [Station(*x[:-1]) for x in filter(lambda x: x[-1] == 'R', r)]

            return (h, r)
        else:
            return ([], [])


class Station(Base, LocationMixIn, NameMixIn):
    __tablename__ = 'stations'
    __table_definition__ = """CREATE TABLE stations (id INTEGER NOT NULL,
                                                     name VARCHAR(50) NOT NULL,
                                                     type VARCHAR(10),
                                                     commune_id INTEGER NOT NULL,
                                                     lat FLOAT,
                                                     lon FLOAT,
                                                     last_changed DATETIME,
                                                     PRIMARY KEY (id),
                                                     FOREIGN KEY(commune_id) REFERENCES communes (id)
                                                    )"""

    def __init__(self, sid, name, typ, cid, lat, lon, last_changed):
        super().__init__()
        self['id'] = sid
        self['name'] = name
        self['type'] = typ
        self['commune_id'] = cid
        self['lat'] = lat
        self['lon'] = lon
        self['last_changed'] = last_changed

    @classmethod
    def get_by_commune(cls, cid):
        r = c.execute(
            """SELECT id, name, commune_id, lat, lon, last_changed FROM %s WHERE commune_id=?""" % cls.__tablename__,
            (cid,))
        a = r.fetchall()
        if a:
            return map(lambda x: cls(*x), a)
        else:
            return []

    def save(self, commit=True):
        if self['id'] is None:
            c.execute(
                """INSERT INTO %s VALUES (?,?,?,?,?,?)""" % self.__tablename__,
                (self['name'], self['type'], self['commune_id'],
                self['lat'], self['lon'],
                self['last_changed']))
        else:
            c.execute(
                """INSERT OR REPLACE INTO %s VALUES (?,?,?,?,?,?,?)""" % self.__tablename__,
                (self['id'], self['name'], self['type'],
                self['commune_id'], self['lat'], self['lon'],
                self['last_changed']))

        if commit:
            conn.commit()

    def get_stops(self):
        r = c.execute(
            """SELECT * FROM %s WHERE station_id=?""" % Stop.__tablename__,
            (self['id'],)).fetchall()
        if r:
            return [Stop(*x) for x in r]
        else:
            return []

    def get_lines(self):
        sql = """SELECT DISTINCT lines.*
                    FROM stations
                    JOIN lines_stations
                        ON lines_stations.station_id=stations.id
                    JOIN lines
                        ON lines.id=line_id
                    WHERE stations.id=?
                    ORDER BY lines.name"""
        r = self.cursor.execute(sql, (self['id'],))
        f = r.fetchall()
        return [Line(*l) for l in f]

    @property
    def line_count(self):
        return len(self.get_lines())


class LineStop(Base):
    __tablename__ = 'lines_stops'
    __table_definition__ = '''CREATE TABLE lines_stops (line_id INTEGER NOT NULL,
                                                        stop_id INTEGER NOT NULL,
                                                        direction VARCHAR(1),
                                                        "order" INTEGER,
                                                        PRIMARY KEY (line_id, stop_id))
                           '''

    def __init__(self, lid, sid, direction, order):
        super().__init__()
        self['line_id'] = lid
        self['stop_id'] = sid
        self['direction'] = direction
        self['order'] = order

    @classmethod
    def get(cls, lid, sid):
        r = c.execute(
            """SELECT * FROM %s WHERE line_id=? AND stop_id=?""" % cls.__tablename__,
            (lid, sid))
        f = r.fetchone()
        if f:
            return cls(*f)

    def delete(self, commit=True):
        self.cursor.execute(
            """DELETE FROM %s WHERE line_id=? AND stop_id=?""" % self.__tablename__,
            (self['line_id'], self['station_id']))
        if commit:
            self.connection.commit()

    def save(self, commit=True):
        c.execute(
            """INSERT OR REPLACE INTO %s VALUES (?,?,?,?)""" % self.__tablename__,
            (self['line_id'], self['stop_id'], self['direction'],
            self['order']))

        if commit:
            conn.commit()


class LineStation(Base):
    __tablename__ = 'lines_stations'
    __table_definition__ = '''CREATE TABLE lines_stations (line_id INTEGER NOT NULL,
                                                           station_id INTEGER NOT NULL,
                                                           PRIMARY KEY (line_id, station_id))
                           '''

    def __init__(self, lid, sid):
        super().__init__()
        self['line_id'] = lid
        self['station_id'] = sid

    @classmethod
    def get(cls, lid, sid):
        r = c.execute(
            """SELECT * FROM %s WHERE line_id=? AND station_id=?""" % cls.__tablename__,
            (lid, sid))
        f = r.fetchone()
        if f:
            return cls(*f)

    def delete(self, commit=True):
        self.cursor.execute(
            """DELETE FROM %s WHERE line_id=? AND station_id=?""" % self.__tablename__,
            (self['line_id'], self['station_id']))
        if commit:
            self.connection.commit()

    def save(self, commit=True):
        c.execute(
            """INSERT OR REPLACE INTO %s VALUES (?,?)""" % self.__tablename__,
            (self['line_id'], self['station_id']))

        if commit:
            conn.commit()


class Stop(Base, LocationMixIn):
    __tablename__ = 'stops'
    __table_definition__ = """CREATE TABLE stops (id INTEGER NOT NULL,
                                                  name VARCHAR(50) NOT NULL,
                                                  lat FLOAT, lon FLOAT,
                                                  station_id INTEGER NOT NULL,
                                                  section VARCHAR(20),
                                                  last_changed DATETIME,
                                                  PRIMARY KEY (id),
                                                  FOREIGN KEY(station_id) REFERENCES stations (id))
                           """

    def __init__(self, sid, name, lat, lon, station, section, last_changed):
        super().__init__()
        self['id'] = sid
        self['name'] = name
        self['lat'] = lat
        self['lon'] = lon
        if isinstance(station, int):
            self['station_id'] = station
            self['station'] = Station.get(station)
        elif isinstance(station, Station):
            self['station_id'] = station['id']
            self['station'] = station
        else:
            raise TypeError('station has type {}, has to be Station or int'.format(type(station)))
        self['section'] = section
        self['last_changed'] = last_changed

    def save(self, commit=True):
        if self['id'] is None:
            c.execute(
                """INSERT INTO %s VALUES (?,?,?,?,?,?)""" % self.__tablename__,
                (self['name'], self['lat'], self['lon'], self['station']['id'],
                self['section'], self['last_changed']))
        else:
            c.execute(
                """INSERT OR REPLACE INTO %s VALUES (?,?,?,?,?,?,?)""" % self.__tablename__,
                (self['id'], self['name'], self['lat'], self['lon'],
                self['station']['id'], self['section'], self['last_changed']))
        if commit:
            conn.commit()

    def connect_line(self, lid, direction, order, commit=True):
        line_stop = LineStop(lid, self['id'], direction, order)
        line_stop.save(commit)
        line_station = LineStation(lid, self['station_id'])
        line_station.save(commit)

    def disconnect_line(self, lid, commit=True):
        LineStop.get(lid, self['id']).delete(commit)
        LineStation.get(lid, self['station_id']).delete(commit)

    def get_station(self):
        return self['station']

    def get_lines(self):
        sql = """SELECT DISTINCT lines.*
                    FROM stops
                    JOIN lines_stops
                        ON lines_stops.stop_id=stops.id
                    JOIN lines
                        ON lines.id=line_id
                    WHERE stops.id=?
                    ORDER BY lines.name"""
        r = self.cursor.execute(sql, (self['id'],))
        f = r.fetchall()
        return [Line(*l) for l in f]
