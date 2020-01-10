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

import logging
import os
import subprocess
from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import resources


class PowerShellError(Exception):
  pass


class PowerShell(object):
  """Interact with the powershell interpreter to run scripts."""

  def __init__(self, echo_off=True):
    self.echo_off = echo_off
    self._build_info = buildinfo.BuildInfo()

  def _PowerShellPath(self):
    if self._build_info.CheckWinPE():
      return constants.WINPE_POWERSHELL
    else:
      return constants.SYS_POWERSHELL

  def _LaunchPs(self, op, args, ok_result):
    """Launch the powershell executable to run a script.

    Args:
      op: -Command or -File
      args: any additional commandline args as a list
      ok_result: a list of acceptable exit codes; default is 0

    Raises:
      PowerShellError: failure to execute powershell command cleanly
    """
    if op not in ['-Command', '-File']:
      raise PowerShellError('Unsupported operation type. [%s]' % op)
    if not ok_result:
      ok_result = [0]
    cmd = [self._PowerShellPath(), '-NoProfile', '-NoLogo', op] + args
    if not self.echo_off:
      logging.debug('Running Powershell:%s', cmd)
    result = subprocess.call(cmd, shell=True)
    if result not in ok_result:
      raise PowerShellError('Powershell command returned non-zero.\n%s' % cmd)

  def RunCommand(self, command, ok_result=None):
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

  def _GetResPath(self, path):
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

  def RunResource(self, path, args=None, ok_result=None):
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

  def RunLocal(self, path, args=None, ok_result=None):
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

  def SetExecutionPolicy(self, policy):
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
    subprocess.call([self._PowerShellPath(), '-NoProfile', '-NoLogo'],
                    shell=True)
