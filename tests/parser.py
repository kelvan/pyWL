#!/usr/bin/env python3

import sys
import unittest
from requests import Response
import json

sys.path.insert(0, '..')
import realtime
from textformat import *


def json_loads_stub(content):
    def stub():
        return json.loads(content)

    return stub

def requests_get_stub(json, status_code):
    def stub(url):
        response = Response()
        response._content = json
        response.url = url
        response.status_code = status_code
        response.json = json_loads_stub(json)
        return response

    return stub

class ParsingTestCase(unittest.TestCase):
    def setUp(self):
        with open('data/singlestation.json') as f:
            self.single_station_json = f.read()
        with open('data/multistation.json') as f:
            self.multi_station_json = f.read()

    def testParsingSingleStation(self):
        realtime.requests.get = requests_get_stub(self.single_station_json, 200)
        d = realtime.Departures(0)

        d.refresh()

        self.assertIn('Karlsplatz', d.keys(), inred('Stationname not found'))
        self.assertEqual(22, len(d.departures), inred('wrong departure count'))

    def testParsingMultipleStations(self):
        realtime.requests.get = requests_get_stub(self.multi_station_json, 200)
        d = realtime.Departures(0)
        d.refresh()

        self.assertTrue(False, inblue('TODO'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
