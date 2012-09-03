import unittest
import mock
import tempfile
import datetime
import os
import shutil

from balancer.db import api as db_api
from balancer.db import session
from balancer import exception
from balancer.core import lb_status


device_fake1 = {'name': 'fake1',
                'type': 'FAKE',
                'version': '1',
                'ip': '10.0.0.10',
                'port': 1010,
                'user': 'user1',
                'password': 'secrete1',
                'extra': {'supports_vlan': False}}

device_fake2 = {'name': 'fake2',
                'type': 'FAKE',
                'version': '2',
                'ip': '10.0.0.20',
                'port': 2020,
                'user': 'user2',
                'password': 'secrete2',
                'extra': {'supports_vlan': True,
                          'vip_vlan': 10,
                          'requires_vip_ip': True}}


def get_fake_probe(sf_id):
    probe = {'sf_id': sf_id,
             'name': 'probe1',
             'type': 'ICMP',
             'deployed': 'True',
             'extra': {'delay': 10,
                       'attemptsDeforeDeactivation': 5,
                       'timeout': 10}}
    return probe


def get_fake_lb(device_id, tenant_id):
    lb = {'device_id': device_id,
          'name': 'lb1',
          'algorithm': 'ROUNDROBIN',
          'protocol': 'HTTP',
          'status': 'INSERVICE',
          'tenant_id': tenant_id,
          'created_at': datetime.datetime(2000, 01, 01, 12, 00, 00),
          'updated_at': datetime.datetime(2000, 01, 02, 12, 00, 00),
          'deployed': 'True',
          'extra': {}}
    return lb


def get_fake_sf(lb_id):
    sf = {'lb_id': lb_id,
          'name': 'serverfarm1',
          'type': 'UNKNOWN',
          'status': 'UNKNOWN',
          'deployed': 'True',
          'extra': {}}
    return sf


def get_fake_virtualserver(sf_id, lb_id):
    vip = {'sf_id': sf_id,
           'lb_id': lb_id,
           'name': 'vip1',
           'address': '10.0.0.30',
           'mask': '255.255.255.255',
           'port': '80',
           'status': 'UNKNOWN',
           'deployed': 'True',
           'extra': {'ipVersion': 'IPv4',
                     'VLAN': 200,
                     'ICMPreply': True}}
    return vip


def get_fake_server(sf_id, vm_id, address='100.1.1.25', parent_id=None):
    server = {'sf_id': sf_id,
              'name': 'server1',
              'type': 'HOST',
              'address': address,

              'port': '8080',
              'weight': 2,
              'status': 'INSERVICE',
              'parent_id': parent_id,
              'deployed': 'True',
              'vm_id': vm_id,
              'extra': {'minCon': 300000,
                        'maxCon': 400000,
                        'rateBandwidth': 12,
                        'rateConnection': 1000}}
    return server


def get_fake_sticky(sf_id):
    sticky = {'sf_id': sf_id,
              'name': 'sticky1',
              'type': 'HTTP-COOKIE',
              'deployed': 'True',
              'extra': {'cookieName': 'testHTTPCookie',
                        'enableInsert': True,
                        'browserExpire': True,
                        'offset': True,
                        'length': 10,
                        'secondaryName': 'cookie'}}
    return sticky


def get_fake_predictor(sf_id):
    predictor = {'sf_id': sf_id,
                 'type': 'ROUNDROBIN',
                 'deployed': 'True',
                 'extra': {}}
    return predictor


class TestExtra(unittest.TestCase):
    @mock.patch("balancer.db.api.pack_update")
    def test_pack_extra(self, mock):
        model = mock.MagicMock()
        values = {'name': 'fakename', 'type': 'faketype', 'other': 'fakeother'}
        db_api.pack_extra(model, values)
        self.assertTrue(mock.called)

    def test_unpack_extra(self):
        obj_ref = {'name': 'fakename',
                   'type': 'faketype',
                   'extra': {'other': 'fakeother'}}
        values = db_api.unpack_extra(obj_ref)
        expected = {'name': 'fakename',
                    'type': 'faketype',
                    'other': 'fakeother'}
        self.assertEqual(values, expected)

    def test_pack_update_0(self):
        """1 way"""
        obj_ref = {'name': 'fakename', 'type': 'faketype',
                   'other': 'fakeother',
                   'extra': {'dejkstra': 'dejkstra'}}
        values = {'name': 'fakename', 'type': 'faketype', 'other': 'fakeother',
                'extra': {}}
        db_api.pack_update(obj_ref, values)
        self.assertEqual(values, obj_ref)

    def test_pack_update_1(self):
        """else way"""
        values = {'name': 'fakename', 'type': 'faketype',
                  'other': 'fakeother',
                  'dejkstra': 'dejkstra'}
        obj_ref = {'name': 'fakename', 'type': 'faketype',
                   'other': 'fakeother',
                   'extra': {}}
        final = {'name': 'fakename', 'type': 'faketype', 'other': 'fakeother',
                'extra': {'dejkstra': 'dejkstra'}}
        db_api.pack_update(obj_ref, values)
        self.assertEqual(obj_ref, final)

    def test_pack_update_2(self):
        """else way"""
        values = {'name': 'fakename', 'type': 'faketype', 'other': 'fakeother',
                'dejkstra': 'dejkstra'}
        obj_ref = {'name': 'fakename', 'type': 'faketype',
                   'other': 'fakeother',
                   'extra': {'dejkstra': 'fool'}}
        final = {'name': 'fakename', 'type': 'faketype', 'other': 'fakeother',
                'extra': {'dejkstra': 'dejkstra'}}
        db_api.pack_update(obj_ref, values)
        self.assertEqual(obj_ref, final)


class TestDBAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.golden_filename = tempfile.mkstemp()
        conf = mock.Mock()
        conf.sql.connection = "sqlite:///%s" % (cls.golden_filename,)
        session.sync(conf)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.golden_filename)

    def setUp(self):
        self.maxDiff = None
        _, self.filename = tempfile.mkstemp()
        self.conf = mock.Mock()
        self.conf.sql.connection = "sqlite:///%s" % self.filename
        shutil.copyfile(self.golden_filename, self.filename)

    def tearDown(self):
        os.remove(self.filename)

    def test_device_create(self):
        device_ref = db_api.device_create(self.conf, device_fake1)
        device = dict(device_ref.iteritems())
        expected = device_fake1.copy()
        self.assertIsNotNone(device['id'])
        expected['id'] = device['id']
        self.assertEqual(device, expected)

    def test_device_update(self):
        device_ref = db_api.device_create(self.conf, device_fake1)
        self.assertIsNotNone(device_ref['id'])
        update = {'password': 'test',
                  'extra': {'supports_vlan': True,
                            'vip_vlan': 100,
                            'requires_vip_ip': True}}
        device_ref = db_api.device_update(self.conf, device_ref['id'], update)
        device = dict(device_ref.iteritems())
        expected = device_fake1.copy()
        expected.update(update)
        self.assertIsNotNone(device['id'])
        expected['id'] = device['id']
        self.assertEqual(device, expected)

    def test_device_get_all(self):
        device_ref1 = db_api.device_create(self.conf, device_fake1)
        device_ref2 = db_api.device_create(self.conf, device_fake2)
        devices = db_api.device_get_all(self.conf)
        self.assertEqual([dict(dev.iteritems()) for dev in devices],
                         [dict(dev.iteritems()) for dev in [device_ref1,
                                                            device_ref2]])

    def test_device_get(self):
        device_ref1 = db_api.device_create(self.conf, device_fake1)
        device_ref2 = db_api.device_get(self.conf, device_ref1['id'])
        self.assertEqual(dict(device_ref1.iteritems()),
                         dict(device_ref2.iteritems()))

    def test_device_get_several(self):
        device_ref1 = db_api.device_create(self.conf, device_fake1)
        device_ref2 = db_api.device_create(self.conf, device_fake2)
        device_ref3 = db_api.device_get(self.conf, device_ref1['id'])
        device_ref4 = db_api.device_get(self.conf, device_ref2['id'])
        self.assertEqual(dict(device_ref3.iteritems()),
                         dict(device_ref1.iteritems()))
        self.assertEqual(dict(device_ref4.iteritems()),
                         dict(device_ref2.iteritems()))

    def test_device_destroy(self):
        device_ref = db_api.device_create(self.conf, device_fake1)
        db_api.device_destroy(self.conf, device_ref['id'])
        with self.assertRaises(exception.DeviceNotFound) as cm:
            db_api.device_get(self.conf, device_ref['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'device_id': device_ref['id']})

    def test_loadbalancer_create(self):
        values = get_fake_lb('1', 'tenant1')
        lb_ref = db_api.loadbalancer_create(self.conf, values)
        lb = dict(lb_ref.iteritems())
        self.assertIsNotNone(lb['id'])
        values['id'] = lb['id']
        self.assertEqual(lb, values)

    def test_loadbalancer_update(self):
        values = get_fake_lb('1', 'tenant1')
        lb_ref = db_api.loadbalancer_create(self.conf, values)
        update = {'protocol': 'FTP',
                  'extra': {'extrafield': 'extravalue'}}
        lb_ref = db_api.loadbalancer_update(self.conf, lb_ref['id'],
                                            update)
        lb = dict(lb_ref.iteritems())
        values.update(update)
        self.assertIsNotNone(lb['id'])
        values['id'] = lb['id']
        values['updated_at'] = lb['updated_at']
        self.assertEqual(lb, values)

    def test_loadbalancer_get(self):
        values = get_fake_lb('1', 'tenant1')
        lb_ref1 = db_api.loadbalancer_create(self.conf, values)
        lb_ref2 = db_api.loadbalancer_get(self.conf, lb_ref1['id'])
        self.assertEqual(dict(lb_ref1.iteritems()),
                         dict(lb_ref2.iteritems()))

    def test_loadbalancer_get_all_by_project(self):
        values = get_fake_lb('1', 'tenant1')
        lb_ref1 = db_api.loadbalancer_create(self.conf, values)
        values = get_fake_lb('2', 'tenant2')
        lb_ref2 = db_api.loadbalancer_create(self.conf, values)
        lbs1 = db_api.loadbalancer_get_all_by_project(self.conf, 'tenant1')
        lbs2 = db_api.loadbalancer_get_all_by_project(self.conf, 'tenant2')
        self.assertEqual([dict(lb_ref1.iteritems())],
                         [dict(lb.iteritems()) for lb in lbs1])
        self.assertEqual([dict(lb_ref2.iteritems())],
                         [dict(lb.iteritems()) for lb in lbs2])
        self.assertNotEqual(lbs1[0]['id'], lbs2[0]['id'])

    def test_loadbalancer_get_all_by_vm_id(self):
        lb_fake1 = get_fake_lb('1', 'tenant1')
        lb_fake2 = get_fake_lb('2', 'tenant2')
        lb_ref1 = db_api.loadbalancer_create(self.conf, lb_fake1)
        lb_ref2 = db_api.loadbalancer_create(self.conf, lb_fake2)
        sf_fake1 = get_fake_sf(lb_ref1['id'])
        sf_fake2 = get_fake_sf(lb_ref2['id'])
        sf_ref1 = db_api.serverfarm_create(self.conf, sf_fake1)
        sf_ref2 = db_api.serverfarm_create(self.conf, sf_fake2)
        node_fake1 = get_fake_server(sf_ref1['id'], 1, '10.0.0.1')
        node_fake2 = get_fake_server(sf_ref1['id'], 20, '10.0.0.2')
        node_fake3 = get_fake_server(sf_ref2['id'], 1, '10.0.0.3')
        node_fake4 = get_fake_server(sf_ref2['id'], 30, '10.0.0.4')
        node_ref1 = db_api.server_create(self.conf, node_fake1)
        node_ref2 = db_api.server_create(self.conf, node_fake2)
        node_ref3 = db_api.server_create(self.conf, node_fake3)
        node_ref4 = db_api.server_create(self.conf, node_fake4)
        lbs1 = db_api.loadbalancer_get_all_by_vm_id(self.conf, 1, 'tenant1')
        lbs2 = db_api.loadbalancer_get_all_by_vm_id(self.conf, 30, 'tenant2')
        lbs3 = db_api.loadbalancer_get_all_by_vm_id(self.conf, 20, 'tenant2')
        self.assertEqual([dict(lb_ref1.iteritems())],
                         [dict(lb.iteritems()) for lb in lbs1])
        self.assertEqual([dict(lb_ref2.iteritems())],
                         [dict(lb.iteritems()) for lb in lbs2])
        self.assertFalse(lbs3)

    def test_lb_count_active_by_device(self):
        lb_fake1 = get_fake_lb('1', 'tenant1')
        lb_fake2 = get_fake_lb('1', 'tenant2')
        lb_fake2['status'] = lb_status.ACTIVE
        lb_ref1 = db_api.loadbalancer_create(self.conf, lb_fake1)
        lb_ref2 = db_api.loadbalancer_create(self.conf, lb_fake2)
        result = db_api.lb_count_active_by_device(self.conf, '1')
        self.assertEqual(result, 1)

    def test_loadbalancer_destroy(self):
        values = get_fake_lb('1', 'tenant1')
        lb = db_api.loadbalancer_create(self.conf, values)
        db_api.loadbalancer_destroy(self.conf, lb['id'])
        with self.assertRaises(exception.LoadBalancerNotFound) as cm:
            db_api.loadbalancer_get(self.conf, lb['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'loadbalancer_id': lb['id']})

    def test_probe_create(self):
        values = get_fake_probe('1')
        probe_ref = db_api.probe_create(self.conf, values)
        probe = dict(probe_ref.iteritems())
        self.assertIsNotNone(probe['id'])
        values['id'] = probe['id']
        self.assertEqual(probe, values)

    def test_probe_get_all(self):
        values = get_fake_probe('1')
        probe_ref1 = db_api.probe_create(self.conf, values)
        probe_ref2 = db_api.probe_create(self.conf, values)
        probes = db_api.probe_get_all(self.conf)
        self.assertEqual([dict(probe.iteritems()) for probe in probes],
                         [dict(probe.iteritems()) for probe in [probe_ref1,
                                                                probe_ref2]])

    def test_probe_get_all_by_sf_id(self):
        values = get_fake_probe('1')
        pr1 = db_api.probe_create(self.conf, values)
        values = get_fake_probe('2')
        pr2 = db_api.probe_create(self.conf, values)
        probes1 = db_api.probe_get_all_by_sf_id(self.conf, '1')
        probes2 = db_api.probe_get_all_by_sf_id(self.conf, '2')
        self.assertEqual([dict(pr1.iteritems())],
                         [dict(pr.iteritems()) for pr in probes1])
        self.assertEqual([dict(pr2.iteritems())],
                         [dict(pr.iteritems()) for pr in probes2])

    def test_probe_update(self):
        values = get_fake_probe('1')
        probe_ref = db_api.probe_create(self.conf, values)
        update = {'name': 'test',
                  'extra': {'delay': 20,
                            'attemptsDeforeDeactivation': 5,
                            'timeout': 15}}
        probe_ref = db_api.probe_update(self.conf, probe_ref['id'], update)
        probe = dict(probe_ref.iteritems())
        values.update(update)
        self.assertIsNotNone(probe['id'])
        values['id'] = probe['id']
        self.assertEqual(probe, values)

    def test_probe_get(self):
        values = get_fake_probe('1')
        probe_ref1 = db_api.probe_create(self.conf, values)
        probe_ref2 = db_api.probe_get(self.conf, probe_ref1['id'])
        self.assertEqual(dict(probe_ref1.iteritems()),
                         dict(probe_ref2.iteritems()))

    def test_probe_destroy_by_sf_id(self):
        values1 = get_fake_probe('1')
        values2 = get_fake_probe('2')
        probe_ref1 = db_api.probe_create(self.conf, values1)
        probe_ref2 = db_api.probe_create(self.conf, values2)
        db_api.probe_destroy_by_sf_id(self.conf, '1')
        probes = db_api.probe_get_all(self.conf)
        self.assertEqual(len(probes), 1)
        self.assertEqual(dict(probe_ref2.iteritems()),
                         dict(probes[0].iteritems()))

    def test_probe_destroy(self):
        values = get_fake_probe('1')
        probe = db_api.probe_create(self.conf, values)
        db_api.probe_destroy(self.conf, probe['id'])
        with self.assertRaises(exception.ProbeNotFound) as cm:
            db_api.probe_get(self.conf, probe['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'probe_id': probe['id']})

    def test_sticky_create(self):
        values = get_fake_sticky('1')
        sticky_ref = db_api.sticky_create(self.conf, values)
        sticky = dict(sticky_ref.iteritems())
        self.assertIsNotNone(sticky['id'])
        values['id'] = sticky['id']
        self.assertEqual(sticky, values)

    def test_sticky_get_all(self):
        values = get_fake_sticky('1')
        st1 = db_api.sticky_create(self.conf, values)
        st2 = db_api.sticky_create(self.conf, values)
        stickies = [dict(sticky.iteritems()) for sticky
                                           in db_api.sticky_get_all(self.conf)]
        self.assertEqual(stickies, [dict(st.iteritems()) for st in [st1, st2]])

    def test_sticky_get_all_by_sf_id(self):
        values = get_fake_sticky('1')
        st1 = db_api.sticky_create(self.conf, values)
        values = get_fake_sticky('2')
        st2 = db_api.sticky_create(self.conf, values)
        stickies1 = db_api.sticky_get_all_by_sf_id(self.conf, '1')
        stickies2 = db_api.sticky_get_all_by_sf_id(self.conf, '2')
        self.assertEqual(len(stickies1), 1)
        self.assertEqual(dict(st1.iteritems()), dict(stickies1[0].iteritems()))
        self.assertEqual(len(stickies2), 1)
        self.assertEqual(dict(st2.iteritems()), dict(stickies2[0].iteritems()))

    def test_sticky_update(self):
        values = get_fake_sticky('1')
        sticky_ref = db_api.sticky_create(self.conf, values)
        update = {'name': 'test',
                  'extra': {'cookieName': 'testHTTPCookie',
                            'enableInsert': True,
                            'browserExpire': False,
                            'offset': False,
                            'length': 1000,
                            'secondaryName': 'cookie'}}
        sticky_ref = db_api.sticky_update(self.conf, sticky_ref['id'], update)
        sticky = dict(sticky_ref.iteritems())
        values.update(update)
        self.assertIsNotNone(sticky['id'])
        values['id'] = sticky['id']
        self.assertEqual(sticky, values)

    def test_sticky_get(self):
        values = get_fake_sticky('1')
        sticky_ref1 = db_api.sticky_create(self.conf, values)
        sticky_ref2 = db_api.sticky_get(self.conf, sticky_ref1['id'])
        self.assertEqual(dict(sticky_ref1.iteritems()),
                         dict(sticky_ref2.iteritems()))

    def test_sticky_destroy_by_sf_id(self):
        values = get_fake_sticky('1')
        sticky_ref1 = db_api.sticky_create(self.conf, values)
        values = get_fake_sticky('2')
        sticky_ref2 = db_api.sticky_create(self.conf, values)
        db_api.sticky_destroy_by_sf_id(self.conf, '1')
        stickies = db_api.sticky_get_all(self.conf)
        self.assertEqual([dict(sticky_ref2.iteritems())],
                         [dict(st.iteritems()) for st in stickies])

    def test_sticky_destroy(self):
        values = get_fake_sticky('1')
        sticky = db_api.sticky_create(self.conf, values)
        db_api.sticky_destroy(self.conf, sticky['id'])
        with self.assertRaises(exception.StickyNotFound) as cm:
            db_api.sticky_get(self.conf, sticky['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'sticky_id': sticky['id']})

    def test_server_create(self):
        values = get_fake_server('1', 1)
        server_ref = db_api.server_create(self.conf, values)
        server = dict(server_ref.iteritems())
        self.assertIsNotNone(server['id'])
        values['id'] = server['id']
        self.assertEqual(server, values)

    def test_server_get_all(self):
        values = get_fake_server('1', 1)
        server1 = db_api.server_create(self.conf, values)
        server2 = db_api.server_create(self.conf, values)
        servers = db_api.server_get_all(self.conf)
        self.assertEqual([dict(server.iteritems()) for server in servers],
                         [dict(server.iteritems()) for server in [server1,
                                                                  server2]])

    def test_server_get_all_by_sf_id(self):
        values = get_fake_server('1', 1)
        sr1 = db_api.server_create(self.conf, values)
        sr2 = db_api.server_create(self.conf, values)
        values = get_fake_server('2', 1)
        sr3 = db_api.server_create(self.conf, values)
        sr4 = db_api.server_create(self.conf, values)
        servers1 = db_api.server_get_all_by_sf_id(self.conf, '1')
        servers2 = db_api.server_get_all_by_sf_id(self.conf, '2')

        self.assertEqual([dict(server.iteritems()) for server in servers1],
                         [dict(server.iteritems()) for server in [sr1, sr2]])
        self.assertEqual([dict(server.iteritems()) for server in servers2],
                         [dict(server.iteritems()) for server in [sr3, sr4]])

    def test_server_update(self):
        values = get_fake_server('1', 1)
        server_ref = db_api.server_create(self.conf, values)
        update = {'name': 'test',
                  'extra': {'cookieName': 'testHTTPCookie',
                            'enableInsert': True,
                            'browserExpire': False,
                            'offset': False,
                            'length': 1000,
                            'secondaryName': 'cookie'}}
        server_ref = db_api.server_update(self.conf, server_ref['id'], update)
        server = dict(server_ref.iteritems())
        values.update(update)
        self.assertIsNotNone(server['id'])
        values['id'] = server['id']
        self.assertEqual(server, values)

    def test_server_get0(self):
        values = get_fake_server('1', 1)
        server_ref1 = db_api.server_create(self.conf, values)
        server_ref2 = db_api.server_get(self.conf, server_ref1['id'])
        self.assertEqual(dict(server_ref1.iteritems()),
                         dict(server_ref2.iteritems()))

    def test_server_get1(self):
        lb_values = get_fake_lb('1', 'tenant1')
        lb = db_api.loadbalancer_create(self.conf, lb_values)
        sf_values = get_fake_sf(lb['id'])
        sf = db_api.serverfarm_create(self.conf, sf_values)

        server_values = get_fake_server(sf['id'], 1)
        server_ref1 = db_api.server_create(self.conf, server_values)
        server_ref2 = db_api.server_get(self.conf, server_ref1['id'], lb['id'])
        self.assertEqual(dict(server_ref1.iteritems()),
                         dict(server_ref2.iteritems()))

    def test_server_destroy_by_sf_id(self):
        values = get_fake_server('1', 1)
        server_ref1 = db_api.server_create(self.conf, values)
        values = get_fake_server('2', 1)
        server_ref2 = db_api.server_create(self.conf, values)
        db_api.server_destroy_by_sf_id(self.conf, '1')
        servers = db_api.server_get_all(self.conf)
        self.assertEqual([dict(server_ref2.iteritems())],
                         [dict(server.iteritems()) for server in servers])

    def test_server_destroy(self):
        values = get_fake_server('1', 1)
        server = db_api.server_create(self.conf, values)
        db_api.server_destroy(self.conf, server['id'])
        with self.assertRaises(exception.ServerNotFound) as cm:
            db_api.server_get(self.conf, server['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'server_id': server['id']})

    def test_server_get_by_address(self):
        values1 = get_fake_server('1', 1, '10.0.0.1')
        values2 = get_fake_server('1', 1, '10.0.0.2')
        server1 = db_api.server_create(self.conf, values1)
        server2 = db_api.server_create(self.conf, values2)
        server = db_api.server_get_by_address(self.conf, '10.0.0.1')
        self.assertEqual(dict(server.iteritems()), dict(server1.iteritems()))
        with self.assertRaises(exception.ServerNotFound) as cm:
            db_api.server_get_by_address(self.conf, '192.168.0.1')
        err = cm.exception
        self.assertEqual(err.kwargs, {'server_address': '192.168.0.1'})

    def test_server_get_by_address_on_device(self):
        lb_fake = get_fake_lb('1', 'tenant1')
        lb_ref = db_api.loadbalancer_create(self.conf, lb_fake)
        sf_fake = get_fake_sf(lb_ref['id'])
        sf_ref = db_api.serverfarm_create(self.conf, sf_fake)
        server_fake = get_fake_server(sf_ref['id'], 1, '10.0.0.1')
        server_ref = db_api.server_create(self.conf, server_fake)
        server = db_api.server_get_by_address_on_device(self.conf, '10.0.0.1',
                                                        '1')
        with self.assertRaises(exception.ServerNotFound) as cm:
            server = db_api.server_get_by_address_on_device(self.conf,
                                                            '10.0.0.2', '1')
        expected = {'server_address': '10.0.0.2',
                    'device_id': '1'}
        err = cm.exception
        self.assertEqual(err.kwargs, expected)
        with self.assertRaises(exception.ServerNotFound) as cm:
            server = db_api.server_get_by_address_on_device(self.conf,
                                                            '10.0.0.1', '2')
        err = cm.exception
        expected = {'server_address': '10.0.0.1',
                    'device_id': '2'}
        self.assertEqual(err.kwargs, expected)

    def test_server_get_all_by_parent_id(self):
        values1 = get_fake_server('1', 1, '10.0.0.1', 1)
        values2 = get_fake_server('1', 1, '10.0.0.2', 2)
        values3 = get_fake_server('1', 1, '10.0.0.3')
        server_ref1 = db_api.server_create(self.conf, values1)
        server_ref2 = db_api.server_create(self.conf, values2)
        server_ref3 = db_api.server_create(self.conf, values3)
        servers = db_api.server_get_all_by_parent_id(self.conf, 1)
        self.assertEqual([dict(server_ref1.iteritems())],
                         [dict(server.iteritems()) for server in servers])

    def test_serverfarm_create(self):
        values = get_fake_sf('1')
        serverfarm_ref = db_api.serverfarm_create(self.conf, values)
        serverfarm = dict(serverfarm_ref.iteritems())
        self.assertIsNotNone(serverfarm['id'])
        values['id'] = serverfarm['id']
        self.assertEqual(serverfarm, values)

    def test_serverfarm_get_all_by_lb_id(self):
        values1 = get_fake_sf('1')
        values2 = get_fake_sf('2')
        sf_ref1 = db_api.serverfarm_create(self.conf, values1)
        sf_ref2 = db_api.serverfarm_create(self.conf, values2)
        sfs1 = db_api.serverfarm_get_all_by_lb_id(self.conf, '1')
        sfs2 = db_api.serverfarm_get_all_by_lb_id(self.conf, '2')
        self.assertEqual([dict(sf_ref1.iteritems())],
                         [dict(sf.iteritems()) for sf in sfs1])
        self.assertEqual([dict(sf_ref2.iteritems())],
                         [dict(sf.iteritems()) for sf in sfs2])

    def test_serverfarm_update(self):
        values = get_fake_sf('1')
        serverfarm_ref = db_api.serverfarm_create(self.conf, values)
        update = {'name': 'test',
                  'extra': {'extrafield': 'extravalue'}}
        serverfarm_ref = db_api.serverfarm_update(self.conf,
                                                  serverfarm_ref['id'],
                                                  update)
        serverfarm = dict(serverfarm_ref.iteritems())
        values.update(update)
        self.assertIsNotNone(serverfarm['id'])
        values['id'] = serverfarm['id']
        self.assertEqual(serverfarm, values)

    def test_serverfarm_get(self):
        values = get_fake_sf('1')
        serverfarm_ref1 = db_api.serverfarm_create(self.conf, values)
        serverfarm_ref2 = db_api.serverfarm_get(self.conf,
                                                serverfarm_ref1['id'])
        self.assertEqual(dict(serverfarm_ref1.iteritems()),
                         dict(serverfarm_ref2.iteritems()))

    def test_serverfarm_destroy(self):
        values = get_fake_sf('1')
        serverfarm = db_api.serverfarm_create(self.conf, values)
        db_api.serverfarm_destroy(self.conf, serverfarm['id'])
        with self.assertRaises(exception.ServerFarmNotFound) as cm:
            db_api.serverfarm_get(self.conf, serverfarm['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'serverfarm_id': serverfarm['id']})

    def test_predictor_create(self):
        values = get_fake_predictor('1')
        predictor_ref = db_api.predictor_create(self.conf, values)
        predictor = dict(predictor_ref.iteritems())
        self.assertIsNotNone(predictor['id'])
        values['id'] = predictor['id']
        self.assertEqual(predictor, values)

    def test_predictor_get_all_by_sf_id(self):
        values = get_fake_predictor('1')
        predictor1 = db_api.predictor_create(self.conf, values)
        values = get_fake_predictor('2')
        predictor2 = db_api.predictor_create(self.conf, values)
        predictors1 = db_api.predictor_get_all_by_sf_id(self.conf, '1')
        predictors2 = db_api.predictor_get_all_by_sf_id(self.conf, '2')
        self.assertEqual([dict(predictor1.iteritems())],
                         [dict(pr.iteritems()) for pr in predictors1])
        self.assertEqual([dict(predictor2.iteritems())],
                         [dict(pr.iteritems()) for pr in predictors2])

    def test_predictor_update(self):
        values = get_fake_predictor('1')
        predictor_ref = db_api.predictor_create(self.conf, values)
        update = {'type': 'LEASTCONNECTIONS',
                  'extra': {'extrafield': 'extravalue'}}
        predictor_ref = db_api.predictor_update(self.conf, predictor_ref['id'],
                                                update)
        predictor = dict(predictor_ref.iteritems())
        values.update(update)
        self.assertIsNotNone(predictor['id'])
        values['id'] = predictor['id']
        self.assertEqual(predictor, values)

    def test_predictor_get(self):
        values = get_fake_predictor('1')
        predictor_ref1 = db_api.predictor_create(self.conf, values)
        predictor_ref2 = db_api.predictor_get(self.conf, predictor_ref1['id'])
        self.assertEqual(dict(predictor_ref1.iteritems()),
                         dict(predictor_ref2.iteritems()))

    def test_predictor_destroy_by_sf_id(self):
        values = get_fake_predictor('1')
        predictor_ref1 = db_api.predictor_create(self.conf, values)
        values = get_fake_predictor('2')
        predictor_ref2 = db_api.predictor_create(self.conf, values)
        db_api.predictor_destroy_by_sf_id(self.conf, '1')
        with self.assertRaises(exception.PredictorNotFound) as cm:
            db_api.predictor_get(self.conf, predictor_ref1['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'predictor_id': predictor_ref1['id']})
        predictor_ref3 = db_api.predictor_get(self.conf, predictor_ref2['id'])
        self.assertEqual(dict(predictor_ref2.iteritems()),
                         dict(predictor_ref3.iteritems()))

    def test_predictor_destroy(self):
        values = get_fake_predictor('1')
        predictor = db_api.predictor_create(self.conf, values)
        db_api.predictor_destroy(self.conf, predictor['id'])
        with self.assertRaises(exception.PredictorNotFound) as cm:
            db_api.predictor_get(self.conf, predictor['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'predictor_id': predictor['id']})

    def test_virtualserver_create(self):
        values = get_fake_virtualserver('1', '1')
        virtualserver_ref = db_api.virtualserver_create(self.conf, values)
        virtualserver = dict(virtualserver_ref.iteritems())
        self.assertIsNotNone(virtualserver['id'])
        values['id'] = virtualserver['id']
        self.assertEqual(virtualserver, values)

    def test_virtualserver_get_all_by_sf_id(self):
        values = get_fake_virtualserver('1', '1')
        virtualserver1 = db_api.virtualserver_create(self.conf, values)
        virtualserver2 = db_api.virtualserver_create(self.conf, values)
        values = get_fake_virtualserver('2', '1')
        virtualserver3 = db_api.virtualserver_create(self.conf, values)
        virtualserver4 = db_api.virtualserver_create(self.conf, values)
        virtualservers1 = db_api.virtualserver_get_all_by_sf_id(self.conf, '1')
        virtualservers2 = db_api.virtualserver_get_all_by_sf_id(self.conf, '2')
        self.assertEqual([dict(vs.iteritems()) for vs in virtualservers1],
                         [dict(vs.iteritems()) for vs in [virtualserver1,
                                                          virtualserver2]])
        self.assertEqual([dict(vs.iteritems()) for vs in virtualservers2],
                         [dict(vs.iteritems()) for vs in [virtualserver3,
                                                          virtualserver4]])

    def test_virtualserver_update(self):
        values = get_fake_virtualserver('1', '1')
        virtualserver_ref = db_api.virtualserver_create(self.conf, values)
        update = {'port': '80',
                  'deployed': 'True',
                  'extra': {'ipVersion': 'IPv4',
                            'VLAN': 400,
                            'ICMPreply': False}}
        virtualserver_ref = db_api.virtualserver_update(self.conf,
                                    virtualserver_ref['id'], update)
        virtualserver = dict(virtualserver_ref.iteritems())
        values.update(update)
        self.assertIsNotNone(virtualserver['id'])
        values['id'] = virtualserver['id']
        self.assertEqual(virtualserver, values)

    def test_virtualserver_get(self):
        values = get_fake_virtualserver('1', '1')
        virtualserver_ref1 = db_api.virtualserver_create(self.conf, values)
        virtualserver_ref2 = db_api.virtualserver_get(self.conf,
                                                      virtualserver_ref1['id'])
        self.assertEqual(dict(virtualserver_ref1.iteritems()),
                         dict(virtualserver_ref2.iteritems()))

    def test_virtualserver_destroy_by_sf_id(self):
        values = get_fake_virtualserver('1', '1')
        virtualserver_ref1 = db_api.virtualserver_create(self.conf, values)
        values = get_fake_virtualserver('2', '1')
        virtualserver_ref2 = db_api.virtualserver_create(self.conf, values)
        db_api.virtualserver_destroy_by_sf_id(self.conf, '1')
        with self.assertRaises(exception.VirtualServerNotFound) as cm:
            db_api.virtualserver_get(self.conf, virtualserver_ref1['id'])
        err = cm.exception
        expected = {'virtualserver_id': virtualserver_ref1['id']}
        self.assertEqual(err.kwargs, expected)
        virtualserver_ref3 = db_api.virtualserver_get(self.conf,
                                                      virtualserver_ref2['id'])
        self.assertEqual(dict(virtualserver_ref2.iteritems()),
                         dict(virtualserver_ref3.iteritems()))

    def test_virtualserver_destroy(self):
        values = get_fake_virtualserver('1', '1')
        virtualserver = db_api.virtualserver_create(self.conf, values)
        db_api.virtualserver_destroy(self.conf, virtualserver['id'])
        with self.assertRaises(exception.VirtualServerNotFound) as cm:
            db_api.virtualserver_get(self.conf, virtualserver['id'])
        err = cm.exception
        self.assertEqual(err.kwargs, {'virtualserver_id': virtualserver['id']})
