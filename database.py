from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
from sqlalchemy.orm import relation, backref, relationship

Base = declarative_base()


class Commune(Base):
    __tablename__ = 'communes'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    stations = relationship("Station")


class Line(Base):
    __tablename__ = 'lines'

    id = Column(Integer, primary_key=True)
    name = Column(String(10))
    realtime = Column(Boolean)
    type = Column(String(10))
    last_changed = Column(DateTime)


class Station(Base):
    __tablename__ = 'stations'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    type = Column(String(10))
    commune_id = Column(Integer, ForeignKey('communes.id'), nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    last_changed = Column(DateTime)

    stops = relationship("Stop")


class LineStop(Base):
    __tablename__ = 'lines_stops'

    line_id = Column(Integer, primary_key=True)
    stop_id = Column(Integer, primary_key=True)
    direction = Column(String(1))
    order = Column(Integer)


class Stop(Base):
    __tablename__ = 'stops'

    id = Column(Integer, primary_key=True)
    lat = Column(Float)
    lon = Column(Float)
    station_id = Column(Integer, ForeignKey('stations.id'), nullable=False)
    station = relation(Station)
    section = Column(String(20))
    last_changed = Column(DateTime)

