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
"""Tests for glazier.lib.splice."""

from unittest import mock

from absl.testing import absltest
from glazier.lib import splice
from pyfakefs import fake_filesystem

_USERNAME = 'bert'
_HOSTNAME = 'earnie-pc'


class SpliceTest(absltest.TestCase):

  def setUp(self):
    super(SpliceTest, self).setUp()
    self.fs = fake_filesystem.FakeFilesystem()
    splice.os = fake_filesystem.FakeOsModule(self.fs)
    splice.open = fake_filesystem.FakeFileOpen(self.fs)
    splice.os.environ['ProgramFiles'] = r'C:\Program Files'
    self.splice = splice.Splice()
    self.error = splice.execute.Error

  @mock.patch.object(splice.identity, 'get_hostname', autospec=True)
  def test_get_hostname_exists(self, mock_get_hostname):
    mock_get_hostname.return_value = _HOSTNAME
    self.assertEqual(
        self.splice._get_hostname(), splice.identity.get_hostname())

  @mock.patch.object(splice.identity, 'set_hostname', autospec=True)
  def test_get_hostname_error(self, mock_set_hostname):
    mock_set_hostname.side_effect = splice.identity.Error
    with self.assertRaises(splice.Error):
      self.splice._get_hostname()

  @mock.patch.object(splice.identity, 'set_username', autospec=True)
  @mock.patch.object(splice.identity, 'get_username', autospec=True)
  def test_get_username_none(self, mock_get_username, mock_set_username):
    mock_get_username.return_value = None
    mock_set_username.return_value = _USERNAME
    self.assertEqual(
        self.splice._get_username(),
        fr'{splice.constants.DOMAIN_NAME}\{splice.identity.set_username()}')
    self.assertTrue(mock_get_username.called)
    self.assertTrue(mock_set_username.called)

  @mock.patch.object(splice.identity, 'get_username', autospec=True)
  def test_get_username_exists(self, mock_get_username):
    mock_get_username.return_value = _USERNAME
    self.assertEqual(
        self.splice._get_username(),
        fr'{splice.constants.DOMAIN_NAME}\{splice.identity.get_username()}')

  @mock.patch.object(splice.identity, 'set_username', autospec=True)
  def test_get_username_error(self, mock_set_username):
    mock_set_username.side_effect = splice.identity.Error
    with self.assertRaises(splice.Error):
      self.splice._get_username()

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  @mock.patch.object(splice.logging, 'info', autospec=True)
  def test_user_domain_join_success(
      self, mock_info, mock_get_username, mock_get_hostname,
      mock_execute_binary):

    self.fs.CreateFile(self.splice.splice_binary)
    mock_get_hostname.return_value = 'foo'
    mock_get_username.return_value = 'bar'
    mock_execute_binary.return_value = 0
    self.splice.domain_join(unattended=False, fallback=False)
    mock_info.assert_called_with(
        'Domain join succeeded after %d attempt(s).', 1)

  @mock.patch.object(splice.time, 'sleep', autospec=True)
  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  @mock.patch.object(splice, 'logging', autospec=True)
  def test_user_domain_join_failure_success(
      self, mock_logging, mock_get_username, mock_get_hostname,
      mock_execute_binary, mock_sleep):

    self.fs.CreateFile(self.splice.splice_binary)
    mock_get_hostname.return_value = 'foo'
    mock_get_username.return_value = 'bar'
    mock_execute_binary.side_effect = iter([self.error, 0])
    self.splice.domain_join(unattended=False, fallback=False)
    mock_logging.warning.assert_called_with(
        'Domain join attempt %d of %d failed. '
        'Retrying in %d second(s).', 1, 5, 30)
    mock_logging.info.assert_called_with(
        'Domain join succeeded after %d attempt(s).', 2)
    self.assertTrue(mock_sleep.called)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  def test_user_domain_join_execute_error(
      self, mock_get_username, mock_get_hostname, mock_execute_binary):

    self.fs.CreateFile(self.splice.splice_binary)
    mock_get_hostname.return_value = 'foo'
    mock_get_username.return_value = 'bar'
    mock_execute_binary.side_effect = self.error
    with self.assertRaises(splice.Error):
      self.splice.domain_join(unattended=False, fallback=False)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  def test_unattended_domain_join_execute_error(
      self, mock_get_username, mock_get_hostname, mock_execute_binary):

    self.fs.CreateFile(self.splice.splice_binary)
    mock_get_hostname.return_value = 'foo'
    mock_get_username.return_value = 'bar'
    mock_execute_binary.side_effect = self.error
    with self.assertRaises(splice.Error):
      self.splice.domain_join(unattended=True, fallback=False)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  @mock.patch.object(splice, 'logging', autospec=True)
  def test_unattended_domain_join_fallback_success(
      self, mock_logging, mock_get_username, mock_get_hostname,
      mock_execute_binary):

    self.fs.CreateFile(self.splice.splice_binary)
    mock_get_hostname.return_value = 'foo'
    mock_get_username.return_value = 'bar'
    mock_execute_binary.side_effect = iter([self.error, 0, 0])
    self.splice.domain_join(max_retries=1)
    mock_logging.warning.assert_called_with(
        'Failed to join domain after %d attempt(s).', 1)
    mock_logging.info.assert_called_with(
        'Fallback domain join succeeded after %d attempt(s).', 1)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.logging, 'info', autospec=True)
  def test_unattended_domain_join_success(
      self, mock_info, mock_get_hostname, mock_execute_binary):

    self.fs.CreateFile(self.splice.splice_binary)
    mock_get_hostname.return_value = 'foo'
    mock_execute_binary.return_value = 0
    self.splice.domain_join()
    mock_info.assert_called_with(
        'Domain join succeeded after %d attempt(s).', 1)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  def test_domain_join_empty_generator(
      self, mock_get_hostname, mock_execute_binary):

    self.fs.CreateFile(self.splice.splice_binary)
    mock_get_hostname.return_value = 'foo'
    mock_execute_binary.return_value = 0
    self.splice.domain_join()
    args = [
        '-cert_issuer=client', f'-cert_container={self.splice.cert_container}',
        f'-server={self.splice.splice_server}',
        '-really_join=true', '-unattended=true',
        f'-name={self.splice._get_hostname()}'
    ]
    mock_execute_binary.assert_called_with(
        self.splice.splice_binary, args, shell=True)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  def test_domain_join_generator(self, mock_get_hostname, mock_execute_binary):
    self.fs.CreateFile(self.splice.splice_binary)
    mock_get_hostname.return_value = 'foo'
    mock_execute_binary.return_value = 0
    self.splice.domain_join(generator='baz')
    args = [
        '-cert_issuer=client', f'-cert_container={self.splice.cert_container}',
        f'-server={self.splice.splice_server}',
        '-really_join=true', '-unattended=true', '-generator_id=baz'
    ]
    mock_execute_binary.assert_called_with(
        self.splice.splice_binary, args, shell=True)


if __name__ == '__main__':
  absltest.main()
