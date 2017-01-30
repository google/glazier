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

"""Tests for glazier.lib.actions.system."""

from glazier.lib.actions import system
import mock
from google.apputils import basetest


class SystemTest(basetest.TestCase):

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testReboot(self, build_info):
    r = system.Reboot([30, 'reboot for reasons'], build_info)
    with self.assertRaises(system.RestartEvent) as evt:
      r.Run()
      self.assertEqual(evt.timeout, '30')
      self.assertEqual(evt.message, 'reboot for reasons')

    r = system.Reboot([10], build_info)
    with self.assertRaises(system.RestartEvent) as evt:
      r.Run()
      self.assertEqual(evt.timeout, '10')
      self.assertEqual(evt.message, 'undefined')

  def testRebootValidate(self):
    r = system.Reboot(30, None)
    self.assertRaises(system.ValidationError, r.Validate)
    r = system.Reboot([], None)
    self.assertRaises(system.ValidationError, r.Validate)
    r = system.Reboot([30, 40], None)
    self.assertRaises(system.ValidationError, r.Validate)
    r = system.Reboot([30, 'reasons'], None)
    r.Validate()

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testShutdown(self, build_info):
    r = system.Shutdown([15, 'reboot for reasons'], build_info)
    with self.assertRaises(system.ShutdownEvent) as evt:
      r.Run()
      self.assertEqual(evt.timeout, '15')
      self.assertEqual(evt.message, 'reboot for reasons')

    r = system.Shutdown([1], build_info)
    with self.assertRaises(system.ShutdownEvent) as evt:
      r.Run()
      self.assertEqual(evt.timeout, '1')
      self.assertEqual(evt.message, 'undefined')

  def testShutdownValidate(self):
    s = system.Shutdown(30, None)
    self.assertRaises(system.ValidationError, s.Validate)
    s = system.Shutdown([], None)
    self.assertRaises(system.ValidationError, s.Validate)
    s = system.Shutdown([30, 40], None)
    self.assertRaises(system.ValidationError, s.Validate)
    s = system.Shutdown([30, 'reasons'], None)
    s.Validate()
    s = system.Shutdown([10], None)
    s.Validate()

if __name__ == '__main__':
  basetest.main()
