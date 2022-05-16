# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Tests for glazier.lib.beyondcorp."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from unittest import mock

from absl.testing import absltest
from absl.testing import flagsaver
from glazier.lib import beyondcorp
from glazier.lib import registry
from pyfakefs import fake_filesystem
from requests.models import Response

_TEST_SEED = '{"Seed": {"Seed": "seed_contents"}, "Signature": "Signature"}'
_TEST_WIM = 'test_wim'
_TEST_WIM_PATH = r'D:\sources\boot.wim'
_TEST_WIM_HASH = b'xxaroj1bgT5sObhJ0HwOtqpn+Nx0gO/Wz5wATtYK7Tk='
DECODED_HASH = _TEST_WIM_HASH.decode('utf-8')


def _create_sign_response(code, status, wim_hash):
  sign_resp = Response()
  sign_resp.encoding = 'utf-8'
  sign_resp._content = ('{"Status": "%s", "ErrorCode": 0, "SignedURL": '
                        '"%s", "Path": ""}' % (status, wim_hash)).encode()
  sign_resp.status_code = code
  return sign_resp


class BeyondcorpTest(absltest.TestCase):

  def patch_constant(self, module, constant_name, new_value):
    patcher = mock.patch.object(module, constant_name, new_value)
    self.addCleanup(patcher.stop)
    return patcher.start()

  def setUp(self):
    super(BeyondcorpTest, self).setUp()
    self.__saved_flags = flagsaver.save_flag_values()
    mock_wmi = mock.patch.object(
        beyondcorp.wmi_query, 'WMIQuery', autospec=True)
    self.addCleanup(mock_wmi.stop)
    self.mock_wmi = mock_wmi.start()
    self.filesystem = fake_filesystem.FakeFilesystem()
    self.filesystem.create_file(r'C:\seed.json', contents=_TEST_SEED)
    self.filesystem.create_file(_TEST_WIM_PATH, contents=_TEST_WIM)
    beyondcorp.os = fake_filesystem.FakeOsModule(self.filesystem)
    beyondcorp.open = fake_filesystem.FakeFileOpen(self.filesystem)
    self.beyondcorp = beyondcorp.BeyondCorp()

    # Very important, unless you want tests that fail indefinitely to backoff
    # for 10 minutes.
    self.patch_constant(beyondcorp, 'BACKOFF_MAX_TIME', 20)  # in seconds

  def tearDown(self):
    super(BeyondcorpTest, self).tearDown()
    flagsaver.restore_flag_values(self.__saved_flags)

  def test_signed_url_disabled(self):
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp.GetSignedUrl('unstable/test.yaml')

  def test_path_and_endpoint_none(self):
    beyondcorp.FLAGS.use_signed_url = True
    beyondcorp.FLAGS.sign_endpoint = 'https://sign-endpoint/sign'
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp.GetSignedUrl('unstable/test.yaml')

    beyondcorp.FLAGS.sign_endpoint = None
    beyondcorp.FLAGS.seed_path = '/seed/seed.json'
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp.GetSignedUrl('unstable/test.yaml')

  @mock.patch.object(beyondcorp.BeyondCorp, '_GetDisk', autospec=True)
  @mock.patch.object(beyondcorp.hw_info.HWInfo, 'MacAddresses', autospec=True)
  @mock.patch.object(beyondcorp.requests, 'post', autospec=True)
  def test_signed_url(self, mock_post, mock_mac_addresses, mock_get_disk):
    mock_get_disk.return_value = 'D'
    mock_mac_addresses.return_value = ['00:00:00:00:00:00']
    mock_post.return_value = _create_sign_response(200, 'Success', DECODED_HASH)
    beyondcorp.FLAGS.use_signed_url = True
    beyondcorp.FLAGS.sign_endpoint = 'https://sign-endpoint/sign'
    beyondcorp.FLAGS.seed_path = r'C:\seed.json'

    sign = self.beyondcorp.GetSignedUrl('unstable/test.yaml')
    mock_post.assert_called_once_with(
        'https://sign-endpoint/sign',
        data='{"Hash": "%s",'
        '"Mac": ["00:00:00:00:00:00"],'
        '"Path": "unstable/test.yaml",'
        '"Seed": {"Seed": "seed_contents"},'
        '"Signature": "Signature"'
        '}' % _TEST_WIM_HASH.decode('utf-8'))
    self.assertEqual(sign, _TEST_WIM_HASH.decode('utf-8'))

  @mock.patch.object(beyondcorp.BeyondCorp, '_GetDisk', autospec=True)
  @mock.patch.object(beyondcorp.hw_info.HWInfo, 'MacAddresses', autospec=True)
  @mock.patch.object(beyondcorp.requests, 'post', autospec=True)
  def test_signed_url_fail(self, mock_post, mock_mac_addresses, mock_get_disk):

    mock_get_disk.return_value = 'D'
    mock_mac_addresses.return_value = ['00:00:00:00:00:00']
    mock_post.return_value = _create_sign_response(200, 'Success', DECODED_HASH)
    beyondcorp.FLAGS.use_signed_url = True
    beyondcorp.FLAGS.sign_endpoint = 'https://sign-endpoint/sign'
    beyondcorp.FLAGS.seed_path = r'C:\seed.json'

    mock_post.return_value = _create_sign_response(400, 'Success', DECODED_HASH)
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp.GetSignedUrl('unstable/test.yaml')

    mock_post.return_value = _create_sign_response(200, 'Failed', DECODED_HASH)
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp.GetSignedUrl('unstable/test.yaml')

    mock_post.return_value = _create_sign_response(400, 'Failed', DECODED_HASH)
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp.GetSignedUrl('unstable/test.yaml')

    mock_post.return_value = _create_sign_response(
        200, 'Failed', 'invalid_hash')
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp.GetSignedUrl('unstable/test.yaml')

  @mock.patch.object(beyondcorp.BeyondCorp, '_GetDisk', autospec=True)
  @mock.patch.object(beyondcorp.hw_info.HWInfo, 'MacAddresses', autospec=True)
  @mock.patch.object(beyondcorp.requests, 'post', autospec=True)
  def test_signed_url_connection_error(
      self, mock_post, mock_mac_addresses, mock_get_disk):

    mock_get_disk.return_value = 'D'
    mock_mac_addresses.return_value = ['00:00:00:00:00:00']
    mock_post.return_value = _create_sign_response(200, 'Success', DECODED_HASH)
    beyondcorp.FLAGS.use_signed_url = True
    beyondcorp.FLAGS.sign_endpoint = 'https://sign-endpoint/sign'
    beyondcorp.FLAGS.seed_path = r'C:\seed.json'

    mock_post.side_effect = beyondcorp.requests.exceptions.ConnectionError
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp.GetSignedUrl('unstable/test.yaml')

  def test_read_file(self):
    beyondcorp.FLAGS.seed_path = r'C:\seed.json'
    seed = self.beyondcorp._ReadFile()
    self.assertEqual(
        seed,
        json.loads('{"Seed": {"Seed": "seed_contents"},'
                   '"Signature": "Signature"}'))

    with self.assertRaises(beyondcorp.BCError):
      beyondcorp.FLAGS.seed_path = r'C:\bad_seed.json'
      self.beyondcorp._ReadFile()

  @mock.patch.object(registry, 'set_value', autospec=True)
  def test_check_beyond_corp_true(self, mock_set_value):
    beyondcorp.FLAGS.use_signed_url = True
    mock_set_value.assert_called_with = ('beyond_corp', 'True')
    self.assertEqual(self.beyondcorp.CheckBeyondCorp(), True)

  @mock.patch.object(registry, 'set_value', autospec=True)
  def test_check_beyond_corp_true_error(self, mock_set_value):
    beyondcorp.FLAGS.use_signed_url = True
    mock_set_value.side_effect = registry.Error
    self.assertRaises(beyondcorp.BCError, self.beyondcorp.CheckBeyondCorp)

  @mock.patch.object(registry, 'get_value', autospec=True)
  def test_check_beyond_corp_get(self, mock_get_value):
    mock_get_value.return_value = 'True'
    self.assertEqual(self.beyondcorp.CheckBeyondCorp(), True)

  @mock.patch.object(registry, 'get_value', autospec=True)
  def test_check_beyond_corp_get_error(self, mock_get_value):
    mock_get_value.side_effect = registry.Error
    self.assertRaises(beyondcorp.BCError, self.beyondcorp.CheckBeyondCorp)

  @mock.patch.object(registry, 'set_value', autospec=True)
  def test_check_beyond_corp_false(self, mock_set_value):
    beyondcorp.FLAGS.use_signed_url = False
    mock_set_value.assert_called_with = ('beyond_corp', 'False')
    self.assertEqual(self.beyondcorp.CheckBeyondCorp(), False)

  @mock.patch.object(registry, 'set_value', autospec=True)
  def test_check_beyond_corp_false_error(self, mock_set_value):
    beyondcorp.FLAGS.use_signed_url = False
    mock_set_value.side_effect = registry.Error
    self.assertRaises(beyondcorp.BCError, self.beyondcorp.CheckBeyondCorp)

  def test_get_disk(self):
    self.mock_wmi.return_value.Query.return_value = [mock.Mock(Name='D')]
    self.assertEqual(
        self.beyondcorp._GetDisk(beyondcorp.constants.USB_VOLUME_LABEL), 'D')

  def test_get_disk_none(self):
    self.mock_wmi.return_value.Query.return_value = [mock.Mock(Name=None)]
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp._GetDisk(beyondcorp.constants.USB_VOLUME_LABEL)

  def test_get_disk_error(self):
    self.mock_wmi.return_value.Query.side_effect = beyondcorp.wmi_query.WmiError
    with self.assertRaises(beyondcorp.BCError):
      self.beyondcorp._GetDisk(beyondcorp.constants.USB_VOLUME_LABEL)


if __name__ == '__main__':
  absltest.main()
