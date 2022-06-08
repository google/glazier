# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Centrally defines all "event"-type Exceptions."""

# pylint: disable=g-bad-exception-name


class PowerEvent(Exception):
  """Base class for all power-based events."""

  def __init__(
      self, message, timeout, retry_on_restart=False, task_list_path=None,
      pop_next=False):

    super(PowerEvent, self).__init__(message)
    self.retry_on_restart = retry_on_restart
    self.task_list_path = task_list_path
    self.timeout = timeout
    self.pop_next = pop_next


class RestartEvent(PowerEvent):
  """Action requesting a host restart."""


class ShutdownEvent(PowerEvent):
  """Action requesting a host shutdown."""


class ServerChangeEvent(Exception):
  """Action indicating a config server change."""
