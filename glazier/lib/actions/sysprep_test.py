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

import builtins
from unittest import mock

from absl.testing import absltest
from glazier.lib import test_utils
from glazier.lib.actions import sysprep
from glazier.lib.config import files

_REAL_OPEN = builtins.open


def _open_with_cp1252_default(*args, **kwargs):
  kwargs.setdefault('encoding', 'cp1252')
  return _REAL_OPEN(*args, **kwargs)


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


class SysprepTest(test_utils.GlazierTestCase):

  def test_config_uses_utf8(self):
    yaml_path = self.create_tempfile(file_path='utf8.yaml').full_path
    with _REAL_OPEN(yaml_path, 'wb') as handle:
      handle.write(b'name: caf\xc3\xa9')

    with mock.patch('builtins.open', side_effect=_open_with_cp1252_default):
      config = files.Read(yaml_path)

    self.assertEqual(config['name'], 'caf\u00e9')

  def test_unattend_uses_utf8(self):
    unattend_path = self.create_tempfile(
        file_path='utf8-unattend.xml', content=UNATTEND_XML).full_path
    xml_data = UNATTEND_XML.encode('ascii').replace(
        b'<RegisteredOwner>Employee</RegisteredOwner>',
        b'<RegisteredOwner>cafe\xcc\x81</RegisteredOwner>')
    with _REAL_OPEN(unattend_path, 'wb') as handle:
      handle.write(xml_data)

    st = sysprep.SetUnattendTimeZone([], mock.Mock())
    with mock.patch('builtins.open', side_effect=_open_with_cp1252_default):
      st._EditUnattend('Yakutsk Standard Time', unattend_path)

    with _REAL_OPEN(unattend_path, 'rb') as handle:
      updated_xml = handle.read().decode('utf-8')
    self.assertIn('<RegisteredOwner>cafe\u0301</RegisteredOwner>', updated_xml)
    self.assertIn('<TimeZone>Yakutsk Standard Time</TimeZone>', updated_xml)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_set_unattend_time_zone_edit_unattend(self, mock_buildinfo):

    unattend_path = self.create_tempfile(
        file_path='unattend.xml', content=UNATTEND_XML).full_path

    st = sysprep.SetUnattendTimeZone([], mock_buildinfo)
    st._EditUnattend('Yakutsk Standard Time', unattend_path=unattend_path)

    with open(unattend_path) as handle:
      result = [line.strip() for line in handle.readlines()]
      self.assertIn('<TimeZone>Yakutsk Standard Time</TimeZone>', result)

    # IOError
    with self.assert_raises_with_validation(sysprep.ActionError):
      st._EditUnattend(
          'Yakutsk Standard Time', '/windows/panther/noneattend.xml')

  @mock.patch.object(sysprep.timezone, 'Timezone', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(
      sysprep.SetUnattendTimeZone, '_EditUnattend', autospec=True)
  @mock.patch.object(sysprep.dhcp, 'GetDhcpOption', autospec=True)
  def test_set_unattend_time_zone_run(
      self, mock_getdhcpoption, mock_editunattend, mock_buildinfo,
      mock_timezone):

    mock_buildinfo.NetInterfaces.return_value = [
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
    st = sysprep.SetUnattendTimeZone([], mock_buildinfo)

    # Normal Run
    mock_timezone.return_value.TranslateZone.return_value = (
        'New Zealand Standard Time')
    mock_getdhcpoption.side_effect = iter([b'', b'', b'Antarctica/McMurdo'])
    st.Run()
    mock_getdhcpoption.assert_has_calls([
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
    mock_editunattend.assert_called_with(st, u'New Zealand Standard Time')
    mock_timezone.assert_called_with(load_map=True)
    mock_timezone.return_value.TranslateZone.assert_called_with(
        'Antarctica/McMurdo')
    mock_timezone.reset_mock()

    # Failed Mapping
    mock_getdhcpoption.side_effect = None
    mock_getdhcpoption.return_value = b'Antarctica/NorthPole'
    mock_timezone.return_value.TranslateZone.return_value = ''
    st.Run()
    mock_editunattend.assert_called_with(st, u'Pacific Standard Time')
    mock_timezone.assert_called_with(load_map=True)
    mock_timezone.return_value.TranslateZone.assert_called_with(
        'Antarctica/NorthPole')
    mock_timezone.reset_mock()

    # No Result
    mock_getdhcpoption.return_value = b''
    st.Run()
    mock_editunattend.assert_called_with(st, u'Pacific Standard Time')
    self.assertFalse(mock_timezone.called)


if __name__ == '__main__':
  absltest.main()
