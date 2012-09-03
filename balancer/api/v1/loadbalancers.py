# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from openstack.common import wsgi

from balancer.api import utils
from balancer.core import api as core_api
from balancer.db import api as db_api

LOG = logging.getLogger(__name__)


class Controller(object):
    def __init__(self, conf):
        LOG.debug("Creating loadbalancers controller with config:"
                                                "loadbalancers.py %s", conf)
        self.conf = conf

    def findLBforVM(self, req, vm_id):
        LOG.debug("Got index request. Request: %s", req)
        tenant_id = req.headers.get('X-Tenant-Id', "")
        params = {}
        params['vm_id'] = vm_id
        params['tenant_id'] = tenant_id
        result = core_api.lb_find_for_vm(self.conf, vm_id)
        return {'loadbalancers': result}

    def index(self, req):
        LOG.debug("Got index request. Request: %s", req)
        tenant_id = req.headers.get('X-Tenant-Id', "")
        result = core_api.lb_get_index(self.conf, tenant_id)
        return {'loadbalancers': result}

    @utils.http_success_code(202)
    def create(self, req, body):
        LOG.debug("Got create request. Request: %s", req)
        #here we need to decide which device should be used
        params = body.copy()
        LOG.debug("Headers: %s", req.headers)
        # We need to create LB object and return its id
        tenant_id = req.headers.get('X-Tenant-Id', "")
        params['tenant_id'] = tenant_id
        lb_id = core_api.create_lb(self.conf, params)
        return {'loadbalancer': {'id': lb_id}}

    @utils.http_success_code(204)
    def delete(self, req, id):
        LOG.debug("Got delete request. Request: %s", req)
        core_api.delete_lb(self.conf, id)

    def show(self, req, id):
        LOG.debug("Got loadbalancerr info request. Request: %s", req)
        result = core_api.lb_get_data(self.conf, id)
        return {'loadbalancer': result}

    def details(self, req, id):
        LOG.debug("Got loadbalancerr info request. Request: %s", req)
        result = core_api.lb_show_details(self.conf, id)
        return result

    @utils.http_success_code(202)
    def update(self, req, id, body):
        LOG.debug("Got update request. Request: %s", req)
        core_api.update_lb(self.conf, id, body)
        return {'loadbalancer': {'id': id}}


def create_resource(conf):
    """Loadbalancers resource factory method"""
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer()
    return wsgi.Resource(Controller(conf), deserializer, serializer)
