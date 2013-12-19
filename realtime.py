import json
import requests
import logging
import operator
from datetime import datetime

import config
from database import *

logger = logging.getLogger("realtime_api")

apiurl = "%s/monitor?sender=%s" % (config.baseurl, config.senderid)

disruption_choices = {'short': 'stoerungkurz', 'long': 'stoerunglang',
                      'elevator': 'aufzugsinfo'}
traf_option = "activateTrafficInfo"
position_option = "rbl"


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
            self.postitions = [positions]
        else:
            self.postitions = positions

        if isinstance(disruptions, str):
            disruptions = [disruptions]
        if not disruptions is None:
            for disruption in disruptions:
                if disruption in disruption_choices:
                    self.disruptions.append(disruption)
                else:
                    logger.error("invalid disruption type: %s", disruption)

    @classmethod
    def by_station(cls, station, disruptions=None):
        rbl = map(operator.itemgetter('id'), Station.get(station).get_stops())
        return cls(list(rbl), disruptions)

    def refresh(self):
        request_url = apiurl

        for position in self.postitions:
            request_url += "&%s=%d" % (position_option, position)

        for disruption in self.disruptions:
            request_url += "&%s=%s" % (traf_option,
                                       disruption_choices[disruption])

        logger.debug("processing %s", request_url)
        r = requests.get(request_url)

        if not r.status_code == 200:
            logger.error('unable to fetch data, statuscode: %d', r.status_code)

        j = json.loads(r.text)

        self.last_status = j['message']['value']
        if not self.last_status == 'OK':
            logger.error('error server status: %s', self.last_status)
        self.last_updated = datify(j['message']['serverTime'])

        for stop in j['data']['monitors']:
            prop = stop['locationStop']['properties']
            stopid = prop['attributes']['rbl']
            if not stopid in self:
                self[stopid] = {'name': prop['title'], 'type': prop['type']}
                self[stopid]['departures'] = []

            for line in stop['lines']:
                for dep in line['departures']['departure']:
                    deptime = dep['departureTime']
                    if 'timePlanned' in deptime:
                        deptime['timePlanned'] = datify(deptime['timePlanned'])
                    if 'timeReal' in deptime:
                        deptime['timeReal'] = datify(deptime['timeReal'])
                    if 'departures' in line:
                        del(line['departures'])
                    deptime['line'] = line
                    self[stopid]['departures'].append(dep['departureTime'])

        # just for testing
        return j
