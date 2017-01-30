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

from glazier.lib.actions import updates
from glazier.lib.buildinfo import BuildInfo
import mock
from google.apputils import basetest


class UpdatesTest(basetest.TestCase):

  @mock.patch.object(BuildInfo, 'ReleasePath')
  @mock.patch('glazier.lib.download.Download.VerifyShaHash', autospec=True)
  @mock.patch('glazier.lib.download.Download.DownloadFile', autospec=True)
  @mock.patch.object(updates, 'Execute', autospec=True)
  @mock.patch.object(updates.file_util, 'CreateDirectories', autospec=True)
  def testUpdateMSU(self, mkdir, exe, dl, sha, rpath):
    bi = BuildInfo()

    # Setup
    remote = '@Drivers/HP/KB2990941-v3-x64.msu'
    local = r'c:\KB2990941-v3-x64.msu'
    sha_256 = (
        'd1acbdd8652d6c78ce284bf511f3a7f5f776a0a91357aca060039a99c6a93a16')
    conf = {'data': {'update': [[remote, local, sha_256]]},
            'path': ['/autobuild']}
    rpath.return_value = '/'

    # Success
    um = updates.UpdateMSU(conf['data']['update'], bi)
    um.Run()
    dl.assert_called_with(
        mock.ANY, ('https://glazier-server.example.com/'
                   'bin/Drivers/HP/KB2990941-v3-x64.msu'),
        local,
        show_progress=True)
    sha.assert_called_with(mock.ANY, local, sha_256)
    cache = updates.constants.SYS_CACHE
    exe.assert_called_with([[(
        'X:\\Windows\\System32\\dism.exe /image:c:\\ '
        '/Add-Package /PackagePath:c:\\KB2990941-v3-x64.msu '
        '/ScratchDir:%s\\Updates\\' % cache)]], mock.ANY)
    mkdir.assert_called_with('%s\\Updates\\' % cache)

    # Invalid format
    conf['data']['update'][0][1] = 'C:\\Windows6.1-KB2990941-v3-x64.cab'
    um = updates.UpdateMSU(conf['data']['update'], bi)
    self.assertRaises(updates.ActionError, um.Run)
    conf['data']['update'][0][1] = 'C:\\Windows6.1-KB2990941-v3-x64.msu'

    # Dism Fail
    exe.return_value.Run.side_effect = updates.ActionError()
    self.assertRaises(updates.ActionError, um.Run)

  def testUpdateMSUValidate(self):
    g = updates.UpdateMSU('String', None)
    self.assertRaises(updates.ValidationError, g.Validate)
    g = updates.UpdateMSU([[1, 2, 3]], None)
    self.assertRaises(updates.ValidationError, g.Validate)
    g = updates.UpdateMSU([[1, '/tmp/out/path']], None)
    self.assertRaises(updates.ValidationError, g.Validate)
    g = updates.UpdateMSU([['/tmp/src.zip', 2]], None)
    self.assertRaises(updates.ValidationError, g.Validate)
    g = updates.UpdateMSU(
        [['https://glazier/bin/src.msu', '/tmp/out/src.zip']], None)
    self.assertRaises(updates.ValidationError, g.Validate)
    g = updates.UpdateMSU(
        [['https://glazier/bin/src.msu', '/tmp/out/src.msu']], None)
    g.Validate()
    g = updates.UpdateMSU(
        [['https://glazier/bin/src.msu', '/tmp/out/src.msu', '12345']], None)
    g.Validate()
    g = updates.UpdateMSU([['https://glazier/bin/src.zip', '/tmp/out/src.zip',
                            '12345', '67890']], None)
    self.assertRaises(updates.ValidationError, g.Validate)


if __name__ == '__main__':
  basetest.main()
