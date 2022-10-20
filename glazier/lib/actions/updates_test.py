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
"""Tests for glazier.lib.actions.updates."""

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import test_utils
from glazier.lib.actions import updates
from glazier.lib.buildinfo import BuildInfo


class UpdatesTest(test_utils.GlazierTestCase):

  @mock.patch.object(BuildInfo, 'ReleasePath')
  @mock.patch.object(BuildInfo, 'Branch')
  @mock.patch('glazier.lib.download.Download.VerifyShaHash', autospec=True)
  @mock.patch('glazier.lib.download.Download.DownloadFile', autospec=True)
  @mock.patch.object(updates.execute, 'execute_binary', autospec=True)
  @mock.patch.object(updates.file_util, 'CreateDirectories', autospec=True)
  def test_update_msu(self, mock_createdirectories, mock_execute_binary,
                      mock_downloadfile, mock_verifyshahash, mock_branch,
                      mock_releasepath):
    bi = BuildInfo()

    # Setup
    remote = '@Drivers/HP/KB2990941-v3-x64.msu'
    local = r'c:\KB2990941-v3-x64.msu'
    sha_256 = (
        'd1acbdd8652d6c78ce284bf511f3a7f5f776a0a91357aca060039a99c6a93a16')
    conf = {
        'data': {
            'update': [[remote, local, sha_256]]
        },
        'path': ['/autobuild']
    }
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = '/'

    # Success
    um = updates.UpdateMSU(conf['data']['update'], bi)
    um.Run()
    mock_downloadfile.assert_called_with(
        mock.ANY, ('https://glazier-server.example.com/'
                   'bin/Drivers/HP/KB2990941-v3-x64.msu'),
        local,
        show_progress=True)
    mock_verifyshahash.assert_called_with(mock.ANY, local, sha_256)
    cache = updates.constants.SYS_CACHE
    mock_execute_binary.assert_called_with(
        f'{updates.constants.SYS_SYSTEM32}/dism.exe', [
            '/image:c:\\', '/Add-Package',
            '/PackagePath:c:\\KB2990941-v3-x64.msu',
            f'/ScratchDir:{cache}\\Updates\\'
        ],
        shell=True)
    mock_createdirectories.assert_called_with('%s\\Updates\\' % cache)

    # Invalid format
    conf['data']['update'][0][1] = 'C:\\Windows6.1-KB2990941-v3-x64.cab'
    um = updates.UpdateMSU(conf['data']['update'], bi)
    with self.assert_raises_with_validation(updates.ActionError):
      um.Run()
    conf['data']['update'][0][1] = 'C:\\Windows6.1-KB2990941-v3-x64.msu'

    # Dism Fail
    mock_execute_binary.side_effect = updates.execute.ExecError('some_command')
    with self.assert_raises_with_validation(updates.ActionError):
      um.Run()

  @parameterized.named_parameters(
      ('_invalid_arg_type_1', 'String'),
      ('_invalid_arg_type_2', [[1, 2, 3]]),
      ('_invalid_arg_type_3', [[1, '/tmp/out/path']]),
      ('_invalid_arg_type_4', [['/tmp/src.zip', 2]]),
      ('_invalid_file_type',
       [['https://glazier/bin/src.msu', '/tmp/out/src.zip']]),
      ('_invalid_args_length',
       [['https://glazier/bin/src.zip', '/tmp/out/src.zip', '12345', '67890']]),
  )
  def test_update_msu_validation_error(self, action_args):
    with self.assert_raises_with_validation(updates.ValidationError):
      updates.UpdateMSU(action_args, None).Validate()

  @parameterized.named_parameters(
      ('_no_hash', [['https://glazier/bin/src.msu', '/tmp/out/src.msu']]),
      ('_all_args',
       [['https://glazier/bin/src.msu', '/tmp/out/src.msu', '12345']]),
  )
  def test_update_msu_validation_success(self, action_args):
    updates.UpdateMSU(action_args, None).Validate()


if __name__ == '__main__':
  absltest.main()
