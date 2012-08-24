# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC.
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

from balancer.drivers.base_driver import BaseDriver

logger = logging.getLogger(__name__)


class DummyStingrayDriver(BaseDriver):
    def import_certificate_or_key(self):
        logger.debug("Called DummyStingrayDriver.importCertificatesAndKeys().")

    def create_ssl_proxy(self, ssl_proxy):
        logger.debug("Called DummyStingrayDriver.createSSLProxy(%r).", ssl_proxy)

    def delete_ssl_proxy(self, ssl_proxy):
        logger.debug("Called DummyStingrayDriver.deleteSSLProxy(%r).", ssl_proxy)

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
        logger.debug("Called DummyStingrayDriver.activateRServerGlobal(%r).", rserver)

    def suspend_real_server(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.suspendRServer(%r, %r).",
                     serverfarm, rserver)

    def suspend_real_server_global(self, rserver):
        logger.debug("Called DummyStingrayDriver.suspendRServerGlobal(%r).", rserver)

    def create_probe(self, probe):
        logger.debug("Called DummyStingrayDriver.createProbe(%r).", probe)

    def delete_probe(self, probe):
        logger.debug("Called DummyStingrayDriver.deleteProbe(%r).", probe)

    def create_server_farm(self, serverfarm, predictor):
        logger.debug("Called DummyStingrayDriver.createServerFarm(%r).", serverfarm)

    def delete_server_farm(self, serverfarm):
        logger.debug("Called DummyStingrayDriver.deleteServerFarm(%r).", serverfarm)

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
        logger.debug("Called DummyStingrayDriver.createStickiness(%r).", sticky)

    def delete_stickiness(self, sticky):
        logger.debug("Called DummyStingrayDriver.deleteStickiness(%r).", sticky)

    def create_virtual_ip(self, vip, serverfarm):
        logger.debug("Called DummyStingrayDriver.createVIP(%r, %r).",
                     vip, serverfarm)

    def delete_virtual_ip(self, vip):
        logger.debug("Called DummyStingrayDriver.deleteVIP(%r).", vip)

    def get_statistics(self, serverfarm, rserver):
        logger.debug("Called DummyStingrayDriver.getStatistics(%r, %r).",
                     serverfarm, rserver)
