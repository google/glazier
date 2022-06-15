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

"""Timezone processing for Windows.

> Resource Requirements

  * resources/cldr/common/supplemental/windowsZones.xml
      The Windows timezone map from http://cldr.unicode.org.

"""
import logging
from xml.dom.minidom import parse
# do not remove: internal placeholder 1
from absl import flags
from glazier.lib import resources

from glazier.lib import errors


FLAGS = flags.FLAGS

RESOURCE_PATH = 'cldr/common/supplemental/windowsZones.xml'

flags.DEFINE_string('windows_zones_resource', RESOURCE_PATH,
                    'Timezone map file location.')


class Error(errors.GlazierError):
  pass


class TimezoneError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.TIMEZONE_ERROR,
        message=f'Cannot load zone map from {FLAGS.windows_zones_resource}.')


class Timezone(object):
  """Timezone processing for Windows."""

  def __init__(self, load_map=False):
    self.zones = {}
    if load_map:
      self.LoadMap()

  def LoadMap(self):
    res = resources.Resources()
    try:
      win_zones = parse(res.GetResourceFileName(FLAGS.windows_zones_resource))
    except resources.FileNotFound as e:
      raise TimezoneError() from e

    for zone in win_zones.getElementsByTagName('mapZone'):
      self.zones[zone.getAttribute('type')] = zone.getAttribute('other')

  def TranslateZone(self, name):
    found = None
    try:
      found = self.zones[name]
    except KeyError:
      logging.error('Unable to translate zone %s.', name)
    return found
