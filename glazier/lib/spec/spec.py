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
"""Generic class for determining the desired host operating system."""

from typing import Any, Dict

# do not remove: internal placeholder 1
from absl import flags
from glazier.lib.spec import flags as flag_spec

from glazier.lib import errors


SPEC_OPTS: Dict[str, Any] = {
    'flag': flag_spec,
}
FLAGS = flags.FLAGS


class Error(errors.GlazierError):
  pass


class UnknownSpec(Error):

  def __init__(self, spec: str):
    super().__init__(
        error_code=errors.ErrorCode.UNKNOWN_SPEC,
        message=f'Unknown spec: {spec}')


def GetModule():
  try:
    return SPEC_OPTS[FLAGS.glazier_spec]
  except KeyError as e:
    raise UnknownSpec(FLAGS.glazier_spec) from e
