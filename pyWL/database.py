import sqlite3
from operator import attrgetter, itemgetter
#import geopy

from pyWL import config

conn = sqlite3.connect(config.database)
c = conn.cursor()


class Base(dict):
    __tablename__ = None

    def __init__(self):
        self['id'] = None
        self.connection = conn
        self.cursor = c

        if self.__tablename__ is None:
            raise Exception("Don't use Base class directly")
        if not self.table_exists:
            self.create_table()

    def create_table(self):
        c.execute(self.__table_definition__)

    @classmethod
    def get(cls, cid):
        """ fetch element by id, returns as dict-like object
        """
        r = c.execute("""SELECT * FROM %s WHERE id = ?""" % cls.__tablename__,
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
        self.cursor.execute("""DELETE FROM %s WHERE id=?""" % self.__tablename__,
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
        #TODO distance in meters
        d = distance
        s = c.execute("""SELECT * FROM %s WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?""" % cls.__tablename__,
                      (lat-d, lat+d, lon-d, lon+d)).fetchall()
        if s:
            return map(lambda x: cls(*x), s)
        else:
            return []


class NameMixIn:
    @classmethod
    def get_by_name(cls, name):
        r = c.execute("""SELECT * FROM %s WHERE name = ?""" % cls.__tablename__,
                                (name,))
        f = r.fetchone()
        if f:
            return cls(*f)

    @classmethod
    def search_by_name(cls, name, exact=False, weight=None):
        if exact:
            s = c.execute("""SELECT * FROM %s WHERE name == ? COLLATE NOCASE""" % cls.__tablename__,
                          (name,)).fetchall()
        else:
            s = c.execute("""SELECT * FROM %s WHERE name LIKE ? COLLATE NOCASE""" % cls.__tablename__,
                          ('%'+name+'%',)).fetchall()

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
            c.execute("""INSERT INTO %s VALUES (?)""" % self.__tablename__,
                      (self['name'],))
        else:
            c.execute("""INSERT OR REPLACE INTO %s VALUES (?, ?)""" % self.__tablename__,
                      (self['id'], self['name']))

        if commit:
            conn.commit()

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
                                                  PRIMARY KEY (id),
                                                  CHECK (realtime IN (0, 1)))"""

    def __init__(self, lid, name, realtime, typ, last_changed):
        super().__init__()
        self['id'] = lid
        self['name'] = name
        self['realtime'] = realtime
        self['type'] = typ
        self['last_changed'] = last_changed

    def save(self, commit=True):
        if self['id'] is None:
            c.execute("""INSERT INTO %s VALUES (?,?,?,?)""" % self.__tablename__,
                      (self['name'], self['realtime'], self['typ'], self['last_changed']))
        else:
            c.execute("""INSERT OR REPLACE INTO %s VALUES (?,?,?,?,?)""" % self.__tablename__,
                      (self['id'], self['name'], self['realtime'], self['type'], self['last_changed']))

        if commit:
            conn.commit()

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
            h = [Station(*x[:-1]) for x in filter(lambda x: x[-1]=='H', r)]
            r = [Station(*x[:-1]) for x in filter(lambda x: x[-1]=='R', r)]

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
        r = c.execute("""SELECT id, name, commune_id, lat, lon, last_changed FROM %s WHERE commune_id=?""" % cls.__tablename__,
                      (cid,))
        a = r.fetchall()
        if a:
            return map(lambda x: cls(*x), a)
        else:
            return []


    def save(self, commit=True):
        if self['id'] is None:
            c.execute("""INSERT INTO %s VALUES (?,?,?,?,?,?)""" % self.__tablename__,
                      (self['name'], self['type'], self['commune_id'],
                       self['lat'], self['lon'],
                       self['last_changed']))
        else:
            c.execute("""INSERT OR REPLACE INTO %s VALUES (?,?,?,?,?,?,?)""" % self.__tablename__,
                      (self['id'], self['name'], self['type'],
                       self['commune_id'], self['lat'], self['lon'],
                       self['last_changed']))

        if commit:
            conn.commit()

    def get_stops(self):
        r = c.execute("""SELECT * FROM %s WHERE station_id=?""" % Stop.__tablename__,
                      (self['id'],)).fetchall()
        if r:
            return [Stop(*x) for x in r]
        else:
            return []

    def get_lines(self):
        sql = """SELECT DISTINCT lines.*
                     FROM stations
                        JOIN stops
                            ON stations.id=station_id
                        JOIN lines_stops
                            ON lines_stops.stop_id=stops.id
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
        r = self.cursor.execute("""SELECT * FROM %s WHERE line_id=? AND station_id=?""" % cls.__tablename__,
                                (lid,sid))
        f = r.fetchone()
        if f:
            return cls(*f)

    def delete(self, commit=True):
        self.cursor.execute("""DELETE FROM %s WHERE line_id=? AND station_id=?""" % self.__tablename__,
                            (self['line_id'], self['station_id']))
        if commit:
            self.connection.commit()

    def save(self, commit=True):
        c.execute("""INSERT OR REPLACE INTO %s VALUES (?,?,?,?)""" % self.__tablename__,
                  (self['line_id'], self['stop_id'], self['direction'],
                   self['order']))

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
            self['station'] = Station.get(station)
        elif isinstance(station, Station):
            self['station'] = station
        else:
            raise TypeError('station has type {}, has to be Station or int'.format(type(station)))
        self['section'] = section
        self['last_changed'] = last_changed

    def save(self, commit=True):
        if self['id'] is None:
            c.execute("""INSERT INTO %s VALUES (?,?,?,?,?,?)""" % self.__tablename__,
                      (self['name'], self['lat'], self['lon'], self['station']['id'],
                       self['section'], self['last_changed']))
        else:
            c.execute("""INSERT OR REPLACE INTO %s VALUES (?,?,?,?,?,?,?)""" % self.__tablename__,
                      (self['id'], self['name'], self['lat'], self['lon'],
                       self['station']['id'], self['section'], self['last_changed']))
        if commit:
            conn.commit()

    def connect_line(self, lid, direction, order, commit=True):
        ls = LineStop(lid, self['id'], direction, order)
        ls.save(commit)

    def disconnect_line(self, lid, commit=True):
        LineStop.get(lid).delete(commit)

    def get_station(self):
        return Station(self['station_id'])