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
from typing import List, Optional

# do not remove: internal placeholder 1
from glazier.lib import constants
from glazier.lib import execute
from glazier.lib import resources
from glazier.lib import winpe

from glazier.lib import errors


_SUPPORTED_EXECUTION_POLICIES = frozenset([
    'Restricted', 'RemoteSigned', 'AllSigned', 'Unrestricted'
])
_SUPPORTED_PARAMETERS = frozenset(['-Command', '-File'])


class Error(errors.GlazierError):
  pass


class UnsupportedParameterError(Error):

  def __init__(self, parameter: str):
    supported_params_str = str(sorted(list(_SUPPORTED_PARAMETERS)))
    message = (
        f'Unsupported PowerShell parameter \'{parameter}\' '
        f'not found in {supported_params_str}.'
    )
    super().__init__(
        error_code=errors.ErrorCode.POWERSHELL_UNSUPPORTED_PARAMETER,
        message=message)


class PowerShellExecutionError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.POWERSHELL_EXECUTION_ERROR,
        message='Error encountered during PowerShell execution')


class InvalidPathError(Error):

  def __init__(self, path: str):
    super().__init__(
        error_code=errors.ErrorCode.POWERSHELL_INVALID_PATH,
        message=f'A path required by PowerShell in invalid: {path}')


class UnsupportedExecutionPolicyError(Error):

  def __init__(self, policy: str):
    supported_policies_str = str(sorted(list(_SUPPORTED_EXECUTION_POLICIES)))
    message = (
        f'Unsupported execution policy \'{policy}\' '
        f'not found in {supported_policies_str}.'
    )
    super().__init__(
        error_code=errors.ErrorCode.POWERSHELL_UNSUPPORTED_EXECUTION_POLICY,
        message=message)


def _Powershell() -> str:
  if winpe.check_winpe():
    return constants.WINPE_POWERSHELL
  else:
    return constants.SYS_POWERSHELL


class PowerShell(object):
  """Interact with the powershell interpreter to run scripts."""

  def __init__(self, shell: Optional[bool] = False, log: Optional[bool] = True):
    self.shell = shell
    self.log = log

  def _LaunchPs(self, op: str,
                args: List[str],
                ok_result: Optional[List[int]] = None) -> int:
    """Launch the powershell executable to run a script.

    Args:
      op: -Command or -File
      args: any additional commandline args as a list
      ok_result: a list of acceptable exit codes; default is 0

    Returns:
      Process returncode if successfully exited.

    Raises:
      Error: failure to execute powershell command cleanly
    """
    if op not in _SUPPORTED_PARAMETERS:
      raise UnsupportedParameterError(op)

    try:
      return execute.execute_binary(
          _Powershell(), ['-NoProfile', '-NoLogo', op] + args, ok_result,
          self.shell, self.log)
    except execute.Error as e:
      raise PowerShellExecutionError() from e

  def RunCommand(self,
                 command: List[str],
                 ok_result: Optional[List[int]] = None) -> int:
    """Run a powershell script on the local filesystem.

    Args:
      command: a list containing the command and all accompanying arguments
      ok_result: a list of acceptable exit codes; default is 0

    Returns:
      Process returncode if successfully exited.
    """
    assert isinstance(command, list), 'command must be passed as a list'
    if ok_result:
      assert isinstance(ok_result,
                        list), 'result codes must be passed as a list'
    return self._LaunchPs('-Command', command, ok_result)

  def _GetResPath(self, path: str) -> str:
    """Translate an installer resource path into a local path.

    Args:
      path: the resource path string

    Raises:
      ResourceNotFoundError: unable to locate the requested resource.

    Returns:
      The local filesystem path as a string.
    """
    r = resources.Resources()
    try:
      path = r.GetResourceFileName(path)
    except resources.FileNotFound as e:
      raise InvalidPathError(path) from e
    return os.path.normpath(path)

  def RunResource(self, path: str, args: List[str],
                  ok_result: Optional[List[int]] = None):
    """Run a Powershell script supplied as an installer resource file.

    Args:
      path: relative path to a script under the installer resources directory
      args: a list of additional powershell arguments
      ok_result: a list of acceptable exit codes; default is 0
    """
    path = self._GetResPath(path)
    assert isinstance(args, list), 'args must be passed as a list'
    if ok_result:
      assert isinstance(ok_result,
                        list), 'result codes must be passed as a list'
    self.RunLocal(path, args, ok_result)

  def RunLocal(self, path: str, args: List[str],
               ok_result: Optional[List[int]] = None) -> int:
    """Run a powershell script on the local filesystem.

    Args:
      path: a local filesystem path string
      args: a list of additional powershell arguments
      ok_result: a list of acceptable exit codes; default is 0

    Returns:
      Process returncode if successfully exited.

    Raises:
      InvalidPathError: Invalid path supplied for execution.
    """
    if not os.path.exists(path):
      raise InvalidPathError(path)
    assert isinstance(args, list), 'args must be passed as a list'
    if ok_result:
      assert isinstance(ok_result,
                        list), 'result codes must be passed as a list'
    return self._LaunchPs('-File', [path] + args, ok_result)

  def SetExecutionPolicy(self, policy: str):
    """Set the shell execution policy.

    Args:
      policy: One of Restricted, RemoteSigned, AllSigned, Unrestricted

    Raises:
      UnsupportedExecutionPolicyError: Attempting to set an unsupported policy.
    """
    if policy not in _SUPPORTED_EXECUTION_POLICIES:
      raise UnsupportedExecutionPolicyError(policy)

    self.RunCommand(['Set-ExecutionPolicy', '-ExecutionPolicy', policy])

  def StartShell(self):
    """Start the PowerShell interpreter."""
    try:
      execute.execute_binary(
          _Powershell(), ['-NoProfile', '-NoLogo'], shell=self.shell,
          log=self.log)
    except execute.Error as e:
      raise PowerShellExecutionError() from e
