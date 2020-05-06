# Lint as: python3
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

"""Tests for glazier.lib.actions.powershell."""

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import buildinfo
from glazier.lib.actions import powershell
import mock

SCRIPT = '#Some-Script.ps1'
SCRIPT_PATH = r'C:\Cache\Some-Script.ps1'
ARGS = ['-Verbose', '-InformationAction', 'Continue']
COMMAND = 'Write-Verbose Foo -Verbose'
TOKENIZED_COMMAND = ['Write-Verbose', 'Foo', '-Verbose']


class PowershellTest(parameterized.TestCase):

  def setUp(self):
    super(PowershellTest, self).setUp()
    buildinfo.constants.FLAGS.config_server = 'https://glazier/'
    self.bi = buildinfo.BuildInfo()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScript(self, cache, run):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS], self.bi)
    run.return_value = 0
    ps.Run()
    cache.assert_called_with(mock.ANY, SCRIPT, self.bi)
    run.assert_called_with(mock.ANY, SCRIPT_PATH, ARGS, [0])
    run.side_effect = powershell.powershell.PowerShellError
    self.assertRaises(powershell.ActionError, ps.Run)
    # Cache error
    run.side_effect = None
    cache.side_effect = powershell.cache.CacheError
    self.assertRaises(powershell.ActionError, ps.Run)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScriptSuccessCodes(self, cache, run):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [1337, 1338]], self.bi)
    run.return_value = 0
    self.assertRaises(powershell.ActionError, ps.Run)
    run.return_value = 1337
    ps.Run()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScriptRebootNoRetry(self, cache, run):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [1337, 1338]], self.bi)
    run.return_value = 1337
    self.assertRaises(powershell.RestartEvent, ps.Run)
    run.assert_called_with(mock.ANY, SCRIPT_PATH, ARGS, [0, 1337, 1338])

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScriptRebootRetry(self, cache, run):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [1337, 1338], True], self.bi)
    run.return_value = 1337
    self.assertRaises(powershell.RestartEvent, ps.Run)
    run.assert_called_with(mock.ANY, SCRIPT_PATH, ARGS, [0, 1337, 1338])
    cache.assert_called_with(mock.ANY, SCRIPT, self.bi)

  @parameterized.named_parameters(
      ('command_type', 30, ARGS, [0], [1337], True),
      ('args_type', SCRIPT, '-Verbose', [0], [1337], True),
      ('success_code_type', SCRIPT, ARGS, 0, [1337], True),
      ('reboot_code_type', SCRIPT, ARGS, [0], 1337, True),
      ('retry_on_restart_type', SCRIPT, ARGS, [0], [1337], 'True'))
  def testPSScriptValidateType(self, script, ps_args, success_codes,
                               reboot_codes, retry_on_restart):
    ps = powershell.PSScript(
        [script, ps_args, success_codes, reboot_codes, retry_on_restart], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)

  def testPSScriptValidateLen(self):
    ps = powershell.PSScript([], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)

    ps = powershell.PSScript([1, 2, 3, 4, 5, 6], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)

  # TODO : Use fail() to make an explicit assertion. go/pytotw/006
  def testPSScriptValidate(self):
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [1337, 1338], True], None)
    ps.Validate()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommand(self, run):
    ps = powershell.PSCommand([COMMAND, [1337]], self.bi)
    run.return_value = 1337
    ps.Run()
    run.assert_called_with(mock.ANY, TOKENIZED_COMMAND, [1337])

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommandError(self, run):
    ps = powershell.PSCommand([COMMAND, [1337]], None)
    run.side_effect = powershell.powershell.PowerShellError
    self.assertRaises(powershell.ActionError, ps.Run)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommandSuccessError(self, run):
    ps = powershell.PSCommand([COMMAND, [0]], self.bi)
    run.return_value = 1337
    self.assertRaises(powershell.ActionError, ps.Run)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSCommandCache(self, cache, run):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSCommand([SCRIPT + ' -confirm:$false'], self.bi)
    run.return_value = 0
    ps.Run()
    run.assert_called_with(mock.ANY, [SCRIPT_PATH, '-confirm:$false'], [0])
    cache.assert_called_with(mock.ANY, SCRIPT, self.bi)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSCommandCacheError(self, cache, run):
    ps = powershell.PSCommand([SCRIPT + ' -confirm:$false'], self.bi)
    run.side_effect = None
    cache.side_effect = powershell.cache.CacheError
    with self.assertRaises(powershell.ActionError):
      ps.Run()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommandRebootNoRetry(self, run):
    ps = powershell.PSCommand([COMMAND, [0], [1337, 1338]], self.bi)
    run.return_value = 1337
    self.assertRaises(powershell.RestartEvent, ps.Run)
    run.assert_called_with(mock.ANY, TOKENIZED_COMMAND, [0, 1337, 1338])

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommandRebootRetry(self, run):
    ps = powershell.PSCommand([COMMAND, [0], [1337, 1338], True], self.bi)
    run.return_value = 1337
    with self.assertRaises(powershell.RestartEvent) as cm:
      ps.Run()
    exception = cm.exception
    self.assertEqual(exception.retry_on_restart, True)
    run.assert_called_with(mock.ANY, TOKENIZED_COMMAND, [0, 1337, 1338])

  @parameterized.named_parameters(
      ('command_type', 30, [0], [1337], True),
      ('success_code_type', COMMAND, 0, [1337], True),
      ('reboot_code_type', COMMAND, [0], 1337, True),
      ('retry_on_restart_type', COMMAND, [0], [1337], 'True'))
  def testPSCommandValidateType(self, command, success_codes, reboot_codes,
                                retry_on_restart):
    ps = powershell.PSCommand(
        [command, success_codes, reboot_codes, retry_on_restart], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)

  def testPSCommandValidateNotEnough(self):
    ps = powershell.PSCommand([], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)

  def testPSCommandValidateTooMany(self):
    ps = powershell.PSCommand([COMMAND, [0], [1337, 1338], True, True], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)

  # TODO : Use fail() to make an explicit assertion. go/pytotw/006
  def testPSCommandValidate(self):
    ps = powershell.PSCommand([COMMAND, [0], [1337, 1338], True], None)
    ps.Validate()

if __name__ == '__main__':
  absltest.main()
