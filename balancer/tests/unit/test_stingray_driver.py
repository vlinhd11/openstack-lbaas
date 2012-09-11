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
predictor = {}

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
    'deployed': '',
    'extra': {}
}

#Virtual IPs represented by virtual servers in models.py
vip = {
    'id': 'vip_1_id',
    'sf_id': 'server_farm_1_id',
    'name': 'vip_1',
    'address': '10.62.166.28',
    'mask': '',
    'port': '',
    'status': '',
    'deployed': '',
    'extra': {}
}

vip_2 = {
    'id': 'vip_2_id',
    'sf_id': 'server_farm_1_id',
    'name': 'vip_2',
    'address': '10.62.166.29',
    'mask': '',
    'port': '',
    'status': '',
    'deployed': '',
    'extra': {}
}

rserver = {
    'id': 'rserver_1_id',
    'sf_id': 'server_farm_1_id',
    'name': 'rserver_1',
    'type': '',
    'address': '10.62.166.28',
    'port': '8080',
    'status': '',
    'parent_id': '',
    'deployed': '',
    'extra': {}
}

rserver_weighted = {
    'id': 'rserver_1_id',
    'sf_id': 'server_farm_1_id',
    'name': 'rserver_1',
    'type': '',
    'address': '10.62.166.28',
    'port': '8080',
    'weight': '3',
    'status': '',
    'parent_id': '',
    'deployed': '',
    'extra': {}
}

probe_incompatible = {
    'id': 'incompatible_id',
    'sf_id': 'server_farm_1_id',
    'name': 'one',
    'type': 'ICMP',
    'extra': {
        'delay': '10',
        'attemptsBeforeDeactivation': '5',
        'timeout': '10'
    }
}

probe_connect = {
    'id': 'connect_id',
    'sf_id': 'server_farm_1_id',
    'name': 'two',
    'type': 'CONNECT',
    'extra': {
        'delay': '10',
        'attemptsBeforeDeactivation': '5',
        'timeout': '10'
    }
}

probe_http = {
    'id': 'http_id',
    'sf_id': 'server_farm_1_id',
    'name': 'three',
    'type': 'HTTP',
    'extra': {
        'delay': '10',
        'attemptsBeforeDeactivation': '5',
        'timeout': '10',
        'method':  'GET',
        'path': '/index.html',
        'expected': '200-204'
    }
}

probe_https = {
    'id': 'https_id',
    'sf_id': 'server_farm_1_id',
    'name': 'four',
    'type': 'HTTPS',
    'extra': {
        'delay': '10',
        'attemptsBeforeDeactivation': '5',
        'timeout': '10',
        'method':  'GET',
        'path': '/index.html',
        'expected': '200-204'
    }
}

sticky_cookie = {
    'id': 'cookie_id',
    'sf_id': 'server_farm_1_id',
    'name': 'cookie',
    'type': '',
    'extra': {
        'persistenceType': 'HTTP_COOKIE'
    }
}

logger = logging.getLogger(__name__)


class StingrayDriverTestCase(unittest.TestCase):

    driver = StingrayDriver(conf, device)

    def check_in_list(self, target, field_name, item_to_find):
        ''' Queries the target URL and field to check if the item is in
        that Stingray formatted list
        '''
        response = self.driver.send_request(target, 'GET')
        response_dict = self.driver.response_to_dict(response)

        if item_to_find in response_dict['properties'][field_name]:
            found = True
        else:
            found = False
        return found

    def check_not_in_list(self, target, field_name, item_to_find):
        return not(self.check_in_list(target,
                                        field_name, item_to_find))

    def check_field_is(self, target, field_name, field_value):
        '''Checks the value fo a field via a HTTP GET request
        '''
        response = self.driver.send_request(target, 'GET')
        response_dict = self.driver.response_to_dict(response)

        found = False

        if field_value == response_dict['properties'][field_name]:
            found = True

        return found

    def setUp(self):
        self.driver.create_server_farm(serverfarm, predictor)
        return

    def tearDown(self):
        self.driver.delete_server_farm(serverfarm)
        return

    def test_REST_connection(self):
        self.driver = StingrayDriver(conf, device)
        response = self.driver.send_request('', 'GET')

    def test_real_server_add_remove(self):
        self.driver.add_real_server_to_server_farm(serverfarm, rserver)
        self.driver.add_real_server_to_server_farm(serverfarm,
                                                        rserver_weighted)

        target = 'pools/' + serverfarm['id'] + '/'
        node = rserver['address'] + ':' + rserver['port']
        node_weighted = (rserver_weighted['address'] + ':' +
                                                    rserver_weighted['port'])

        #Check rserveris have both been added to node list
        self.assertTrue(self.check_in_list(target, 'nodes', node))
        self.assertTrue(self.check_in_list(target, 'nodes', node_weighted))

        self.driver.delete_real_server_from_server_farm(serverfarm,
                                                            rserver_weighted)

        #Check that first has been successfully deleted
        self.assertTrue(self.check_not_in_list(target, 'nodes',
                                                        node_weighted))

        self.driver.delete_real_server_from_server_farm(serverfarm, rserver)

        #Check that second has been successfully deleted
        self.assertTrue(self.check_not_in_list(target, 'nodes', node))

    def test_real_server_weights(self):
        self.driver.add_real_server_to_server_farm(serverfarm, rserver)
        self.driver.add_real_server_to_server_farm(serverfarm,
                                                        rserver_weighted)

        weighted_node = (rserver_weighted['address'] + ':'
                        + rserver_weighted['port'] + ':'
                        + rserver_weighted['weight'])

        non_weighted_node = (rserver['address'] + ':'
                            + rserver['port'] + ':1')

        target = 'pools/' + serverfarm['id'] + '/'

        #Check that weight field has been updated with correct values
        self.assertTrue(self.check_in_list(target, 'priority!values',
                                                            weighted_node))
        self.assertTrue(self.check_in_list(target, 'priority!values',
                                                        non_weighted_node))

        self.driver.delete_real_server_from_server_farm(serverfarm, rserver)
        self.driver.delete_real_server_from_server_farm(serverfarm,
                                                        rserver_weighted)
        #Check values do not linger after removed from node list
        self.assertTrue(self.check_not_in_list(target,
                                            'priority!values', weighted_node))
        self.assertTrue(self.check_not_in_list(target,
                                            'priority!values', non_weighted_node))


    def test_create_delete_virtual_ips(self):
        self.driver.create_virtual_ip(vip, serverfarm)
        self.driver.create_virtual_ip(vip_2, serverfarm)

        #Check traffic ip group created
        vip_target = 'flipper/' + serverfarm['id'] + '/'

        self.assertTrue(self.check_in_list(vip_target, 'ipaddresses',
                                                        vip['address']))
        self.assertTrue(self.check_in_list(vip_target, 'ipaddresses',
                                                        vip_2['address']))

        #Check linked to virtual server
        vserver_target = 'vservers/' + serverfarm['id'] + '/'
        response = self.driver.send_request(vserver_target, 'GET')
        response_dict = self.driver.response_to_dict(response)

        self.assertEqual('!' + vip['sf_id'],
                            response_dict['properties']['address'])

        self.driver.delete_virtual_ip(vip)

        #Check ip deleted but traffic group still linked
        self.assertTrue(self.check_not_in_list(vip_target,
                                'ipaddresses', vip['address']))
        self.assertTrue(self.check_field_is(vserver_target,
                                    'address', '!' + serverfarm['id']))

        self.driver.delete_virtual_ip(vip_2)

        #Check traffic group deleted and no longer linked
        try:
            self.driver.send_request(vip_target, 'GET')
            traffic_group_not_found = False
        except HTTPError as e:
            if e.response.status_code == 404:
                traffic_group_not_found = True

        self.assertTrue(traffic_group_not_found)
        self.assertTrue(self.check_field_is(vserver_target,
                                    'address', ''))

    def test_probe_incompatible(self):
        #Test request for unknown probe type ends in failure
        self.driver.create_probe(probe_incompatible)

        target = 'monitors/' + probe_incompatible['id'] + '/'

        try:
            self.driver.send_request(target, 'GET')
            failed_properly = False
        except HTTPError as e:
            if e.response.status_code == 404:
                failed_properly = True

        self.assertTrue(failed_properly)

    def test_probe_add_delete(self):
        self.driver.create_probe(probe_connect)
        self.driver.add_probe_to_server_farm(serverfarm, probe_connect)

        #Check probe created and added to pool
        probe_target = 'monitors/' + probe_connect['id'] + '/'
        try:
            self.driver.send_request(probe_target, 'GET')
            failed = False
        except HTTPError as e:
            if e.response.status_code == 404:
                failed = True
            else:
                raise

        self.assertFalse(failed)

        pool_target = 'pools/' + serverfarm['id'] + '/'

        self.assertTrue(self.check_in_list(pool_target, 'monitors',
                                                    probe_connect['id']))

        self.driver.delete_probe_from_server_farm(serverfarm, probe_connect)
        self.driver.delete_probe(probe_connect)

    def test_probe_type_http(self):
        self.driver.create_probe(probe_http)
        self.driver.add_probe_to_server_farm(serverfarm, probe_http)

        #TODO: Validate correct configuration here

        self.driver.delete_probe_from_server_farm(serverfarm, probe_http)
        self.driver.delete_probe(probe_http)

    def test_probe_type_https(self):
        self.driver.create_probe(probe_https)
        self.driver.add_probe_to_server_farm(serverfarm, probe_https)

        #TODO: Validate correct configuration here

        self.driver.delete_probe_from_server_farm(serverfarm, probe_https)
        self.driver.delete_probe(probe_https)

    def test_stickiness_add_delete(self):
        self.driver.create_stickiness(sticky_cookie)
        #TODO: Validate correct configuration here

        self.driver.delete_stickiness(sticky_cookie)

    def test_stickiness_type_cookie(self):
        self.driver.create_stickiness(sticky_cookie)
        #TODO: Validate correct configuration here

        self.driver.delete_stickiness(sticky_cookie)
