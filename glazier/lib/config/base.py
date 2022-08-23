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

"""Configuration handling core functionality.

This class contains features common to both the Config Builder and Config Runner
classes.  It is meant to be inherited rather than run directly.
"""

from glazier.lib import actions
from glazier.lib import errors


class Error(errors.GlazierError):
  pass


class ConfigError(Error):

  def __init__(self, message: str):
    super().__init__(
        error_code=errors.ErrorCode.CONFIG_ERROR,
        message=message)


class ConfigBase(object):
  """Core functionality for the configuration handling module."""

  def __init__(self, build_info):
    self._build_info = build_info

  def _GetAction(self, action, params):
    try:
      act_obj = getattr(actions, str(action))
      return act_obj(args=params, build_info=self._build_info)
    except AttributeError as e:
      msg = 'Unknown imaging action: %s' % str(action)
      raise ConfigError(msg) from e  # pytype: disable=wrong-arg-types

  def _IsRealtimeAction(self, action, params):
    """Determine whether $action should happen in realtime."""
    if action not in dir(actions):
      return False
    a = self._GetAction(action, params)
    return a.IsRealtime()

  def _ProcessAction(self, action, params):
    """Attempt to process a dynamic action element.

    Args:
      action: The name of the action.
      params: The params being passed in with the action.

    Raises:
      ConfigError: The action is either undefined, or failed to execute.
    """
    try:
      self._GetAction(action, params).Run()
    except actions.ActionError as e:
      raise ConfigError('Error while running configured action') from e
