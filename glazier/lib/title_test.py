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

from unittest import mock

from absl import flags
from absl.testing import absltest
from absl.testing import flagsaver
from glazier.lib import test_utils
from glazier.lib import title

_PREFIX = 'Glazier'
_STRING = 'Test string with spaces'
_TEST_ID = '1A19SEL90000R90DZN7A-1234567'
_RELEASE = '21.08.00'
_STAGE = '42'

FLAGS = flags.FLAGS


class TitleTest(test_utils.GlazierTestCase):

  @flagsaver.flagsaver()
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.stage, 'get_active_stage', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_all(self, mock_check_winpe, mock_get_active_stage,
                          mock_release, mock_imageid):
    mock_check_winpe.return_value = True
    mock_imageid.return_value = _TEST_ID
    mock_get_active_stage.return_value = _STAGE
    mock_release.return_value = _RELEASE
    FLAGS.config_root_path = '/'
    self.assertEqual(
        title._base_title(),
        f'WinPE - Stage: {_STAGE} - {_RELEASE} - {_TEST_ID}')

  @flagsaver.flagsaver()
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_wpe(self, mock_check_winpe, mock_release, mock_imageid):
    mock_check_winpe.return_value = True
    FLAGS.config_root_path = None
    mock_imageid.return_value = None
    mock_release.return_value = None
    self.assertEqual(title._base_title(), 'WinPE')

  @flagsaver.flagsaver()
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_path(self, mock_check_winpe, mock_release, mock_imageid):
    mock_check_winpe.return_value = False
    FLAGS.config_root_path = '/some/directory'
    mock_imageid.return_value = None
    mock_release.return_value = None
    self.assertEqual(title._base_title(), 'some/directory')

  @flagsaver.flagsaver()
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_id(self, mock_check_winpe, mock_release, mock_imageid):
    mock_check_winpe.return_value = False
    mock_imageid.return_value = _TEST_ID
    mock_release.return_value = None
    FLAGS.config_root_path = None
    self.assertEqual(title._base_title(), _TEST_ID)

  @flagsaver.flagsaver()
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_base_title_none(self, mock_check_winpe, mock_release, mock_imageid):
    mock_check_winpe.return_value = False
    mock_imageid.return_value = None
    mock_release.return_value = None
    FLAGS.config_root_path = None
    self.assertEqual(title._base_title(), '')

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_prefix(self, mock_base_title):
    mock_base_title.return_value = ''
    self.assertEqual(title._build_title(), _PREFIX)

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_string(self, mock_base_title):
    mock_base_title.return_value = ''
    self.assertEqual(title._build_title(_STRING), f'{_PREFIX} [{_STRING}]')

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_string_base(self, mock_base_title):
    mock_base_title.return_value = _TEST_ID
    self.assertEqual(
        title._build_title(_STRING), f'{_PREFIX} [{_STRING} - {_TEST_ID}]')

  @mock.patch.object(title, '_base_title', autospec=True)
  def test_build_title_base(self, mock_base_title):
    mock_base_title.return_value = _TEST_ID
    self.assertEqual(title._build_title(), f'{_PREFIX} [{_TEST_ID}]')

  @flagsaver.flagsaver()
  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_set_title_string(self, mock_check_winpe, mock_release, mock_imageid,
                            mock_system):
    FLAGS.config_root_path = '/'
    mock_check_winpe.return_value = False
    mock_imageid.return_value = _TEST_ID
    mock_release.return_value = None
    self.assertEqual(
        title.set_title(_STRING), f'{_PREFIX} [{_STRING} - {_TEST_ID}]')
    mock_system.assert_called_with(f'title {_PREFIX} [{_STRING} - {_TEST_ID}]')

  @flagsaver.flagsaver()
  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.stage, 'get_active_stage', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_set_title_stage(self, mock_check_winpe, mock_get_active_stage,
                           mock_release, mock_imageid, mock_system):
    mock_check_winpe.return_value = False
    mock_imageid.return_value = None
    mock_get_active_stage.return_value = _STAGE
    FLAGS.config_root_path = '/'
    mock_release.return_value = None
    self.assertEqual(title.set_title(), f'{_PREFIX} [Stage: {_STAGE}]')
    mock_system.assert_called_with(f'title {_PREFIX} [Stage: {_STAGE}]')

  @flagsaver.flagsaver()
  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(title.buildinfo.BuildInfo, 'Release', autospec=True)
  @mock.patch.object(title.winpe, 'check_winpe', autospec=True)
  def test_set_title_release(self, mock_check_winpe, mock_release, mock_imageid,
                             mock_system):
    FLAGS.config_root_path = '/'
    mock_check_winpe.return_value = False
    mock_imageid.return_value = None
    mock_release.return_value = _RELEASE
    self.assertEqual(title.set_title(), f'{_PREFIX} [{_RELEASE}]')
    mock_system.assert_called_with(f'title {_PREFIX} [{_RELEASE}]')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_base(self, mock_build_title, mock_system):
    mock_build_title.return_value = f'{_PREFIX} [{_TEST_ID}]'
    self.assertEqual(title.set_title(), f'{_PREFIX} [{_TEST_ID}]')
    mock_system.assert_called_with(f'title {_PREFIX} [{_TEST_ID}]')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_prefix(self, mock_build_title, mock_system):
    mock_build_title.return_value = _PREFIX
    self.assertEqual(title.set_title(), _PREFIX)
    mock_system.assert_called_with(f'title {_PREFIX}')

  @mock.patch.object(title.os, 'system', autospec=True)
  @mock.patch.object(title, '_build_title', autospec=True)
  def test_set_title_error(self, mock_build_title, mock_system):
    mock_build_title.return_value = _PREFIX
    mock_system.side_effect = OSError
    with self.assert_raises_with_validation(title.Error):
      title.set_title()

if __name__ == '__main__':
  absltest.main()
