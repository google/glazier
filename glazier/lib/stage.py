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
from gwinpy.registry import registry

STAGES_ROOT = constants.REG_ROOT + r'\Stages'
ACTIVE_KEY = '_Active'


class Error(Exception):
  pass


def exit_stage(stage_id):
  """Exit the current stage by setting the End value."""
  end = datetime.datetime.utcnow()
  try:
    logging.info('Exiting stage %d as of %s', stage_id, end)
    reg = registry.Registry(root_key='HKLM')
    reg.SetKeyValue(
        key_path=_stage_root(stage_id),
        key_name='End',
        key_value=str(end),
        key_type='REG_SZ',
        use_64bit=True)
    reg.SetKeyValue(
        key_path=STAGES_ROOT,
        key_name=ACTIVE_KEY,
        key_value='',
        key_type='REG_SZ',
        use_64bit=True)
  except registry.RegistryError as e:
    raise Error(str(e))


def get_active_stage():
  """Get the active build stage, if one exists."""
  try:
    reg = registry.Registry(root_key='HKLM')
    return reg.GetKeyValue(
        key_path=STAGES_ROOT, key_name=ACTIVE_KEY, use_64bit=True)
  except registry.RegistryError as e:
    logging.info(str(e))
  return None


def set_stage(stage_id):
  """Sets or updates the current build stage."""
  if not isinstance(stage_id, int):
    raise Error('Invalid stage type; got: %s, want: int' % type(stage_id))

  active = get_active_stage()
  if active:
    exit_stage(active)

  start = datetime.datetime.utcnow()
  try:
    logging.info('Entering stage %d as of %s', stage_id, start)
    reg = registry.Registry(root_key='HKLM')
    reg.SetKeyValue(
        key_path=_stage_root(stage_id),
        key_name='Start',
        key_value=str(start),
        key_type='REG_SZ',
        use_64bit=True)
    reg.SetKeyValue(
        key_path=STAGES_ROOT,
        key_name=ACTIVE_KEY,
        key_value=str(stage_id),
        key_type='REG_SZ',
        use_64bit=True)
  except registry.RegistryError as e:
    raise Error(str(e))


def _stage_root(stage_id):
  return r'%s\%d' % (STAGES_ROOT, stage_id)
