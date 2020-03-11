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

from absl import flags
from absl.testing import absltest
from absl.testing import flagsaver

from pyfakefs import fake_filesystem
from glazier.lib import powershell
import mock

FLAGS = flags.FLAGS


class PowershellTest(absltest.TestCase):

  def setUp(self):
    super(PowershellTest, self).setUp()
    self.fs = fake_filesystem.FakeFilesystem()
    powershell.os = fake_filesystem.FakeOsModule(self.fs)
    powershell.resources.os = fake_filesystem.FakeOsModule(self.fs)
    self.path = '/resources/bin/script.ps1'
    self.fs.CreateFile(self.path)
    self.ps = powershell.PowerShell()

  @mock.patch.object(powershell.winpe, 'check_winpe', autospec=True)
  def testPowerShell(self, wpe):
    # WinPE
    wpe.return_value = True
    self.assertEqual(powershell._Powershell(),
                     powershell.constants.WINPE_POWERSHELL)

    # Host
    wpe.return_value = False
    self.assertEqual(powershell._Powershell(),
                     powershell.constants.SYS_POWERSHELL)

  def testLaunchPsOpError(self):
    self.assertRaises(powershell.PowerShellError,
                      self.ps._LaunchPs, '-Something', ['Get-ChildItem'])

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def testLaunchPsError(self, eb, path):
    path.return_value = powershell.constants.WINPE_POWERSHELL
    eb.side_effect = powershell.execute.Error
    self.assertRaises(powershell.PowerShellError,
                      self.ps._LaunchPs, '-Command', ['Get-ChildItem'])

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def testLaunchPsEcho(self, eb, path):
    path.return_value = powershell.constants.SYS_POWERSHELL
    self.psecho = powershell.PowerShell(echo_off=True)
    self.psecho._LaunchPs('-File', [self.path])
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo', '-File', self.path],
                          None, False)

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def testRunLocal(self, eb, path):
    path.return_value = powershell.constants.SYS_POWERSHELL
    args = ['-Arg1', '-Arg2']
    with self.assertRaises(powershell.PowerShellError):
      self.ps.RunLocal('/resources/missing.ps1', args=args)

    self.ps.RunLocal(self.path, args=args)
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo', '-File', self.path] + args,
                          None, True)

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def testRunCommand(self, eb, path):
    path.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.RunCommand(['Get-ChildItem', '-Recurse'])
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo', '-Command', 'Get-ChildItem',
                           '-Recurse'], None, True)

  @flagsaver.flagsaver
  @mock.patch.object(powershell.PowerShell, 'RunLocal', autospec=True)
  def testRunResource(self, launch):
    FLAGS.resource_path = '/test/resources'
    self.fs.CreateFile('/test/resources/bin/script.ps1')
    args = ['>>', 'out.txt']
    self.ps.RunResource('bin/script.ps1', args=args)
    launch.assert_called_with(self.ps, '/test/resources/bin/script.ps1', args,
                              None)
    # Not Found
    self.assertRaises(powershell.PowerShellError, self.ps.RunResource,
                      'missing.ps1', args)
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

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.PowerShell, 'RunCommand', autospec=True)
  def testSetExecutionPolicy(self, rc, path):
    path.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.SetExecutionPolicy(policy='RemoteSigned')
    rc.assert_called_with(
        self.ps, ['Set-ExecutionPolicy', '-ExecutionPolicy', 'RemoteSigned'])
    with self.assertRaisesRegex(powershell.PowerShellError,
                                'Unknown execution policy.*'):
      self.ps.SetExecutionPolicy(policy='RandomPolicy')

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def testStartShell(self, eb, path):
    path.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.StartShell()
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo'], log=True)

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def testStartShellEchoOff(self, eb, path):
    path.return_value = powershell.constants.SYS_POWERSHELL
    self.psecho = powershell.PowerShell(echo_off=True)
    self.psecho.StartShell()
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo'], log=False)

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def testStartShellError(self, eb, path):
    path.return_value = powershell.constants.WINPE_POWERSHELL
    eb.side_effect = powershell.execute.Error
    self.assertRaises(powershell.PowerShellError, self.ps.StartShell)

if __name__ == '__main__':
  absltest.main()
