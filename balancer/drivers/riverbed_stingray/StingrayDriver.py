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
    ''' Most (all?) parameters can be found in db.models.py. They all inherit
    from a class which implements the functions allowing for dictionary
    notation. Using this notation allows for easy unit testing.
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

        #Stored as space seperated variable string.
        new_list = old_list + ' ' + item_to_add

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
        current_json = self.send_request(target, 'GET')
        current = self.response_to_dict(current_json)

        try:
            old_list = current['properties'][field_name]
        except KeyError:
            #Raise no item found exception?
            #404 even?
            old_list = ''

        #remove item and replace list in dictionary
        #stripping whitespace means deletions eventually leave empty string
        new_list = old_list.replace(' ' + item_to_remove, '').strip()
        dict_to_remove_from['properties'][field_name] = new_list

        return dict_to_remove_from

    def translate_probe_type(self, probe_type):
        ''' Translate the probe types exposed through the client API to those
        used in the Stingray REST API and config files.
        '''
        probe_type = probe_type.lower()

        #All the types of probe that are supported by Stingray
        supported_probe_types = ('tcp_transaction', 'sip', 'http', 'ping',
                                            'rtsp', 'program', 'connect')

        translation_table = {
            #must add use_ssl option
            'https': 'http',
        }

        try:
            stingray_probe_type = translation_table[probe_type]
        except KeyError:
            #No translation found in dictionary
            stingray_probe_type = probe_type

        if stingray_probe_type in supported_probe_types:
            return stingray_probe_type
        else:
            #Raise exception here?
            logger.debug("Stingray: Probe type not found (%s)",
                            stingray_probe_type)

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

        #Configure options standard across all nodes
        probe_type = self.translate_probe_type(probe['type'])

        '''Iterate through keys fields, building request for new monitor from
        appropriate fields
        '''
        monitor_new = {'properties': {
                'type': probe_type
            }
        }

        stingray_default_options = ('delay', 'failures', 'timeout',
                                    'max_response_len', 'scope',
                                    'can_use_ssl', 'use_ssl')

        #Method implemented by host_method field in Stingray?
        option_translate_dict = {
            'probeInterval': 'delay',
            'attemptsBeforeDeactivation': 'failures',
            'failDetect': 'failures',
            'passDetectInterval': 'timeout',
        }

        for key in probe:
            if key in stingray_default_options:
                monitor_new['properties'][key] = probe[key]
            elif key in option_translate_dict:
                new_key = option_translate_dict[key]
                monitor_new['properties'][new_key] = probe[key]

        #Hack to solve https problem
        if probe['type'].lower() == 'https':
            monitor_new['properties']['use_ssl'] = 'Yes'

        #Create new probe
        self.send_request(target, 'PUT', monitor_new)

        #Configure options specific to this node type
        #Get possible config options from Stingray
        response_json = self.send_request(target, 'GET')
        response = self.response_to_dict(response_json)
        try:
            #Defaultly returns a whitespace seperated string, turn into a list
            allowed_config_options_string = \
                        response['properties']['editable_keys']
            allowed_config_options = allowed_config_options_string.split()

            try:
                options = json.loads(probe['extras'])
            except KeyError:
                options = {}

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
        '''Remove probe
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
        #??Logical naming??
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
        pool_mod = {'properties': {
             'nodes': ''
            }
        }

        #Modify dictionary and send PUT request with that dictionary
        pool_mod = self.rest_delete_from_list(target, 'nodes', node, pool_mod)
        self.send_request(target, 'PUT', pool_mod)

    def add_probe_to_server_farm(self, serverfarm, probe):
        #TODO:
        target = 'pools/' + serverfarm['id'] + '/'

        node_mod = {
            'properties': {}
        }

        self.rest_add_to_list(target, 'monitors', probe['id'], node_mod)

        self.send_request(target, 'PUT', node_mod)

    def delete_probe_from_server_farm(self, serverfarm, probe):
        '''
        '''
        target = 'pools/' + serverfarm['id'] + '/'

        node_mod = {
            'properties': {}
        }

        self.rest_delete_from_list(target, 'monitors', probe['id'], node_mod)

    def create_virtual_ip(self, vip, serverfarm):
        ''' Add the virtual IP to the traffic IP group associated with this
        serverfarm. If no traffic IP exists yet then create it with this IP.
        '''
        #Add support for masks and ports?

        target = 'flipper/' + serverfarm['id'] + '/'

        try:
            #Add IP to existing traffic Ip group
            traffic_ip_mod = {'properties': {
                'ipaddresses': '',
                }
            }
            traffic_ip_mod = self.rest_add_to_list(target, 'ipaddresses',
                                            vip['address'], traffic_ip_mod)

        except HTTPError:
            #No traffic IP group exists, create one
            traffic_ip_new = {'properties': {
                'ipaddresses': vip['address'],
                'machines': self.device_name
                }
            }
            self.send_request(target, 'PUT', traffic_ip_new)

            #hook it up to the virtual server
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

        target = 'flipper/' + serverfarm['id'] + '/'

        traffic_ip_mod = {'porperties': {
            'ipaddresses': '',
            }
        }
        traffic_ip_mod = self.rest_delete_from_list(target,
                    'ipaddresses', vip['address'], traffic_ip_mod)

        if traffic_ip_mod['properties']['ipaddresses'] == '':
            #No more VIPs left in the traffic IP group, delete the group
            self.send_request(target, 'DELETE')
        else:
            #Send request to remove VIP from traffic IP group
            self.send_request(target, 'PUT', traffic_ip_mod)

    ''' Not implemented yet
    '''

    def get_statistics(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.getStatistics(%r, %r).",
                     serverfarm, rserver)

    def create_stickiness(self, sticky):
        logger.debug("Called DummyStingrayDriver.createStickiness(%r).",
                     sticky)

    def delete_stickiness(self, sticky):
        logger.debug("Called DummyStingrayDriver.deleteStickiness(%r).",
                     sticky)

    def import_certificate_or_key(self):
        #Generic FLA licence?! Does nto seem to fit in very well with a
        #commercial system custom keys
        #SSL certificates/Licence keys?
        #No arguments to function?!?!
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
        logger.debug("Called DummyStingrayDriver"
                        ".removeSSLProxyFromVIP(%r, %r).", vip, ssl_proxy)

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

    '''Included for compatibility with other drivers.
    '''
    def create_real_server(self, rserver):
        #Create node in our terminology
        #Do we need to do anythign here?

        logger.debug("Called DummyStingrayDriver.createRServer(%r).", rserver)

    def delete_real_server(self, rserver):
        #Delete node in our terminology
        #Do we need to do anything here?

        logger.debug("Called DummyStingrayDriver.deleteRServer(%r).", rserver)
