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


class PowerShellError(Exception):
  pass


def _Powershell() -> Text:
  if winpe.check_winpe():
    return constants.WINPE_POWERSHELL
  else:
    return constants.SYS_POWERSHELL


class PowerShell(object):
  """Interact with the powershell interpreter to run scripts."""

  def __init__(self, echo_off: bool = False):
    self.echo_off = echo_off

  def _LaunchPs(self, op: Text,
                args: List[Text],
                ok_result: Optional[List[int]] = None):
    """Launch the powershell executable to run a script.

    Args:
      op: -Command or -File
      args: any additional commandline args as a list
      ok_result: a list of acceptable exit codes; default is 0

    Raises:
      PowerShellError: failure to execute powershell command cleanly
    """
    if op not in ['-Command', '-File']:
      raise PowerShellError('Unsupported PowerShell parameter: %s' % op)

    log = not self.echo_off

    try:
      execute.execute_binary(_Powershell(), ['-NoProfile', '-NoLogo',
                                             op] + args, ok_result, log)
    except execute.Error as e:
      raise PowerShellError(str(e))

  def RunCommand(self, command: List[Text], ok_result: List[int] = None):
    """Run a powershell script on the local filesystem.

    Args:
      command: a list containing the command and all accompanying arguments
      ok_result: a list of acceptable exit codes; default is 0
    """
    assert isinstance(command, list), 'command must be passed as a list'
    if ok_result:
      assert isinstance(ok_result,
                        list), 'result codes must be passed as a list'
    self._LaunchPs('-Command', command, ok_result)

  def _GetResPath(self, path: Text) -> Text:
    """Translate an installer resource path into a local path.

    Args:
      path: the resource path string

    Raises:
      PowerShellError: unable to locate the requested resource

    Returns:
      The local filesystem path as a string.
    """
    r = resources.Resources()
    try:
      path = r.GetResourceFileName(path)
    except resources.FileNotFound as e:
      raise PowerShellError(e)
    return os.path.normpath(path)

  def RunResource(self, path: Text, args: List[Text],
                  ok_result: Optional[List[int]] = None):
    """Run a Powershell script supplied as an installer resource file.

    Args:
      path: relative path to a script under the installer resources directory
      args: a list of any optional powershell arguments
      ok_result: a list of acceptable exit codes; default is 0
    """
    path = self._GetResPath(path)
    if not args:
      args = []
    else:
      assert isinstance(args, list), 'args must be passed as a list'
    if ok_result:
      assert isinstance(ok_result,
                        list), 'result codes must be passed as a list'
    self.RunLocal(path, args, ok_result)

  def RunLocal(self, path: Text, args: List[Text],
               ok_result: List[int] = None):
    """Run a powershell script on the local filesystem.

    Args:
      path: a local filesystem path string
      args: a list of any optional powershell arguments
      ok_result: a list of acceptable exit codes; default is 0

    Raises:
      PowerShellError: Invalid path supplied for execution.
    """
    if not os.path.exists(path):
      raise PowerShellError('Cannot find path to script. [%s]' % path)
    if not args:
      args = []
    else:
      assert isinstance(args, list), 'args must be passed as a list'
    if ok_result:
      assert isinstance(ok_result,
                        list), 'result codes must be passed as a list'
    self._LaunchPs('-File', [path] + args, ok_result)

  def SetExecutionPolicy(self, policy: Text):
    """Set the shell execution policy.

    Args:
      policy: One of Restricted, RemoteSigned, AllSigned, Unrestricted

    Raises:
      PowerShellError: Attempting to set an unsupported policy.
    """
    if policy not in ['Restricted', 'RemoteSigned', 'AllSigned', 'Unrestricted'
                     ]:
      raise PowerShellError('Unknown execution policy: %s' % policy)
    self.RunCommand(['Set-ExecutionPolicy', '-ExecutionPolicy', policy])

  def StartShell(self):
    """Start the PowerShell interpreter."""
    log = not self.echo_off
    try:
      execute.execute_binary(_Powershell(), ['-NoProfile', '-NoLogo'], log=log)
    except execute.Error as e:
      raise PowerShellError(str(e))
