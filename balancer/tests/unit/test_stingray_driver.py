# vim: tabstop=4 shiftwidth=4 softtabstop=4

import unittest
import requests

from balancer.drivers.riverbed_stingray.StingrayDriver import StingrayDriver

conf = []

device = {
    'name': 'Stingray1',
    'type': 'stingray',
    'ip': '10.62.166.27',
    'user': 'admin',
    'password': 'jobbie',
    'extra': {}
}

device_with_port = {
    'name': 'Stingray1',
    'type': 'stingray',
    'ip': '10.62.166.27',
    'port': '9070',
    'user': 'admin',
    'password': 'jobbie',
    'extra': {}
}

server_farm = {
    'name':'node1',
    'deployed':'no',
    'extra':{}
}

real_server = {}

virtual_ip = {}




class StingrayDriverTestCase(unittest.TestCase):
    def setUp(self):
        self.driver = StingrayDriver(conf, device)
        return

    def tearDown(self):
        return

    def test_REST_connection(self):
        #Exception will be thrown if status code not acceptable
        response = self.driver.send_request('', 'GET')

    def test_REST_connection_port(self):
        ported_driver = StingrayDriver(conf, device_with_port)
        response = ported_driver.send_request('', 'GET')


