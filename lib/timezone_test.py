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

"""Unittests for the timezone library."""

from glazier.lib import timezone
from google.apputils import basetest


class TimezoneTest(basetest.TestCase):

  def setUp(self):
    self.tz = timezone.Timezone()
    timezone.FLAGS.windows_zones_resource = timezone.RESOURCE_PATH
    self.tz.LoadMap()

  def testLoadMap(self):
    timezone.FLAGS.windows_zones_resource = '/no/such/file.xml'
    self.assertRaises(timezone.TimezoneError, self.tz.LoadMap)

  def testTranslateZone(self):
    zone = self.tz.TranslateZone('Pacific/Tahiti')
    self.assertEqual(zone, 'Hawaiian Standard Time')
    zone = self.tz.TranslateZone('Nonsense/Atlantis')
    self.assertEqual(zone, None)
    zone = self.tz.TranslateZone('Europe/Dublin')
    self.assertEqual(zone, 'GMT Standard Time')


if __name__ == '__main__':
  basetest.main()
