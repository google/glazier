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

from glazier.lib import errors

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
    self.error = errors.BinaryExecutionError('some message')

  @mock.patch.object(splice.identity, 'get_hostname', autospec=True)
  def testGetHostnameExists(self, get_host):
    get_host.return_value = _HOSTNAME
    self.assertEqual(self.splice._get_hostname(),
                     splice.identity.get_hostname())

  @mock.patch.object(splice.identity, 'set_hostname', autospec=True)
  def testGetHostnameError(self, set_host):
    set_host.side_effect = splice.identity.Error
    with self.assertRaises(splice.Error):
      self.splice._get_hostname()

  @mock.patch.object(splice.identity, 'set_username', autospec=True)
  @mock.patch.object(splice.identity, 'get_username', autospec=True)
  def testGetUsernameNone(self, get_user, set_user):
    get_user.return_value = None
    set_user.return_value = _USERNAME
    self.assertEqual(
        self.splice._get_username(),
        fr'{splice.constants.DOMAIN_NAME}\{splice.identity.set_username()}')
    self.assertTrue(get_user.called)
    self.assertTrue(set_user.called)

  @mock.patch.object(splice.identity, 'get_username', autospec=True)
  def testGetUsernameExists(self, get_user):
    get_user.return_value = _USERNAME
    self.assertEqual(
        self.splice._get_username(),
        fr'{splice.constants.DOMAIN_NAME}\{splice.identity.get_username()}')

  @mock.patch.object(splice.identity, 'set_username', autospec=True)
  def testGetUsernameError(self, set_user):
    set_user.side_effect = splice.identity.Error
    with self.assertRaises(splice.Error):
      self.splice._get_username()

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  @mock.patch.object(splice.logging, 'info', autospec=True)
  def test_user_domain_join_success(self, i, user, hostname, eb):
    self.fs.CreateFile(self.splice.splice_binary)
    hostname.return_value = 'foo'
    user.return_value = 'bar'
    eb.return_value = 0
    self.splice.domain_join(unattended=False, fallback=False)
    i.assert_called_with('Domain join succeeded after %d attempt(s).', 1)

  @mock.patch.object(splice.time, 'sleep', autospec=True)
  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  @mock.patch.object(splice, 'logging', autospec=True)
  def test_user_domain_join_failure_success(self, log, user, hostname, eb,
                                            sleep):
    self.fs.CreateFile(self.splice.splice_binary)
    hostname.return_value = 'foo'
    user.return_value = 'bar'
    eb.side_effect = iter([self.error, 0])
    self.splice.domain_join(unattended=False, fallback=False)
    log.warning.assert_called_with(
        'Domain join attempt %d of %d failed. '
        'Retrying in %d second(s).', 1, 5, 30)
    log.info.assert_called_with('Domain join succeeded after %d attempt(s).', 2)
    self.assertTrue(sleep.called)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  def test_user_domain_join_execute_error(self, user, hostname, eb):
    self.fs.CreateFile(self.splice.splice_binary)
    hostname.return_value = 'foo'
    user.return_value = 'bar'
    eb.side_effect = self.error
    self.assertRaises(
        splice.Error, self.splice.domain_join, unattended=False, fallback=False)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  def test_unattended_domain_join_execute_error(self, user, hostname, eb):
    self.fs.CreateFile(self.splice.splice_binary)
    hostname.return_value = 'foo'
    user.return_value = 'bar'
    eb.side_effect = self.error
    self.assertRaises(
        splice.Error, self.splice.domain_join, unattended=True, fallback=False)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.Splice, '_get_username', autospec=True)
  @mock.patch.object(splice, 'logging', autospec=True)
  def test_unattended_domain_join_fallback_success(self, log, user, hostname,
                                                   eb):
    self.fs.CreateFile(self.splice.splice_binary)
    hostname.return_value = 'foo'
    user.return_value = 'bar'
    eb.side_effect = iter([self.error, 0, 0])
    self.splice.domain_join(max_retries=1)
    log.warning.assert_called_with('Failed to join domain after %d attempt(s).',
                                   1)
    log.info.assert_called_with(
        'Fallback domain join succeeded after %d attempt(s).', 1)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  @mock.patch.object(splice.logging, 'info', autospec=True)
  def test_unattended_domain_join_success(self, i, hostname, eb):
    self.fs.CreateFile(self.splice.splice_binary)
    hostname.return_value = 'foo'
    eb.return_value = 0
    self.splice.domain_join()
    i.assert_called_with('Domain join succeeded after %d attempt(s).', 1)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  def test_domain_join_empty_generator(self, hostname, eb):
    self.fs.CreateFile(self.splice.splice_binary)
    hostname.return_value = 'foo'
    eb.return_value = 0
    self.splice.domain_join()
    args = [
        '-cert_issuer=client', f'-cert_container={self.splice.cert_container}',
        f'-server={self.splice.splice_server}',
        '-really_join=true', '-unattended=true',
        f'-name={self.splice._get_hostname()}'
    ]
    eb.assert_called_with(self.splice.splice_binary, args, shell=True)

  @mock.patch.object(splice.execute, 'execute_binary', autospec=True)
  @mock.patch.object(splice.Splice, '_get_hostname', autospec=True)
  def test_domain_join_generator(self, hostname, eb):
    self.fs.CreateFile(self.splice.splice_binary)
    hostname.return_value = 'foo'
    eb.return_value = 0
    self.splice.domain_join(generator='baz')
    args = [
        '-cert_issuer=client', f'-cert_container={self.splice.cert_container}',
        f'-server={self.splice.splice_server}',
        '-really_join=true', '-unattended=true', '-generator_id=baz'
    ]
    eb.assert_called_with(self.splice.splice_binary, args, shell=True)


if __name__ == '__main__':
  absltest.main()
