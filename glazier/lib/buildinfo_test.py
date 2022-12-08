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
"""Tests for glazier.lib.buildinfo."""

import datetime
import re
from unittest import mock

from absl import flags
from absl.testing import absltest
from absl.testing import flagsaver
from glazier.lib import buildinfo
from glazier.lib import test_utils
from glazier.lib import timers
from glazier.lib.config import files
import yaml

from gwinpy.wmi.hw_info import DeviceId

FLAGS = flags.FLAGS

_RELEASE_INFO = """
supported_models:
  tier1:
    [
      Windows Tier 1 Device,  # Testing
    ]
  tier2:
    [
      Windows Tier 2 Device,  # Testing
    ]
"""

_VERSION_INFO = """
winpe-version: 12345
versions:
  windows-7-stable: 'stable'
  windows-10-stable: 'stable'
  windows-10-unstable: 'unstable'
"""


class _REGEXP(object):
  """Mock helper for matching regexp matches.."""

  def __init__(self, pattern):
    self._regexp = re.compile(pattern)

  def __eq__(self, other):
    return bool(self._regexp.search(other))

  def __ne__(self, other):
    return not self._regexp.search(other)

  def __repr__(self):
    return '<REGEXP(%s)>' % self._regexp.pattern


class BuildInfoTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(BuildInfoTest, self).setUp()

    # setup
    mock_wmi = mock.patch.object(
        buildinfo.hw_info.wmi_query, 'WMIQuery', autospec=True)
    self.addCleanup(mock_wmi.stop)
    mock_wmi.start()
    self.buildinfo = buildinfo.BuildInfo()

  def test_chooser_options(self):
    opt1 = {
        'name': 'system_locale',
        'type': 'radio_menu',
        'prompt': 'System Locale',
        'options': []
    }
    opt2 = {
        'name': 'core_ps_shell',
        'type': 'toggle',
        'prompt': 'Set system shell to PowerShell',
        'options': []
    }
    self.buildinfo.AddChooserOption(opt1)
    self.buildinfo.AddChooserOption(opt2)
    back = self.buildinfo.GetChooserOptions()
    self.assertEqual(back[0]['name'], 'system_locale')
    self.assertEqual(back[1]['name'], 'core_ps_shell')
    self.assertLen(back, 2)
    self.buildinfo.FlushChooserOptions()
    back = self.buildinfo.GetChooserOptions()
    self.assertEmpty(back)

  def test_store_chooser_responses(self):
    """Store responses from the Chooser UI."""
    resp = {'system_locale': 'en-us', 'core_ps_shell': True}
    self.buildinfo.StoreChooserResponses(resp)
    self.assertEqual(self.buildinfo._chooser_responses['USER_system_locale'],
                     'en-us')
    self.assertTrue(self.buildinfo._chooser_responses['USER_core_ps_shell'])

  @flagsaver.flagsaver
  def test_binary_server_from_flag(self):
    FLAGS.binary_server = 'https://glazier-server.example.com'
    self.assertEqual(self.buildinfo.BinaryServer(),
                     'https://glazier-server.example.com')

  def test_binary_server_changes(self):
    r = self.buildinfo.BinaryServer(
        set_to='https://glazier-server-1.example.com')
    self.assertEqual(r, 'https://glazier-server-1.example.com')
    # remains the same
    self.assertEqual(self.buildinfo.BinaryServer(),
                     'https://glazier-server-1.example.com')
    # changes
    r = self.buildinfo.BinaryServer(
        set_to='https://glazier-server-2.example.com/')
    self.assertEqual(r, 'https://glazier-server-2.example.com')
    # remains the same
    self.assertEqual(self.buildinfo.BinaryServer(),
                     'https://glazier-server-2.example.com')

  @flagsaver.flagsaver
  def test_binary_server_fallback(self):
    FLAGS.config_server = 'https://glazier-server-3.example.com'
    self.assertEqual(self.buildinfo.BinaryServer(),
                     'https://glazier-server-3.example.com')

  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  def test_config_path(self, mock_bin):
    mock_bin.return_value = 'https://glazier-server.example.com/bin/'
    self.assertEqual(self.buildinfo.BinaryPath(), mock_bin.return_value)

  @flagsaver.flagsaver
  def test_config_server_from_flag(self):
    FLAGS.config_server = 'https://glazier-server.example.com'
    self.assertEqual(self.buildinfo.ConfigServer(),
                     'https://glazier-server.example.com')

  def test_config_server_changes(self):
    r = self.buildinfo.ConfigServer(
        set_to='https://glazier-server-1.example.com')
    self.assertEqual(r, 'https://glazier-server-1.example.com')
    # remains the same
    self.assertEqual(self.buildinfo.ConfigServer(),
                     'https://glazier-server-1.example.com')
    # changes
    r = self.buildinfo.ConfigServer(
        set_to='https://glazier-server-2.example.com/')
    self.assertEqual(r, 'https://glazier-server-2.example.com')
    # remains the same
    self.assertEqual(self.buildinfo.ConfigServer(),
                     'https://glazier-server-2.example.com')

  def test_config_server(self):
    return_value = 'https://glazier-server.example.com'
    self.assertEqual(self.buildinfo.ConfigServer(), return_value)

  @mock.patch.object(buildinfo.identifier, 'check_id', autospec=True)
  def test_image_id(self, mock_check_id):
    mock_check_id.return_value = '1A19SEL90000R90DZN7A-1234567'
    result = self.buildinfo.ImageID()
    self.assertEqual(result, '1A19SEL90000R90DZN7A-1234567')

  def test_build_pin_match(self):
    with mock.patch.object(
        buildinfo.BuildInfo, 'ComputerModel', autospec=True) as mock_model:
      mock_model.return_value = 'HP Z620 Workstation'
      # Direct include
      self.assertTrue(
          self.buildinfo.BuildPinMatch(
              'computer_model', ['HP Z640 Workstation', 'HP Z620 Workstation']))
      # Direct exclude
      self.assertFalse(
          self.buildinfo.BuildPinMatch(
              'computer_model', ['HP Z640 Workstation', 'HP Z840 Workstation']))
      # Inverse exclude
      self.assertFalse(
          self.buildinfo.BuildPinMatch('computer_model',
                                       ['!HP Z620 Workstation']))
      # Inverse exclude (second)
      self.assertFalse(
          self.buildinfo.BuildPinMatch(
              'computer_model',
              ['!HP Z840 Workstation', '!HP Z620 Workstation']))
      # Inverse include
      self.assertTrue(
          self.buildinfo.BuildPinMatch('computer_model',
                                       ['!VMWare Virtual Platform']))
      # Inverse include (second)
      self.assertTrue(
          self.buildinfo.BuildPinMatch(
              'computer_model',
              ['!HP Z640 Workstation', '!HP Z840 Workstation']))
      # Substrings
      self.assertTrue(
          self.buildinfo.BuildPinMatch('computer_model',
                                       ['hp Z840', 'hp Z620']))

    # Device Ids
    with mock.patch.object(
        buildinfo.BuildInfo, 'DeviceIds', autospec=True) as mock_deviceids:
      mock_deviceids.return_value = ['WW-XX-YY-ZZ', '11-22-33-44']
      # Mismatch
      self.assertFalse(
          self.buildinfo.BuildPinMatch(
              'device_id', ['AA-BB-CC-DD', 'EE-FF-GG-HH', '11-22-33-55']))
      # Match
      self.assertTrue(
          self.buildinfo.BuildPinMatch(
              'device_id', ['AA-BB-CC-DD', 'WW-XX-YY-ZZ', 'EE-FF-GG-HH']))
      # Match
      self.assertTrue(
          self.buildinfo.BuildPinMatch('device_id',
                                       ['AA-BB-CC-DD', 'WW-XX-YY-VV', '11-22']))

    # Strict matches
    with mock.patch.object(
        buildinfo.BuildInfo, 'OsCode', autospec=True) as mock_oscode:
      mock_oscode.return_value = 'win10'
      self.assertTrue(self.buildinfo.BuildPinMatch('os_code', ['win10']))
      self.assertTrue(self.buildinfo.BuildPinMatch('os_code', ['WIN10']))
      self.assertFalse(self.buildinfo.BuildPinMatch('os_code', ['win7']))
      self.assertFalse(self.buildinfo.BuildPinMatch('os_code', ['wi']))
      self.assertFalse(self.buildinfo.BuildPinMatch('os_code', ['']))

    # Invalid pin
    with self.assert_raises_with_validation(buildinfo.Error):
      self.buildinfo.BuildPinMatch('no_existo', ['invalid pin value'])

  def test_build_user_pin_match(self):
    self.buildinfo.StoreChooserResponses({'puppet': True, 'locale': 'de-de'})
    self.assertFalse(self.buildinfo.BuildPinMatch('USER_puppet', [False]))
    self.assertTrue(self.buildinfo.BuildPinMatch('USER_puppet', [True]))
    self.assertTrue(
        self.buildinfo.BuildPinMatch('USER_locale', ['en-us', 'de-de']))
    self.assertFalse(
        self.buildinfo.BuildPinMatch('USER_locale', ['en-us', 'fr-fr']))
    self.assertFalse(self.buildinfo.BuildPinMatch('USER_locale', []))
    self.assertFalse(self.buildinfo.BuildPinMatch('USER_missing', ['na']))

  @flagsaver.flagsaver
  def test_image_type_ffu(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_image_type = 'FFU'
    self.assertEqual(self.buildinfo.ImageType(), 'ffu')

  @flagsaver.flagsaver
  def test_image_type_unknown(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_image_type = ''
    self.assertEqual(self.buildinfo.ImageType(), 'unknown')

  @mock.patch.object(buildinfo.registry, 'get_values', autospec=True)
  def test_installed_software(self, mock_get_values):
    mock_get_values.return_value = [
        'Mozilla FireFox', 'Google Chrome', 'Microsoft Edge'
    ]

    self.assertTrue(
        self.buildinfo.BuildPinMatch('is_installed', ['Google Chrome']))
    self.assertTrue(self.buildinfo.BuildPinMatch('is_installed', ['!Safari']))
    self.assertFalse(self.buildinfo.BuildPinMatch('is_installed', ['Chrome']))
    self.assertFalse(
        self.buildinfo.BuildPinMatch('is_installed', ['!Google Chrome']))

  @mock.patch.object(buildinfo.winpe, 'check_winpe', autospec=True)
  def test_cache_path(self, mock_check_winpe):
    mock_check_winpe.return_value = False
    self.assertEqual(self.buildinfo.CachePath(), buildinfo.constants.SYS_CACHE)

  @mock.patch.object(buildinfo.winpe, 'check_winpe', autospec=True)
  def test_cache_path_win_pe(self, mock_check_winpe):
    mock_check_winpe.return_value = True
    self.assertEqual(self.buildinfo.CachePath(),
                     buildinfo.constants.WINPE_CACHE)

  @mock.patch.object(
      buildinfo.hw_info.HWInfo, 'ComputerSystemManufacturer', autospec=True)
  def test_computer_manufacturer(self, mock_manufacturer):
    mock_manufacturer.return_value = 'Google Inc.'
    result = self.buildinfo.ComputerManufacturer()
    self.assertEqual(result, 'Google Inc.')
    self.buildinfo.ComputerManufacturer.cache_clear()
    mock_manufacturer.return_value = None
    with self.assert_raises_with_validation(buildinfo.Error):
      self.buildinfo.ComputerManufacturer()

  @mock.patch.object(
      buildinfo.hw_info.HWInfo, 'ComputerSystemModel', autospec=True)
  def test_computer_model(self, mock_model):
    mock_model.return_value = 'HP Z620 Workstation'
    result = self.buildinfo.ComputerModel()
    self.assertEqual(result, 'HP Z620 Workstation')
    mock_model.return_value = '2537CE2'
    self.assertEqual(result, 'HP Z620 Workstation')  # caching
    self.buildinfo.ComputerModel.cache_clear()
    result = self.buildinfo.ComputerModel()
    self.assertEqual(result, '2537CE2')
    self.buildinfo.ComputerModel.cache_clear()
    mock_model.return_value = None
    with self.assert_raises_with_validation(buildinfo.Error):
      self.buildinfo.ComputerModel()

  @flagsaver.flagsaver
  def test_host_spec_flags(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_hostname = 'TEST-HOST'
    FLAGS.glazier_spec_fqdn = 'TEST-HOST.example.com'
    self.assertEqual(self.buildinfo.ComputerName(), 'TEST-HOST')
    self.assertEqual(self.buildinfo.Fqdn(), 'TEST-HOST.example.com')

  @flagsaver.flagsaver
  def test_os_spec_flags(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_os = 'windows-10-test'
    self.assertEqual(self.buildinfo.ComputerOs(), 'windows-10-test')

  @flagsaver.flagsaver
  def test_lab_spec_flags_true(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_lab = 'True'
    self.assertTrue(self.buildinfo.Lab())

  @flagsaver.flagsaver
  def test_lab_spec_flags_false(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_lab = ''
    self.assertFalse(self.buildinfo.Lab())

  @mock.patch.object(
      buildinfo.beyondcorp.BeyondCorp, 'CheckBeyondCorp', autospec=True)
  @flagsaver.flagsaver
  def test_beyond_corp_pin_true(self, mock_checkbeyondcorp):
    mock_checkbeyondcorp.return_value = True
    self.assertTrue(self.buildinfo.BuildPinMatch('beyond_corp', ['True']))
    self.assertTrue(self.buildinfo.BeyondCorp())

  @mock.patch.object(
      buildinfo.beyondcorp.BeyondCorp, 'CheckBeyondCorp', autospec=True)
  @flagsaver.flagsaver
  def test_beyond_corp_pin_false(self, mock_checkbeyondcorp):
    mock_checkbeyondcorp.return_value = False
    self.assertTrue(self.buildinfo.BuildPinMatch('beyond_corp', ['!True']))
    self.assertFalse(self.buildinfo.BeyondCorp())
    self.assertTrue(self.buildinfo.BuildPinMatch('beyond_corp', ['False']))
    self.assertFalse(self.buildinfo.BeyondCorp())

  @mock.patch.object(buildinfo.hw_info.HWInfo, 'BiosSerial', autospec=True)
  def test_computer_serial(self, mock_biosserial):
    mock_biosserial.return_value = '5KD1BP1'
    result = self.buildinfo.ComputerSerial()
    self.assertEqual(result, '5KD1BP1')

  @mock.patch.object(buildinfo.hw_info.HWInfo, 'PciDevices', autospec=True)
  def test_device_ids(self, mock_pcidevices):
    test_dev = DeviceId(ven='8086', dev='1E10', subsys='21FB17AA', rev='C4')
    mock_pcidevices.return_value = [test_dev]
    self.assertEqual(['8086-1E10-21FB17AA-C4'], self.buildinfo.DeviceIds())

  def test_device_id_pinning(self):
    local_ids = ['11-22-33-44', 'AA-BB-CC-DD', 'AA-BB-CC-DD']
    self.assertTrue(
        self.buildinfo._StringPinner(local_ids, ['AA-BB-CC-DD'], loose=True))
    self.assertTrue(
        self.buildinfo._StringPinner(local_ids, ['AA-BB-CC'], loose=True))
    self.assertTrue(
        self.buildinfo._StringPinner(local_ids, ['AA-BB'], loose=True))
    self.assertTrue(self.buildinfo._StringPinner(local_ids, ['AA'], loose=True))
    self.assertFalse(
        self.buildinfo._StringPinner(local_ids, ['DD-CC-BB-AA'], loose=True))
    self.assertFalse(
        self.buildinfo._StringPinner(local_ids, ['BB-CC'], loose=True))

  @mock.patch.object(buildinfo.hw_info, 'HWInfo', autospec=True)
  def test_hw_info(self, mock_hwinfo):
    result = self.buildinfo._HWInfo()
    self.assertEqual(result, mock_hwinfo.return_value)
    self.assertEqual(self.buildinfo._hw_info, mock_hwinfo.return_value)

  @mock.patch.object(buildinfo.hw_info.HWInfo, 'IsLaptop', autospec=True)
  def test_is_laptop(self, mock_islaptop):
    mock_islaptop.return_value = True
    self.assertTrue(self.buildinfo.IsLaptop())
    self.buildinfo.IsLaptop.cache_clear()
    mock_islaptop.return_value = False
    self.assertFalse(self.buildinfo.IsLaptop())

  @mock.patch.object(buildinfo.hw_info.HWInfo, 'IsOnBattery', autospec=True)
  def test_is_on_battery(self, mock_isonbattery):
    mock_isonbattery.return_value = True
    self.assertTrue(self.buildinfo.IsOnBattery())
    self.buildinfo.IsOnBattery.cache_clear()
    mock_isonbattery.return_value = False
    self.assertFalse(self.buildinfo.IsOnBattery())

  @mock.patch.object(
      buildinfo.hw_info.HWInfo, 'IsVirtualMachine', autospec=True)
  def test_is_virtual(self, mock_isvirtualmachine):
    mock_isvirtualmachine.return_value = False
    self.assertFalse(self.buildinfo.IsVirtual())
    self.buildinfo.IsVirtual.cache_clear()
    mock_isvirtualmachine.return_value = True
    self.assertTrue(self.buildinfo.IsVirtual())

  @mock.patch.object(buildinfo.BuildInfo, '_ReleaseInfo', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'ComputerOs', autospec=True)
  def test_os_code(self, mock_computeros, mock_releaseinfo):
    codes = {
        'os_codes': {
            'windows-7-stable-x64': {
                'code': 'win7'
            },
            'windows-10-stable': {
                'code': 'win10'
            },
            'win2012r2-x64-se': {
                'code': 'win2012r2-x64-se'
            }
        }
    }
    mock_releaseinfo.return_value = codes
    mock_computeros.return_value = 'windows-10-stable'
    self.assertEqual(self.buildinfo.OsCode(), 'win10')
    mock_computeros.return_value = 'win2012r2-x64-se'
    self.buildinfo.OsCode.cache_clear()
    self.assertEqual(self.buildinfo.OsCode(), 'win2012r2-x64-se')
    mock_computeros.return_value = 'win2000-x64-se'
    self.buildinfo.OsCode.cache_clear()
    with self.assert_raises_with_validation(buildinfo.Error):
      self.buildinfo.OsCode()

  @mock.patch.object(buildinfo.net_info, 'NetInfo', autospec=True)
  def test_net_interfaces(self, mock_netinfo):
    mock_netinfo.return_value.Interfaces.return_value = [
        mock.Mock(description='d1', mac_address='11:22:33:44:55'),
        mock.Mock(description='d2', mac_address='AA:BB:CC:DD:EE'),
        mock.Mock(description='d3', mac_address='AA:22:CC:44:EE'),
    ]
    ints = self.buildinfo.NetInterfaces()
    self.assertEqual(ints[1].description, 'd2')
    mock_netinfo.assert_called_with(poll=True, active_only=True)
    ints = self.buildinfo.NetInterfaces(False)
    mock_netinfo.assert_called_with(poll=True, active_only=False)

  @mock.patch.object(files, 'Read', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  def test_release(self, mock_branch, mock_read):

    mock_branch.return_value = 'unstable'
    mock_read.return_value = {'release_id': '1234'}
    self.assertEqual(self.buildinfo.Release(), '1234')
    mock_read.assert_called_with(
        'https://glazier-server.example.com/unstable/release-id.yaml')
    self.buildinfo.Release.cache_clear()
    mock_read.return_value = {'no_release_id': '1234'}
    self.assertIsNone(self.buildinfo.Release())
    self.buildinfo.Release.cache_clear()

    # read error
    mock_read.side_effect = buildinfo.files.FileReadError('some_path')
    with self.assert_raises_with_validation(buildinfo.Error):
      self.buildinfo.Release()

  @mock.patch.object(files, 'Read', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  def test_release_info(self, mock_branch, mock_read):

    mock_branch.return_value = 'testing'
    mock_read.return_value = {}
    self.buildinfo._ReleaseInfo()
    mock_read.assert_called_with(
        'https://glazier-server.example.com/testing/release-info.yaml')

    # read error
    mock_read.side_effect = buildinfo.files.FileReadError('some_path')
    with self.assert_raises_with_validation(buildinfo.Error):
      self.buildinfo._ReleaseInfo()

  @mock.patch.object(files, 'Read', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'ComputerOs', autospec=True)
  def test_release_path(self, mock_computeros, mock_read):

    mock_read.return_value = yaml.safe_load(_VERSION_INFO)
    mock_computeros.return_value = 'windows-7-stable'
    expected = 'https://glazier-server.example.com/stable/'
    self.assertEqual(self.buildinfo.ReleasePath(), expected)
    self.buildinfo.ComputerOs.cache_clear()
    mock_computeros.return_value = 'windows-10-unstable'
    expected = 'https://glazier-server.example.com/unstable/'
    self.assertEqual(self.buildinfo.ReleasePath(), expected)
    self.buildinfo.ComputerOs.cache_clear()

    # no os
    mock_computeros.return_value = None
    with self.assert_raises_with_validation(buildinfo.Error):
      self.buildinfo.ReleasePath()
    self.buildinfo.ComputerOs.cache_clear()

    # invalid os
    mock_computeros.return_value = 'invalid-os-string'
    with self.assert_raises_with_validation(buildinfo.Error):
      self.buildinfo.ReleasePath()

  def test_active_config_path(self):
    self.buildinfo.ActiveConfigPath(append='/foo')
    self.buildinfo.ActiveConfigPath(append='/bar')
    self.assertEqual(self.buildinfo.ActiveConfigPath(), ['/foo', '/bar'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(pop=True), ['/foo'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(pop=True), [])
    self.assertEqual(self.buildinfo.ActiveConfigPath(pop=True), [])

  def test_active_config_path_set(self):
    self.assertEqual(
        self.buildinfo.ActiveConfigPath(set_to=['/foo', '/bar']),
        ['/foo', '/bar'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(), ['/foo', '/bar'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(set_to=[]), [])
    self.buildinfo.ActiveConfigPath(set_to=['/foo', 'bar', 'baz'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(), ['/foo', 'bar', 'baz'])

  def test_string_pinner(self):
    self.assertFalse(self.buildinfo._StringPinner(['A', 'B'], []))
    self.assertFalse(self.buildinfo._StringPinner(['A', 'B'], None))
    self.assertFalse(self.buildinfo._StringPinner([], ['A', 'B']))
    self.assertFalse(self.buildinfo._StringPinner(None, ['A', 'B']))
    self.assertTrue(self.buildinfo._StringPinner(['A'], ['A', 'B']))
    self.assertTrue(self.buildinfo._StringPinner(['B'], ['A', 'B']))
    self.assertTrue(self.buildinfo._StringPinner(['A'], ['!C', '!D']))
    self.assertFalse(self.buildinfo._StringPinner(['D'], ['!C', '!D']))
    self.assertFalse(self.buildinfo._StringPinner([True], [False]))
    self.assertFalse(self.buildinfo._StringPinner([False], [True]))
    self.assertTrue(self.buildinfo._StringPinner([True], [True]))
    self.assertTrue(self.buildinfo._StringPinner([False], [False]))

  @mock.patch.object(files, 'Read', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  def test_supported_models(self, unused_releasepath, mock_read):
    mock_read.return_value = yaml.safe_load(_RELEASE_INFO)
    results = self.buildinfo.SupportedModels()
    self.assertIn('tier1', results)
    self.assertIn('tier2', results)
    for model in results['tier1'] + results['tier2']:
      self.assertEqual(type(model), str)
    self.assertIn('windows tier 1 device', results['tier1'])
    self.assertIn('windows tier 2 device', results['tier2'])

  @mock.patch.object(buildinfo.BuildInfo, 'ComputerModel', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'SupportedModels', autospec=True)
  def test_support_tier(self, mock_supportedmodels, mock_computermodel):

    # Tier1
    mock_computermodel.return_value = 'VMWare Virtual Platform'
    mock_supportedmodels.return_value = {
        'tier1': ['vmware virtual platform', 'hp z620 workstation'],
        'tier2': ['precision workstation t3400', '20BT'],
    }
    self.assertEqual(self.buildinfo.SupportTier(), 1)
    self.buildinfo.SupportTier.cache_clear()

    # Tier 2
    mock_computermodel.return_value = 'Precision WorkStation T3400'
    self.assertEqual(self.buildinfo.SupportTier(), 2)
    self.buildinfo.SupportTier.cache_clear()

    # Partial Match
    mock_computermodel.return_value = '20BTS0A400'
    self.assertEqual(self.buildinfo.SupportTier(), 2)
    self.buildinfo.SupportTier.cache_clear()

    # Unsupported
    mock_computermodel.return_value = 'Best Buy Special of the Day'
    self.assertEqual(self.buildinfo.SupportTier(), 0)

  @mock.patch.object(buildinfo.tpm_info, 'TpmInfo', autospec=True)
  def test_tpm_info(self, mock_tpminfo):
    result = self.buildinfo._TpmInfo()
    self.assertEqual(result, mock_tpminfo.return_value)
    self.assertEqual(self.buildinfo._tpm_info, mock_tpminfo.return_value)

  @mock.patch.object(buildinfo.tpm_info.TpmInfo, 'TpmPresent', autospec=True)
  def test_tpm_present(self, mock_tpmpresent):
    mock_tpmpresent.return_value = True
    self.assertTrue(self.buildinfo.TpmPresent())
    mock_tpmpresent.return_value = False
    self.assertTrue(self.buildinfo.TpmPresent())  # caching
    self.buildinfo.TpmPresent.cache_clear()
    self.assertFalse(self.buildinfo.TpmPresent())

  @mock.patch.object(files, 'Read', autospec=True)
  def test_winpe_version(self, mock_read):
    mock_read.return_value = yaml.safe_load(_VERSION_INFO)
    self.assertEqual(type(self.buildinfo.WinpeVersion()), int)
    mock_read.assert_called_with(f'{FLAGS.config_server}/version-info.yaml')

  @mock.patch.object(files, 'Read', autospec=True)
  def test_winpe_version_fallback(self, mock_read):
    mock_read.side_effect = files.Error
    self.buildinfo.ConfigServer(set_to='https://glazier-server-1.example.com')

    with self.assertRaises(buildinfo.YamlFileError):
      self.buildinfo.WinpeVersion()

    mock_read.assert_has_calls([
        mock.call('https://glazier-server-1.example.com/version-info.yaml'),
        mock.call(f'{FLAGS.config_server}/version-info.yaml'),
    ])

  @mock.patch.object(buildinfo.BuildInfo, 'ComputerModel', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'IsVirtual', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'TpmPresent', autospec=True)
  @mock.patch.object(buildinfo.logging, 'info', autospec=True)
  def test_encryption_level(self, mock_info, mock_tpmpresent, mock_isvirtual,
                            mock_computermodel):

    mock_computermodel.return_value = 'HP Z440 Workstation'
    mock_tpmpresent.return_value = False
    mock_isvirtual.return_value = True

    # virtual machine
    self.assertEqual(self.buildinfo.EncryptionLevel(), 'none')
    mock_info.assert_called_with(_REGEXP('^Virtual machine type .*'), mock.ANY)
    mock_isvirtual.return_value = False
    self.buildinfo.EncryptionLevel.cache_clear()

    # tpm
    mock_tpmpresent.return_value = True
    self.assertEqual(self.buildinfo.EncryptionLevel(), 'tpm')
    mock_info.assert_called_with(_REGEXP('^TPM detected .*'))
    self.buildinfo.EncryptionLevel.cache_clear()

    # default
    self.assertEqual(self.buildinfo.EncryptionLevel(), 'tpm')

  @mock.patch.object(timers.Timers, 'GetAll', autospec=True)
  def test_serialize(self, mock_get_all):

    mock_buildinfo = mock.Mock(spec_set=self.buildinfo)
    mock_buildinfo._chooser_responses = {
        'USER_choice_one': 'value1',
        'USER_choice_two': 'value2'
    }
    mock_get_all.return_value = {
        'TIMER_timer_1':
            datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=6)))
    }
    mock_buildinfo.Serialize = buildinfo.BuildInfo.Serialize.__get__(
        mock_buildinfo)
    yaml_path = self.create_tempfile(file_path='build_info.yaml')
    mock_buildinfo.Serialize(yaml_path)
    parsed = yaml.safe_load(open(yaml_path))

    self.assertIn('branch', parsed['BUILD'])
    self.assertIn('Model', parsed['BUILD'])
    self.assertIn('SerialNumber', parsed['BUILD'])
    self.assertIn('USER_choice_two', parsed['BUILD'])
    self.assertIn('TIMER_timer_1', parsed['BUILD'])
    self.assertEqual(parsed['BUILD']['USER_choice_two'], 'value2')

  @mock.patch.object(
      buildinfo.hw_info.HWInfo, 'VideoControllers', autospec=True)
  def test_video_controllers(self, mock_videocontrollers):
    mock_videocontrollers.return_value = [{
        'name': 'NVIDIA Quadro 600'
    }, {
        'name': 'Intel(R) HD Graphics 4000'
    }]
    result = self.buildinfo.VideoControllers()
    self.assertEqual(result[0]['name'], 'NVIDIA Quadro 600')
    self.assertTrue(
        self.buildinfo.BuildPinMatch(
            'graphics', ['Intel(R) HD Graphics 3000', 'NVIDIA Quadro 600']))
    self.assertFalse(
        self.buildinfo.BuildPinMatch(
            'graphics', ['Intel(R) HD Graphics 3000', 'NVIDIA Quadro 500']))


if __name__ == '__main__':
  absltest.main()
