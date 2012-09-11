# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging
import base64
import urlparse
import json
import requests

from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from balancer.drivers.base_driver import BaseDriver

from pprint import pprint

logger = logging.getLogger(__name__)


class StingrayDriver(BaseDriver):
    ''' Most (all?) parameters can be found in db.models.py. They all inherit
    from a class which implements the functions allowing for dictionary
    notation. Using this notation seems to be the convention from the other
    drivers.
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
        of the SSL certificate is ignored and that requests include HTTP Basic
        Auth.
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
        #Make sure request reported as successful
        response.raise_for_status()

        return response

    def rest_add_to_list(self, target, field_name,
                            item_to_add, dict_to_add_to):
        ''' Given a target url, property name and dictionary add the new item
        to the list stored in field and return the new list in the correct
        Stingray REST format. Can be used regardless of whether field currently
        exists.
        '''
        #TODO: Get new version of REST so list syntax used
        #Requests data from Stingray and extract current list
        current_json = self.send_request(target, 'GET')
        current = self.response_to_dict(current_json)

        try:
            old_list = current['properties'][field_name]
        except KeyError:
            old_list = ''

        #Add new node to list (Stored as space seperated variable string)
        new_list = old_list + ' ' + item_to_add
        new_list = new_list.strip()

        #Put in correct dictionary form
        dict_to_add_to['properties'][field_name] = new_list

        return dict_to_add_to

    def rest_delete_from_list(self, target, field_name,
                                item_to_remove, dict_to_remove_from):
        ''' Given a target url, property name and dictionary removes the item
        from the list stroed in field and returns the list in the correct
        Stingray REST format. If not found just returns dictionary with empty
        list.
        '''
        #TODO: Get new version of REST so list syntax used.
        #Requests data from Stingray and extract current list
        current_json = self.send_request(target, 'GET')
        current = self.response_to_dict(current_json)

        try:
            old_list = current['properties'][field_name]
        except KeyError:
            logger.debug('Stingray: No list found, returning empty list')
            old_list = ''

        #remove item and replace list in dictionary
        #stripping whitespace means deletions eventually leave empty string
        new_list = old_list.replace(item_to_remove, '').strip()

        #Check something has changed, else log message
        if new_list == old_list:
            logger.debug('Stingray: Item  ' + item_to_remove
                                            + ' not found in list')
        #Put in dictionary form
        dict_to_remove_from['properties'][field_name] = new_list

        return dict_to_remove_from

    def response_to_dict(self, response):
        '''Returns a dictionary of the contents of a response objects body
        '''
        json_string = response.text
        return json.loads(json_string)

    def create_probe(self, probe):
        '''Creates a probe in two stages. Firstly creates a named probe with
        options valid for all probes. Then edits this probe with protocol
        specific options. Will ignore any other parameters.
        '''
        target = 'monitors/' + probe['id'] + '/'
        monitor_new = {'properties': {}}
        probe_type = probe['type'].lower()

        #TODO: Fill in all possible probe types + neccessary translations here
        if probe_type == 'https':
            monitor_new['properties']['use_ssl'] = 'Yes'
            probe_type = 'http'

        #Check that the type of probe is supported by stingray, otherwise abort
        supported_probe_types = ('tcp_transaction', 'sip', 'http', 'ping',
                                            'rtsp', 'program', 'connect')

        if probe_type not in supported_probe_types:
            logger.debug("Stingray: Unsupported probe type(%s),"
                                " quitting", probe_type)
            return

        monitor_new['properties']['type'] = probe_type

        #Load all options out of extras field
        given_options = probe.get('extra')

        '''
        Stingray default options: delay, failures, timeout,
        max_response_len, scope, can_use_ssl, use_ssl.
        '''
        #Perform translation of terms -- meanings must exactly correlate!
        opt_translation_dict = {
            'probeInterval': 'delay',
            'attemptsBeforeDeactivation': 'failures',
            'failDetect': 'failures',
            'passDetectInterval': 'timeout',
        }

        #Perform copy of given_options, translating where necessary
        given_options_translated = {}

        for opt in given_options:
            if opt in opt_translation_dict:
                new_key = opt_translation_dict[opt]
                given_options_translated[new_key] = given_options[opt]
            else:
                given_options_translated[opt] = given_options[opt]

        #Include options in request
        monitor_new['properties']['delay'] = (
                                given_options_translated.get('delay', '10'))
        monitor_new['properties']['failures'] = (
                                given_options_translated.get('failures', '3'))
        monitor_new['properties']['timeout'] = (
                                given_options_translated.get('timeout', '10'))
        #Create new probe
        self.send_request(target, 'PUT', monitor_new)

        #Configure options specific to this node type
        #Get possible config options from Stingray
        response_json = self.send_request(target, 'GET')
        response = self.response_to_dict(response_json)
        try:
            #Defaultly returns a whitespace seperated string, turn into a list
            allowed_config_options_string = (
                        response['properties']['editable_keys'])
            allowed_config_options = allowed_config_options_string.split()

            monitor_mod = {'properties': {}}

            #Copy all appropriate keys from the probe object to the Stingray
            for key in options:
                if key in allowed_config_options:
                    monitor_mod['properties'][key] = options[key]

            self.send_request(target, 'PUT', monitor_mod)
        except KeyError:
            #editable_keys wasn't set in the response, there are no such keys
            pass

    def delete_probe(self, probe):
        '''Remove probe from device
        '''
        target = 'monitors/' + probe['id'] + '/'
        self.send_request(target, 'DELETE')

    def create_server_farm(self, serverfarm, predictor):
        ''' Sets up virtual server and pool and connects the two. Virtual
        server defaultly listens on all addresses, changed to traffic IP
        group later on. Stingray defaultly throws an error if pool has no
        nodes, but this dissapears once a node is added.

        ID of serverfarm is used to name node, pool and traffic IP group on
        stingray.
        '''
        #TODO: serverfarm.loadbalancer
        #Create pool with no attached nodes
        target = 'pools/' + serverfarm['id'] + '/'
        pool_new = {"properties": {
            "monitors": "Ping"
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

        #TODO: Allow selection of protocol and algorithm
        #FIXME: Where is this sepcified (loadbalancer object in models but
        #never passed to this module)

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
            self.send_request(target, 'DELETE')
        except HTTPError as e:
            #Traffic IP group may not exist, if so just continue
            if e.response.status_code == 404:
                pass
            else:
                raise

    def add_real_server_to_server_farm(self, serverfarm, rserver):
        ''' Adds a new node to the nodelist for pool associated with
        this serverfarm
        '''
        #Set up variables for request
        target = 'pools/' + serverfarm['id'] + '/'
        new_node = rserver['address'] + ':' + rserver['port']
        new_node_weight = new_node + ':' + rserver.get('weight', '1')
        pool_mod = {'properties': {
             'nodes': ''
            }
        }

        #Modify dictionary and send PUT request with that dictionary
        pool_mod = self.rest_add_to_list(target, 'nodes', new_node, pool_mod)
        pool_mod = self.rest_add_to_list(target, 'priority!values',
                                                    new_node_weight, pool_mod)
        self.send_request(target, 'PUT', pool_mod)

    def delete_real_server_from_server_farm(self, serverfarm, rserver):
        '''Remove node from nodelist for pool associated with this serverfarm
        '''
        #Set up variables for request
        target = 'pools/' + serverfarm['id'] + '/'
        node = rserver['address'] + ':' + rserver['port']
        node_weight = node + ':' + (rserver.get('weight') or '1')
        pool_mod = {'properties': {
            'nodes': '',
            'priority!values': ''
            }
        }

        #Modify dictionary and send PUT request with that dictionary
        pool_mod = self.rest_delete_from_list(target, 'nodes', node, pool_mod)
        pool_mod = self.rest_delete_from_list(target,
                                                'priority!values',
                                                node_weight, pool_mod)

        self.send_request(target, 'PUT', pool_mod)

    def add_probe_to_server_farm(self, serverfarm, probe):
        ''' Add the specified probe to the list of monitors for the pool
        associated with this serverfarm
        '''
        target = 'pools/' + serverfarm['id'] + '/'

        node_mod = {
            'properties': {}
        }

        #Modify dictionary and send request
        self.rest_add_to_list(target, 'monitors', probe['id'], node_mod)

        self.send_request(target, 'PUT', node_mod)

    def delete_probe_from_server_farm(self, serverfarm, probe):
        ''' Remove the specified probe from the list of monitors for the
        pool associated with this serverfarm
        '''
        target = 'pools/' + serverfarm['id'] + '/'

        node_mod = {
            'properties': {}
        }

        #Modify dictionary and send request
        node_mod = self.rest_delete_from_list(target, 'monitors',
                                                probe['id'], node_mod)
        self.send_request(target, 'PUT', node_mod)

    def create_virtual_ip(self, vip, serverfarm):
        ''' Add the virtual IP to the traffic IP group associated with this
        serverfarm. If no traffic IP exists yet then create it with this IP.
        '''
        #Stingray has no support for masks/ports for virtual IPs
        #TODO:Custom expanding of a mask to range of individual IP addresses
        target = 'flipper/' + serverfarm['id'] + '/'

        try:
            #Add IP to existing traffic IP group
            traffic_ip_mod = {'properties': {
                'ipaddresses': '',
                }
            }
            traffic_ip_mod = self.rest_add_to_list(target, 'ipaddresses',
                                            vip['address'], traffic_ip_mod)
            self.send_request(target, 'PUT', traffic_ip_mod)
        except HTTPError:
            #No traffic IP group exists, create one
            traffic_ip_new = {'properties': {
                'ipaddresses': vip['address'],
                'machines': self.device_name
                }
            }
            self.send_request(target, 'PUT', traffic_ip_new)

            #Hook it up to the virtual server
            vserver_target = 'vservers/' + serverfarm['id'] + '/'
            vserver_mod = {'properties': {
                        'address': ('!' + serverfarm['id']),
                }
            }
            self.send_request(vserver_target, 'PUT', vserver_mod)

    def delete_virtual_ip(self, vip):
        '''Remove the virtual Ip from the traffic IP group associated with
        this serverfarm. If it is the last such virtual IP, remove the
        traffic IP group entirely (ensures that the traffic manager will
        go back to listening on all interfaces).
        '''
        target = 'flipper/' + vip['sf_id'] + '/'

        traffic_ip_mod = {'properties': {
            'ipaddresses': '',
            }
        }
        traffic_ip_mod = self.rest_delete_from_list(target,
                    'ipaddresses', vip['address'], traffic_ip_mod)

        if traffic_ip_mod['properties']['ipaddresses'] == '':
            #No more VIPs left in the traffic IP group, delete the group
            self.send_request(target, 'DELETE')

            #Remove group from vserver
            vserver_target = 'vservers/' + vip['sf_id'] + '/'
            vserver_mod = {'properties': {
                        'address': ''
                }
            }
            self.send_request(vserver_target, 'PUT', vserver_mod)

        else:
            #Send request to remove VIP from traffic IP group
            self.send_request(target, 'PUT', traffic_ip_mod)

    def suspend_real_server(self, serverfarm, rserver):
        ''' Stop a node from receiving traffic by adding it to disabled
        node list for the serverfarms associated pool
        '''
        target = 'pools/' + serverfarm['id'] + '/'

        node = rserver['address'] + ':' + rserver['port']

        node_mod = {
            'properties': {}
        }

        self.rest_add_to_list(target, 'disabled', node, node_mod)
        self.send_request(target, 'PUT', node_mod)

    def activate_real_server(self, serverfarm, rserver):
        ''' Allow node that was suspended to receive traffic again by removing
        it from serverfarms associated pool's disabled list
        '''
        target = 'pools/' + serverfarm['id'] + '/'

        node = rserver['address'] + ':' + rserver['port']

        node_mod = {
            'properties': {}
        }
        #Modify dictionary and send requst
        node_mod = self.rest_delete_from_list(target, 'disabled',
                                                probe['id'], node_mod)
        self.send_request(target, 'PUT', node_mod)

    def create_stickiness(self, sticky):
        ''' First create a session persistence class and then associate
        that class with the pool.
        '''
        #Create session persistence class
        pers_target = 'persistence/' + sticky['id'] + '/'

        pers_mod = {'properties': {}}

        #Translate type and set type specific options
        sticky_type = sticky['extra']['persistenceType'].lower()

        if sticky_type == 'http_cookie':
            pers_mod['properties']['type'] = 'sardine'
        elif sticky_type == 'ip':
            pers_mod['properties']['type'] = 'ip'
        elif sticky_type == 'http_header':
            logger.debug("Stingray does not support session persistence type "
                         "(%s)", extra['persistenceType'])
            return

        #Crete class on Stingray
        self.send_request(pers_target, 'PUT', pers_mod)

        #Attach new class to node
        pool_target = 'pools/' + sticky['sf_id'] + '/'

        pool_mod = {'properties': {
                'persistence': sticky['id']
            }
        }

        self.send_request(pool_target, 'PUT', pool_mod)

    def delete_stickiness(self, sticky):
        '''Checks if the persistence class is currently connected to the node,
        and removes it if so. Then deletes the session persistence class from
        the device.
        '''
        #Check if class is currently connected to the node
        pool_target = 'pools/' + sticky['sf_id'] + '/'
        response = self.send_request(pool_target, 'GET')
        pool_dict = self.response_to_dict(response)

        if pool_dict['properties'].get('persistence') == sticky['id']:
            #Set node to using no persistence class
            pool_mod = {'properties': {
                'persistence': ''
                }
            }
            self.send_request(pool_target, 'PUT', pool_mod)
        else:
            #Different session persistence class being used, do not modify
            #node
            pass

        self.send_request(pool_target, 'PUT', pool_mod)

        #Delete persistance class instance
        pers_target = 'persistence/' + sticky['id'] + '/'

        self.send_request(pers_target, 'DELETE')

    ''' Not implemented yet
    '''
    def get_statistics(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.getStatistics(%r, %r).",
                     serverfarm, rserver)

    def import_certificate_or_key(self):
        #Generic FLA licence?! Does nto seem to fit in very well with a
        #commercial system custom keys
        #SSL certificates/Licence keys?
        #No arguments to function?!?!
        logger.debug("Called DummyStingrayDriver.importCertificatesAndKeys().")

    ''' No information on API doc and ssl_proxy not in models.py
    May have to wait until F5 driver is released before this can be
    implemented properly
    '''
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
        logger.debug("Called DummyStingrayDriver"
                        ".removeSSLProxyFromVIP(%r, %r).", vip, ssl_proxy)

    '''What on earth does this mean?
    '''
    def activate_real_server_global(self, rserver):
        logger.debug("Called DummyStingrayDriver.activateRServerGlobal(%r).",
                     rserver)

    def suspend_real_server_global(self, rserver):
        logger.debug("Called DummyStingrayDriver.suspendRServerGlobal(%r).",
                     rserver)

    '''Included for compatibility with other drivers.
    '''
    def create_real_server(self, rserver):
        #Create node in our terminology
        #Do we need to do anythiggn here?

        logger.debug("Called StingrayDriver.createRServer(%r).", rserver)

    def delete_real_server(self, rserver):
        #Delete node in our terminology
        #Do we need to do anything here?

        logger.debug("Called StingrayDriver.deleteRServer(%r).", rserver)
