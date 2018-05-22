import os

try:
    from key import senderid
except ImportError:
    from key import senderid_dev as senderid

proj_dir = os.path.dirname(__file__)

realtime_baseurl = 'http://www.wienerlinien.at/ogd_realtime'
routing_baseurl = 'http://www.wienerlinien.at/ogd_routing/XML_TRIP_REQUEST2'

datetimeformat = '%Y-%m-%dT%H:%M:%S.%f%z'

database = os.path.join(proj_dir, 'stations.db')
