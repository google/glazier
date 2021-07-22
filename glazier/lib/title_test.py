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

_PREFIX = 'Glazier'
_STRING = 'Test string with spaces'
_TEST_ID = '1A19SEL90000R90DZN7A-1234567'
_RELEASE = '21.08.00'
_STAGE = '42'


class TitleTest(absltest.TestCase):

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.stage, 'get_active_stage', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_all(self, wpe, stage, release, ii):
    wpe.return_value = True
    ii.return_value = _TEST_ID
    stage.return_value = _STAGE
    release.return_value = _RELEASE
    title.constants.FLAGS.config_root_path = '/some/directory'
    self.assertEqual(
        title._base_title(),
        f'WinPE - some/directory - Stage: {_STAGE} - {_RELEASE} - {_TEST_ID}')

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_wpe(self, wpe, release, ii):
    wpe.return_value = True
    title.constants.FLAGS.config_root_path = None
    ii.return_value = None
    release.return_value = None
    self.assertEqual(title._base_title(), 'WinPE')

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_path(self, wpe, release, ii):
    wpe.return_value = False
    title.constants.FLAGS.config_root_path = '/some/directory'
    ii.return_value = None
    release.return_value = None
    self.assertEqual(title._base_title(), 'some/directory')

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_id(self, wpe, release, ii):
    wpe.return_value = False
    ii.return_value = _TEST_ID
    release.return_value = None
    title.constants.FLAGS.config_root_path = None
    self.assertEqual(title._base_title(), _TEST_ID)

  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_none(self, wpe, release, ii):
    wpe.return_value = False
    ii.return_value = None
    release.return_value = None
    title.constants.FLAGS.config_root_path = None
    self.assertEqual(title._base_title(), '')

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_prefix(self, bt):
    bt.return_value = ''
    self.assertEqual(title._build_title(), _PREFIX)

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_string(self, bt):
    bt.return_value = ''
    self.assertEqual(title._build_title(_STRING), f'{_PREFIX} [{_STRING}]')

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_string_base(self, bt):
    bt.return_value = _TEST_ID
    self.assertEqual(
        title._build_title(_STRING), f'{_PREFIX} [{_STRING} - {_TEST_ID}]')

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_base(self, bt):
    bt.return_value = _TEST_ID
    self.assertEqual(title._build_title(), f'{_PREFIX} [{_TEST_ID}]')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_set_title_string(self, wpe, release, ii, sys):
    wpe.return_value = False
    ii.return_value = _TEST_ID
    release.return_value = None
    self.assertEqual(
        title.set_title(_STRING), f'{_PREFIX} [{_STRING} - {_TEST_ID}]')
    sys.assert_called_with(f'title {_PREFIX} [{_STRING} - {_TEST_ID}]')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.stage, 'get_active_stage', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_set_title_stage(self, wpe, stage, release, ii, sys):
    wpe.return_value = False
    ii.return_value = None
    stage.return_value = _STAGE
    release.return_value = None
    self.assertEqual(title.set_title(), f'{_PREFIX} [Stage: {_STAGE}]')
    sys.assert_called_with(f'title {_PREFIX} [Stage: {_STAGE}]')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_set_title_release(self, wpe, release, ii, sys):
    wpe.return_value = False
    ii.return_value = None
    release.return_value = _RELEASE
    self.assertEqual(title.set_title(), f'{_PREFIX} [{_RELEASE}]')
    sys.assert_called_with(f'title {_PREFIX} [{_RELEASE}]')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_base(self, bt, sys):
    bt.return_value = f'{_PREFIX} [{_TEST_ID}]'
    self.assertEqual(title.set_title(), f'{_PREFIX} [{_TEST_ID}]')
    sys.assert_called_with(f'title {_PREFIX} [{_TEST_ID}]')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_prefix(self, bt, sys):
    bt.return_value = _PREFIX
    self.assertEqual(title.set_title(), _PREFIX)
    sys.assert_called_with(f'title {_PREFIX}')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_error(self, bt, sys):
    bt.return_value = _PREFIX
    sys.side_effect = OSError
    self.assertRaises(title.Error, title.set_title)

if __name__ == '__main__':
  absltest.main()
