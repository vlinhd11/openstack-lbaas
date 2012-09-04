# vim: tabstop=4 shiftwidth=4 softtabstop=4

import unittest
import requests

from balancer.drivers.riverbed_stingray.StingrayDriver import StingrayDriver

''' Missing fields in test values may be due to lack of implmementation
as opposed to lack of desired use.
'''


conf = []

device = {
    'id': 'Stingray1ID',
    'name': 'Stingray1',
    'type': 'stingray',
    'version': '',
    'ip': '10.62.166.27',
    'user': 'admin',
    'password': 'jobbie',
    'extra': {}
}

device_with_port = {
    'id': 'Stingray1ID',
    'name': 'Stingray1',
    'type': 'stingray',
    'version': '',
    'ip': '10.62.166.27',
    'port': '9070',
    'user': 'admin',
    'password': 'jobbie',
    'extra': {}
}

serverfarm = {
    'id': 'server_farm_1_id',
    'name': 'server_farm_1',
    'type': '',
    'deployed': '',
    'extra': {}
}

rserver = {
    'id': 'rserver_1_id',
    'name': 'rserver_1',
    'type': '',
    'address': '10.62.166.28',
    'port': '8080',
    'weight': '',
    'status': '',
    'parent_id': '',
    'deployed': '',
    'extra': {}
}

#Virtual IPs represented by virtual servers in models.py
vip = {
    'id': 'vip_1_id',
    'name': 'vip_1',
    'address': '10.62.166.28',
    'mask': '',
    'port': '',
    'status': '',
    'deployed': '',
    'extra': {}
}

vip_2 = {
    'id': 'vip_1_id',
    'name': 'vip_1',
    'address': '10.62.166.28',
    'mask': '',
    'port': '',
    'status': '',
    'deployed': '',
    'extra': {}
}

predictor = {}

probe_1 = {
    'name': 'one',
    'type': 'ICMP',
    'delay': '10',
    'attemptsBeforeDeactivation': '5',
    'timeout': '10'
}

probe_2 = {
    'name': 'two',
    'type': 'CONNECT',
    'delay': '10',
    'attemptsBeforeDeactivation': '5',
    'timeout': '10'
}

probe_3 = {
    'name': 'three',
    'type': 'HTTP',
    'delay': '10',
    'attemptsBeforeDeactivation': '5',
    'timeout': '10',
    'method':  'GET',
    'path': '/index.html',
    'expected': '200-204'
}


class StingrayDriverTestCase(unittest.TestCase):

    driver = StingrayDriver(conf, device)

    def setUp(self):
        self.driver.create_server_farm(serverfarm, predictor)
        return

    def tearDown(self):
        self.driver.delete_server_farm(serverfarm)
        return

    def test_REST_connection(self):
        self.driver = StingrayDriver(conf, device)
        response = self.driver.send_request('', 'GET')

    def test_REST_connection_port(self):
        ported_driver = StingrayDriver(conf, device_with_port)
        response = ported_driver.send_request('', 'GET')

    def test_add_real_server(self):
        self.driver.add_real_server_to_server_farm(serverfarm, rserver)

        #TODO:Validate correct configuration here

        self.driver.delete_real_server_from_server_farm(serverfarm, rserver)

    @unittest.skip("Known issue with deleting Virtual IPs")
    def test_create_delete_virtual_ips(self):
        self.driver.create_virtual_ip(vip, serverfarm)
        self.driver.create_virtual_ip(vip_2, serverfarm)

        #TODO:Validate correct configuration here

        self.driver.delete_virtual_ip(vip)
        self.driver.delete_virtual_ip(vip_2)

    def test_probe_1(self):
        #UNSUPPORTED DRIVER TEST THAT IT FAILS!!!
        self.driver.create_probe(probe_1)
        self.driver.add_probe_to_server_farm(serverfarm, probe_1)

        #TODO: Validate correct configuration here

        self.driver.delete_probe_from_server_farm(serverfarm, probe_1)
        self.driver.delete_probe(probe_1)

    def test_probe_2(self):
        self.driver.create_probe(probe_2)
        self.driver.add_probe_to_server_farm(serverfarm, probe_2)

        #TODO: Validate correct configuration here

        self.driver.delete_probe_from_server_farm(serverfarm, probe_2)
        self.driver.delete_probe(probe_2)

    def test_probe_3(self):
        self.driver.create_probe(probe_3)
        self.driver.add_probe_to_server_farm(serverfarm, probe_3)

        #TODO: Validate correct configuration here

        self.driver.delete_probe_from_server_farm(serverfarm, probe_3)
        self.driver.delete_probe(probe_3)
