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

from unittest import mock

from absl.testing import absltest
from glazier.lib.actions import system


class SystemTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testRebootPop(self, build_info):
    r = system.Reboot([30, 'reboot for reasons', True], build_info)
    with self.assertRaises(system.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '30')
    self.assertEqual(str(ex), 'reboot for reasons')
    self.assertEqual(ex.pop_next, True)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testRebootReason(self, build_info):
    r = system.Reboot([30, 'reboot for reasons'], build_info)
    with self.assertRaises(system.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '30')
    self.assertEqual(str(ex), 'reboot for reasons')
    self.assertEqual(ex.pop_next, False)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testRebootTimeout(self, build_info):
    r = system.Reboot([10], build_info)
    with self.assertRaises(system.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '10')
    self.assertEqual(str(ex), 'unspecified')
    self.assertEqual(ex.pop_next, False)

  def testRebootValidate(self):
    r = system.Reboot(True, None)
    self.assertRaises(system.ValidationError, r.Validate)
    r = system.Reboot([30, 40], None)
    self.assertRaises(system.ValidationError, r.Validate)
    r = system.Reboot([30, 'reasons', 'True'], None)
    self.assertRaises(system.ValidationError, r.Validate)
    r = system.Reboot([1, 2, 3, 4], None)
    self.assertRaises(system.ValidationError, r.Validate)
    r = system.Reboot([30, 'reasons', True], None)
    r.Validate()
    r = system.Reboot([30, 'reasons'], None)
    r.Validate()
    r = system.Reboot([30], None)
    r.Validate()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testShutdownPop(self, build_info):
    r = system.Shutdown([15, 'shutdown for reasons', True], build_info)
    with self.assertRaises(system.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '15')
    self.assertEqual(str(ex), 'shutdown for reasons')
    self.assertEqual(ex.pop_next, True)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testShutdownReason(self, build_info):
    r = system.Shutdown([15, 'shutdown for reasons'], build_info)
    with self.assertRaises(system.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '15')
    self.assertEqual(str(ex), 'shutdown for reasons')
    self.assertEqual(ex.pop_next, False)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testShutdownTimeout(self, build_info):
    r = system.Shutdown([1], build_info)
    with self.assertRaises(system.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '1')
    self.assertEqual(str(ex), 'unspecified')
    self.assertEqual(ex.pop_next, False)

  def testShutdownValidate(self):
    s = system.Shutdown(True, None)
    self.assertRaises(system.ValidationError, s.Validate)
    s = system.Shutdown([30, 40], None)
    self.assertRaises(system.ValidationError, s.Validate)
    s = system.Shutdown([30, 'reasons', 'True'], None)
    self.assertRaises(system.ValidationError, s.Validate)
    s = system.Shutdown([1, 2, 3, 4], None)
    self.assertRaises(system.ValidationError, s.Validate)
    s = system.Shutdown([30, 'reasons', True], None)
    s.Validate()
    s = system.Shutdown([30, 'reasons'], None)
    s.Validate()
    s = system.Shutdown([10], None)
    s.Validate()

if __name__ == '__main__':
  absltest.main()
