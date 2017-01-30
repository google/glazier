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

"""Tests for glazier.lib.powershell."""

from pyfakefs import fake_filesystem
from glazier.lib import powershell
import mock
from google.apputils import basetest


class PowershellTest(basetest.TestCase):

  def setUp(self):
    self.fs = fake_filesystem.FakeFilesystem()
    powershell.os = fake_filesystem.FakeOsModule(self.fs)
    powershell.resources.os = fake_filesystem.FakeOsModule(self.fs)
    self.fs.CreateFile('/resources/bin/script.ps1')
    self.ps = powershell.PowerShell()

  @mock.patch.object(powershell.subprocess, 'call', autospec=True)
  def testRunLocal(self, call):
    args = ['-Arg1', '-Arg2']
    call.return_value = 0
    with self.assertRaises(powershell.PowerShellError):
      self.ps.RunLocal('/resources/missing.ps1', args=args)

    self.ps.RunLocal('/resources/bin/script.ps1', args=args)
    cmd = [
        powershell._Powershell(), '-NoProfile', '-NoLogo', '-File',
        '/resources/bin/script.ps1', '-Arg1', '-Arg2'
    ]
    call.assert_called_with(cmd, shell=True)
    with self.assertRaises(powershell.PowerShellError):
      self.ps.RunLocal('/resources/bin/script.ps1', args=args, ok_result=[100])

  @mock.patch.object(powershell.subprocess, 'call', autospec=True)
  def testRunCommand(self, call):
    call.return_value = 0
    self.ps.RunCommand(['Get-ChildItem', '-Recurse'])
    cmd = [
        powershell._Powershell(), '-NoProfile', '-NoLogo', '-Command',
        'Get-ChildItem', '-Recurse'
    ]
    call.assert_called_with(cmd, shell=True)
    with self.assertRaises(powershell.PowerShellError):
      self.ps.RunCommand(['Get-ChildItem', '-Recurse'], ok_result=[100])

  @mock.patch.object(powershell.PowerShell, '_LaunchPs', autospec=True)
  def testRunResource(self, launch):
    self.ps.RunResource('bin/script.ps1', args=['>>', 'out.txt'], ok_result=[0])
    launch.assert_called_with = '/resources/bin/script.ps1'
    # Not Found
    self.assertRaises(powershell.PowerShellError, self.ps.RunResource,
                      'missing.ps1')
    # Validation
    self.assertRaises(
        AssertionError,
        self.ps.RunResource,
        'bin/script.ps1',
        args='not a list')
    self.assertRaises(
        AssertionError,
        self.ps.RunResource,
        'bin/script.ps1',
        args=[],
        ok_result='0')

  @mock.patch.object(powershell.subprocess, 'call', autospec=True)
  def testSetExecutionPolicy(self, call):
    call.return_value = 0
    self.ps.SetExecutionPolicy(policy='RemoteSigned')
    call.assert_called_with(
        [
            'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
            '-NoProfile', '-NoLogo', '-Command', 'Set-ExecutionPolicy',
            '-ExecutionPolicy', 'RemoteSigned'
        ],
        shell=True)
    with self.assertRaisesRegexp(powershell.PowerShellError,
                                 'Unknown execution policy.*'):
      self.ps.SetExecutionPolicy(policy='RandomPolicy')

  @mock.patch.object(powershell.subprocess, 'call', autospec=True)
  def testStartShell(self, unused_call):
    self.ps.StartShell()


if __name__ == '__main__':
  basetest.main()
