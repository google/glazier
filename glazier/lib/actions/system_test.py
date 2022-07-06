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
from glazier.lib import events
from glazier.lib.actions import system


class SystemTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_reboot_pop(self, mock_buildinfo):
    r = system.Reboot([30, 'reboot for reasons', True], mock_buildinfo)
    with self.assertRaises(events.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '30')
    self.assertEqual(str(ex), 'reboot for reasons')
    self.assertEqual(ex.pop_next, True)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_reboot_reason(self, mock_buildinfo):
    r = system.Reboot([30, 'reboot for reasons'], mock_buildinfo)
    with self.assertRaises(events.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '30')
    self.assertEqual(str(ex), 'reboot for reasons')
    self.assertEqual(ex.pop_next, False)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_reboot_timeout(self, mock_buildinfo):
    r = system.Reboot([10], mock_buildinfo)
    with self.assertRaises(events.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '10')
    self.assertEqual(str(ex), 'unspecified')
    self.assertEqual(ex.pop_next, False)

  # TODO(b/237812617): Parameterize this test.
  def test_reboot_validate(self):
    r = system.Reboot(True, None)
    with self.assertRaises(system.ValidationError):
      r.Validate()
    r = system.Reboot([30, 40], None)
    with self.assertRaises(system.ValidationError):
      r.Validate()
    r = system.Reboot([30, 'reasons', 'True'], None)
    with self.assertRaises(system.ValidationError):
      r.Validate()
    r = system.Reboot([1, 2, 3, 4], None)
    with self.assertRaises(system.ValidationError):
      r.Validate()
    r = system.Reboot([30, 'reasons', True], None)
    r.Validate()
    r = system.Reboot([30, 'reasons'], None)
    r.Validate()
    r = system.Reboot([30], None)
    r.Validate()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_shutdown_pop(self, mock_buildinfo):
    r = system.Shutdown([15, 'shutdown for reasons', True], mock_buildinfo)
    with self.assertRaises(events.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '15')
    self.assertEqual(str(ex), 'shutdown for reasons')
    self.assertEqual(ex.pop_next, True)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_shutdown_reason(self, mock_buildinfo):
    r = system.Shutdown([15, 'shutdown for reasons'], mock_buildinfo)
    with self.assertRaises(events.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '15')
    self.assertEqual(str(ex), 'shutdown for reasons')
    self.assertEqual(ex.pop_next, False)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_shutdown_timeout(self, mock_buildinfo):
    r = system.Shutdown([1], mock_buildinfo)
    with self.assertRaises(events.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '1')
    self.assertEqual(str(ex), 'unspecified')
    self.assertEqual(ex.pop_next, False)

  # TODO(b/237812617): Parameterize this test.
  def test_shutdown_validate(self):
    s = system.Shutdown(True, None)
    with self.assertRaises(system.ValidationError):
      s.Validate()
    s = system.Shutdown([30, 40], None)
    with self.assertRaises(system.ValidationError):
      s.Validate()
    s = system.Shutdown([30, 'reasons', 'True'], None)
    with self.assertRaises(system.ValidationError):
      s.Validate()
    s = system.Shutdown([1, 2, 3, 4], None)
    with self.assertRaises(system.ValidationError):
      s.Validate()
    s = system.Shutdown([30, 'reasons', True], None)
    s.Validate()
    s = system.Shutdown([30, 'reasons'], None)
    s.Validate()
    s = system.Shutdown([10], None)
    s.Validate()

if __name__ == '__main__':
  absltest.main()
