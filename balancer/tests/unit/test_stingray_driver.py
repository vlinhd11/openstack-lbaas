# vim: tabstop=4 shiftwidth=4 softtabstop=4

import unittest
import requests
import logging

from balancer.drivers.riverbed_stingray.StingrayDriver import StingrayDriver
from requests.exceptions import HTTPError

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

probe_incompatible = {
    'id': 'incompatible_id',
    'name': 'one',
    'type': 'ICMP',
    'delay': '10',
    'attemptsBeforeDeactivation': '5',
    'timeout': '10'
}

probe_connect = {
    'id': 'connect_id',
    'name': 'two',
    'type': 'CONNECT',
    'delay': '10',
    'attemptsBeforeDeactivation': '5',
    'timeout': '10'
}

probe_http = {
    'id': 'http_id',
    'name': 'three',
    'type': 'HTTP',
    'delay': '10',
    'attemptsBeforeDeactivation': '5',
    'timeout': '10',
    'method':  'GET',
    'path': '/index.html',
    'expected': '200-204'
}

probe_https = {
    'id': 'https_id',
    'name': 'four',
    'type': 'HTTPS',
    'delay': '10',
    'attemptsBeforeDeactivation': '5',
    'timeout': '10',
    'method':  'GET',
    'path': '/index.html',
    'expected': '200-204'
}

logger = logging.getLogger(__name__)


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

    def test_real_server_add_remove(self):
        self.driver.add_real_server_to_server_farm(serverfarm, rserver)

        target = 'pools/' + serverfarm['id'] + '/'
        response = self.driver.send_request(target, 'GET')
        response_dict = self.driver.response_to_dict(response)

        node = rserver['address'] + ':' + rserver['port']
        logger.debug(node)

        if node in response_dict['properties']['nodes']:
            successful = True
        else:
            successful = False

        self.assertTrue(successful)
        self.driver.delete_real_server_from_server_farm(serverfarm, rserver)

    @unittest.skip("Feature not implemented")
    def test_real_server_weights(self):
        pass

    @unittest.skip("Known issue with deleting Virtual IPs")
    def test_create_delete_virtual_ips(self):
        self.driver.create_virtual_ip(vip, serverfarm)
        self.driver.create_virtual_ip(vip_2, serverfarm)

        #TODO: Validation in progress
        target = 'flipper/' + serverfarm['id'] + '/'
        response = self.driver.send_request(target, 'GET')
        response_dict = self.driver.response_to_dict(response)

        self.driver.delete_virtual_ip(vip)
        self.driver.delete_virtual_ip(vip_2)

    def test_probe_incompatible(self):
        #Test request for unknown probe type ends in failure
        failed_properly = False

        try:
            self.driver.create_probe(probe_incompatible)
        except HTTPError as e:
            if e.response.status_code == 400:
                failed_properly = True

        self.assertTrue(failed_properly)

    def test_probe_connect(self):
        self.driver.create_probe(probe_connect)
        self.driver.add_probe_to_server_farm(serverfarm, probe_connect)

        #TODO: Validate correct configuration here

        self.driver.delete_probe_from_server_farm(serverfarm, probe_connect)
        self.driver.delete_probe(probe_connect)

    def test_probe_http(self):
        self.driver.create_probe(probe_http)
        self.driver.add_probe_to_server_farm(serverfarm, probe_http)

        #TODO: Validate correct configuration here

        self.driver.delete_probe_from_server_farm(serverfarm, probe_http)
        self.driver.delete_probe(probe_http)

    def test_probe_https(self):
        self.driver.create_probe(probe_https)
        self.driver.add_probe_to_server_farm(serverfarm, probe_https)

        #TODO: Validate correct configuration here

        self.driver.delete_probe_from_server_farm(serverfarm, probe_https)
        self.driver.delete_probe(probe_https)
