import sqlite3

conn = sqlite3.connect("stations.db")
c = conn.cursor()


class Base(dict):
    __tablename__ = None

    def __init__(self):
        if self.__tablename__ is None:
            raise Exception("Don't use Base class directly")
        if not self.table_exists:
            self.create_table()

    @property
    def table_exists(self):
        r = c.execute("""SELECT COUNT(*) 
                           FROM sqlite_master
                           WHERE type=? AND 
                                 name=?""",
                      ('table', self.__tablename__))
        return r.fetchone()[0] > 0

    def save(self):
        pass

    def create_table(self):
        pass

    def fetch(self):
        pass

class Commune(Base):
    __tablename__ = 'communes'

    def create_table(self):
        c.execute("""CREATE TABLE communes (
                       id INTEGER NOT NULL, 
                       name VARCHAR(50), 
                       PRIMARY KEY (id))""")

#    id = Column(Integer, primary_key=True)
#    name = Column(String(50))
#    stations = relationship("Station")


class Line(Base):
    __tablename__ = 'lines'

#    id = Column(Integer, primary_key=True)
#    name = Column(String(10))
#    realtime = Column(Boolean)
#    type = Column(String(10))
#    last_changed = Column(DateTime)


class Station(Base):
    __tablename__ = 'stations'

#    id = Column(Integer, primary_key=True)
#    name = Column(String(50), nullable=False)
#    type = Column(String(10))
#    commune_id = Column(Integer, ForeignKey('communes.id'), nullable=False)
#    lat = Column(Float)
#    lon = Column(Float)
#    last_changed = Column(DateTime)

#    stops = relationship("Stop")


class LineStop(Base):
    __tablename__ = 'lines_stops'

#    line_id = Column(Integer, primary_key=True)
#    stop_id = Column(Integer, primary_key=True)
#    direction = Column(String(1))
#    order = Column(Integer)


class Stop(Base):
    __tablename__ = 'stops'

#    id = Column(Integer, primary_key=True)
#    lat = Column(Float)
#    lon = Column(Float)
#    station_id = Column(Integer, ForeignKey('stations.id'), nullable=False)
#    station = relation(Station)
#    section = Column(String(20))
#    last_changed = Column(DateTime)

