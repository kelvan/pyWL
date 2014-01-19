import os

from key import senderid_dev

proj_dir = os.path.dirname(__file__)

baseurl = "http://www.wienerlinien.at/ogd_realtime"
senderid= senderid_dev

datetimeformat = '%Y-%m-%dT%H:%M:%S.%f%z'

database = os.path.join(proj_dir, 'stations.db')
