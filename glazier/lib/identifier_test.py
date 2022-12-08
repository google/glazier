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
"""Tests for glazier.lib.winpe."""

import os
from unittest import mock

from absl.testing import absltest
from glazier.lib import identifier
from glazier.lib import test_utils

from glazier.lib import constants

TEST_UUID = identifier.uuid.UUID('12345678123456781234567812345678')
TEST_SERIAL = '1A19SEL90000R90DZN7A'
TEST_ID = TEST_SERIAL + '-' + str(TEST_UUID)[:7]


class IdentifierTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(IdentifierTest, self).setUp()
    mock_wmi = mock.patch.object(
        identifier.hw_info.wmi_query, 'WMIQuery', autospec=True)
    self.addCleanup(mock_wmi.stop)
    mock_wmi.start()

    temp_dir = self.create_tempdir().full_path
    self.patch_constant(identifier.constants, 'SYS_CACHE', temp_dir)

  @mock.patch.object(identifier.hw_info.HWInfo, 'BiosSerial', autospec=True)
  @mock.patch.object(identifier.uuid, 'uuid4', autospec=True)
  def test_generate_id(self, mock_uuid, mock_serial):
    mock_uuid.return_value = str(TEST_UUID)[:7]
    mock_serial.return_value = TEST_SERIAL
    self.assertEqual(identifier._generate_id(), TEST_ID)

  @mock.patch.object(identifier.registry, 'set_value', autospec=True)
  @mock.patch.object(identifier, '_generate_id', autospec=True)
  def test_set_id(self, mock_generate_id, mock_set_value):
    mock_generate_id.return_value = TEST_ID
    identifier._set_id()
    mock_set_value.assert_called_with(
        'image_id', TEST_ID, path=constants.REG_ROOT)
    self.assertEqual(identifier._set_id(), TEST_ID)

  @mock.patch.object(identifier.registry, 'set_value', autospec=True)
  def test_set_reg_error(self, mock_set_value):
    mock_set_value.side_effect = identifier.registry.RegistryWriteError(
        'some_name', 'some_value', 'some_path')
    with self.assert_raises_with_validation(identifier.Error):
      identifier._set_id()

  @mock.patch.object(identifier.registry, 'set_value', autospec=True)
  def test_check_file(self, mock_set_value):
    self.create_tempfile(
        file_path=os.path.join(identifier.constants.SYS_CACHE,
                               'build_info.yaml'),
        content='{BUILD: {opt 1: true, TIMER_opt 2: some value, image_id: 12345}}\n'
    )
    identifier._check_file()
    mock_set_value.assert_called_with(
        'image_id', 12345, path=constants.REG_ROOT)
    self.assertEqual(identifier._check_file(), 12345)

  def test_check_file_no_id(self):
    self.create_tempfile(
        file_path=os.path.join(identifier.constants.SYS_CACHE,
                               'build_info.yaml'),
        content='{BUILD: {opt 1: true, TIMER_opt 2: some value, image_num: 12345}}\n'
    )
    with self.assert_raises_with_validation(identifier.Error):
      identifier._check_file()

  @mock.patch.object(identifier.registry, 'set_value', autospec=True)
  def test_check_file_reg_error(self, mock_set_value):
    self.create_tempfile(
        file_path=os.path.join(identifier.constants.SYS_CACHE,
                               'build_info.yaml'),
        content='{BUILD: {opt 1: true, TIMER_opt 2: some value, image_id: 12345}}\n'
    )
    mock_set_value.side_effect = identifier.registry.RegistryWriteError(
        'some_name', 'some_value', 'some_path')
    with self.assert_raises_with_validation(identifier.Error):
      identifier._check_file()

  def test_check_file_no_file(self):
    with self.assert_raises_with_validation(identifier.Error):
      identifier._check_file()

  @mock.patch.object(identifier.registry, 'get_value', autospec=True)
  def test_check_id_get(self, mock_get_value):
    mock_get_value.return_value = TEST_ID
    self.assertEqual(identifier.check_id(), TEST_ID)

  @mock.patch.object(identifier.registry, 'get_value', autospec=True)
  @mock.patch.object(identifier.winpe, 'check_winpe', autospec=True)
  def test_check_id_get_error(self, mock_check_winpe, mock_get_value):
    mock_check_winpe.return_value = False
    mock_get_value.side_effect = identifier.registry.Error
    with self.assert_raises_with_validation(identifier.Error):
      identifier.check_id()

  @mock.patch.object(identifier, '_set_id', autospec=True)
  @mock.patch.object(identifier.registry, 'get_value', autospec=True)
  @mock.patch.object(identifier.winpe, 'check_winpe', autospec=True)
  def test_check_id_set(self, mock_check_winpe, mock_get_value, mock_set_id):
    mock_get_value.return_value = None
    mock_check_winpe.return_value = True
    identifier.check_id()
    self.assertTrue(mock_set_id.called)

  @mock.patch.object(identifier, '_check_file', autospec=True)
  @mock.patch.object(identifier.registry, 'get_value', autospec=True)
  @mock.patch.object(identifier.winpe, 'check_winpe', autospec=True)
  def test_check_id_file(self, mock_check_winpe, mock_get_value,
                         mock_check_file):
    mock_get_value.return_value = None
    mock_check_winpe.return_value = False
    mock_check_file.return_value = TEST_ID
    self.assertEqual(identifier.check_id(), TEST_ID)


if __name__ == '__main__':
  absltest.main()
