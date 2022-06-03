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

"""Tests for glazier.lib.config.base."""

from unittest import mock

from absl.testing import absltest
from glazier.lib import buildinfo
from glazier.lib.config import base

from glazier.lib import errors


class BaseTest(absltest.TestCase):

  def setUp(self):
    super(BaseTest, self).setUp()
    self.buildinfo = buildinfo.BuildInfo()
    self.cb = base.ConfigBase(self.buildinfo)

  @mock.patch.object(base.actions, 'SetTimer', autospec=True)
  def testProcessActions(self, set_timer):
    # valid command
    self.cb._ProcessAction('SetTimer', ['TestTimer'])
    set_timer.assert_called_with(build_info=self.buildinfo, args=['TestTimer'])
    self.assertTrue(set_timer.return_value.Run.called)
    # invalid command
    self.assertRaises(errors.ConfigError, self.cb._ProcessAction, 'BadSetTimer',
                      ['Timer1'])
    # action error
    set_timer.side_effect = errors.ActionError
    self.assertRaises(errors.ConfigError, self.cb._ProcessAction, 'SetTimer',
                      ['Timer1'])


if __name__ == '__main__':
  absltest.main()
