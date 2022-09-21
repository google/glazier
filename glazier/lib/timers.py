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

"""Store points in time to be used for metrics."""

import datetime
import logging
from typing import Dict, Optional

from glazier.lib import gtime
from glazier.lib import registry

from glazier.lib import constants
from glazier.lib import errors

TIMERS_PATH = fr'{constants.REG_ROOT}\Timers'


class Error(errors.GlazierError):
  pass


class SetTimerError(Error):

  def __init__(self,
               name: str,
               value: str):
    message = (f'Failed to set Glazier timer: [{name} = {value}]')
    super().__init__(
        error_code=errors.ErrorCode.SET_TIMER_ERROR, message=message)


class Timers(object):
  """Store named time elements."""

  def Get(self, name: str) -> Optional['datetime.datetime']:
    """Get the stored value of a single timer.

    Args:
      name: The name of the timer being requested.

    Returns:
      A specific named datetime value if stored, or None
    """
    timer = registry.get_value(f'TIMER_{name}', path=TIMERS_PATH)
    return datetime.datetime.strptime(timer, '%Y-%m-%d %H:%M:%S.%f%z')

  def GetAll(self) -> Optional[Dict[str, 'datetime.datetime']]:
    """Get the dictionary of all stored timers.

    Returns:
      A dictionary of all stored timer names and values.
    """
    timers_dict = {}
    timers = registry.get_keys_and_values(path=TIMERS_PATH)

    if not timers:
      return None

    for k, v in timers.items():
      timers_dict[k] = datetime.datetime.strptime(v, '%Y-%m-%d %H:%M:%S.%f%z')
    return timers_dict

  def Set(self, name: str) -> None:
    """Set a timer at a specific time.

    Defaults to the current time in UTC.

    Args:
      name: Name of the timer being set.
    """
    value_name = f'TIMER_{name}'
    value_data = str(gtime.now())
    try:
      registry.set_value(value_name, value_data, 'HKLM', TIMERS_PATH, log=False)
      logging.info('Set image timer: %s (%s)', name, value_data)
    except registry.Error as e:
      raise SetTimerError(value_name, value_data) from e
