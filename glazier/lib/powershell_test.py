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

from unittest import mock

from absl import flags
from absl.testing import absltest
from absl.testing import flagsaver

from glazier.lib import powershell
from glazier.lib import test_utils

FLAGS = flags.FLAGS


class PowershellTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(PowershellTest, self).setUp()

    self.path = self.create_tempfile(file_path='script.ps1')
    self.ps = powershell.PowerShell()

  @mock.patch.object(powershell.winpe, 'check_winpe', autospec=True)
  def test_power_shell(self, mock_check_winpe):
    # WinPE
    mock_check_winpe.return_value = True
    self.assertEqual(powershell._Powershell(),
                     powershell.constants.WINPE_POWERSHELL)

    # Host
    mock_check_winpe.return_value = False
    self.assertEqual(powershell._Powershell(),
                     powershell.constants.SYS_POWERSHELL)

  def test_launch_ps_op_error(self):
    with self.assert_raises_with_validation(
        powershell.UnsupportedParameterError):
      self.ps._LaunchPs('-Something', ['Get-ChildItem'])

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def test_launch_ps_error(self, mock_execute_binary, mock_powershell):
    mock_powershell.return_value = powershell.constants.WINPE_POWERSHELL
    mock_execute_binary.side_effect = powershell.execute.ExecError(
        'some_command')
    with self.assert_raises_with_validation(
        powershell.PowerShellExecutionError):
      self.ps._LaunchPs('-Command', ['Get-ChildItem'])

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def test_launch_ps_silent(self, mock_execute_binary, mock_powershell):
    mock_powershell.return_value = powershell.constants.SYS_POWERSHELL
    self.pssilent = powershell.PowerShell(log=False)
    self.pssilent._LaunchPs('-File', [self.path])
    mock_execute_binary.assert_called_with(
        powershell.constants.SYS_POWERSHELL,
        ['-NoProfile', '-NoLogo', '-File', self.path], None, False, False)

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def test_run_local(self, mock_execute_binary, mock_powershell):
    mock_powershell.return_value = powershell.constants.SYS_POWERSHELL
    args = ['-Arg1', '-Arg2']
    with self.assert_raises_with_validation(powershell.InvalidPathError):
      self.ps.RunLocal('/resources/missing.ps1', args=args)

    self.ps.RunLocal(self.path, args=args)
    mock_execute_binary.assert_called_with(
        powershell.constants.SYS_POWERSHELL,
        ['-NoProfile', '-NoLogo', '-File', self.path] + args, None, False, True)

  def test_run_local_validate(self):
    with self.assert_raises_with_validation(AssertionError):
      self.ps.RunLocal(self.path, args='not a list')

    with self.assert_raises_with_validation(AssertionError):
      self.ps.RunLocal(self.path, args=[], ok_result='0')

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def test_run_command(self, mock_execute_binary, mock_powershell):
    mock_powershell.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.RunCommand(['Get-ChildItem', '-Recurse'])
    mock_execute_binary.assert_called_with(
        powershell.constants.SYS_POWERSHELL,
        ['-NoProfile', '-NoLogo', '-Command', 'Get-ChildItem', '-Recurse'],
        None, False, True)

  def test_run_command_validate(self):
    with self.assert_raises_with_validation(AssertionError):
      self.ps.RunCommand(self.path)

    with self.assert_raises_with_validation(AssertionError):
      self.ps.RunCommand([self.path], ok_result='0')

  @flagsaver.flagsaver
  @mock.patch.object(powershell.PowerShell, 'RunLocal', autospec=True)
  def test_run_resource(self, mock_runlocal):
    resource_dir = self.create_tempdir()
    FLAGS.resource_path = resource_dir.full_path
    script_path = resource_dir.create_file(file_path='bin/script.ps1').full_path
    args = ['>>', 'out.txt']
    self.ps.RunResource('bin/script.ps1', args=args)
    mock_runlocal.assert_called_with(self.ps, script_path, args, None)

    # Not Found
    with self.assert_raises_with_validation(powershell.InvalidPathError):
      self.ps.RunResource('missing.ps1', args)

  @flagsaver.flagsaver
  def test_run_resource_validate(self):

    resource_dir = self.create_tempdir()
    FLAGS.resource_path = resource_dir.full_path
    resource_dir.create_file(file_path='bin/script.ps1')

    with self.assert_raises_with_validation(AssertionError):
      self.ps.RunResource('bin/script.ps1', args='not a list')

    with self.assert_raises_with_validation(AssertionError):
      self.ps.RunResource('bin/script.ps1', args=[], ok_result='0')

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.PowerShell, 'RunCommand', autospec=True)
  def test_set_execution_policy(self, mock_runcommand, mock_powershell):
    mock_powershell.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.SetExecutionPolicy(policy='RemoteSigned')
    mock_runcommand.assert_called_with(
        self.ps, ['Set-ExecutionPolicy', '-ExecutionPolicy', 'RemoteSigned'])
    with self.assertRaisesRegex(powershell.UnsupportedExecutionPolicyError,
                                'Unsupported execution policy.*'):
      self.ps.SetExecutionPolicy(policy='RandomPolicy')

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def test_start_shell(self, mock_execute_binary, mock_powershell):
    mock_powershell.return_value = powershell.constants.SYS_POWERSHELL
    self.ps.StartShell()
    mock_execute_binary.assert_called_with(
        powershell.constants.SYS_POWERSHELL, ['-NoProfile', '-NoLogo'],
        shell=False,
        log=True)

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def test_start_shell_shell(self, mock_execute_binary, mock_powershell):
    mock_powershell.return_value = powershell.constants.SYS_POWERSHELL
    self.psshell = powershell.PowerShell(shell=True)
    self.psshell.StartShell()
    mock_execute_binary.assert_called_with(
        powershell.constants.SYS_POWERSHELL, ['-NoProfile', '-NoLogo'],
        shell=True,
        log=True)

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def test_start_shell_silent(self, mock_execute_binary, mock_powershell):
    mock_powershell.return_value = powershell.constants.SYS_POWERSHELL
    self.pssilent = powershell.PowerShell(log=False)
    self.pssilent.StartShell()
    mock_execute_binary.assert_called_with(
        powershell.constants.SYS_POWERSHELL, ['-NoProfile', '-NoLogo'],
        shell=False,
        log=False)

  @mock.patch.object(powershell, '_Powershell', autospec=True)
  @mock.patch.object(powershell.execute, 'execute_binary', autospec=True)
  def test_start_shell_error(self, mock_execute_binary, mock_powershell):
    mock_powershell.return_value = powershell.constants.WINPE_POWERSHELL
    mock_execute_binary.side_effect = powershell.execute.ExecError(
        'some_command')
    with self.assert_raises_with_validation(
        powershell.PowerShellExecutionError):
      self.ps.StartShell()


if __name__ == '__main__':
  absltest.main()
