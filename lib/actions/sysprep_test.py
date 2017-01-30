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

"""Tests for glazier.lib.actions.sysprep."""

from pyfakefs import fake_filesystem
from glazier.lib.actions import sysprep
import mock
from google.apputils import basetest

UNATTEND_XML = r"""<?xml version='1.0' encoding='utf-8'?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
    <settings pass="specialize" wasPassProcessed="true">
        <component name="Microsoft-Windows-Shell-Setup">
            <RegisteredOrganization>Company</RegisteredOrganization>
            <RegisteredOwner>Employee</RegisteredOwner>
            <ComputerName>*</ComputerName>
            <ShowWindowsLive>false</ShowWindowsLive>
            <TimeZone>Central Standard Time</TimeZone>
            <CopyProfile>true</CopyProfile>
        </component>
    </settings>
    <settings pass="oobeSystem" wasPassProcessed="true">
        <component name="Microsoft-Windows-International-Core">
            <InputLocale>en-us</InputLocale>
            <SystemLocale>en-us</SystemLocale>
            <UILanguage>en-us</UILanguage>
            <UserLocale>en-us</UserLocale>
        </component>
        <component name="Microsoft-Windows-Shell-Setup">
            <TimeZone>Central Standard Time</TimeZone>
            <LogonCommands>
                <AsynchronousCommand wcm:action="add">
                    <CommandLine>cmd /c C:\prepare_build.bat</CommandLine>
                    <Description>Prepare build</Description>
                    <Order>1</Order>
                    <RequiresUserInput>true</RequiresUserInput>
                </AsynchronousCommand>
            </LogonCommands>
        </component>
    </settings>
</unattend>"""


class SysprepTest(basetest.TestCase):

  def setUp(self):
    fs = fake_filesystem.FakeFilesystem()
    fs.CreateDirectory('/windows/panther')
    fs.CreateFile('/windows/panther/unattend.xml', contents=UNATTEND_XML)
    self.fake_open = fake_filesystem.FakeFileOpen(fs)
    sysprep.os = fake_filesystem.FakeOsModule(fs)
    sysprep.open = self.fake_open

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testSetUnattendTimeZoneEditUnattend(self, build_info):
    st = sysprep.SetUnattendTimeZone([], build_info)
    st._EditUnattend(
        'Yakutsk Standard Time', unattend_path='/windows/panther/unattend.xml')
    with self.fake_open('/windows/panther/unattend.xml') as handle:
      result = [line.strip() for line in handle.readlines()]
      self.assertIn('<TimeZone>Yakutsk Standard Time</TimeZone>', result)
    # IOError
    self.assertRaises(sysprep.ActionError, st._EditUnattend,
                      'Yakutsk Standard Time',
                      '/windows/panther/noneattend.xml')

  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(
      sysprep.SetUnattendTimeZone, '_EditUnattend', autospec=True)
  @mock.patch.object(sysprep.dhcp, 'GetDhcpOption', autospec=True)
  def testSetUnattendTimeZoneRun(self, dhcp, edit, build_info):
    build_info.NetInterfaces.return_value = [
        mock.Mock(
            ip_address='127.0.0.1',
            mac_address='11:22:33:44:55:66',
            dhcp_server=None),
        mock.Mock(ip_address='127.0.0.2', mac_address=None, dhcp_server=None),
        mock.Mock(
            ip_address=None, mac_address='22:11:33:44:55:66', dhcp_server=None),
        mock.Mock(
            ip_address='10.1.10.1',
            mac_address='AA:BB:CC:DD:EE:FF',
            dhcp_server='192.168.1.1')
    ]
    st = sysprep.SetUnattendTimeZone([], build_info)
    # Normal Run
    dhcp.side_effect = iter([None, None, 'Antarctica/McMurdo'])
    st.Run()
    dhcp.assert_has_calls([
        mock.call(
            client_addr='127.0.0.1',
            client_mac='11:22:33:44:55:66',
            option=101,
            server_addr='255.255.255.255'),
        mock.call(
            client_addr='10.1.10.1',
            client_mac='AA:BB:CC:DD:EE:FF',
            option=101,
            server_addr='192.168.1.1'),
        mock.call(
            client_addr='10.1.10.1',
            client_mac='AA:BB:CC:DD:EE:FF',
            option=101,
            server_addr='255.255.255.255')
    ])
    edit.assert_called_with(st, u'New Zealand Standard Time')
    # Failed Mapping
    dhcp.side_effect = None
    dhcp.return_value = 'Antarctica/NorthPole'
    st.Run()
    edit.assert_called_with(st, u'Pacific Standard Time')
    # No Result
    dhcp.return_value = None
    st.Run()
    edit.assert_called_with(st, u'Pacific Standard Time')


if __name__ == '__main__':
  basetest.main()
