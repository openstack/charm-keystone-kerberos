# Copyright 2019 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function

import mock

import charm.openstack.keystone_kerberos as keystone_kerberos
import reactive.keystone_kerberos_handlers as handlers

import charms_openstack.test_utils as test_utils


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = [
            'charm.installed',
            'update-status']
        hook_set = {
            'hook': {
                'default_upgrade_charm': ('upgrade-charm',),
            },
            'when': {
                'publish_sp_fid': (
                    'keystone-fid-service-provider.connected',),
                'render_config': (
                    'keystone-fid-service-provider.available',),
            },
            'when_not': {
                'keystone_departed': (
                    'keystone-fid-service-provider.connected',),
                'assess_status': ('always.run',),
            },
        }
        # test that the hooks were registered via the
        # reactive.keystone_kerberos_handlers
        self.registered_hooks_test_helper(handlers, hook_set, defaults)


class TestKeystoneKerberosHandlers(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(
            keystone_kerberos.KeystoneKerberosCharm.release)
        self.keystone_kerberos_charm = mock.MagicMock()
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = (
            self.keystone_kerberos_charm)
        self.provide_charm_instance().__exit__.return_value = None

        self.patch_object(handlers.reactive, 'any_file_changed',
                          new=mock.MagicMock())

        self.endpoint = mock.MagicMock()

        self.protocol_name = "kerberos"
        self.kerberos_realm = "project.serverstack"
        self.kerberos_server = "freeipa.project.serverstack"
        self.kerberos_domain = "k8s"
        self.keystone_kerberos_charm.options.protocol_name = (
            self.protocol_name)
        self.keystone_kerberos_charm.options.kerberos_realm = (
            self.kerberos_realm)
        self.keystone_kerberos_charm.options.kerberos_server = (
            self.kerberos_server)
        self.keystone_kerberos_charm.options.kerberos_domain = (
            self.kerberos_domain)

        self.all_joined_units = []
        for i in range(0, 2):
            unit = mock.MagicMock()
            unit.name = "keystone-{}".format(i)
            unit.received = {"hostname": unit.name}
            self.all_joined_units.append(unit)

    def test_keystone_departed(self):
        handlers.keystone_departed()
        self.keystone_kerberos_charm.remove_config.assert_called_once_with()

    def test_publish_sp_fid(self):
        handlers.publish_sp_fid(self.endpoint)
        self.endpoint.publish.assert_called_once_with(
            self.protocol_name, self.kerberos_server)

    def test_render_config(self):
        # No restart
        self.any_file_changed.return_value = False
        (self.keystone_kerberos_charm
            .configuration_complete.return_value) = True

        handlers.render_config(self.endpoint)
        self.keystone_kerberos_charm.render_config.assert_called_once_with(
            self.endpoint)
        self.endpoint.request_restart.assert_not_called()

        # Restart
        self.any_file_changed.return_value = True
        handlers.render_config(self.endpoint)
        self.endpoint.request_restart.assert_called_once_with()

    def test_assess_status(self):
        handlers.assess_status()
        self.keystone_kerberos_charm.assess_status.assert_called_once_with()
