# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for glazier.lib.actions.registry."""

from glazier.lib.actions import registry
import mock
from google.apputils import basetest


class RegistryTest(basetest.TestCase):

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def testRun(self, winreg, build_info):
    kpath = (r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
             r'\SoftwareProtectionPlatform')
    args = [
        'HKLM', kpath, 'KeyManagementServiceName', 'kms-server.example.com',
        'REG_SZ', False
    ]
    skv = winreg.return_value.SetKeyValue
    ra = registry.RegAdd(args, build_info)
    ra.Run()
    skv.assert_called_with(
        key_path=kpath,
        key_name='KeyManagementServiceName',
        key_value='kms-server.example.com',
        key_type='REG_SZ',
        use_64bit=False)
    # registry error
    skv.side_effect = registry.registry.RegistryError
    self.assertRaises(registry.ActionError, ra.Run)
    skv.side_effect = None
    # missing arguments
    ra = registry.RegAdd(args[2:], build_info)
    self.assertRaises(registry.ActionError, ra.Run)


if __name__ == '__main__':
  basetest.main()
