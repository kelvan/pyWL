import os

try:
    from pyWL.key import senderid
except ImportError:
    from pyWL.key import senderid_dev as senderid

proj_dir = os.path.dirname(__file__)

realtime_baseurl = "http://www.wienerlinien.at/ogd_realtime"
routing_baseurl = "http://www.wienerlinien.at/ogd_routing/XML_TRIP_REQUEST2"
senderid= senderid

datetimeformat = '%Y-%m-%dT%H:%M:%S.%f%z'

database = os.path.join(proj_dir, 'stations.db')
