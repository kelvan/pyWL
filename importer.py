from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from database import *
import stations

engine = create_engine('sqlite:///wl.db', echo=False)

metadata = Base.metadata
metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

dt_format = "%Y-%m-%d %H:%M:%S"

for line in stations.Lines().values():
    last_changed = datetime.strptime(line.last_changed, dt_format)
    l2 = session.query(Line).get(line.id)

    if l2:
        if l2.last_changed >= last_changed:
            continue
        l = l2
    else:
        l = Line()

    l.id = line.id
    l.name = line.name
    l.realtime = line.realtime
    l.type = line.type
    l.last_changed = datetime.strptime(line.last_changed, dt_format)
    session.add(l)

session.commit()
