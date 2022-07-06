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

"""Actions for sysprep-related activities."""

import logging
import re
# do not remove: internal placeholder 1
from glazier.lib import timezone
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from gwinpy.net import dhcp


class SetUnattendTimeZone(BaseAction):
  """Configure the TimeZone entries in unattend.xml."""

  def _EditUnattend(self,
                    zone,
                    unattend_path=r'C:\Windows\Panther\unattend.xml'):
    """Edit the unattend.xml to replace the timezone entry.

    Args:
      zone: The timezone string to insert into <TimeZone></TimeZone>
      unattend_path: Path to the unattend.xml file.
    """
    lines = []
    try:
      with open(unattend_path) as unattend:
        lines = unattend.readlines()
      lines = [
          re.sub('<TimeZone>.*?</TimeZone>', '<TimeZone>%s</TimeZone>' % zone,
                 l) for l in lines
      ]
      with open(unattend_path, 'w') as unattend:
        unattend.write(''.join(lines))
    except IOError as e:
      raise ActionError('Unable to set time zone in unattend.xml') from e

  def Run(self):
    """Sets the timezone inside unattend.xml."""
    local_tz = 'Pacific Standard Time'
    from_dhcp = False
    retries = 0
    while not from_dhcp and retries < 5:
      for intf in self._build_info.NetInterfaces():
        if intf.ip_address and intf.mac_address:
          servers = ['255.255.255.255']
          if intf.dhcp_server:
            servers.insert(0, intf.dhcp_server)
          logging.debug(
              'Attempting to get timezone from interface with IP %s and MAC %s',
              intf.ip_address, intf.mac_address)
          for dhcp_server in servers:
            dhcp_response = dhcp.GetDhcpOption(
                client_addr=intf.ip_address,
                client_mac=intf.mac_address,
                option=101, server_addr=dhcp_server)
            try:
              from_dhcp = dhcp_response.decode('utf-8')
            except AttributeError:
              logging.warning('could not decode dhcp response %s',
                              dhcp_response)
              from_dhcp = None
            logging.debug('DHCP server %s returned: %s', dhcp_server, from_dhcp)
            if from_dhcp:
              break
          if from_dhcp:
            break
      logging.debug('No result from DHCP.  Retrying...')
      retries += 1

    if from_dhcp:
      logging.debug('Got timezone %s from DHCP.', from_dhcp)
      tz = timezone.Timezone(load_map=True)
      translated = tz.TranslateZone(from_dhcp)
      if translated:
        local_tz = translated
        logging.debug('Successfully translated timezone to %s.', local_tz)
      else:
        logging.error('Could not translate DHCP timezone.')
    else:
      logging.error('Could not find timezone from DHCP.')
    logging.debug('Finalized timezone is %s.', local_tz)
    self._EditUnattend(local_tz)
