# Lint as: python3
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

"""Tests for glazier.lib.actions.registry."""

from absl.testing import absltest
from glazier.lib import constants
from glazier.lib.actions import registry
import mock

ROOT = 'HKLM'
PATH = constants.REG_ROOT
NAME = 'some_name'
VALUE = 'some_data'
TYPE = 'REG_SZ'
USE_64 = constants.USE_REG_64
ARGS = [ROOT, PATH, NAME, VALUE, TYPE]


class RegistryTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'set_value', autospec=True)
  def testAdd(self, sv, build_info):
    # Mock add registry keys
    ra = registry.RegAdd(ARGS, build_info)
    ra.Run()
    sv.assert_called_with(NAME, VALUE, ROOT, PATH, TYPE, USE_64)

    # Registry error
    sv.side_effect = registry.registry.Error
    self.assertRaises(registry.ActionError, ra.Run)

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'set_value', autospec=True)
  def testMultiAdd(self, sv, build_info):
    ra = registry.RegAdd(ARGS, build_info)
    ra.Run()
    sv.assert_called_with(NAME, VALUE, ROOT, PATH, TYPE, USE_64)

    # Missing arguments
    args = [ROOT, PATH, NAME, VALUE]
    ra = registry.RegAdd(args, build_info)
    self.assertRaises(registry.ActionError, ra.Run)

    # Multiple missing arguments
    args = [ARGS, [ROOT, PATH, NAME, VALUE]]
    ra = registry.MultiRegAdd(args, build_info)
    self.assertRaises(registry.ActionError, ra.Run)

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'remove_value', autospec=True)
  def testDel(self, rv, build_info):
    # Variable definition
    args = [ROOT, PATH, NAME]

    # Mock delete registry keys
    rd = registry.RegDel(args, build_info)
    rd.Run()
    rv.assert_called_with(NAME, ROOT, PATH, USE_64)

    # Registry error
    rv.side_effect = registry.registry.Error
    self.assertRaises(registry.ActionError, rd.Run)

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'remove_value', autospec=True)
  def testMultiDel(self, rv, build_info):
    # Mock delete registry keys
    args = [ROOT, PATH, NAME, False]
    rd = registry.RegDel(args, build_info)
    rd.Run()
    rv.assert_called_with(NAME, ROOT, PATH, False)

    # Missing arguments
    args = [ROOT, PATH]
    rd = registry.RegDel(args, build_info)
    self.assertRaises(registry.ActionError, rd.Run)

    # Multiple missing arguments
    args = [[ROOT, PATH], [ROOT]]
    rd = registry.MultiRegDel(args, build_info)
    self.assertRaises(registry.ActionError, rd.Run)

  def testAddValidation(self):
    # List not passed
    r = registry.RegAdd(NAME, None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Too many args
    r = registry.RegAdd([ROOT, PATH, NAME, NAME, TYPE, True, NAME], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Not enough args
    r = registry.RegAdd([PATH, NAME, NAME, TYPE], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Type error
    r = registry.RegAdd([ROOT, PATH, NAME, '1', 'REG_DWORD'], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Too many keys
    r = registry.RegAdd([
        [ROOT, PATH, NAME, 1, TYPE],
        [ROOT, PATH, NAME, 100, TYPE]], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Valid calls
    r = registry.RegAdd([ROOT, PATH, NAME, VALUE, TYPE], None)
    r.Validate()

  def testMultiAddValidation(self):
    # Valid calls
    r = registry.MultiRegAdd([ARGS, [ROOT, PATH, NAME, 100, 'REG_DWORD']], None)
    r.Validate()

  def testDelValidation(self):
    # List not passed
    r = registry.RegDel(NAME, None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Too many args
    r = registry.RegDel([ROOT, PATH, NAME, VALUE], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Not enough args
    r = registry.RegDel([PATH, NAME], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Too many keys
    r = registry.RegDel([[ROOT, PATH, NAME], [ROOT, PATH, NAME]], None)
    self.assertRaises(registry.ValidationError, r.Validate)

    # Valid calls
    r = registry.RegDel([ROOT, PATH, NAME], None)
    r.Validate()

  def testMultiDelValidation(self):
    # Valid calls
    r = registry.MultiRegDel([[ROOT, PATH, NAME], [ROOT, PATH, NAME]], None)
    r.Validate()

if __name__ == '__main__':
  absltest.main()
