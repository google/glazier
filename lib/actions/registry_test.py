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

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def testAdd(self, winreg, build_info):
    # Mock add registry keys
    kpath = (r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
             r'\SoftwareProtectionPlatform')
    args = [
        'HKLM', kpath, 'KeyManagementServiceName',
        'kms-server.example.com',
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

    # Registry error
    skv.side_effect = registry.registry.RegistryError
    self.assertRaises(registry.ActionError, ra.Run)

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def testMultiAdd(self, winreg, build_info):
    # Mock add registry keys
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

    # Missing arguments
    args = [
        'HKLM', kpath, 'KeyManagementServiceName', 'kms-server.example.com']
    ra = registry.RegAdd(args, build_info)
    self.assertRaises(registry.ActionError, ra.Run)

    args = [
        ['HKLM', kpath, 'KeyManagementServiceName', 'kms-server.example.com',
         'REG_SZ'],
        ['HKLM', kpath, 'KeyManagementServiceName', 'kms-server.example.com']
    ]
    ra = registry.MultiRegAdd(args, build_info)
    self.assertRaises(registry.ActionError, ra.Run)

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  @mock.patch.object(registry.logging, 'warn', autospec=True)
  def testDel(self, warn, winreg, build_info):
    # Variable definition
    registry.WindowsError = Exception

    # Mock delete registry keys
    kpath = (r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
             r'\SoftwareProtectionPlatform')
    args = [
        'HKLM', kpath, 'KeyManagementServiceName']
    rkv = winreg.return_value.RemoveKeyValue
    rd = registry.RegDel(args, build_info)

    # Registry error
    rkv.side_effect = registry.registry.RegistryError('Test')
    self.assertRaises(registry.ActionError, rd.Run)

    # Key not found
    err = registry.registry.RegistryError('Test', errno=2)
    rkv.side_effect = err
    rd.Run()
    warn.assert_called_with('Registry key %s not found', args)

  def testAddValidation(self):
    # List not passed
    r = registry.RegAdd('String', None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Too many args
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

    # Too many keys
    r = registry.RegAdd([['HKLM', 'SOFTWARE/fake', 'foo', 1, 'REG_DWORD'],
                         ['HKLM', 'SOFTWARE/boo', 'fake', 100, 'REG_DWORD']],
                        None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Valid calls
    r = registry.RegAdd(['HKLM', 'SOFTWARE\fake', 'foo', 'bar', 'REG_SZ'],
                        None)
    r.Validate()

  def testMultiAddValidation(self):
    # Valid calls
    r = registry.MultiRegAdd([
        ['HKLM', 'SOFTWARE/fake', 'foo', 'bazzz', 'REG_SZ'],
        ['HKLM', 'SOFTWARE/boo', 'fake', 100, 'REG_DWORD']
    ], None)
    r.Validate()

  def testDelValidation(self):
    # List not passed
    r = registry.RegDel('String', None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Too many args
    r = registry.RegDel(['HKLM', 'SOFTWARE/fake', 'foo', 'bar'], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Not enough args
    r = registry.RegDel(['SOFTWARE/fake', 'foo'], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Too many keys
    r = registry.RegDel([['HKLM', 'SOFTWARE/fake', 'foo'],
                         ['HKLM', 'SOFTWARE/boo', 'fake']],
                        None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Valid calls
    r = registry.RegDel(['HKLM', 'SOFTWARE\fake', 'foo'], None)
    r.Validate()

if __name__ == '__main__':
  absltest.main()
