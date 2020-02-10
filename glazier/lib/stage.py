# Lint as: python3
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Build stages track progress through the build.

Build stages use the registry to track the points at which Glazier enters
different phases of operation. Stage start and end points are associated with
the time during which the stage began and finished, useful for tracking end to
end progress.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import logging
from glazier.lib import constants
from glazier.lib import registry

STAGES_ROOT = constants.REG_ROOT + r'\Stages'
ACTIVE_KEY = '_Active'


class Error(Exception):
  pass


def exit_stage(stage_id):
  """Exit the current stage by setting the End value."""
  end = _utc_now().isoformat()
  logging.info('Exiting stage %d as of %s', stage_id, end)
  try:
    registry.set_value('End', str(end), 'HKLM', _stage_root(stage_id))
    registry.set_value(ACTIVE_KEY, '', 'HKLM', STAGES_ROOT)
  except registry.Error as e:
    raise Error(str(e))


def get_active_stage():
  """Get the active build stage, if one exists."""
  try:
    return registry.get_value(ACTIVE_KEY, 'HKLM', STAGES_ROOT)
  except registry.Error as e:
    logging.error(str(e))


def get_active_time(stage_id):
  """Get the amount of time we've been in the current stage."""
  start = _load_time(stage_id, 'Start')
  if not start:
    raise Error('Stage %d does not contain a valid Start time.' % stage_id)
  end = _load_time(stage_id, 'End')
  if not end:
    logging.info('Stage %d not complete. Using current time.', stage_id)
    end = _utc_now()
  return end - start


def _load_time(stage_id, key):
  """Load a time string and convert it into a native datetime value."""
  val = None
  try:
    val = registry.get_value(key, 'HLKM', _stage_root(stage_id))
  except registry.Error as e:
    logging.error(str(e))
  if val:
    try:
      val = datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError as e:
      logging.error(str(e))
      return None
  return val


def set_stage(stage_id):
  """Sets or updates the current build stage."""
  if not isinstance(stage_id, int):
    raise Error('Invalid stage type; got: %s, want: int' % type(stage_id))

  active = get_active_stage()
  if active:
    exit_stage(active)

  start = _utc_now().isoformat()
  try:
    registry.set_value('Start', str(start), 'HKLM', _stage_root(stage_id))
    registry.set_value(ACTIVE_KEY, str(stage_id), 'HKLM', STAGES_ROOT)
  except registry.Error as e:
    raise Error(str(e))


def _stage_root(stage_id):
  return r'%s\%d' % (STAGES_ROOT, stage_id)


def _utc_now():
  return datetime.datetime.utcnow()
