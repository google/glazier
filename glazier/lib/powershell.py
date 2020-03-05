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

"""Run scripts with Windows Powershell."""

import os
from typing import List, Optional, Text

from glazier.lib import constants
from glazier.lib import execute
from glazier.lib import resources
from glazier.lib import winpe


class Error(Exception):
  pass


def _powershell_path() -> Text:
  path = constants.SYS_POWERSHELL
  if winpe.check_winpe():
    path = constants.WINPE_POWERSHELL
  return path


class PowerShell(object):
  """Interact with the PowerShell interpreter to run scripts."""

  def __init__(self, log: bool = True):
    self.log = log

  def _launch_ps(self,
                 op: Text,
                 args: List[Text],
                 return_codes: Optional[List[int]] = None):
    """Launch the PowerShell executable to run a script.

    Args:
      op: -Command or -File
      args: Additional commandline arguments.
      return_codes: Acceptable exit/return codes. Defaults to 0.

    Raises:
      Error: PowerShell returned invalid exit code.
    """
    if op not in ['-Command', '-File']:
      raise Error('Unsupported PowerShell parameter: %s' % op)

    log = self.log

    try:
      execute.execute_binary(_powershell_path(),
                             ['-NoProfile', '-NoLogo', op] + args, return_codes,
                             log)
    except execute.Error as e:
      raise Error(str(e))

  def run_command(self, command: List[Text], return_codes: List[int] = None):
    """Run a powershell script on the local filesystem.

    Args:
      command: Command and all accompanying parameters.
      return_codes: Acceptable exit/return codes. Defaults to 0.
    """
    self._launch_ps('-Command', command, return_codes)

  def _get_res_path(self, path: Text) -> Text:
    """Translate an installer resource path into a local path.

    Args:
      path: Resource Path.

    Raises:
      Error: Unable to locate the requested resource.

    Returns:
      The local file path as a string.
    """
    r = resources.Resources()
    try:
      path = r.GetResourceFileName(path)
    except resources.FileNotFound as e:
      raise Error(e)
    return os.path.normpath(path)

  def run_resource(self,
                   path: Text,
                   args: List[Text] = None,
                   return_codes: List[int] = None):
    """Run a Powershell script supplied as an installer resource file.

    Args:
      path: Relative path to a script under the installer resources directory.
      args: Optional PowerShell arguments.
      return_codes: Acceptable exit/return codes. Defaults to 0.
    """
    path = self._get_res_path(path)
    self.run_local(path, args, return_codes)

  def run_local(self,
                path: Text,
                args: List[Text] = None,
                return_codes: List[int] = None):
    """Run a powershell script on the local filesystem.

    Args:
      path: Local file path.
      args: Optional PowerShell arguments.
      return_codes: Acceptable exit/return codes. Defaults to 0.
    """
    self._launch_ps('-File', [path] + args, return_codes)

  def set_execution_policy(self, policy: Text):
    """Set the shell execution policy.

    Args:
      policy: One of Restricted, RemoteSigned, AllSigned, or Unrestricted.

    Raises:
      Error: Attempting to set an unsupported policy.
    """
    if policy not in ['Restricted', 'RemoteSigned', 'AllSigned', 'Unrestricted'
                     ]:
      raise Error('Unknown execution policy: %s' % policy)
    self.run_command(['Set-ExecutionPolicy', '-ExecutionPolicy', policy])

  def start_shell(self):
    """Start the PowerShell interpreter."""
    try:
      execute.execute_binary(_powershell_path(), ['-NoProfile', '-NoLogo'])
    except execute.Error as e:
      raise Error(str(e))
