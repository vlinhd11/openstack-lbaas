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

from balancer.db import api as db_api
from balancer import exception as exp
from balancer.common import cfg, utils
from balancer import drivers

LOG = logging.getLogger(__name__)

bind_opts = [
    cfg.ListOpt('device_filters',
        default=['balancer.core.scheduler.filter_capabilities']),
    cfg.ListOpt('device_cost_functions',
        default=['balancer.core.scheduler.lbs_on']),
]


def schedule_loadbalancer(conf, lb_ref):
    conf.register_opts(bind_opts)
    device_filters = [utils.import_class(foo) for foo in conf.device_filters]
    all_devices = db_api.device_get_all(conf)
    if not all_devices:
        raise exp.DeviceNotFound
    cost_functions = []
    for fullname in conf.device_cost_functions:
        conf_name = 'device_cost_%s_weight' % fullname.rpartition('.')[-1]
        try:
            weight = getattr(conf, conf_name)
        except cfg.NoSuchOptError:
            conf.register_opt(cfg.FloatOpt(conf_name, default=1.))
            weight = getattr(conf, conf_name)
        cost_functions.append((utils.import_class(fullname), weight))
    filtered_devices = [dev for dev in all_devices
                        if all(filt(conf, lb_ref, dev)
                        for filt in device_filters)]
    if not filtered_devices:
        raise exp.NoValidDevice
    costed = []
    for dev in filtered_devices:
        w = 0.
        for cost_func, weight in cost_functions:
            w += weight * cost_func(conf, lb_ref, dev)
        costed.append((w, dev))
    costed.sort()
    return costed[0][1]


def filter_capabilities(conf, lb_ref, dev_ref):
    try:
        device_filter_capabilities = conf.device_filter_capabilities
    except cfg.NoSuchOptError:
        conf.register_opt(cfg.ListOpt('device_filter_capabilities',
                                      default=['algorithm']))
        device_filter_capabilities = conf.device_filter_capabilities
    device_driver = drivers.get_device_driver(conf, dev_ref['id'])
    capabilities = device_driver.get_capabilities()
    if capabilities is None:
        capabilities = {}
    for opt in device_filter_capabilities:
        lb_req = lb_ref.get(opt)
        if not lb_req:
            continue
        dev_caps = capabilities.get(opt + 's', [])
        if not (lb_req in dev_caps):
            LOG.debug('Device %s does not support %s "%s"', dev_ref['id'], opt,
                    lb_req)
            return False
    return True


def lbs_on(conf, lb_ref, dev_ref):
    return db_api.lb_count_active_by_device(conf, dev_ref['id'])
