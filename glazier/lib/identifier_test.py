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
"""Tests for glazier.lib.winpe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from glazier.lib import identifier
import mock

TEST_UUID = identifier.uuid.UUID('12345678123456781234567812345678')
TEST_SERIAL = '1A19SEL90000R90DZN7A'
TEST_ID = TEST_SERIAL+'-'+str(TEST_UUID)[:7]


class IdentifierTest(absltest.TestCase):

  def setUp(self):
    super(IdentifierTest, self).setUp()
    self.identifier = identifier.ImageID()
    mock_wmi = mock.patch.object(
        identifier.buildinfo.hw_info.wmi_query, 'WMIQuery', autospec=True)
    self.addCleanup(mock_wmi.stop)
    mock_wmi.start()

  @mock.patch.object(identifier.uuid, 'uuid4', autospec=True)
  def test_generate_uuid(self, mock_uuid):
    mock_uuid.return_value = str(TEST_UUID)[:7]
    self.assertEqual(self.identifier._generate_uuid(), '1234567')

  @mock.patch.object(
      identifier.buildinfo.hw_info.HWInfo, 'BiosSerial', autospec=True)
  @mock.patch.object(identifier.uuid, 'uuid4', autospec=True)
  def test_generate_id(self, mock_uuid, mock_serial):
    mock_uuid.return_value = str(TEST_UUID)[:7]
    mock_serial.return_value = TEST_SERIAL
    self.assertEqual(self.identifier._generate_id(), TEST_ID)

  @mock.patch.object(identifier.ImageID, 'get_id', autospec=True)
  @mock.patch.object(identifier.winpe, 'check_winpe', autospec=True)
  def test_need_id_true(self, wpe, getid):
    wpe.return_value = True
    getid.return_value = None
    self.assertTrue(self.identifier._need_id())

  @mock.patch.object(identifier.winpe, 'check_winpe', autospec=True)
  def test_need_id_host(self, wpe):
    wpe.return_value = False
    self.assertFalse(self.identifier._need_id())

  @mock.patch.object(identifier.ImageID, 'get_id', autospec=True)
  @mock.patch.object(identifier.registry, 'Registry', autospec=True)
  def test_need_id_exists(self, unused_reg, getid):
    getid.return_value = TEST_ID
    self.assertFalse(self.identifier._need_id())

  @mock.patch.object(identifier.ImageID, '_need_id', autospec=True)
  @mock.patch.object(identifier.ImageID, '_generate_id', autospec=True)
  @mock.patch.object(identifier.registry, 'Registry', autospec=True)
  def test_set_id(self, reg, genid, needid):
    needid.return_value = True
    genid.return_value = TEST_ID
    self.identifier.set_id()
    reg.assert_called_with('HKLM')
    reg.return_value.SetKeyValue.assert_has_calls([
        mock.call(
            key_path=identifier.constants.REG_ROOT,
            key_name='image_id',
            key_value=TEST_ID,
            key_type='REG_SZ',
            use_64bit=identifier.constants.USE_REG_64),
    ])

  @mock.patch.object(identifier.ImageID, '_need_id', autospec=True)
  def test_set_id_none(self, needid):
    needid.return_value = False
    self.identifier.set_id()
    self.assertEqual(self.identifier.set_id(), None)

  @mock.patch.object(identifier.ImageID, '_need_id', autospec=True)
  @mock.patch.object(identifier.registry, 'Registry', autospec=True)
  def test_set_id_error(self, reg, needid):
    needid.return_value = True
    reg.return_value.SetKeyValue.side_effect = identifier.registry.RegistryError
    self.assertRaises(identifier.Error, self.identifier.set_id)

  @mock.patch.object(identifier.registry, 'Registry', autospec=True)
  def test_get_id(self, reg):
    reg.return_value.GetKeyValue.return_value = TEST_ID
    self.assertEqual(self.identifier.get_id(), TEST_ID)
    reg.assert_called_with('HKLM')
    reg.return_value.GetKeyValue.assert_called_with(
        key_path=identifier.constants.REG_ROOT,
        key_name='image_id',
        use_64bit=identifier.constants.USE_REG_64)

  @mock.patch.object(identifier.registry, 'Registry', autospec=True)
  def test_get_id_none(self, reg):
    reg.return_value.GetKeyValue.side_effect = identifier.registry.RegistryError
    self.assertEqual(self.identifier.get_id(), None)

if __name__ == '__main__':
  absltest.main()
