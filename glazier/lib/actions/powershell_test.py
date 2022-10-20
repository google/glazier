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
from glazier.lib import cache
from glazier.lib import events
from glazier.lib import test_utils
from glazier.lib.actions import powershell

SCRIPT = '#Some-Script.ps1'
SCRIPT_PATH = r'C:\Cache\Some-Script.ps1'
ARGS = ['-Verbose', '-InformationAction', 'Continue']
COMMAND = 'Write-Verbose Foo -Verbose'
TOKENIZED_COMMAND = ['Write-Verbose', 'Foo', '-Verbose', '; exit $LASTEXITCODE']


class PowershellTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(PowershellTest, self).setUp()
    buildinfo.constants.FLAGS.config_server = 'https://glazier/'
    self.bi = buildinfo.BuildInfo()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_script(self, mock_cachefromline, mock_runlocal):

    mock_cachefromline.return_value = SCRIPT_PATH
    mock_runlocal.return_value = 0
    ps = powershell.PSScript([SCRIPT, ARGS], self.bi)
    ps.Run()
    mock_runlocal.assert_called_with(mock.ANY, SCRIPT_PATH, ARGS, [0])
    mock_runlocal.side_effect = powershell.powershell.InvalidPathError(
        'some_path')
    with self.assert_raises_with_validation(powershell.ActionError):
      ps.Run()

    # Cache error
    mock_runlocal.side_effect = None
    mock_cachefromline.side_effect = cache.CacheError('some/file/path')
    with self.assert_raises_with_validation(powershell.ActionError):
      ps.Run()

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_script_no_shell(self, mock_cachefromline, mock_powershell):
    """Assert Shell=False by default for mutation testing."""
    mock_cachefromline.return_value = SCRIPT_PATH
    mock_powershell.return_value.RunLocal.return_value = 0
    powershell.PSScript([SCRIPT], self.bi).Run()
    mock_powershell.assert_called_with(False, True)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_script_success_codes(self, mock_cachefromline, mock_runlocal):
    mock_cachefromline.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [1337, 1338]], self.bi)
    mock_runlocal.return_value = 0
    with self.assert_raises_with_validation(powershell.ActionError):
      ps.Run()
    mock_runlocal.return_value = 1337
    ps.Run()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_script_reboot_no_retry(self, mock_cachefromline, mock_runlocal):
    mock_cachefromline.return_value = SCRIPT_PATH
    mock_runlocal.return_value = 1337
    with self.assert_raises_with_validation(events.RestartEvent) as cm:
      powershell.PSScript([SCRIPT, ARGS, [0], [1337, 1338]], self.bi).Run()
    self.assertEqual(cm.exception.retry_on_restart, False)
    mock_runlocal.assert_called_with(mock.ANY, SCRIPT_PATH, ARGS,
                                     [0, 1337, 1338])

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_script_reboot_retry(self, mock_cachefromline, mock_runlocal):
    mock_cachefromline.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [1337, 1338], True], self.bi)
    mock_runlocal.return_value = 1337
    with self.assert_raises_with_validation(events.RestartEvent):
      ps.Run()
    mock_runlocal.assert_called_with(mock.ANY, SCRIPT_PATH, ARGS,
                                     [0, 1337, 1338])
    mock_cachefromline.assert_called_with(mock.ANY, SCRIPT, self.bi)

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_script_shell(self, mock_cachefromline, mock_powershell):
    mock_cachefromline.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [], False, True], self.bi)
    mock_powershell.return_value.RunLocal.return_value = 0
    ps.Run()
    mock_powershell.assert_called_with(True, True)

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_script_log(self, mock_cachefromline, mock_powershell):
    mock_cachefromline.return_value = SCRIPT_PATH
    ps = powershell.PSScript([SCRIPT, ARGS, [0], [], False, True, False],
                             self.bi)
    mock_powershell.return_value.RunLocal.return_value = 0
    ps.Run()
    mock_powershell.assert_called_with(True, False)

  @parameterized.named_parameters(
      ('command_type', 30, ARGS, [0], [1337], True, False, True),
      ('args_type', SCRIPT, '-Verbose', [0], [1337], True, False, True),
      ('success_code_type', SCRIPT, ARGS, 0, [1337], True, False, True),
      ('reboot_code_type', SCRIPT, ARGS, [0], 1337, True, False, True),
      ('retry_on_restart_type', SCRIPT, ARGS, [0], [1337], 'True', False, True),
      ('shell_type', SCRIPT, ARGS, [0], [1337], True, 'False', True),
      ('log_type', SCRIPT, ARGS, [0], [1337], True, False, 'True'))
  def test_ps_script_validate_type(self, script, ps_args, success_codes,
                                   reboot_codes, retry_on_restart, shell, log):
    ps = powershell.PSScript([
        script, ps_args, success_codes, reboot_codes, retry_on_restart, shell,
        log
    ], None)
    with self.assert_raises_with_validation(powershell.ValidationError):
      ps.Validate()

  def test_ps_script_validate_len(self):
    ps = powershell.PSScript([], None)
    with self.assert_raises_with_validation(powershell.ValidationError):
      ps.Validate()

    ps = powershell.PSScript([1, 2, 3, 4, 5, 6], None)
    with self.assert_raises_with_validation(powershell.ValidationError):
      ps.Validate()

  # TODO(b/140891452): Use fail() to make an explicit assertion.
  # (go/python-tips/006)
  def test_ps_script_validate(self):
    ps = powershell.PSScript(
        [SCRIPT, ARGS, [0], [1337, 1338], True, False, True], None)
    ps.Validate()

  @mock.patch.object(powershell, 'PSScript', autospec=True)
  def test_multi_ps_script(self, mock_psscript):
    """Valid inputs should call PSScript with the appropriate args."""
    powershell.MultiPSScript([[SCRIPT], [SCRIPT]], self.bi).Run()
    mock_psscript.assert_has_calls(
        [mock.call([SCRIPT], self.bi),
         mock.call([SCRIPT], self.bi)],
        any_order=True)

  def test_multi_ps_script_index_error(self):
    """Missing input fields should raise IndexError."""
    with self.assert_raises_with_validation(powershell.ActionError):
      powershell.MultiPSScript([[]], self.bi).Run()

  def test_multi_ps_script_validate(self):
    """Valid inputs should pass validation tests."""
    powershell.MultiPSScript([[SCRIPT]], self.bi).Validate()

  def test_multi_ps_script_validate_error(self):
    """String input should raise ValidationError."""
    with self.assert_raises_with_validation(powershell.ActionError):
      powershell.MultiPSScript(SCRIPT, self.bi).Validate()

  def test_multi_ps_script_validate_args_type(self):
    """Non-list args should raise ValidationError."""
    with self.assert_raises_with_validation(powershell.ValidationError):
      powershell.MultiPSScript([[SCRIPT], SCRIPT], self.bi).Validate()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def test_ps_command(self, mock_runcommand):
    ps = powershell.PSCommand([COMMAND, [1337]], self.bi)
    mock_runcommand.return_value = 1337
    ps.Run()
    mock_runcommand.assert_called_with(mock.ANY, TOKENIZED_COMMAND, [1337])

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  def test_ps_command_no_shell(self, mock_powershell):
    """Assert Shell=False by default for mutation testing."""
    mock_powershell.return_value.RunCommand.return_value = 0
    powershell.PSCommand([COMMAND], self.bi).Run()
    mock_powershell.assert_called_with(False, True)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def test_ps_command_success_error(self, mock_runcommand):
    ps = powershell.PSCommand([COMMAND, [0]], self.bi)
    mock_runcommand.return_value = 1337
    with self.assert_raises_with_validation(powershell.ActionError):
      ps.Run()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_command_cache(self, mock_cachefromline, mock_runcommand):
    mock_cachefromline.return_value = SCRIPT_PATH
    ps = powershell.PSCommand([SCRIPT + ' -confirm:$false'], self.bi)
    mock_runcommand.return_value = 0
    ps.Run()
    mock_runcommand.assert_called_with(
        mock.ANY, [SCRIPT_PATH, '-confirm:$false', '; exit $LASTEXITCODE'], [0])
    mock_cachefromline.assert_called_with(mock.ANY, SCRIPT, self.bi)

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def test_ps_command_cache_error(self, mock_cachefromline, mock_runcommand):
    ps = powershell.PSCommand([SCRIPT + ' -confirm:$false'], self.bi)
    mock_runcommand.side_effect = None
    mock_cachefromline.side_effect = cache.CacheError('some/file/path')
    with self.assert_raises_with_validation(powershell.ActionError):
      ps.Run()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def test_ps_command_reboot_no_retry(self, mock_runcommand):
    mock_runcommand.return_value = 1337
    with self.assert_raises_with_validation(events.RestartEvent) as cm:
      powershell.PSCommand([COMMAND, [0], [1337, 1338]], self.bi).Run()
    self.assertEqual(cm.exception.retry_on_restart, False)
    mock_runcommand.assert_called_with(mock.ANY, TOKENIZED_COMMAND,
                                       [0, 1337, 1338])

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def test_ps_command_reboot_retry(self, mock_runcommand):
    ps = powershell.PSCommand([COMMAND, [0], [1337, 1338], True], self.bi)
    mock_runcommand.return_value = 1337
    with self.assert_raises_with_validation(events.RestartEvent) as cm:
      ps.Run()
    exception = cm.exception
    self.assertEqual(exception.retry_on_restart, True)
    mock_runcommand.assert_called_with(mock.ANY, TOKENIZED_COMMAND,
                                       [0, 1337, 1338])

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  def test_ps_command_shell(self, mock_powershell):
    ps = powershell.PSCommand([COMMAND, [0], [], False, True], self.bi)
    mock_powershell.return_value.RunCommand.return_value = 0
    ps.Run()
    mock_powershell.assert_called_with(True, True)

  @mock.patch.object(powershell.powershell, 'PowerShell', autospec=True)
  def test_ps_command_log(self, mock_powershell):
    ps = powershell.PSCommand([COMMAND, [0], [], False, True, False], self.bi)
    mock_powershell.return_value.RunCommand.return_value = 0
    ps.Run()
    mock_powershell.assert_called_with(True, False)

  @parameterized.named_parameters(
      ('command_type', 30, [0], [1337], True, False, True),
      ('success_code_type', COMMAND, 0, [1337], True, False, True),
      ('reboot_code_type', COMMAND, [0], 1337, True, False, True),
      ('retry_on_restart_type', COMMAND, [0], [1337], 'True', False, True),
      ('shell_type', COMMAND, [0], [1337], True, 'False', True),
      ('log_type', COMMAND, [0], [1337], True, False, 'True'))
  def test_ps_command_validate_type(self, command, success_codes, reboot_codes,
                                    retry_on_restart, shell, log):
    ps = powershell.PSCommand(
        [command, success_codes, reboot_codes, retry_on_restart, shell, log],
        None)
    with self.assert_raises_with_validation(powershell.ValidationError):
      ps.Validate()

  def test_ps_command_validate_not_enough(self):
    ps = powershell.PSCommand([], None)
    with self.assert_raises_with_validation(powershell.ValidationError):
      ps.Validate()

  def test_ps_command_validate_too_many(self):
    ps = powershell.PSCommand(
        [COMMAND, [0], [1337, 1338], True, True, True, True], None)
    with self.assert_raises_with_validation(powershell.ValidationError):
      ps.Validate()

  # TODO (b/140891452): Use fail() to make an explicit assertion.
  # (go/python-tips/006)
  def test_ps_command_validate(self):
    ps = powershell.PSCommand([COMMAND, [0], [1337, 1338], True, False, True],
                              None)
    ps.Validate()

  @mock.patch.object(powershell, 'PSCommand', autospec=True)
  def test_multi_ps_command(self, mock_pscommand):
    """Valid inputs should call PSCommand with the appropriate args."""
    powershell.MultiPSCommand([[COMMAND], [COMMAND]], self.bi).Run()
    mock_pscommand.assert_has_calls(
        [mock.call([COMMAND], self.bi),
         mock.call([COMMAND], self.bi)],
        any_order=True)

  def test_multi_ps_command_index_error(self):
    """Missing input fields should raise IndexError."""
    with self.assert_raises_with_validation(powershell.ActionError):
      powershell.MultiPSCommand([[]], self.bi).Run()

  def test_multi_ps_command_validate(self):
    """Valid inputs should pass validation tests."""
    powershell.MultiPSCommand([[COMMAND]], self.bi).Validate()

  def test_multi_ps_command_validate_type(self):
    """String input should raise ValidationError."""
    with self.assert_raises_with_validation(powershell.ActionError):
      powershell.MultiPSCommand(COMMAND, self.bi).Validate()

  def test_multi_ps_command_validate_args_type(self):
    """Non-list args should raise ValidationError."""
    with self.assert_raises_with_validation(powershell.ValidationError):
      powershell.MultiPSCommand([[COMMAND], COMMAND], self.bi).Validate()


if __name__ == '__main__':
  absltest.main()
