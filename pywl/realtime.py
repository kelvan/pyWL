import requests
import logging
import operator
from datetime import datetime

import config
from db.database import Stop, Station, Line

logger = logging.getLogger(__name__)

apiurl = '{config.realtime_baseurl}/monitor'.format(config=config)

disruption_choices = {'short': 'stoerungkurz', 'long': 'stoerunglang',
                      'elevator': 'aufzugsinfo'}
traf_option = 'activateTrafficInfo'
position_option = 'rbl'


def datify(date_string):
    return datetime.strptime(date_string, config.datetimeformat)


class Departures(dict):

    def __init__(self, positions, disruptions=None):
        """ position: rbl as int or iterable
            disruptions: get disruption info ['short', 'long', 'elevator']
        """
        self.disruptions = []
        self.last_updated = None

        if isinstance(positions, int):
            self.positions = [positions]
        else:
            self.positions = positions

        for position in self.positions:
            if isinstance(position, Stop):
                position = position['id']

        if isinstance(disruptions, str):
            disruptions = [disruptions]
        if disruptions is not None:
            for disruption in disruptions:
                if disruption in disruption_choices:
                    self.disruptions.append(disruption_choices[disruption])
                else:
                    logger.error('invalid disruption type: %s', disruption)

    @classmethod
    def get_by_station(cls, station, disruptions=None):
        if isinstance(station, Station):
            station = station['id']
        rbl = map(operator.itemgetter('id'), Station.get(station).get_stops())
        c = cls(list(rbl), disruptions)
        c.refresh()
        return c

    @classmethod
    def get_by_stops(cls, stops, disruptions=None):
        if not stops:
            # FIXME
            return {}
        if isinstance(stops[0], Stop):
            stops = map(lambda st: st['id'], stops)
        c = cls(stops, disruptions)
        c.refresh()
        return c

    @classmethod
    def get_nearby(cls, lat, lon, distance=0.005):
        stops = Stop.get_nearby(lat, lon, distance)
        c = cls.get_by_station(stops)
        return c

    def refresh(self):
        # XXX too complex
        params = { position_option : self.positions }
        if len(self.disruptions) > 0:
            params[traf_option] = self.disruptions

        r = requests.get(apiurl, params=params )

        if not r.status_code == 200:
            logger.error('unable to fetch data, statuscode: %d', r.status_code)

        j = r.json()

        self.last_status = j['message']['value']
        if not self.last_status == 'OK':
            logger.error('error server status: %s', self.last_status)
        self.last_updated = datify(j['message']['serverTime'])

        for stop in j['data']['monitors']:
            prop = stop['locationStop']['properties']
            stopid = prop['attributes']['rbl']
            station = Stop.get(stopid)['station']
            station_name = station['name']
            if station_name not in self:
                self[station_name] = {'name': station_name,
                                      'type': station['type']}
                self[station_name]['departures'] = []

            for line in stop['lines']:
                for dep in line['departures']['departure']:
                    deptime = dep['departureTime']
                    if len(deptime) == 0:
                        # ignore empty crappy departures
                        continue

                    if 'timePlanned' in deptime:
                        deptime['timePlanned'] = datify(deptime['timePlanned'])
                    if 'timeReal' in deptime:
                        deptime['timeReal'] = datify(deptime['timeReal'])
                    if 'departures' in line:
                        del(line['departures'])
                    deptime['line'] = line
                    line_db = Line.get_by_name(line['name'])
                    if line_db:
                        line['colour'] = Line.get_by_name(line['name']).hex_colour
                    else:
                        # Line not found in DB
                        line['colour'] = None
                    self[station_name]['departures'].append(deptime)
