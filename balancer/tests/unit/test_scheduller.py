import mock
import unittest

from balancer.core import scheduler
from balancer import exception as exp
from balancer.common import cfg


def fake_filter(conf, lb_ref, dev_ref):
    return True if ord(dev_ref) > 98 else False


def fake_cost(conf, lb_ref, dev_ref):
    return 1. * ord(dev_ref)


class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.conf = mock.MagicMock()
        self.lb_ref = mock.Mock()
        self.attrs = {'device_filters':
                 ['%s.fake_filter' % __name__],
                 'device_cost_functions':
                 ['%s.fake_cost' % __name__],
                 'device_cost_fake_cost_weight': 1.}
        self.conf.configure_mock(**self.attrs)

    @mock.patch('balancer.db.api.device_get_all')
    def test_scheduler_no_proper_devs(self, dev_get_all):
        dev_get_all.return_value = ['a', 'b']
        with self.assertRaises(exp.NoValidDevice):
            scheduler.schedule_loadbalancer(self.conf, self.lb_ref)
            self.assertTrue(dev_get_all.called)

    @mock.patch('balancer.db.api.device_get_all')
    def test_scheduler_with_proper_devs(self, dev_get_all):
        dev_get_all.return_value = ['a', 'b', 'c', 'd']
        res = scheduler.schedule_loadbalancer(self.conf, self.lb_ref)
        self.assertTrue(dev_get_all.called)
        self.assertEqual('c', res)

    @mock.patch('balancer.db.api.device_get_all')
    def test_scheduler_without_devices(self, dev_get_all):
        dev_get_all.return_value = []
        with self.assertRaises(exp.DeviceNotFound):
            scheduler.schedule_loadbalancer(self.conf, self.lb_ref)
            self.assertTrue(dev_get_all.called)

    @mock.patch('balancer.db.api.device_get_all')
    def test_scheduler_no_cfg(self, dev_get_all):
        conf = cfg.ConfigOpts(default_config_files=[])
        conf._oparser = mock.Mock()
        conf._oparser.parse_args.return_value = mock.Mock(), None
        conf._oparser.parse_args.return_value[0].__dict__ = self.attrs
        conf()
        dev_get_all.return_value = ['a', 'b', 'c', 'd']
        res = scheduler.schedule_loadbalancer(conf, self.lb_ref)
        self.assertTrue(dev_get_all.called)
        self.assertEqual('c', res)


class TestFilterCapabilities(unittest.TestCase):
    def setUp(self):
        self.conf = mock.MagicMock()
        self.conf.device_filter_capabilities = ['algorithm']
        self.lb_ref = {'id': 5}
        self.dev_ref = {'id': 1}

    @mock.patch("balancer.drivers.get_device_driver", autospec=True)
    def test_proper(self, mock_getdev):
        self.lb_ref['algorithm'] = 'test'
        mock_getdev.return_value.get_capabilities.return_value = {
                'algorithms': ['test'],
        }
        res = scheduler.filter_capabilities(self.conf, self.lb_ref,
                                           self.dev_ref)
        self.assertTrue(res)

    @mock.patch("balancer.drivers.get_device_driver", autospec=True)
    def test_no_req(self, mock_getdev):
        mock_getdev.return_value.get_capabilities.return_value = {
                'algorithms': ['test'],
        }
        res = scheduler.filter_capabilities(self.conf, self.lb_ref,
                                           self.dev_ref)
        self.assertTrue(res)

    @mock.patch("balancer.drivers.get_device_driver", autospec=True)
    def test_no_cap(self, mock_getdev):
        self.lb_ref['algorithm'] = 'test'
        mock_getdev.return_value.get_capabilities.return_value = {}
        res = scheduler.filter_capabilities(self.conf, self.lb_ref,
                                           self.dev_ref)
        self.assertFalse(res)

    @mock.patch("balancer.drivers.get_device_driver", autospec=True)
    def test_none_cap(self, mock_getdev):
        self.lb_ref['algorithm'] = 'test'
        mock_getdev.return_value.get_capabilities.return_value = None
        res = scheduler.filter_capabilities(self.conf, self.lb_ref,
                                           self.dev_ref)
        self.assertFalse(res)

    @mock.patch("balancer.drivers.get_device_driver", autospec=True)
    def test_no_cfg(self, mock_getdev):
        conf = cfg.ConfigOpts(default_config_files=[])
        conf._oparser = mock.Mock()
        conf._oparser.parse_args.return_value = mock.Mock(), None
        conf._oparser.parse_args.return_value[0].__dict__ = {}
        conf()
        self.lb_ref['algorithm'] = 'test'
        mock_getdev.return_value.get_capabilities.return_value = {
                'algorithms': ['test'],
        }
        res = scheduler.filter_capabilities(conf, self.lb_ref, self.dev_ref)
        self.assertTrue(res)


class TestWeigthsFunctions(unittest.TestCase):
    def setUp(self):
        self.conf = mock.MagicMock()
        self.lb_ref = {}
        self.dev_ref = {}

    @mock.patch('balancer.db.api.lb_count_active_by_device')
    def test_lbs_on(self, lb_count):
        lb_count.return_value = 3
        self.dev_ref['id'] = '1'
        res = scheduler.lbs_on(self.conf, self.lb_ref, self.dev_ref)
        self.assertEqual(res, 3)
