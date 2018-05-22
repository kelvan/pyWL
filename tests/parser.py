import unittest
from requests import Response
import json
from pathlib import Path

from pywl import realtime


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
        data_dir = Path(__file__).parent / 'data'

        with open(data_dir / 'singlestation.json') as f:
            self.single_station_json = f.read()
        with open(data_dir / 'multistation.json') as f:
            self.multi_station_json = f.read()

    def testParsingSingleStation(self):
        realtime.requests.get = requests_get_stub(self.single_station_json, 200)
        d = realtime.Departures(0)

        d.refresh()

        self.assertEqual(1, len(d.keys()))
        self.assertIn('Karlsplatz', d.keys(), 'Stationname not found')
        self.assertEqual(22, len(d['Karlsplatz']['departures']), 'wrong departure count')

    def testParsingMultipleStations(self):
        realtime.requests.get = requests_get_stub(self.multi_station_json, 200)
        d = realtime.Departures(0)
        d.refresh()

        self.assertEqual(7, len(d.keys()))
        stations = [
            'Erzherzog-Karl-Straße', 'Karlsplatz', 'Ring/Volkstheater U', 'Karl-Meißl-Straße', 'Karl-Bekehrty-Str.',
            'Karl-Schwed-Gasse', 'Karl-Popper-Straße']
        self.assertAlmostEqual(stations, list(d.keys()))
        self.assertEqual(22, len(d['Karlsplatz']['departures']), 'wrong departure count')


if __name__ == '__main__':
    unittest.main(verbosity=2)
