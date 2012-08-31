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
        #Store
        self.device_id = device_ref['id']

        #Standard port for REST daemon is 9070
        port = '9070'
        #Overwrite default port if one is specified
        try:
            if device_ref['port'] is not None:
                port = '9070'
        except KeyError:
            pass

        #Set up base URL and authorization for HTTP requests
        self.url = ("https://%s:%s/latest/config/active/"
                        % (device_ref['ip'], port))
        self.basic_auth = HTTPBasicAuth(device_ref['user'],
                            device_ref['password'])


    def __del__(self):
        response = self.send_request('vservers/' + self.name, 'DELETE')

    def send_request(self, url_extension, method, payload=None):
        #Generate appropriate url
        target_url = urlparse.urljoin(self.url, url_extension)
        #Create headers dictionary
        #FIXME: Check If-Match with someone on the REST team
        headers = {'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'If-Match': 'NEW'}

        logger.debug("Request to Stingray:\n" + method
                        + ':' + str(payload))
        try:
            #Send request
            #Stingray API on wiki explains what mehtod is approprite
            if method == 'GET':
                response = requests.get(target_url, headers=headers,
                                auth=self.basic_auth, verify=False)
            elif method == 'PUT':
                response = requests.put(target_url, headers=headers,
                                data=json.dumps(payload),
                                auth=self.basic_auth, verify=False)
            elif method == 'POST':
                response = requests.post(target_url, headers=headers,
                                data=json.dumps(payload),
                                auth=self.basic_auth, verify=False)

            elif method == 'DELETE':
                response = requests.delete(target_url, headers=headers,
                                auth=self.basic_auth, verify=False)

        except Exception:
            #Most likely could not reach the specified URL
            raise

        logger.debug("Data from Stingray:\n" + response.text)
        #Make sure error code is acceptable, ensures unit tests will fail
        response.raise_for_status()

        return response

    def import_certificate_or_key(self):
        #SSL certificates/Licence keys?
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
        #Create node in our terminology

        logger.debug("Called DummyStingrayDriver.createRServer(%r).", rserver)

    def delete_real_server(self, rserver):
        #Delete node in our terminology

        logger.debug("Called DummyStingrayDriver.deleteRServer(%r).", rserver)

    def activate_real_server(self, serverfarm, rserver):
        #??
        logger.debug("Called DummyStingrayDriver.activateRServer(%r, %r).",
                     serverfarm, rserver)

    def activate_real_server_global(self, rserver):
        logger.debug("Called DummyStingrayDriver.activateRServerGlobal(%r).",
                     rserver)

    def suspend_real_server(self, serverfarm, rserver):
        #??
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
        ''' Set up virtual server and pool and connect the two
        '''
        #??Logical naming??
        #Create pool with no attached nodes
        target = 'pools/' + serverfarm['id'] + '/'
        data = {"properties": {"monitors": "ping"}}

        self.send_request(target, 'PUT', data)

        #Create Virtual Server for this Load balancing Service
        self.default_vserver = {"properties": {
            "enabled": "no",
            "port": "8080",
            "timeout": 40,
            "pool": serverfarm['id'],
            }
        }

        target = 'vservers/' + serverfarm['id'] + '/'
        self.send_request(target, 'PUT',
                              payload=self.default_vserver)

    def delete_server_farm(self, serverfarm):
        #Delete pool referenced by serverfarm
        target = 'pools/' + serverfarm['id'] + '/'
        self.send_request(target, 'DELETE')

    def add_real_server_to_server_farm(self, serverfarm, rserver):
        logger.debug('creating')
        logger.debug(rserver.address + ':' + rserver.port)
        #Add node to pool
        target = 'pools/' + serverfarm['id'] + '/'

        #TODO: Get new version of REST so list syntax used.
        #space seperated variable string for now.
#ERROR
        sf_current_json = self.send_request(target, 'GET').text
        sf_current = json.loads(sf_current_json)

        try:
            nodelist = sf_current['properties']['nodes']
        except KeyError:
            nodelist = ''
        #Add new node to list and put in correct dictionary form
#probably
        newnode = rserver.address + ':' + rserver.port + ' '
        nodelist =  '"' + nodelist + newnode + '"'
        data = {"properties": {"nodes": nodelist}}
#SOMEWHERE HERE
        self.send_request(target, 'PUT', data)

    def delete_real_server_from_server_farm(self, serverfarm, rserver):
        logger.debug('deleting')
        #Remove node from pool
        target = 'pools/' + serverfarm['id'] + '/'

        #TODO: Get new version of REST so list syntax used.
        #space seperated variable string for now.
        sf_current_json = self.send_request(target, 'GET').text
        sf_current = json.loads(sf_current_json)
        try:
            nodelist = sf_current['properties']['nodes']
        except KeyError:
            #Raise no server found exception?
            nodelist = ''
        '''Remove node from list, package existing nodes in
        correct dictionary form
        '''
        nodelist.replace(rserver.address + ':' + rserver.port + ' ',
                             '')
        data = {"properties": {"nodes": nodelist}}

        self.send_request(target, 'PUT', data)
        logger.debug('PUT was from delete_real_server_from_server_farm')

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
        #Traffic IP in our terminology
        logger.debug("Called DummyStingrayDriver.createVIP(%r, %r).",
                     vip, serverfarm)

    def delete_virtual_ip(self, vip):
        #Traffic IP in our terminology
        logger.debug("Called DummyStingrayDriver.deleteVIP(%r).", vip)

    def get_statistics(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.getStatistics(%r, %r).",
                     serverfarm, rserver)
