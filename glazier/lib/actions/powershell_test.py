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

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import buildinfo
from glazier.lib.actions import powershell

from glazier.lib import errors


SCRIPT = '#Some-Script.ps1'
SCRIPT_PATH = r'C:\Cache\Some-Script.ps1'
ARGS = ['-Verbose', '-InformationAction', 'Continue']
COMMAND = 'Write-Verbose Foo -Verbose'
TOKENIZED_COMMAND = ['Write-Verbose', 'Foo', '-Verbose', '; exit $LASTEXITCODE']


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
    run.return_value = 0
    ps = powershell.PSScript([SCRIPT, ARGS], self.bi)
    ps.Run()
    run.assert_called_with(mock.ANY, SCRIPT_PATH, ARGS, [0])
    run.side_effect = powershell.powershell.PowerShellError
    self.assertRaises(errors.ActionError, ps.Run)
    # Cache error
    run.side_effect = None
    cache.side_effect = errors.CacheError('some/file/path')
    self.assertRaises(errors.ActionError, ps.Run)

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScriptNoShell(self, cache, ps_lib):
    """Assert Shell=False by default for mutation testing."""
    cache.return_value = SCRIPT_PATH
    ps_lib.return_value.RunLocal.return_value = 0
    powershell.PSScript([SCRIPT], self.bi).Run()
    ps_lib.assert_called_with(False, True)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScriptSuccessCodes(self, cache, run):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [1337, 1338]], self.bi)
    run.return_value = 0
    self.assertRaises(errors.ActionError, ps.Run)
    run.return_value = 1337
    ps.Run()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScriptRebootNoRetry(self, cache, run):
    cache.return_value = SCRIPT_PATH
    run.return_value = 1337
    with self.assertRaises(powershell.RestartEvent) as cm:
      powershell.PSScript([SCRIPT, ARGS, [0], [1337, 1338]], self.bi).Run()
    self.assertEqual(cm.exception.retry_on_restart, False)
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

  @mock.patch.object(
      powershell.powershell, 'PowerShell', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScriptShell(self, cache, ps_lib):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [], False, True], self.bi)
    ps_lib.return_value.RunLocal.return_value = 0
    ps.Run()
    ps_lib.assert_called_with(True, True)

  @mock.patch.object(
      powershell.powershell, 'PowerShell', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScriptLog(self, cache, ps_lib):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [], False, True, False],
                             self.bi)
    ps_lib.return_value.RunLocal.return_value = 0
    ps.Run()
    ps_lib.assert_called_with(True, False)

  @parameterized.named_parameters(
      ('command_type', 30, ARGS, [0], [1337], True, False, True),
      ('args_type', SCRIPT, '-Verbose', [0], [1337], True, False, True),
      ('success_code_type', SCRIPT, ARGS, 0, [1337], True, False, True),
      ('reboot_code_type', SCRIPT, ARGS, [0], 1337, True, False, True),
      ('retry_on_restart_type', SCRIPT, ARGS, [0], [1337], 'True', False, True),
      ('shell_type', SCRIPT, ARGS, [0], [1337], True, 'False', True),
      ('log_type', SCRIPT, ARGS, [0], [1337], True, False, 'True'))
  def testPSScriptValidateType(self, script, ps_args, success_codes,
                               reboot_codes, retry_on_restart, shell, log):
    ps = powershell.PSScript([script, ps_args, success_codes, reboot_codes,
                              retry_on_restart, shell, log], None)
    self.assertRaises(errors.ValidationError, ps.Validate)

  def testPSScriptValidateLen(self):
    ps = powershell.PSScript([], None)
    self.assertRaises(errors.ValidationError, ps.Validate)

    ps = powershell.PSScript([1, 2, 3, 4, 5, 6], None)
    self.assertRaises(errors.ValidationError, ps.Validate)

  # TODO (b/140891452): Use fail() to make an explicit assertion.
  # (go/python-tips/006)
  def testPSScriptValidate(self):
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [1337, 1338], True, False,
                              True], None)
    ps.Validate()

  @mock.patch.object(powershell, 'PSScript', autospec=True)
  def testMultiPSScript(self, psscript):
    """Valid inputs should call PSScript with the appropriate args."""
    powershell.MultiPSScript([[SCRIPT], [SCRIPT]], self.bi).Run()
    psscript.assert_has_calls(
        [mock.call([SCRIPT], self.bi),
         mock.call([SCRIPT], self.bi)],
        any_order=True)

  def testMultiPSScriptIndexError(self):
    """Missing input fields should raise IndexError."""
    with self.assertRaises(errors.ActionError):
      powershell.MultiPSScript([[]], self.bi).Run()

  def testMultiPSScriptValidate(self):
    """Valid inputs should pass validation tests."""
    powershell.MultiPSScript([[SCRIPT]], self.bi).Validate()

  def testMultiPSScriptValidateError(self):
    """String input should raise errors.ValidationError."""
    with self.assertRaises(errors.ActionError):
      powershell.MultiPSScript(SCRIPT, self.bi).Validate()

  def testMultiPSScriptValidateArgsType(self):
    """Non-list args should raise errors.ValidationError."""
    with self.assertRaises(errors.ValidationError):
      powershell.MultiPSScript([[SCRIPT], SCRIPT], self.bi).Validate()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommand(self, run):
    ps = powershell.PSCommand([COMMAND, [1337]], self.bi)
    run.return_value = 1337
    ps.Run()
    run.assert_called_with(mock.ANY, TOKENIZED_COMMAND, [1337])

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  def testPSCommandNoShell(self, ps_lib):
    """Assert Shell=False by default for mutation testing."""
    ps_lib.return_value.RunCommand.return_value = 0
    powershell.PSCommand([COMMAND], self.bi).Run()
    ps_lib.assert_called_with(False, True)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommandError(self, run):
    ps = powershell.PSCommand([COMMAND, [1337]], None)
    run.side_effect = powershell.powershell.PowerShellError
    self.assertRaises(errors.ActionError, ps.Run)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommandSuccessError(self, run):
    ps = powershell.PSCommand([COMMAND, [0]], self.bi)
    run.return_value = 1337
    self.assertRaises(errors.ActionError, ps.Run)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSCommandCache(self, cache, run):
    cache.return_value = SCRIPT_PATH
    ps = powershell.PSCommand([SCRIPT + ' -confirm:$false'], self.bi)
    run.return_value = 0
    ps.Run()
    run.assert_called_with(
        mock.ANY, [SCRIPT_PATH, '-confirm:$false', '; exit $LASTEXITCODE'], [0])
    cache.assert_called_with(mock.ANY, SCRIPT, self.bi)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSCommandCacheError(self, cache, run):
    ps = powershell.PSCommand([SCRIPT + ' -confirm:$false'], self.bi)
    run.side_effect = None
    cache.side_effect = errors.CacheError('some/file/path')
    with self.assertRaises(errors.ActionError):
      ps.Run()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommandRebootNoRetry(self, run):
    run.return_value = 1337
    with self.assertRaises(powershell.RestartEvent) as cm:
      powershell.PSCommand([COMMAND, [0], [1337, 1338]], self.bi).Run()
    self.assertEqual(cm.exception.retry_on_restart, False)
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

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  def testPSCommandShell(self, ps_lib):
    ps = powershell.PSCommand([COMMAND, [0], [], False, True], self.bi)
    ps_lib.return_value.RunCommand.return_value = 0
    ps.Run()
    ps_lib.assert_called_with(True, True)

  @mock.patch.object(
      powershell.powershell, 'PowerShell', autospec=True)
  def testPSCommandLog(self, ps_lib):
    ps = powershell.PSCommand([COMMAND, [0], [], False, True, False], self.bi)
    ps_lib.return_value.RunCommand.return_value = 0
    ps.Run()
    ps_lib.assert_called_with(True, False)

  @parameterized.named_parameters(
      ('command_type', 30, [0], [1337], True, False, True),
      ('success_code_type', COMMAND, 0, [1337], True, False, True),
      ('reboot_code_type', COMMAND, [0], 1337, True, False, True),
      ('retry_on_restart_type', COMMAND, [0], [1337], 'True', False, True),
      ('shell_type', COMMAND, [0], [1337], True, 'False', True),
      ('log_type', COMMAND, [0], [1337], True, False, 'True'))
  def testPSCommandValidateType(self, command, success_codes, reboot_codes,
                                retry_on_restart, shell, log):
    ps = powershell.PSCommand([command, success_codes, reboot_codes,
                               retry_on_restart, shell, log], None)
    self.assertRaises(errors.ValidationError, ps.Validate)

  def testPSCommandValidateNotEnough(self):
    ps = powershell.PSCommand([], None)
    self.assertRaises(errors.ValidationError, ps.Validate)

  def testPSCommandValidateTooMany(self):
    ps = powershell.PSCommand([COMMAND, [0], [1337, 1338], True, True, True,
                               True], None)
    self.assertRaises(errors.ValidationError, ps.Validate)

  # TODO (b/140891452): Use fail() to make an explicit assertion.
  # (go/python-tips/006)
  def testPSCommandValidate(self):
    ps = powershell.PSCommand([COMMAND, [0], [1337, 1338], True, False, True],
                              None)
    ps.Validate()

  @mock.patch.object(powershell, 'PSCommand', autospec=True)
  def testMultiPSCommand(self, pscommand):
    """Valid inputs should call PSCommand with the appropriate args."""
    powershell.MultiPSCommand([[COMMAND], [COMMAND]], self.bi).Run()
    pscommand.assert_has_calls(
        [mock.call([COMMAND], self.bi),
         mock.call([COMMAND], self.bi)],
        any_order=True)

  def testMultiPSCommandIndexError(self):
    """Missing input fields should raise IndexError."""
    with self.assertRaises(errors.ActionError):
      powershell.MultiPSCommand([[]], self.bi).Run()

  def testMultiPSCommandValidate(self):
    """Valid inputs should pass validation tests."""
    powershell.MultiPSCommand([[COMMAND]], self.bi).Validate()

  def testMultiPSCommandValidateType(self):
    """String input should raise errors.ValidationError."""
    with self.assertRaises(errors.ActionError):
      powershell.MultiPSCommand(COMMAND, self.bi).Validate()

  def testMultiPSCommandValidateArgsType(self):
    """Non-list args should raise errors.ValidationError."""
    with self.assertRaises(errors.ValidationError):
      powershell.MultiPSCommand([[COMMAND], COMMAND], self.bi).Validate()


if __name__ == '__main__':
  absltest.main()
