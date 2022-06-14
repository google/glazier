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
from typing import Optional, Tuple

from absl import flags
from glazier.lib import constants
from glazier.lib import registry

from glazier.lib import errors

FLAGS = flags.FLAGS
STAGES_ROOT = constants.REG_ROOT + r'\Stages'
ACTIVE_KEY = '_Active'

flags.DEFINE_integer(
    'stage_timeout_minutes', 60 * 24 * 7,
    'Time in minutes until an active stage is considered expired.')


class Error(errors.GlazierError):
  pass


class ExpirationError(Error):

  def __init__(self, stage_id: int):
    super().__init__(
        error_code=errors.ErrorCode.STAGE_EXPIRATION_ERROR,
        message=f'Active stage {stage_id} has expired')


class InvalidStartTimeError(Error):

  def __init__(self, stage_id: int):
    super().__init__(
        error_code=errors.ErrorCode.STAGE_INVALID_START_TIME_ERROR,
        message=f'Stage {stage_id} does not contain a valid start time.')


class InvalidStageIdError(Error):

  def __init__(self, stage_id_type: type(type)):
    super().__init__(
        error_code=errors.ErrorCode.STAGE_INVALID_ID_ERROR,
        message=f'Invalid stage ID type; got: {stage_id_type}, want: int')


class ExitError(Error):

  def __init__(self, stage_id: int):
    super().__init__(
        error_code=errors.ErrorCode.STAGE_EXIT_ERROR,
        message=f'Error while exiting stage: {stage_id}')


class UpdateError(Error):

  def __init__(self, stage_id: int):
    super().__init__(
        error_code=errors.ErrorCode.STAGE_UPDATE_ERROR,
        message=f'Error while updating stage: {stage_id}')


def exit_stage(stage_id: int):
  """Exit the current stage by setting the End value."""
  end = _utc_now().isoformat()
  logging.info('Exiting stage %d as of %s', stage_id, end)
  try:
    registry.set_value('End', str(end), 'HKLM', _stage_root(stage_id))
    registry.set_value(ACTIVE_KEY, '', 'HKLM', STAGES_ROOT)
  except registry.Error as e:
    raise ExitError(stage_id) from e


def _check_expiration(stage_id: int):
  expiration = datetime.timedelta(minutes=FLAGS.stage_timeout_minutes)
  time_in_stage = get_active_time(stage_id)
  if time_in_stage > expiration:
    raise ExpirationError(stage_id)


def get_active_stage() -> Optional[int]:
  """Get the active build stage, if one exists."""
  val = None
  try:
    val = registry.get_value(ACTIVE_KEY, 'HKLM', STAGES_ROOT)
  except registry.Error as e:
    logging.error(str(e))
  if not val:
    return None
  val = int(val)
  _check_expiration(val)
  return val


def get_active_time(stage_id: int) -> datetime.timedelta:
  """Get the amount of time we've been in the current stage."""
  start, end = _get_start_end(stage_id)
  if not start:
    raise InvalidStartTimeError(stage_id)
  if not end:
    logging.info('Stage %d not complete. Using current time.', stage_id)
    end = _utc_now()
  return end - start


def get_status() -> str:
  """Get the interpreted build status.

  Returns:
    str

    * Unknown: The stage cannot be determined.
    * Complete: Glazier is comlete.
    * Running: Glazier is active.
    * Expired: Glazier started, but has not completed all stages within the
        allowed time limit.
  """
  stage_id = get_active_stage()
  if not stage_id:
    return 'Unknown'
  start, end = _get_start_end(stage_id)
  if not start:
    return 'Unknown'
  if start and end:
    return 'Complete'
  try:
    _check_expiration(stage_id)
  except Error:
    return 'Expired'
  return 'Running'


def _get_start_end(
    stage_id: int
) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
  start = _load_time(stage_id, 'Start')
  end = _load_time(stage_id, 'End')
  return start, end


def _load_time(stage_id: int, key: str) -> Optional[datetime.datetime]:
  """Load a time string and convert it into a native datetime value."""
  val = None
  try:
    v = registry.get_value(key, 'HKLM', _stage_root(stage_id))
    if v:
      val = datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f')
  except (registry.Error, ValueError) as e:
    logging.error(str(e))
    return None
  return val


def set_stage(stage_id: int):
  """Sets or updates the current build stage."""
  if not isinstance(stage_id, int):
    raise InvalidStageIdError(type(stage_id))

  active = get_active_stage()
  if active:
    exit_stage(active)

  start = _utc_now().isoformat()
  try:
    registry.set_value('Start', str(start), 'HKLM', _stage_root(stage_id))
    registry.set_value(ACTIVE_KEY, str(stage_id), 'HKLM', STAGES_ROOT)
  except registry.Error as e:
    raise UpdateError(stage_id) from e


def _stage_root(stage_id: int) -> str:
  return r'%s\%d' % (STAGES_ROOT, stage_id)


def _utc_now():
  return datetime.datetime.utcnow()
