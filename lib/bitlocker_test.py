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

from glazier.lib import bitlocker
import mock
from google.apputils import basetest


class BitlockerTest(basetest.TestCase):

  @mock.patch.object(
      bitlocker.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPowershell(self, ps):
    bit = bitlocker.Bitlocker(mode='ps_tpm')
    bit.Enable()
    ps.assert_has_calls([
        mock.call(mock.ANY, [
            "$ErrorActionPreference='Stop'", ';', 'Enable-BitLocker', 'C:',
            '-TpmProtector', '-UsedSpaceOnly', '-SkipHardwareTest ', '>>',
            '%s\\enable-bitlocker.txt' % bitlocker.constants.SYS_LOGS_PATH
        ]), mock.call(mock.ANY, [
            "$ErrorActionPreference='Stop'", ';', 'Add-BitLockerKeyProtector',
            'C:', '-RecoveryPasswordProtector', '>NUL'
        ])
    ])
    ps.side_effect = bitlocker.powershell.PowerShellError
    self.assertRaises(bitlocker.BitlockerError, bit.Enable)

  @mock.patch.object(bitlocker.subprocess, 'call', autospec=True)
  def testManageBde(self, call):
    bit = bitlocker.Bitlocker(mode='bde_tpm')
    call.return_value = 0
    cmdline = ('C:\\Windows\\System32\\cmd.exe /c '
               'C:\\Windows\\System32\\manage-bde.exe -on c: -rp >NUL')
    bit.Enable()
    call.assert_called_with(cmdline, shell=True)
    call.return_value = 1
    self.assertRaises(bitlocker.BitlockerError, bit.Enable)

  def testFailure(self):
    bit = bitlocker.Bitlocker(mode='unsupported')
    self.assertRaises(bitlocker.BitlockerError, bit.Enable)


if __name__ == '__main__':
  basetest.main()
