# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging
import base64
import urlparse
import json
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError

from balancer.drivers.base_driver import BaseDriver

logger = logging.getLogger(__name__)

class StingrayDriver(BaseDriver):
    ''' Most (all)  parameters can be found in db.models.py. They all inherit from
    a class which implements the functions allowing for dictionary notation.
    Using this notation allows for easy unit testing.
    '''
    def __init__(self,  conf,  device_ref):
        super(StingrayDriver, self).__init__(conf, device_ref)
        #Store id and name for later functions
        self.device_id = device_ref['id']
        self.device_name = device_ref['name']

        #Standard port for REST daemon is 9070
        port = '9070'
        #Overwrite default port if one is specified
        try:
            if device_ref['port'] is not None:
                port = device_ref['port']
        except KeyError:
            pass

        #Set up base URL and authorization for HTTP requests
        self.url = ("https://%s:%s/latest/config/active/"
                        % (device_ref['ip'], port))
        self.basic_auth = HTTPBasicAuth(device_ref['user'],
                            device_ref['password'])

    def send_request(self, url_extension, method, payload=None):
        ''' Wrapper around the python requests library. Ensures that valiidity
        of the SSL certificate is ignored and that requests include HTTP Basic Auth.
        '''
        #Generate appropriate url
        target_url = urlparse.urljoin(self.url, url_extension)
        #Create headers dictionary
        #If-Match not implemented by REST team as of yet 
        headers = {'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'If-Match': 'NEW'}

        logger.debug("Request to Stingray:\n" + method
                        + ':' + str(payload))
        try:
            #Send request
            #Stingray API on wiki explains what method is approprite
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
            '''Most likely could not reach the specified URL.
            Useful to let errors be passed on to be dealt with in
            calling function
            '''
            raise

        logger.debug("Data from Stingray:\n" + response.text)
        #Make sure request reported as successful.
        response.raise_for_status()

        return response

    def rest_add_to_list(self, target, field_name,
                            item_to_add, dict_to_add_to):
        ''' Given a target url, property name and dictionary add the new item
        to the list stored in field and return the new list in the correct
        Stingray REST format. Can be used regardless of whether field currently
        exists.
        '''
        #TODO: Get new version of REST so list syntax used.
        #Requests data from Stingray and extract current list 
        current_json = self.send_request(target, 'GET').text
        current = json.loads(current_json)

        try:
            old_list = current['properties'][field_name]
        except KeyError:
            old_list = ''

        #Stored as space seperated variable string.
        new_list = old_list + ' '  + item_to_add

        #Add new node to list and put in correct dictionary form
        dict_to_add_to['properties'][field_name] = new_list

        return dict_to_add_to

    def rest_delete_from_list(self, target, field_name,
                                item_to_remove, dict_to_remove_from):
        ''' Given a target url, property name and dictionary removes the item
        from the list stroed in field and returns the list in the correct
        Stingray REST format. If not found just returns dictionary with empty
        list.
        '''
        #??change to throw item not found exception??
        #TODO: Get new version of REST so list syntax used.
        current_json = self.send_request(target, 'GET').text
        current = json.loads(current_json)

        try:
            old_list = current['properties'][field_name]
        except KeyError:
            #Raise no item found exception?
            old_list = ''

        #remove item and replace list in dictionary
        new_list = old_list.replace(item_to_remove, '')
        dict_to_remove_from['properties'][field_name] = new_list

        return dict_to_remove_from

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
        #Do we need to do anythign here?

        logger.debug("Called DummyStingrayDriver.createRServer(%r).", rserver)

    def delete_real_server(self, rserver):
        #Delete node in our terminology
        #Do we need to do anything here?

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
        ''' Sets up virtual server and pool and connects the two. Virtual server
        defaultly listens on all addresses, changed to traffic IP group later on.
        Stingray defaultly throws an error if pool has no nodes, but this dissapears
        once a node is added.

        ID of serverfarm is used to name node, pool and traffic IP group on stingray.
        '''
        #??Logical naming??
        #Create pool with no attached nodes
        target = 'pools/' + serverfarm['id'] + '/'
        pool_new = {"properties": {
            "monitors": "ping"
            }
        }

        self.send_request(target, 'PUT', pool_new)

        #Create Virtual Server for this Load balancing Service
        #Linked to pool by giving the name of pool in the dictionary
        target = 'vservers/' + serverfarm['id'] + '/'
        vserver_new = {"properties": {
            "enabled": "no",
            "port": "8080",
            "timeout": 40,
            "pool": serverfarm['id'],
            }
        }

        self.send_request(target, 'PUT', vserver_new)

    def delete_server_farm(self, serverfarm):
        '''Delete pool, vserver and any traffic IP group referenced by
        serverfarm.
        '''
        #DELETE request to Pool
        target = 'pools/' + serverfarm['id'] + '/'
        self.send_request(target, 'DELETE')

        #DELETE request to vserver
        target = 'vservers/' + serverfarm['id'] + '/'
        self.send_request(target, 'DELETE')

        #DELETE request to traffic IP group
        try:
            target = 'flipper/' + serverfarm['id'] + '/'
            response = self.send_request(target, 'DELETE')
        except HTTPError:
            #Traffic IP group may not exist, if so just continue
            #FIXME: This cannot work this way under current version of requests
            if response.status_code == '404':
                pass
            else:
                raise


    def add_real_server_to_server_farm(self, serverfarm, rserver):
        ''' Adds a new node to the nodelist for pool associated with
        this serverfarm
        '''
        #Set up variables for request
        target = 'pools/' + serverfarm['id'] + '/'
        new_node = rserver['address'] + ':' + rserver['port'] + ' '
        pool_mod = {"properties": {
             "nodes": ''
            }
        }

        #Modify dictionary and send PUT request with that dictionary
        pool_mod = self.rest_add_to_list(target, 'nodes', new_node, pool_mod)
        self.send_request(target, 'PUT', pool_mod)

    def delete_real_server_from_server_farm(self, serverfarm, rserver):
        '''Remove node from nodelist for pool associated with this serverfarm
        '''
        #Set up variables for request
        target = 'pools/' + serverfarm['id'] + '/'
        node = rserver['address'] + ':' + rserver['port'] + ' '
        pool_mod = {"properties": {
             "nodes": ''
            }
        }

        #Modify dictionary and send PUT request with that dictionary
        pool_mod = self.rest_delete_from_list(target, 'nodes', node, pool_mod)
        self.send_request(target, 'PUT', pool_mod)

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
        ''' Add the virtual IP to the traffic IP group associated with this
        serverfarm. If no traffic IP exists yet then create it with this IP.
        '''
        #Add support for masks and ports?

        target = 'flipper/' + serverfarm['id'] + '/'

        try:
            #Add IP to existing traffic Ip group
            traffic_ip_mod = {'properties' : {
                'ipaddresses': '',
                }
            }
            traffic_ip_mod = self.rest_delete_from_list(target, 'ipaddresses',
                                            vip['address'], traffic_ip_mod)

        except HTTPError:
            #No traffic IP group exists, create one
            traffic_ip_new = {'properties' : {
                'ipaddresses': vip['address'],
                'machines': self.device_name
                }
            }
            self.send_request(target, 'PUT', traffic_ip_new)

            #hook it up to the virtual server
            vserver_target = 'vservers/' + serverfarm['id'] + '/'
            vserver_mod = {'properties': {
                        'address':('!' + serverfarm['id']),
                }
            }
            self.send_request(vserver_target, 'PUT', vserver_mod)


    def delete_virtual_ip(self, vip):
        #Traffic IP in our terminology
        #TODO:
        logger.debug("Called DummyStingrayDriver.deleteVIP(%r).", vip)

    def get_statistics(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.getStatistics(%r, %r).",
                     serverfarm, rserver)
