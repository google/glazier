# Lint as: python3
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for glazier.lib.title."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from glazier.lib import title
import mock

PREFIX = 'Glazier'
STRING = 'Stage: 42'
TEST_ID = '1A19SEL90000R90DZN7A-1234567'


class TitleTest(absltest.TestCase):

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.reg_util, 'check_winpe', autospec=True)
  def test_base_title_all(self, wpe, ii):
    wpe.return_value = True
    ii.return_value = TEST_ID
    title.constants.FLAGS.config_root_path = '/some/directory'
    self.assertEqual(title._base_title(),
                     'WinPE - some/directory - {}'.format(TEST_ID))

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.reg_util, 'check_winpe', autospec=True)
  def test_base_title_wpe(self, wpe, ii):
    wpe.return_value = True
    title.constants.FLAGS.config_root_path = None
    ii.return_value = None
    self.assertEqual(title._base_title(), 'WinPE')

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.reg_util, 'check_winpe', autospec=True)
  def test_base_title_path(self, wpe, ii):
    wpe.return_value = False
    title.constants.FLAGS.config_root_path = '/some/directory'
    ii.return_value = None
    self.assertEqual(title._base_title(), 'some/directory')

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.reg_util, 'check_winpe', autospec=True)
  def test_base_title_id(self, wpe, ii):
    wpe.return_value = False
    ii.return_value = TEST_ID
    title.constants.FLAGS.config_root_path = None
    self.assertEqual(
        title._base_title(), TEST_ID)

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.reg_util, 'check_winpe', autospec=True)
  def test_base_title_none(self, wpe, ii):
    wpe.return_value = False
    ii.return_value = None
    title.constants.FLAGS.config_root_path = None
    self.assertEqual(title._base_title(), '')

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_prefix(self, bt):
    bt.return_value = ''
    self.assertEqual(title._build_title(), PREFIX)

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_string(self, bt):
    bt.return_value = ''
    self.assertEqual(title._build_title(STRING),
                     '{0} [{1}]'.format(PREFIX, STRING))

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_string_base(self, bt):
    bt.return_value = TEST_ID
    self.assertEqual(title._build_title(STRING),
                     '{0} [{1} - {2}]'.format(PREFIX, STRING, TEST_ID))

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_base(self, bt):
    bt.return_value = TEST_ID
    self.assertEqual(title._build_title(),
                     '{0} [{1}]'.format(PREFIX, TEST_ID))

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.reg_util, 'check_winpe', autospec=True)
  def test_set_title_string(self, wpe, ii, sys):
    wpe.return_value = False
    ii.return_value = TEST_ID
    self.assertEqual(title.set_title(STRING),
                     '{0} [{1} - {2}]'.format(PREFIX, STRING, TEST_ID))
    sys.assert_called_with(
        'title {0} [{1} - {2}]'.format(PREFIX, STRING, TEST_ID))

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_base(self, bt, sys):
    bt.return_value = '{0} [{1}]'.format(PREFIX, TEST_ID)
    self.assertEqual(
        title.set_title(), '{0} [{1}]'.format(PREFIX, TEST_ID))
    sys.assert_called_with('title {0} [{1}]'.format(PREFIX, TEST_ID))

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_prefix(self, bt, sys):
    bt.return_value = PREFIX
    self.assertEqual(title.set_title(), PREFIX)
    sys.assert_called_with('title {}'.format(PREFIX))

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_error(self, bt, sys):
    bt.return_value = PREFIX
    sys.side_effect = OSError
    self.assertRaises(title.Error, title.set_title)

if __name__ == '__main__':
  absltest.main()
