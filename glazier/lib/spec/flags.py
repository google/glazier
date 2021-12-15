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

"""Class for determining host spec via flags."""

# do not remove: internal placeholder 1
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('glazier_spec_hostname', '',
                    'Host name for this installation.')
flags.DEFINE_string('glazier_spec_fqdn', '',
                    'Host FQDN for this installation.')
flags.DEFINE_string('glazier_spec_lab', '',
                    'Whether the machine lives in an imaging lab.')
flags.DEFINE_string('glazier_spec_image_type', '', 'Glazier image type.')
flags.DEFINE_string('glazier_spec_os', '',
                    'Operating system code for this image.')


def GetOs():
  """Get the desired OS via flags."""
  return FLAGS.glazier_spec_os


def GetFqdn():
  """Get the desired FQDN via flags."""
  return FLAGS.glazier_spec_fqdn


def GetHostname():
  """Get the desired hostname via flags."""
  return FLAGS.glazier_spec_hostname


def GetImageType():
  """Get the image type via flags."""
  return FLAGS.glazier_spec_image_type


def GetLab():
  """Get the lab state via flags."""
  return FLAGS.glazier_spec_lab
