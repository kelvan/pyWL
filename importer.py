from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from database import *
import stations

engine = create_engine('sqlite:///wl.db', echo=True)

metadata = Base.metadata
metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

dt_format = "%Y-%m-%d %H:%M:%S"

for line in stations.Lines().values():
    l = Line()
    l.id = line.id
    l.name = line.name
    l.realtime = line.realtime
    l.type = line.type
    l.last_changed = datetime.strptime(line.last_changed, dt_format)
    session.add(l)

session.commit()
