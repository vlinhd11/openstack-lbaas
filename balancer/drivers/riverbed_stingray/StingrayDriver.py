# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging
import base64
import urlparse
import json
import requests
from requests.auth import HTTPBasicAuth

from balancer.drivers.base_driver import BaseDriver

logger = logging.getLogger(__name__)


class StingrayDriver(BaseDriver):
    def __init__(self,  conf,  device_ref):
        super(StingrayDriver, self).__init__(conf, device_ref)
        try:
            port = device_ref['port']
        except KeyErrorException:
            #Standard port for REST daemon is 9070
            port = '9070'

        #Set up base URL and authorization for HTTP requests
        self.url = ("https://%s:%s/latest/config/active/"
                        % device_ref['ip'], port)
        self.basic_auth = HTTPBasicAuth(device_ref['login'],
                            device_ref['port'])


    def send_request(self, url_extension, payload=None):
        #Generate appropriate url
        target_url = urlparse.urljoin(self.url, url_extension)
        #Create headers dictionary
        headers = {'Content-Type': 'application/json'}
        try:
            #Send request
            if payload is not None:
                '''Add in support for POST later
                    PUT specified by Stingray API'''
                response = requests.put(target_url, headers=headers,
                                data=json.dumps(payload),
                                auth=self.basic_auth, verify=False)
            else:
                response = requests.get(target_url, auth=self.basic_auth,
                                verify=False)
        except (Exception):
            #Most likely could not reach the specified URL
            raise

        logger.debug("Data from Stingray:\n" + response.text)
        #Make sure error code is acceptable
        response.raise_for_status()

    def import_certificate_or_key(self):
        logger.debug("Called DummyStingrayDriver.importCertificatesAndKeys().")

    def create_ssl_proxy(self, ssl_proxy):
        logger.debug("Called DummyStingrayDriver.createSSLProxy(%r).",
                     ssl_proxy)

    def delete_ssl_proxy(self, ssl_proxy):
        logger.debug("Called DummyStingrayDriver.deleteSSLProxy(%r).",
                     ssl_proxy)

    def add_ssl_proxy_to_virtual_ip(self, vip, ssl_proxy):
        logger.debug("Called DummyStingrayDriver.deleteSSLProxy(%r, %r).",
                     vip, ssl_proxy)

    def remove_ssl_proxy_from_virtual_ip(self, vip, ssl_proxy):
        logger.debug("Called DummyStingrayDriver.removeSSLProxyFromVIP(%r, %r).",
                     vip, ssl_proxy)

    def create_real_server(self, rserver):
        logger.debug("Called DummyStingrayDriver.createRServer(%r).", rserver)

    def delete_real_server(self, rserver):
        logger.debug("Called DummyStingrayDriver.deleteRServer(%r).", rserver)

    def activate_real_server(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.activateRServer(%r, %r).",
                     serverfarm, rserver)

    def activate_real_server_global(self, rserver):
        logger.debug("Called DummyStingrayDriver.activateRServerGlobal(%r).",
                     rserver)

    def suspend_real_server(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.suspendRServer(%r, %r).",
                     serverfarm, rserver)

    def suspend_real_server_global(self, rserver):
        logger.debug("Called DummyStingrayDriver.suspendRServerGlobal(%r).",
                     rserver)

    def create_probe(self, probe):
        logger.debug("Called DummyStingrayDriver.createProbe(%r).", probe)

    def delete_probe(self, probe):
        logger.debug("Called DummyStingrayDriver.deleteProbe(%r).", probe)

    def create_server_farm(self, serverfarm, predictor):
        logger.debug("Called DummyStingrayDriver.createServerFarm(%r).",
                     serverfarm)

    def delete_server_farm(self, serverfarm):
        logger.debug("Called DummyStingrayDriver.deleteServerFarm(%r).",
                     serverfarm)

    def add_real_server_to_server_farm(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.addRServerToSF(%r, %r).",
                     serverfarm, rserver)

    def delete_real_server_from_server_farm(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.deleteRServerFromSF(%r, %r).",
                     serverfarm, rserver)

    def add_probe_to_server_farm(self, serverfarm, probe):
        logger.debug("Called DummyStingrayDriver.addProbeToSF(%r, %r).",
                     serverfarm, probe)

    def delete_probe_from_server_farm(self, serverfarm, probe):
        logger.debug("Called DummyStingrayDriver.deleteProbeFromSF(%r, %r).",
                     serverfarm, probe)

    def create_stickiness(self, sticky):
        logger.debug("Called DummyStingrayDriver.createStickiness(%r).",
                     sticky)

    def delete_stickiness(self, sticky):
        logger.debug("Called DummyStingrayDriver.deleteStickiness(%r).",
                     sticky)

    def create_virtual_ip(self, vip, serverfarm):
        logger.debug("Called DummyStingrayDriver.createVIP(%r, %r).",
                     vip, serverfarm)

    def delete_virtual_ip(self, vip):
        logger.debug("Called DummyStingrayDriver.deleteVIP(%r).", vip)

    def get_statistics(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.getStatistics(%r, %r).",
                     serverfarm, rserver)
