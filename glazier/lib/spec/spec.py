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

# do not remove: internal placeholder 1
from absl import flags
from glazier.lib.spec import flags as flag_spec

SPEC_OPTS = {
    'flag': flag_spec,
}

FLAGS = flags.FLAGS
flags.DEFINE_enum(
    'glazier_spec', 'flag', list(SPEC_OPTS.keys()),
    ('Which host specification module to use for determining host features '
     'like Hostname and OS.'))


class UnknownSpec(Exception):
  pass


def GetModule():
  try:
    return SPEC_OPTS[FLAGS.glazier_spec]
  except KeyError:
    raise UnknownSpec(FLAGS.glazier_spec)
