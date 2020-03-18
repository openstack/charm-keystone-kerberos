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

import charms_openstack.test_utils as test_utils

import charm.openstack.keystone_kerberos as keystone_kerberos


def FakeConfig(init_dict):

    def _config(key=None):
        return init_dict[key] if key else init_dict

    return _config


def FakeResourceGet(init_dict):

    def _config(key=None):
        return init_dict[key] if key else init_dict

    return _config


class Helper(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(
            keystone_kerberos.KeystoneKerberosCharm.release)

        self.endpoint = mock.MagicMock()

        self.kerberos_realm = "project.serverstack"
        self.kerberos_server = "freeipa.project.serverstack"
        self.kerberos_domain = "k8s"
        self.test_config = {
            "kerberos-realm": self.kerberos_realm,
            "kerberos-server": self.kerberos_server,
            "kerberos-domain": self.kerberos_domain,
        }
        self.resources = {
            "keystone_keytab": "/path/to/keystone.keytab",
        }
        self.patch_object(keystone_kerberos.hookenv, 'config',
                          side_effect=FakeConfig(self.test_config))
        self.patch_object(keystone_kerberos.hookenv, 'resource_get',
                          side_effect=FakeResourceGet(self.resources))
        self.patch_object(
            keystone_kerberos.hookenv, 'application_version_set')
        self.patch_object(keystone_kerberos.hookenv, 'status_set')
        self.patch_object(keystone_kerberos.ch_host, 'mkdir')
        self.patch_object(keystone_kerberos.core.templating, 'render')

        self.template_loader = mock.MagicMock()
        self.patch_object(keystone_kerberos.os_templating, 'get_loader',
                          return_value=self.template_loader)
        self.patch_object(
            keystone_kerberos.KeystoneKerberosCharm,
            'application_version',
            return_value="1.0.0")

        self.patch_object(
            keystone_kerberos.KeystoneKerberosCharm, 'render_configs')
        self.patch_object(keystone_kerberos, 'os')
        self.patch_object(keystone_kerberos, 'shutil')

        self.patch(
            "builtins.open", new_callable=mock.mock_open(), name="open")
        self.file = mock.MagicMock()
        self.fileobj = mock.MagicMock()
        self.fileobj.__enter__.return_value = self.file
        self.open.return_value = self.fileobj


class TestKeystoneKerberosConfigurationAdapter(Helper):

    def setUp(self):
        super().setUp()
        self.protocol_name = "kerberos"

    def test_keytab_path(self):
        self.os.path.exists.return_value = True
        kkca = keystone_kerberos.KeystoneKerberosConfigurationAdapter()
        self.assertEqual(
            kkca.keytab_path, self.resources['keystone_keytab'])

    def test_protocol_name(self):
        kkca = keystone_kerberos.KeystoneKerberosConfigurationAdapter()
        self.assertEqual(
            kkca.protocol_name, self.protocol_name)


class TestKeystoneKerberosCharm(Helper):

    def setUp(self):
        super().setUp()
        self.patch_object(
            keystone_kerberos.KeystoneKerberosConfigurationAdapter,
            'keytab_path')
        self.keytab_path.return_value = self.resources["keystone_keytab"]
        self.keytab_path.__bool__.return_value = True

    def test_configuration_complete(self):
        kk = keystone_kerberos.KeystoneKerberosCharm()
        self.assertTrue(kk.configuration_complete())

        # One option not ready
        self.keytab_path.__bool__.return_value = False
        self.assertFalse(kk.configuration_complete())

    def test_custom_assess_status_check(self):
        kk = keystone_kerberos.KeystoneKerberosCharm()
        self.assertEqual(
            kk.custom_assess_status_check(),
            (None, None))

    def test_render_config(self):
        kk = keystone_kerberos.KeystoneKerberosCharm()
        kk.render_config()
        self.assertEqual(self.render_configs.call_count, 1)
        self.assertEqual(self.render.call_count, 2)

    def test_remove_config(self):
        self.os.path.exists.return_value = True
        kk = keystone_kerberos.KeystoneKerberosCharm()
        kk.remove_config()
        self.assertEqual(self.os.path.exists.call_count, 3)
        self.assertEqual(self.os.unlink.call_count, 3)
