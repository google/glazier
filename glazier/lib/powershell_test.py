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
  def test_powershell_path_wpe(self, wpe):
    wpe.return_value = True
    self.assertEqual(powershell._powershell_path(),
                     powershell.constants.WINPE_POWERSHELL)

  @mock.patch.object(powershell.winpe, 'check_winpe', autospec=True)
  def test_powershell_path_host(self, wpe):
    wpe.return_value = False
    self.assertEqual(powershell._powershell_path(),
                     powershell.constants.SYS_POWERSHELL)

  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  @mock.patch.object(powershell, '_powershell_path', autospec=True)
  def test_launch_ps(self, pp, eb):
    pp.return_value = powershell.constants.SYS_POWERSHELL
    self.ps._launch_ps('-File', [self.path], [1337])
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo', '-File', self.path],
                          [1337], True)

  def test_launch_ps_op_errer(self):
    self.assertRaises(powershell.Error,
                      self.ps._launch_ps, '-Something', ['-NoExit'])

  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  @mock.patch.object(powershell, '_powershell_path', autospec=True)
  def test_launch_ps_no_log(self, pp, eb):
    pp.return_value = powershell.constants.SYS_POWERSHELL
    self.pslog = powershell.PowerShell(log=False)
    self.pslog._launch_ps('-File', [self.path])
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo', '-File', self.path],
                          None, False)

  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  @mock.patch.object(powershell, '_powershell_path', autospec=True)
  def test_launch_ps_error(self, pp, eb):
    pp.return_value = powershell.constants.SYS_POWERSHELL
    eb.side_effect = powershell.execute.Error
    self.assertRaises(powershell.Error, self.ps._launch_ps, '-File',
                      [self.path])

  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  @mock.patch.object(powershell, '_powershell_path', autospec=True)
  def test_run_command(self, pp, eb):
    pp.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.run_command(['Get-ChildItem', '-Recurse'])
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo', '-Command', 'Get-ChildItem',
                           '-Recurse'], None, True)

  @flagsaver.flagsaver
  @mock.patch.object(powershell.PowerShell, 'run_local', autospec=True)
  def test_run_resource(self, rl):
    FLAGS.resource_path = '/test/resources'
    self.fs.CreateFile('/test/resources/bin/script.ps1')
    self.ps.run_resource('bin/script.ps1', ['>>', 'out.txt'], [1337])
    rl.assert_called_with(self.ps, '/test/resources/bin/script.ps1',
                          ['>>', 'out.txt'], [1337])

  def test_get_res_path_error(self):
    self.assertRaises(powershell.Error, self.ps.run_resource,
                      'missing.ps1')

  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  @mock.patch.object(powershell, '_powershell_path', autospec=True)
  def test_run_local(self, pp, eb):
    pp.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.run_local(self.path, ['-Arg1', '-Arg2'], [1337])
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL, [
        '-NoProfile', '-NoLogo', '-File', self.path, '-Arg1',
        '-Arg2'
    ], [1337], True)

  @mock.patch.object(powershell.PowerShell, 'run_command', autospec=True)
  def test_set_execution_policy(self, rc):
    self.ps.set_execution_policy('RemoteSigned')
    rc.assert_called_with(
        self.ps, ['Set-ExecutionPolicy', '-ExecutionPolicy', 'RemoteSigned'])

  def test_set_execution_policy_error(self):
    self.assertRaises(powershell.Error, self.ps.set_execution_policy, 'Foo')

  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  @mock.patch.object(powershell, '_powershell_path', autospec=True)
  def test_start_shell(self, pp, eb):
    pp.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.start_shell()
    eb.assert_called_with(powershell.constants.SYS_POWERSHELL,
                          ['-NoProfile', '-NoLogo'])

  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  @mock.patch.object(powershell, '_powershell_path', autospec=True)
  def test_start_shell_error(self, pp, eb):
    pp.return_value = powershell.constants.SYS_POWERSHELL
    eb.side_effect = powershell.execute.Error
    self.assertRaises(powershell.Error, self.ps.start_shell)

if __name__ == '__main__':
  absltest.main()
