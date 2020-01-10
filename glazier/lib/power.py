# python3
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

"""Turn things on and off."""

import subprocess
import typing
from typing import Text

from glazier.lib import constants

if typing.TYPE_CHECKING:
  from glazier.lib import buildinfo


def _System32(build_info: 'buildinfo.BuildInfo') -> Text:
  if build_info.CheckWinPE():
    return constants.WINPE_SYSTEM32
  else:
    return constants.SYS_SYSTEM32


def Shutdown(timeout: Text, reason: Text, build_info: 'buildinfo.BuildInfo'):
  """Shuts down a Windows machine, given a timeout period and a reason.

  Args:
    timeout: How long to wait before shutting down the machine.
    reason: Reason why the machine is being shut down.  This will be displayed
      to the user and written to the Windows event log.
    build_info: the current build information
  """
  subprocess.call(r'%s\shutdown.exe -s -t %s -c "%s" -f'
                  % (_System32(build_info), timeout, reason))


def Restart(timeout: Text, reason: Text, build_info: 'buildinfo.BuildInfo'):
  """Restarts a Windows machine, given a timeout period and a reason.

  Args:
    timeout: How long to wait before restarting the machine.
    reason: Reason why the machine is being restarted. This will be displayed
      to the user and written to the Windows event log.
    build_info: the current build information
  """
  subprocess.call(r'%s\shutdown.exe -r -t %s -c "%s" -f'
                  % (_System32(build_info), timeout, reason))
