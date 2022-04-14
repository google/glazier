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

import logging
import subprocess

from glazier.lib import powershell

from glazier.lib import constants

SUPPORTED_MODES = ['ps_tpm', 'bde_tpm']


class BitlockerError(Exception):
  pass


class Bitlocker(object):
  """Manage Bitlocker related operations on the local host."""

  def __init__(self, mode: str):
    self._mode = mode

  def _LaunchSubproc(self, command: str):
    """Launch a subprocess.

    Args:
      command: A command string to pass to subprocess.call()

    Raises:
      BitlockerError: An unexpected exit code from manage-bde.
    """
    logging.info('Running BitLocker command: %s', command)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      raise BitlockerError('Unexpected exit code from Bitlocker: %s.' %
                           str(exit_code))

  def _PsTpm(self):
    """Enable TPM mode using Powershell (Win8 +)."""
    ps = powershell.PowerShell()
    try:
      ps.RunCommand(['$ErrorActionPreference=\'Stop\'', ';', 'Enable-BitLocker',
                     'C:', '-TpmProtector', '-UsedSpaceOnly',
                     '-SkipHardwareTest ', '>>',
                     r'%s\enable-bitlocker.txt' % constants.SYS_LOGS_PATH])
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
      self._LaunchSubproc(r'C:\Windows\System32\cmd.exe /c '
                          r'C:\Windows\System32\manage-bde.exe -on c: -rp '
                          '>NUL')
    else:
      raise BitlockerError('Unknown mode: %s.' % self._mode)
