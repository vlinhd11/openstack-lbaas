# vim: tabstop=4 shiftwidth=4 softtabstop=4

import unittest
import requests

from balancer.drivers.riverbed_stingray.StingrayDriver import StingrayDriver

dev = {'ip': '10.62.166.27', 'login': 'admin',
        'password': 'jobbie'}

conf = []

driver = StingrayDriver(conf, dev)

class StingrayDriverTestCase(unittest.TestCase):
    def setUp(self):
        return

    def test_REST_connection(self):
        #Exception will be thrown if status code not acceptable
        response = driver.send_request('')

#    def test_REST_simple_put(self, data):
#        return
