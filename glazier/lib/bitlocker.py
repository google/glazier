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

SUPPORTED_MODES = ['ps_tpm', 'bde_tpm']


class BitlockerError(Exception):
  pass


class Bitlocker(object):
  """Manage Bitlocker related operations on the local host."""

  def __init__(self, mode: str):
    self._mode = mode

  def _PsTpm(self):
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
    except powershell.PowerShellError as e:
      raise BitlockerError('Error enabling Bitlocker via Powershell: %s.' %
                           str(e)) from e

  def Enable(self):
    """Enable bitlocker."""
    if self._mode == 'ps_tpm':
      self._PsTpm()
    elif self._mode == 'bde_tpm':
      try:
        execute.execute_binary(
            'C:/Windows/System32/cmd.exe', [
                '/c', 'C:/Windows/System32/manage-bde.exe', '-on', 'c:', '-rp',
                '>NUL'
            ],
            shell=True)
      except execute.Error as e:
        raise BitlockerError(str(e)) from e
    else:
      raise BitlockerError(f'Unknown mode: {self._mode}.')
