import os

proj_dir = os.path.dirname(__file__)

realtime_baseurl = 'https://www.wienerlinien.at/ogd_realtime'
routing_baseurl = 'https://www.wienerlinien.at/ogd_routing/XML_TRIP_REQUEST2'

datetimeformat = '%Y-%m-%dT%H:%M:%S.%f%z'

database = os.path.join(proj_dir, 'stations.db')
