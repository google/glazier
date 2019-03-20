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
from absl.testing import absltest


class RegistryTest(absltest.TestCase):

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
    args = [
        'HKLM', kpath, 'KeyManagementServiceName', 'kms-server.example.com']
    ra = registry.RegAdd(args, build_info)
    self.assertRaises(registry.ActionError, ra.Run)
    # bad multi args
    args = [
        ['HKLM', kpath, 'KeyManagementServiceName', 'kms-server.example.com',
         'REG_SZ'],
        ['HKLM', kpath, 'KeyManagementServiceName', 'kms-server.example.com']
    ]
    ra = registry.MultiRegAdd(args, build_info)
    self.assertRaises(registry.ActionError, ra.Run)

  def testRegistryValidation(self):
    # List not passed
    r = registry.RegAdd('String', None)
    self.assertRaises(registry.ValidationError, r.Validate)
    # To many args
    r = registry.RegAdd(['HKLM', 'SOFTWARE/fake', 'foo', 'bar', 'REG_SZ', True,
                         'baz'], None)
    self.assertRaises(registry.ValidationError, r.Validate)
    # Not enough args
    r = registry.RegAdd(['SOFTWARE/fake', 'foo', 'bar', 'REG_SZ'], None)
    self.assertRaises(registry.ValidationError, r.Validate)
    # Type error
    r = registry.RegAdd(['HKLM', 'SOFTWARE/fake', 'foo', '1', 'REG_DWORD'],
                        None)
    self.assertRaises(registry.ValidationError, r.Validate)
    # To many keys
    r = registry.RegAdd([['HKLM', 'SOFTWARE/fake', 'foo', 1, 'REG_DWORD'],
                         ['HKLM', 'SOFTWARE/boo', 'fake', 100, 'REG_DWORD']],
                        None)
    self.assertRaises(registry.ValidationError, r.Validate)
    # Valid calls
    r = registry.RegAdd(['HKLM', 'SOFTWARE\fake', 'foo', 'bar', 'REG_SZ'],
                        None)
    r.Validate()
    r = registry.MultiRegAdd([
        ['HKLM', 'SOFTWARE/fake', 'foo', 'bazzz', 'REG_SZ'],
        ['HKLM', 'SOFTWARE/boo', 'fake', 100, 'REG_DWORD']
    ], None)
    r.Validate()


if __name__ == '__main__':
  absltest.main()
