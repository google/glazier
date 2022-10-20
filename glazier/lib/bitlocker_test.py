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
"""Tests for glazier.lib.bitlocker."""

from unittest import mock

from absl.testing import absltest
from glazier.lib import bitlocker
from glazier.lib import execute
from glazier.lib import powershell
from glazier.lib import test_utils

from glazier.lib import constants


class BitlockerTest(test_utils.GlazierTestCase):

  @mock.patch.object(
      bitlocker.powershell.PowerShell, 'RunCommand', autospec=True)
  def test_enable_tpm_error(self, mock_runcommand):
    bit = bitlocker.Bitlocker(mode='ps_tpm')
    bit.Enable()
    mock_runcommand.assert_has_calls([
        mock.call(mock.ANY, [
            "$ErrorActionPreference='Stop'", ';', 'Enable-BitLocker', 'C:',
            '-TpmProtector', '-UsedSpaceOnly', '-SkipHardwareTest ', '>>',
            f'{constants.SYS_LOGS_PATH}/enable-bitlocker.txt'
        ]),
        mock.call(mock.ANY, [
            "$ErrorActionPreference='Stop'", ';', 'Add-BitLockerKeyProtector',
            'C:', '-RecoveryPasswordProtector', '>NUL'
        ])
    ])
    mock_runcommand.side_effect = powershell.PowerShellExecutionError
    with self.assert_raises_with_validation(bitlocker.BitlockerEnableTpmError):
      bit.Enable()

  @mock.patch.object(execute, 'execute_binary', autospec=True)
  def test_enable_execute_binary_error(self, mock_execute_binary):
    bit = bitlocker.Bitlocker(mode='bde_tpm')
    mock_execute_binary.return_value = 0
    bit.Enable()
    mock_execute_binary.assert_called_with(
        'C:/Windows/System32/cmd.exe', [
            '/c', 'C:/Windows/System32/manage-bde.exe', '-on', 'c:', '-rp',
            '>NUL'
        ],
        shell=True)
    mock_execute_binary.side_effect = execute.ExecError('some_command')
    with self.assert_raises_with_validation(
        bitlocker.BitlockerActivationFailedError):
      bit.Enable()

  def test_enable_unknown_mode(self):
    bit = bitlocker.Bitlocker(mode='unsupported')
    with self.assert_raises_with_validation(
        bitlocker.BitlockerUnknownModeError):
      bit.Enable()


if __name__ == '__main__':
  absltest.main()
