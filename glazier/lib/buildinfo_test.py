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

from absl import flags
from absl.testing import absltest
from absl.testing import flagsaver

from glazier.lib import buildinfo
import mock
from pyfakefs import fake_filesystem
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


class BuildInfoTest(absltest.TestCase):

  def setUp(self):
    super(BuildInfoTest, self).setUp()
    # fake filesystem
    self.filesystem = fake_filesystem.FakeFilesystem()
    self.filesystem.create_dir('/dev')
    buildinfo.os = fake_filesystem.FakeOsModule(self.filesystem)
    buildinfo.open = fake_filesystem.FakeFileOpen(self.filesystem)
    # setup
    mock_wmi = mock.patch.object(
        buildinfo.hw_info.wmi_query, 'WMIQuery', autospec=True)
    self.addCleanup(mock_wmi.stop)
    mock_wmi.start()
    self.buildinfo = buildinfo.BuildInfo()

  def testChooserOptions(self):
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

  def testStoreChooserResponses(self):
    """Store responses from the Chooser UI."""
    resp = {'system_locale': 'en-us', 'core_ps_shell': True}
    self.buildinfo.StoreChooserResponses(resp)
    self.assertEqual(self.buildinfo._chooser_responses['USER_system_locale'],
                     'en-us')
    self.assertEqual(self.buildinfo._chooser_responses['USER_core_ps_shell'],
                     True)

  @flagsaver.flagsaver
  def testBinaryServerFromFlag(self):
    FLAGS.binary_server = 'https://glazier-server.example.com'
    self.assertEqual(self.buildinfo.BinaryServer(),
                     'https://glazier-server.example.com')

  def testBinaryServerChanges(self):
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
  def testBinaryServerFallback(self):
    FLAGS.config_server = 'https://glazier-server-3.example.com'
    self.assertEqual(self.buildinfo.BinaryServer(),
                     'https://glazier-server-3.example.com')

  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  def testConfigPath(self, mock_bin):
    mock_bin.return_value = 'https://glazier-server.example.com/bin/'
    self.assertEqual(self.buildinfo.BinaryPath(), mock_bin.return_value)

  @flagsaver.flagsaver
  def testConfigServerFromFlag(self):
    FLAGS.config_server = 'https://glazier-server.example.com'
    self.assertEqual(self.buildinfo.ConfigServer(),
                     'https://glazier-server.example.com')

  def testConfigServerChanges(self):
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

  def testConfigServer(self):
    return_value = 'https://glazier-server.example.com'
    self.assertEqual(self.buildinfo.ConfigServer(), return_value)

  @mock.patch.object(buildinfo.identifier, 'check_id', autospec=True)
  def test_image_id(self, checkid):
    checkid.return_value = '1A19SEL90000R90DZN7A-1234567'
    result = self.buildinfo.ImageID()
    self.assertEqual(result, '1A19SEL90000R90DZN7A-1234567')

  def testBuildPinMatch(self):
    with mock.patch.object(
        buildinfo.BuildInfo, 'ComputerModel', autospec=True) as mock_mod:
      mock_mod.return_value = 'HP Z620 Workstation'
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
          self.buildinfo.BuildPinMatch('computer_model', [
              '!HP Z840 Workstation', '!HP Z620 Workstation'
          ]))
      # Inverse include
      self.assertTrue(
          self.buildinfo.BuildPinMatch('computer_model',
                                       ['!VMWare Virtual Platform']))
      # Inverse include (second)
      self.assertTrue(
          self.buildinfo.BuildPinMatch('computer_model', [
              '!HP Z640 Workstation', '!HP Z840 Workstation'
          ]))
      # Substrings
      self.assertTrue(
          self.buildinfo.BuildPinMatch('computer_model',
                                       ['hp Z840', 'hp Z620']))

    # Device Ids
    with mock.patch.object(
        buildinfo.BuildInfo, 'DeviceIds', autospec=True) as did:
      did.return_value = ['WW-XX-YY-ZZ', '11-22-33-44']
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
        buildinfo.BuildInfo, 'OsCode', autospec=True) as os:
      os.return_value = 'win10'
      self.assertTrue(self.buildinfo.BuildPinMatch('os_code', ['win10']))
      self.assertTrue(self.buildinfo.BuildPinMatch('os_code', ['WIN10']))
      self.assertFalse(self.buildinfo.BuildPinMatch('os_code', ['win7']))
      self.assertFalse(self.buildinfo.BuildPinMatch('os_code', ['wi']))
      self.assertFalse(self.buildinfo.BuildPinMatch('os_code', ['']))

    # Invalid pin
    self.assertRaises(buildinfo.Error, self.buildinfo.BuildPinMatch,
                      'no_existo', ['invalid pin value'])

  def testBuildUserPinMatch(self):
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
  def testImageTypeFFU(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_image_type = 'FFU'
    self.assertEqual(self.buildinfo.ImageType(), 'ffu')

  @flagsaver.flagsaver
  def testImageTypeUnknown(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_image_type = ''
    self.assertEqual(self.buildinfo.ImageType(), 'unknown')

  @mock.patch.object(buildinfo.registry, 'get_values', autospec=True)
  def testInstalledSoftware(self, mock_software):
    mock_software.return_value = ['Mozilla FireFox',
                                  'Google Chrome', 'Microsoft Edge']

    self.assertTrue(
        self.buildinfo.BuildPinMatch('is_installed', ['Google Chrome']))
    self.assertTrue(
        self.buildinfo.BuildPinMatch('is_installed', ['!Safari']))
    self.assertFalse(
        self.buildinfo.BuildPinMatch('is_installed', ['Chrome']))
    self.assertFalse(
        self.buildinfo.BuildPinMatch('is_installed', ['!Google Chrome']))

  @mock.patch.object(buildinfo.winpe, 'check_winpe', autospec=True)
  def testCachePath(self, wpe):
    wpe.return_value = False
    self.assertEqual(self.buildinfo.CachePath(), buildinfo.constants.SYS_CACHE)

  @mock.patch.object(buildinfo.winpe, 'check_winpe', autospec=True)
  def testCachePathWinPE(self, wpe):
    wpe.return_value = True
    self.assertEqual(self.buildinfo.CachePath(),
                     buildinfo.constants.WINPE_CACHE)

  @mock.patch.object(
      buildinfo.hw_info.HWInfo, 'ComputerSystemManufacturer', autospec=True)
  def testComputerManufacturer(self, mock_man):
    mock_man.return_value = 'Google Inc.'
    result = self.buildinfo.ComputerManufacturer()
    self.assertEqual(result, 'Google Inc.')
    self.buildinfo.ComputerManufacturer.cache_clear()
    mock_man.return_value = None
    self.assertRaises(buildinfo.Error,
                      self.buildinfo.ComputerManufacturer)

  @mock.patch.object(
      buildinfo.hw_info.HWInfo, 'ComputerSystemModel', autospec=True)
  def testComputerModel(self, sys_model):
    sys_model.return_value = 'HP Z620 Workstation'
    result = self.buildinfo.ComputerModel()
    self.assertEqual(result, 'HP Z620 Workstation')
    sys_model.return_value = '2537CE2'
    self.assertEqual(result, 'HP Z620 Workstation')  # caching
    self.buildinfo.ComputerModel.cache_clear()
    result = self.buildinfo.ComputerModel()
    self.assertEqual(result, '2537CE2')
    self.buildinfo.ComputerModel.cache_clear()
    sys_model.return_value = None
    self.assertRaises(buildinfo.Error, self.buildinfo.ComputerModel)

  @flagsaver.flagsaver
  def testHostSpecFlags(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_hostname = 'TEST-HOST'
    FLAGS.glazier_spec_fqdn = 'TEST-HOST.example.com'
    self.assertEqual(self.buildinfo.ComputerName(), 'TEST-HOST')
    self.assertEqual(self.buildinfo.Fqdn(), 'TEST-HOST.example.com')

  @flagsaver.flagsaver
  def testOsSpecFlags(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_os = 'windows-10-test'
    self.assertEqual(self.buildinfo.ComputerOs(), 'windows-10-test')

  @flagsaver.flagsaver
  def testLabSpecFlagsTrue(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_lab = 'True'
    self.assertEqual(self.buildinfo.Lab(), True)

  @flagsaver.flagsaver
  def testLabSpecFlagsFalse(self):
    FLAGS.glazier_spec = 'flag'
    FLAGS.glazier_spec_lab = ''
    self.assertEqual(self.buildinfo.Lab(), False)

  @mock.patch.object(
      buildinfo.beyondcorp.BeyondCorp, 'CheckBeyondCorp', autospec=True)
  @flagsaver.flagsaver
  def testBeyondCorpPinTrue(self, cbc):
    cbc.return_value = True
    self.assertTrue(self.buildinfo.BuildPinMatch('beyond_corp', ['True']))
    self.assertEqual(self.buildinfo.BeyondCorp(), True)

  @mock.patch.object(
      buildinfo.beyondcorp.BeyondCorp, 'CheckBeyondCorp', autospec=True)
  @flagsaver.flagsaver
  def testBeyondCorpPinFalse(self, cbc):
    cbc.return_value = False
    self.assertTrue(self.buildinfo.BuildPinMatch('beyond_corp', ['!True']))
    self.assertEqual(self.buildinfo.BeyondCorp(), False)
    self.assertTrue(self.buildinfo.BuildPinMatch('beyond_corp', ['False']))
    self.assertEqual(self.buildinfo.BeyondCorp(), False)

  @mock.patch.object(buildinfo.hw_info.HWInfo, 'BiosSerial', autospec=True)
  def testComputerSerial(self, bios_serial):
    bios_serial.return_value = '5KD1BP1'
    result = self.buildinfo.ComputerSerial()
    self.assertEqual(result, '5KD1BP1')

  @mock.patch.object(buildinfo.hw_info.HWInfo, 'PciDevices', autospec=True)
  def testDeviceIds(self, mock_pci):
    test_dev = DeviceId(ven='8086', dev='1E10', subsys='21FB17AA', rev='C4')
    mock_pci.return_value = [test_dev]
    self.assertEqual(['8086-1E10-21FB17AA-C4'], self.buildinfo.DeviceIds())

  def testDeviceIdPinning(self):
    local_ids = ['11-22-33-44', 'AA-BB-CC-DD', 'AA-BB-CC-DD']
    self.assertTrue(
        self.buildinfo._StringPinner(
            local_ids, ['AA-BB-CC-DD'], loose=True))
    self.assertTrue(
        self.buildinfo._StringPinner(
            local_ids, ['AA-BB-CC'], loose=True))
    self.assertTrue(
        self.buildinfo._StringPinner(
            local_ids, ['AA-BB'], loose=True))
    self.assertTrue(self.buildinfo._StringPinner(local_ids, ['AA'], loose=True))
    self.assertFalse(
        self.buildinfo._StringPinner(
            local_ids, ['DD-CC-BB-AA'], loose=True))
    self.assertFalse(
        self.buildinfo._StringPinner(
            local_ids, ['BB-CC'], loose=True))

  @mock.patch.object(buildinfo.hw_info, 'HWInfo', autospec=True)
  def testHWInfo(self, hw_info):
    result = self.buildinfo._HWInfo()
    self.assertEqual(result, hw_info.return_value)
    self.assertEqual(self.buildinfo._hw_info, hw_info.return_value)

  @mock.patch.object(buildinfo.hw_info.HWInfo, 'IsLaptop', autospec=True)
  def testIsLaptop(self, mock_lap):
    mock_lap.return_value = True
    self.assertTrue(self.buildinfo.IsLaptop())
    self.buildinfo.IsLaptop.cache_clear()
    mock_lap.return_value = False
    self.assertFalse(self.buildinfo.IsLaptop())

  @mock.patch.object(
      buildinfo.hw_info.HWInfo, 'IsVirtualMachine', autospec=True)
  def testIsVirtual(self, virt):
    virt.return_value = False
    self.assertFalse(self.buildinfo.IsVirtual())
    self.buildinfo.IsVirtual.cache_clear()
    virt.return_value = True
    self.assertTrue(self.buildinfo.IsVirtual())

  @mock.patch.object(buildinfo.BuildInfo, '_ReleaseInfo', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'ComputerOs', autospec=True)
  def testOsCode(self, comp_os, rel_info):
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
    rel_info.return_value = codes
    comp_os.return_value = 'windows-10-stable'
    self.assertEqual(self.buildinfo.OsCode(), 'win10')
    comp_os.return_value = 'win2012r2-x64-se'
    self.buildinfo.OsCode.cache_clear()
    self.assertEqual(self.buildinfo.OsCode(), 'win2012r2-x64-se')
    comp_os.return_value = 'win2000-x64-se'
    self.buildinfo.OsCode.cache_clear()
    self.assertRaises(buildinfo.Error, self.buildinfo.OsCode)

  @mock.patch.object(buildinfo.net_info, 'NetInfo', autospec=True)
  def testNetInterfaces(self, netinfo):
    netinfo.return_value.Interfaces.return_value = [
        mock.Mock(
            description='d1', mac_address='11:22:33:44:55'),
        mock.Mock(
            description='d2', mac_address='AA:BB:CC:DD:EE'),
        mock.Mock(
            description='d3', mac_address='AA:22:CC:44:EE'),
    ]
    ints = self.buildinfo.NetInterfaces()
    self.assertEqual(ints[1].description, 'd2')
    netinfo.assert_called_with(poll=True, active_only=True)
    ints = self.buildinfo.NetInterfaces(False)
    netinfo.assert_called_with(poll=True, active_only=False)

  @mock.patch.object(buildinfo.files, 'Read', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  def testRelease(self, branch, fread):
    branch.return_value = 'unstable'
    fread.return_value = {'release_id': '1234'}
    self.assertEqual(self.buildinfo.Release(), '1234')
    fread.assert_called_with(
        'https://glazier-server.example.com/unstable/release-id.yaml')
    self.buildinfo.Release.cache_clear()
    fread.return_value = {'no_release_id': '1234'}
    self.assertIsNone(self.buildinfo.Release())
    self.buildinfo.Release.cache_clear()
    # read error
    fread.side_effect = buildinfo.files.Error
    self.assertRaises(buildinfo.Error, self.buildinfo.Release)

  @mock.patch.object(buildinfo.files, 'Read', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  def testReleaseInfo(self, branch, fread):
    branch.return_value = 'testing'
    fread.return_value = {}
    self.buildinfo._ReleaseInfo()
    fread.assert_called_with(
        'https://glazier-server.example.com/testing/release-info.yaml')
    # read error
    fread.side_effect = buildinfo.files.Error
    self.assertRaises(buildinfo.Error, self.buildinfo._ReleaseInfo)

  @mock.patch.object(buildinfo.files, 'Read', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'ComputerOs', autospec=True)
  def testReleasePath(self, comp_os, read):
    read.return_value = yaml.safe_load(_VERSION_INFO)
    comp_os.return_value = 'windows-7-stable'
    expected = 'https://glazier-server.example.com/stable/'
    self.assertEqual(self.buildinfo.ReleasePath(), expected)
    self.buildinfo.ComputerOs.cache_clear()
    comp_os.return_value = 'windows-10-unstable'
    expected = 'https://glazier-server.example.com/unstable/'
    self.assertEqual(self.buildinfo.ReleasePath(), expected)
    self.buildinfo.ComputerOs.cache_clear()
    # no os
    comp_os.return_value = None
    self.assertRaises(buildinfo.Error, self.buildinfo.ReleasePath)
    self.buildinfo.ComputerOs.cache_clear()
    # invalid os
    comp_os.return_value = 'invalid-os-string'
    self.assertRaises(buildinfo.Error, self.buildinfo.ReleasePath)

  def testActiveConfigPath(self):
    self.buildinfo.ActiveConfigPath(append='/foo')
    self.buildinfo.ActiveConfigPath(append='/bar')
    self.assertEqual(self.buildinfo.ActiveConfigPath(), ['/foo', '/bar'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(pop=True), ['/foo'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(pop=True), [])
    self.assertEqual(self.buildinfo.ActiveConfigPath(pop=True), [])

  def testActiveConfigPathSet(self):
    self.assertEqual(
        self.buildinfo.ActiveConfigPath(set_to=['/foo', '/bar']),
        ['/foo', '/bar'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(), ['/foo', '/bar'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(set_to=[]), [])
    self.buildinfo.ActiveConfigPath(set_to=['/foo', 'bar', 'baz'])
    self.assertEqual(self.buildinfo.ActiveConfigPath(), ['/foo', 'bar', 'baz'])

  def testStringPinner(self):
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

  @mock.patch.object(buildinfo.files, 'Read', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  def testSupportedModels(self, unused_rel_path, fread):
    fread.return_value = yaml.safe_load(_RELEASE_INFO)
    results = self.buildinfo.SupportedModels()
    self.assertIn('tier1', results)
    self.assertIn('tier2', results)
    for model in results['tier1'] + results['tier2']:
      self.assertEqual(type(model), str)
    self.assertIn('windows tier 1 device', results['tier1'])
    self.assertIn('windows tier 2 device', results['tier2'])

  @mock.patch.object(buildinfo.BuildInfo, 'ComputerModel', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'SupportedModels', autospec=True)
  def testSupportTier(self, mock_supp, mock_comp):
    # Tier1
    mock_comp.return_value = 'VMWare Virtual Platform'
    mock_supp.return_value = {
        'tier1': ['vmware virtual platform', 'hp z620 workstation'],
        'tier2': ['precision workstation t3400', '20BT'],
    }
    self.assertEqual(self.buildinfo.SupportTier(), 1)
    self.buildinfo.SupportTier.cache_clear()
    # Tier 2
    mock_comp.return_value = 'Precision WorkStation T3400'
    self.assertEqual(self.buildinfo.SupportTier(), 2)
    self.buildinfo.SupportTier.cache_clear()
    # Partial Match
    mock_comp.return_value = '20BTS0A400'
    self.assertEqual(self.buildinfo.SupportTier(), 2)
    self.buildinfo.SupportTier.cache_clear()
    # Unsupported
    mock_comp.return_value = 'Best Buy Special of the Day'
    self.assertEqual(self.buildinfo.SupportTier(), 0)

  @mock.patch.object(buildinfo.tpm_info, 'TpmInfo', autospec=True)
  def testTpmInfo(self, tpm_info):
    result = self.buildinfo._TpmInfo()
    self.assertEqual(result, tpm_info.return_value)
    self.assertEqual(self.buildinfo._tpm_info, tpm_info.return_value)

  @mock.patch.object(buildinfo.tpm_info.TpmInfo, 'TpmPresent', autospec=True)
  def testTpmPresent(self, tpm_present):
    tpm_present.return_value = True
    self.assertTrue(self.buildinfo.TpmPresent())
    tpm_present.return_value = False
    self.assertTrue(self.buildinfo.TpmPresent())  # caching
    self.buildinfo.TpmPresent.cache_clear()
    self.assertFalse(self.buildinfo.TpmPresent())

  @mock.patch.object(buildinfo.files, 'Read', autospec=True)
  def testWinpeVersion(self, fread):
    fread.return_value = yaml.safe_load(_VERSION_INFO)
    self.assertEqual(type(self.buildinfo.WinpeVersion()), int)

  @mock.patch.object(buildinfo.BuildInfo, 'ComputerModel', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'IsVirtual', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'TpmPresent', autospec=True)
  @mock.patch.object(buildinfo.logging, 'info', autospec=True)
  def testEncryptionLevel(self, info, tpm, virtual, model):
    model.return_value = 'HP Z440 Workstation'
    tpm.return_value = False
    virtual.return_value = True
    # virtual machine
    self.assertEqual(self.buildinfo.EncryptionLevel(), 'none')
    info.assert_called_with(
        _REGEXP('^Virtual machine type .*'), mock.ANY)
    virtual.return_value = False
    self.buildinfo.EncryptionLevel.cache_clear()
    # tpm
    tpm.return_value = True
    self.assertEqual(self.buildinfo.EncryptionLevel(), 'tpm')
    info.assert_called_with(_REGEXP('^TPM detected .*'))
    self.buildinfo.EncryptionLevel.cache_clear()
    # default
    self.assertEqual(self.buildinfo.EncryptionLevel(), 'tpm')

  def testSerialize(self):
    mock_b = mock.Mock(spec_set=self.buildinfo)
    mock_b._chooser_responses = {
        'USER_choice_one': 'value1',
        'USER_choice_two': 'value2'
    }
    mock_b._timers.GetAll.return_value = {
        'timer_1': datetime.datetime.utcnow()
    }
    mock_b.Serialize = buildinfo.BuildInfo.Serialize.__get__(mock_b)
    mock_b.Serialize('/build_info.yaml')
    parsed = yaml.safe_load(buildinfo.open('/build_info.yaml'))
    self.assertIn('branch', parsed['BUILD'])
    self.assertIn('Model', parsed['BUILD'])
    self.assertIn('SerialNumber', parsed['BUILD'])
    self.assertIn('USER_choice_two', parsed['BUILD'])
    self.assertIn('TIMER_timer_1', parsed['BUILD'])
    self.assertEqual(parsed['BUILD']['USER_choice_two'], 'value2')

  @mock.patch.object(buildinfo.timers.gtime, 'now', autospec=True)
  def testTimers(self, dt):
    now = datetime.datetime.utcnow()
    dt.return_value = now
    self.buildinfo.TimerSet('test_timer_1')
    self.assertIsNone(self.buildinfo.TimerGet('test_timer_2'))
    self.assertEqual(self.buildinfo.TimerGet('test_timer_1'), now)

  @mock.patch.object(
      buildinfo.hw_info.HWInfo, 'VideoControllers', autospec=True)
  def testVideoControllers(self, controllers):
    controllers.return_value = [{
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
