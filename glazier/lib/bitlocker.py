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

"""Bitlocker management functionality."""

from glazier.lib import execute
from glazier.lib import powershell

from glazier.lib import constants
from glazier.lib import errors

SUPPORTED_MODES = ['ps_tpm', 'bde_tpm']


class Error(errors.GlazierError):
  pass


class BitlockerEnableTpmError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.BITLOCKER_ENABLE_TPM_FAILED,
        message='Error while enabling TPM via Powershell')


class BitlockerActivationFailedError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.BITLOCKER_ACTIVATION_FAILED,
        message='Bitlocker activation failed')


class BitlockerUnknownModeError(Error):

  def __init__(self, mode: str):
    super().__init__(
        error_code=errors.ErrorCode.BITLOCKER_UNKNOWN_MODE,
        message=f'Unknown mode: {mode}')


class Bitlocker(object):
  """Manage Bitlocker related operations on the local host."""

  def __init__(self, mode: str):
    self._mode = mode

  def _EnableTpm(self):
    """Enable TPM mode using Powershell (Win8 +)."""
    ps = powershell.PowerShell()
    try:
      ps.RunCommand([
          '$ErrorActionPreference=\'Stop\'', ';', 'Enable-BitLocker', 'C:',
          '-TpmProtector', '-UsedSpaceOnly', '-SkipHardwareTest ', '>>',
          f'{constants.SYS_LOGS_PATH}/enable-bitlocker.txt'
      ])
      ps.RunCommand(['$ErrorActionPreference=\'Stop\'', ';',
                     'Add-BitLockerKeyProtector', 'C:',
                     '-RecoveryPasswordProtector', '>NUL'])
    except powershell.Error as e:
      raise BitlockerEnableTpmError() from e

  def Enable(self):
    """Enable bitlocker."""
    if self._mode == 'ps_tpm':
      self._EnableTpm()
    elif self._mode == 'bde_tpm':
      try:
        execute.execute_binary(
            'C:/Windows/System32/cmd.exe', [
                '/c', 'C:/Windows/System32/manage-bde.exe', '-on', 'c:', '-rp',
                '>NUL'
            ],
            shell=True)
      except execute.Error as e:
        raise BitlockerActivationFailedError() from e
    else:
      raise BitlockerUnknownModeError(self._mode)
