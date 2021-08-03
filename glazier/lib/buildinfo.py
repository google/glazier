# python3
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
"""Glazier host information discovery subsystem."""

import functools
import logging
import time
from typing import Any, Dict, List, Optional


from absl import flags
from glazier.lib import beyondcorp
from glazier.lib import constants
from glazier.lib import identifier
from glazier.lib import registry
from glazier.lib import timers
from glazier.lib import winpe
from glazier.lib.config import files
from glazier.lib.spec import spec
import yaml

from gwinpy.wmi import hw_info
from gwinpy.wmi import net_info
from gwinpy.wmi import tpm_info

FLAGS = flags.FLAGS


class Error(Exception):
  pass


class BuildInfo(object):
  """Encapsulates information pertaining to the build."""

  def __init__(self):
    self._active_conf_path = []
    self._binary_server = ''
    self._chooser_pending = []
    self._chooser_responses = {}
    self._glazier_server = ''
    self._hw_info = None
    self._net_info = None
    self._release_info = None
    self._timers = timers.Timers()
    self._tpm_info = None
    self._version_info = None

  #
  # Chooser Control Functions
  #

  def AddChooserOption(self, option):
    """Add an option to the chooser pending questions list."""
    self._chooser_pending.append(option)

  def GetChooserOptions(self):
    """Retrieve all pending chooser options."""
    return self._chooser_pending

  def FlushChooserOptions(self):
    """Clear all pending chooser options."""
    self._chooser_pending = []

  def StoreChooserResponses(self, responses):
    """Store responses from the Chooser UI."""
    for key in responses:
      renamed = 'USER_%s' % key
      logging.debug('Importing key %s from chooser.', renamed)
      self._chooser_responses[renamed] = responses[key]

  #
  # Image Configuration Functions
  #

  def BinaryPath(self) -> str:
    """Determines the path to the folder containing all binaries for build.

    Returns:
      The versioned base path to the current build as a string.
    """
    server = self.BinaryServer() or ''
    path = FLAGS.binary_root_path.strip('/')
    path = '%s/%s/' % (server, path)
    return path

  def BinaryServer(self, set_to: str = '') -> str:
    """Get (or set) the binary server address.

    Args:
      set_to: Update the internal server address.

    Returns:
      The binary server without any trailing slashes.
    """
    if set_to:
      self._binary_server = set_to
    if not self._binary_server:
      if FLAGS.binary_server:
        self._binary_server = FLAGS.binary_server
      else:  # backward compatibility
        self._binary_server = self.ConfigServer()
    return self._binary_server.rstrip('/')

  def ConfigServer(self, set_to: str = '') -> str:
    """Get (or set) the config server address.

    Args:
      set_to: Update the internal server address.

    Returns:
      The config server without any trailing slashes.
    """
    if set_to:
      self._glazier_server = set_to
    if not self._glazier_server:
      self._glazier_server = FLAGS.config_server
    return self._glazier_server.rstrip('/')

  @functools.lru_cache()
  def ImageID(self) -> str:
    """Optionally generate a unique image identifier.

    Returns:
      The image identifier as a string.
    """
    return identifier.check_id()

  @functools.lru_cache()
  def Release(self) -> Optional[str]:
    """Determine the current build release.

    Returns:
      The build release as a string.
    """
    rel_id_file = '%s/%s' % (self.ReleasePath().rstrip('/'), 'release-id.yaml')
    try:
      data = files.Read(rel_id_file)
    except files.Error as e:
      raise Error(e)
    if data and 'release_id' in data:
      return data['release_id']
    return None

  def _ReleaseInfo(self):
    if not self._release_info:
      rel_info_file = '%s/%s' % (self.ReleasePath().rstrip('/'),
                                 'release-info.yaml')
      try:
        self._release_info = files.Read(rel_info_file)
      except files.Error as e:
        raise Error(e)
    return self._release_info

  def ReleasePath(self) -> str:
    """Determines the path to the folder containing all files for build.

    Returns:
      The versioned base path to the current build as a string.
    """
    path = self.ConfigServer() or ''
    if FLAGS.config_branches and self.Branch():
      path += '/%s' % str(self.Branch())
    path += '/'
    return path

  def ActiveConfigPath(self,
                       append: Optional[str] = None,
                       pop: bool = False,
                       set_to: Optional[List[str]] = None) -> List[str]:
    """Tracks the active configuration path beneath the config root.

    Use append/pop for directory traversal.

    Args:
      append: Append a string to the active config path.
      pop: Pop the rightmost string from the active config path.
      set_to: Set the config path to an entirely new path.

    Returns:
      The active config path after any modifications.
    """
    if append:
      self._active_conf_path.append(append)
    elif set_to is not None:
      self._active_conf_path = set_to
    elif pop and self._active_conf_path:
      self._active_conf_path.pop()
    return self._active_conf_path

  def _VersionInfo(self):
    if not self._version_info:
      info_file = '%s/%s' % (self.ConfigServer().rstrip('/'),
                             'version-info.yaml')
      try:
        self._version_info = files.Read(info_file)
      except files.Error as e:
        raise Error(e)
    return self._version_info

  #
  # Host Discovery Functions
  #

  def BuildPinMatch(self, pin_name: str, pin_values: List[str]):
    """Compare build pins to local build info data.

    Most pins operate on a simple 1:1 string comparison (eg os_code ==
    os_code).  Pins also support negation match by beginning the pin value
    with ! (!win7 matches anything except win7).  See _StringPinner for details.

    Special cases:
      computer_model: Permits partial string matching.
      device_id:  Performs a many:many matching, as it's comparing against a
        list of all known internal hardware ids instead of just one string.
      USER_*: USER_ pins are dynamic, based on options offered by the chooser.
        There is no validation on the names of these inputs, as they may
        vary between uses.  No negation.

    Args:
      pin_name: The name of the pin (determines function for comparison).
      pin_values: A list of all pin values configured for this pin.

    Returns:
      True for a pin match, else False.

    Raises:
      Error: Reference made to an unsupported pin.
    """
    known_pins = self.GetExportedPins()
    if pin_name.startswith('USER_'):
      if pin_name in self._chooser_responses:
        return self._StringPinner([self._chooser_responses[pin_name]],
                                  pin_values)
      else:
        return False
    elif pin_name not in known_pins:
      raise Error('Referencing illegal pin name: %s' % pin_name)

    loose = False
    if pin_name in ['computer_model', 'device_id']:
      loose = True
    values = known_pins[pin_name]()
    values = values if isinstance(values, list) else [values]
    return self._StringPinner(values, pin_values, loose=loose)

  def GetExportedPins(self) -> Dict[str, Any]:
    return {
        'computer_model': self.ComputerModel,
        'device_id': self.DeviceIds,
        'encryption_type': self.EncryptionLevel,
        'graphics': self.VideoControllersByName,
        'is_laptop': self.IsLaptop,
        'os_code': self.OsCode,
        'beyond_corp': self.BeyondCorp,
        'lab': self.Lab,
        'is_installed': self.InstalledSoftware,
        'image_type': self.ImageType,
    }

  @functools.lru_cache()
  def BeyondCorp(self) -> bool:
    """Cache whether the image is running Beyond Corp.

    Returns:
      True or False bool returned from beyondcorp lib.
    """
    self._beyondcorp = beyondcorp.BeyondCorp()
    return self._beyondcorp.CheckBeyondCorp()

  @functools.lru_cache()
  def CachePath(self):
    """Get the path to the local build cache.

    Returns:
      The path to the local build cache as a string.
    """
    if winpe.check_winpe():
      return constants.WINPE_CACHE
    return constants.SYS_CACHE

  @functools.lru_cache()
  def ComputerManufacturer(self) -> str:
    """Get the computer manufacturer from WMI.

    Returns:
      A string containing the device manufacturer.

    Raises:
      Error: Failure determining the system manufacturer.
    """
    result = self._HWInfo().ComputerSystemManufacturer()
    if not result:
      raise Error('System manufacturer could not be determined.')
    return result

  @functools.lru_cache()
  def ComputerModel(self) -> str:
    """Get the computer model from WMI.

    Lenovo models are trimmed to three characters to mitigate submodel drift.

    Returns:
      the hardware model as a string

    Raises:
      Error: Failure determining the system model.
    """
    result = self._HWInfo().ComputerSystemModel()
    if not result:
      raise Error('System model could not be determined.')
    return result

  @functools.lru_cache()
  def ComputerName(self) -> str:
    """Get the assigned computer name string.

    Returns:
      The name string assigned to this machine.
    """
    return spec.GetModule().GetHostname()

  @functools.lru_cache()
  def ComputerOs(self) -> str:
    """Get the assigned computer OS string.

    Returns:
      The OS string assigned to this machine.
    """
    return spec.GetModule().GetOs()

  @functools.lru_cache()
  def ComputerSerial(self) -> str:
    """Get the computer serial from WMI.

    Returns:
      A string containing the computer serial.
    """
    return self._HWInfo().BiosSerial()

  @functools.lru_cache()
  def DeviceIds(self) -> List[str]:
    """Get local hardware device Ids.

    Returns:
      A list containing all detected hardware device IDs in the format
        [vendor]-[device]-[subsys]-[revision]
    """
    dev_ids = []
    for device in self._HWInfo().PciDevices():
      dev_str = '%s-%s-%s-%s' % (device.ven, device.dev, device.subsys,
                                 device.rev)
      logging.debug('Found local device: %s', dev_str)
      dev_ids.append(dev_str)
    return dev_ids

  @functools.lru_cache()
  def EncryptionLevel(self) -> str:
    """Determines what encryption level is required for this machine.

    Returns:
      The required encryption type as a string (none, tpm)
    """
    if self.IsVirtual():
      logging.info(
          'Virtual machine type %s does not require full disk '
          'encryption.', self.ComputerModel())
      return 'none'

    logging.info('Machine %s requires full disk encryption.',
                 self.ComputerModel())

    if self.TpmPresent():
      logging.info('TPM detected - using TPM encryption.')
      return 'tpm'

    logging.info('No TPM was detected in this machine.')
    return 'tpm'

  def InstalledSoftware(self) -> List[str]:
    """Query registry keys to find installed software.

    Returns:
      A list of installed software.
    """

    subkeys = [
        r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
        r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
    ]
    installed_software = []

    for subkey in subkeys:
      software = registry.get_values(path=subkey)
      if software:
        installed_software.extend(software)

    return installed_software

  @functools.lru_cache()
  def Fqdn(self) -> str:
    """Get the assigned FQDN string.

    Returns:
      The FQDN string assigned to this machine.
    """
    return spec.GetModule().GetFqdn()

  def _HWInfo(self):
    if not self._hw_info:
      self._hw_info = hw_info.HWInfo()
    return self._hw_info

  @functools.lru_cache()
  def ImageType(self) -> str:
    """ImageType returns a string based on the image_type spec setting."""
    t = spec.GetModule().GetImageType()
    return {
        'ffu': 'ffu',
    }.get(t.lower(), 'unknown')

  @functools.lru_cache()
  def IsLaptop(self) -> bool:
    """Whether or not this machine is a laptop.

    Returns:
      true for laptop, else false
    """
    return self._HWInfo().IsLaptop()

  @functools.lru_cache()
  def IsVirtual(self) -> bool:
    """Whether or not this build is in a virtual environment.

    Returns:
      true for a virtual build, else false
    """
    return self._HWInfo().IsVirtualMachine()

  @functools.lru_cache()
  def KnownBranches(self) -> Dict[str, str]:
    return self._VersionInfo()['versions']

  def _NetInfo(self):
    if not self._net_info:
      self._net_info = net_info.NetInfo(active_only=False, poll=True)
    return self._net_info

  def NetInterfaces(self, active_only: bool = True):
    """Access the local network interfaces.

    Args:
      active_only: Only consider active interfaces.

    Returns:
      A list of NetInterface objects corresponding to each detected interface.
    """
    ni = net_info.NetInfo(active_only=active_only, poll=True)
    return ni.Interfaces()

  @functools.lru_cache()
  def Lab(self) -> bool:
    """Get state of lab pin.

    Returns:
      Boolean state of lab pin.
    """
    if spec.GetModule().GetLab().lower() == 'true':
      return True
    return False

  @functools.lru_cache()
  def OsCode(self) -> str:
    """Return the OS code associated with this build.

    Returns:
      the os code as a string

    Raises:
      Error: Reference to an unknown operating system.
    """
    os = self.ComputerOs()
    release_info = self._ReleaseInfo()
    if 'os_codes' in release_info:
      os_codes = release_info['os_codes']
      if os in os_codes:
        return os_codes[os]['code']
    raise Error('Unknown OS [%s]' % os)

  def Serialize(self, to_file):
    """Dumps internal data to a file for later reference."""

    build_data = {
        'BUILD': {
            'beyond_corp': str(self.BeyondCorp()),
            'Binary Path': str(self.BinaryPath()),
            'branch': str(self.Branch()),
            'build_timestamp': str(time.strftime('%m/%d/%Y %H:%M:%S')),
            'Chassis': str(self._HWInfo().ChassisType()),
            'Name': str(self.ComputerName()),
            'encryption_type': str(self.EncryptionLevel()),
            'FQDN': str(self.Fqdn()),
            'isLaptop': str(self.IsLaptop()),
            'image_id': str(self.ImageID()),
            'lab': str(self.Lab()),
            'Manufacturer': str(self.ComputerManufacturer()),
            'Model': str(self.ComputerModel()),
            'OS': str(self.ComputerOs()),
            'release': str(self.Release()),
            'Release Path': str(self.ReleasePath()),
            'SerialNumber': str(self.ComputerSerial()),
            'Support Tier': str(self.SupportTier()),
            'tpm_present': str(self.TpmPresent()),
            'is_virtual': str(self.IsVirtual()),
        }
    }
    # chooser data
    user_data = self._chooser_responses
    if user_data:
      for key in user_data:
        build_data['BUILD'][key] = str(user_data[key])
    # timers
    t = self._timers.GetAll()
    for key in t:
      build_data['BUILD']['TIMER_%s' % key] = str(t[key])
    with open(to_file, 'w') as handle:
      yaml.dump(build_data, handle)

  def _StringPinner(self, check_list, match_list, loose=False):
    """Checks a list of strings for acceptable matches.

    The check_list of strings should be one or more strings we want to verify,
    such as the computer model.

    The match_list is a list of strings which we will verify against, such as
    a list of pinned computer models.

    A direct match occurs when any one entry in check_list matches any one
    entry in match_list.  If loose is True, the direct match will happen if
    any one full string in check_list matches the beginning of any string in
    match_list.

    Also supports inverse pinning.  Inverse pins are strings starting with an
    exclamation point (!).  An inverse pin returns False if any one match
    string matches the inverse string (minus the !).

    Inverse pinning results in all non-list elements being treated as matches.
    If the set is not directly negated by a matching inverse pin, the outcome
    is a successful match.  For example:

    [!A, !B] returns False for A and False for B, but True for C.

    Any check_list with at least one inverse pin is treated strictly as an
    inverse set.  Direct pins are only considered if no inverse pins are
    present.  This is to compensate for direct matches being exclusive in
    nature.  It would not make sense to supply [!A, !B, C], because [C] would
    have the same result.

    All strings are compared in lowered case.

    Args:
      check_list: List of known strings.
      match_list: List of acceptable strings.
      loose: Accept partial matches (start of string only).

    Returns:
      True for a match between check_list and match_list, else False.
    """
    if not check_list or not match_list:
      logging.debug('Invalid string comparison sets. [%s, %s]', check_list,
                    match_list)
      return False
    inverse_in_set = False
    for pin in match_list:
      if not pin:
        continue
      pin = str(pin).lower()
      if pin[0] == '!':
        for item in check_list:
          real_pin = pin[1:]
          if ((loose and str(item).lower().startswith(real_pin)) or
              (not loose and real_pin == str(item).lower())):
            logging.debug('Excluded by inverse pin. [%s]', item)
            return False
        inverse_in_set = True

    if inverse_in_set:
      logging.debug('Included by inverse pinning.')
      return True

    for pin in match_list:
      pin = str(pin).lower()
      for item in check_list:
        if ((loose and str(item).lower().startswith(pin)) or
            (not loose and pin == str(item).lower())):
          logging.debug('Included by direct pin. [%s]', item)
          return True
    return False

  @functools.lru_cache()
  def SupportedModels(self) -> Dict[str, List[str]]:
    """Returns the list of known supported models (tier1 and tier2).

    Returns:
      A dict of two elements, tier1 and tier2, each with a list of models.
    """
    supported_models = {}
    models = self._ReleaseInfo()['supported_models']
    supported_models['tier1'] = [
        str(model).lower() for model in models['tier1']
    ]
    supported_models['tier2'] = [
        str(model).lower() for model in models['tier2']
    ]
    return supported_models

  @functools.lru_cache()
  def SupportTier(self) -> int:
    """Determines the support tier for the current device.

    Returns:
      0 = unknown or totally unsupported platform
      1 = tier1, fully supported platform
      2 = tier2, best effort/partial support
    """
    model = self.ComputerModel()
    supported = self.SupportedModels()
    if self._StringPinner([model], supported['tier1'], loose=True):
      logging.debug('Model %s is fully supported: tier1.', model)
      return 1
    if self._StringPinner([model], supported['tier2'], loose=True):
      logging.debug('Model %s is partially supported: tier2.', model)
      return 2
    logging.debug('Model %s is not recognized as supported.', model)
    return 0

  def TimerGet(self, name: str):
    return self._timers.Get(name)

  def TimerSet(self, name: str):
    self._timers.Set(name)

  def _TpmInfo(self) -> tpm_info.TpmInfo:
    if not self._tpm_info:
      self._tpm_info = tpm_info.TpmInfo()
    return self._tpm_info

  @functools.lru_cache()
  def TpmPresent(self) -> bool:
    """Get the TPM presence from WMI.

    Returns:
      True if a TPM is present, else False.
    """
    return self._TpmInfo().TpmPresent()

  @functools.lru_cache()
  def VideoControllers(self):
    """Get any local video (graphics) controllers.

    Returns:
      A list containing the detected devices.
    """
    return self._HWInfo().VideoControllers()

  @functools.lru_cache()
  def VideoControllersByName(self) -> List[str]:
    """Get all names of detected video controllers.

    Returns:
      A list containing the names of the detected devices.
    """
    names = []
    for v in self.VideoControllers():
      names.append(v['name'])
    return names

  @functools.lru_cache()
  def WinpeVersion(self) -> int:
    """The production WinPE version according to the distribution source."""
    return self._VersionInfo()['winpe-version']

  def Branch(self) -> str:
    """Determine the current build branch.

    Returns:
      The build branch as a string.

    Raises:
      Error: Reference to an unknown operating system.
    """
    versions = self.KnownBranches()
    comp_os = self.ComputerOs()
    if not comp_os:
      raise Error('Unable to determine host OS.')
    if comp_os in versions:
      return versions[comp_os]
    raise Error('Unable to find a release that supports %s.' % comp_os)
