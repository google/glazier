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
from typing import Text

from glazier.lib import constants
from glazier.lib import reg_util


def _System32() -> Text:
  if reg_util.check_winpe():
    return constants.WINPE_SYSTEM32
  else:
    return constants.SYS_SYSTEM32


def Shutdown(timeout: Text, reason: Text):
  """Shuts down a Windows machine, given a timeout period and a reason.

  Args:
    timeout: How long to wait before shutting down the machine.
    reason: Reason why the machine is being shut down.  This will be displayed
      to the user and written to the Windows event log.
  """
  subprocess.call(r'%s\shutdown.exe -s -t %s -c "%s" -f'
                  % (_System32(), timeout, reason))


def Restart(timeout: Text, reason: Text):
  """Restarts a Windows machine, given a timeout period and a reason.

  Args:
    timeout: How long to wait before restarting the machine.
    reason: Reason why the machine is being restarted. This will be displayed
      to the user and written to the Windows event log.
  """
  subprocess.call(r'%s\shutdown.exe -r -t %s -c "%s" -f'
                  % (_System32(), timeout, reason))
