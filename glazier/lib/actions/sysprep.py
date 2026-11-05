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
import time
from typing import Optional
# do not remove: internal placeholder 1
from glazier.lib import timezone
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from gwinpy.net import dhcp

# Number of times to query DHCP for the timezone option before giving up.
_DHCP_ATTEMPTS = 5
# Seconds to wait between DHCP attempts.
_DHCP_RETRY_SECONDS = 5


def _QueryTimezone(intf) -> Optional[str]:
  """Queries the DHCP servers reachable from an interface for option 101.

  The interface's own DHCP server is tried first, if known, followed by the
  broadcast address.

  Args:
    intf: A network interface with ip_address, mac_address and dhcp_server.

  Returns:
    The first non-empty decoded timezone, or None if no server returned one.
  """
  servers = ['255.255.255.255']
  if intf.dhcp_server:
    servers.insert(0, intf.dhcp_server)
  logging.debug(
      'Attempting to get timezone from interface with IP %s and MAC %s',
      intf.ip_address,
      intf.mac_address,
  )
  for dhcp_server in servers:
    dhcp_response = dhcp.GetDhcpOption(
        client_addr=intf.ip_address,
        client_mac=intf.mac_address,
        option=101,
        server_addr=dhcp_server,
    )
    if dhcp_response is None:
      logging.warning(
          'No DHCP option 101 response received from server %s.', dhcp_server
      )
      continue
    try:
      zone = dhcp_response.decode('utf-8')
    except (AttributeError, UnicodeDecodeError):
      logging.warning(
          'Could not decode DHCP option 101 response %r from server %s.',
          dhcp_response,
          dhcp_server,
      )
      continue
    logging.debug('DHCP server %s returned: %s', dhcp_server, zone)
    if zone:
      return zone
  return None


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
    from_dhcp: Optional[str] = None
    attempt = 0
    for attempt in range(1, _DHCP_ATTEMPTS + 1):
      for intf in self._build_info.NetInterfaces():
        if intf.ip_address and intf.mac_address:
          from_dhcp = _QueryTimezone(intf)
          if from_dhcp is not None:
            break
      if from_dhcp is not None or attempt == _DHCP_ATTEMPTS:
        break
      logging.debug(
          'No result from DHCP on attempt %d of %d. Retrying in %d seconds...',
          attempt,
          _DHCP_ATTEMPTS,
          _DHCP_RETRY_SECONDS,
      )
      time.sleep(_DHCP_RETRY_SECONDS)

    if from_dhcp is not None:
      logging.debug('Got timezone %s from DHCP.', from_dhcp)
      tz = timezone.Timezone(load_map=True)
      translated = tz.TranslateZone(from_dhcp)
      if translated:
        local_tz = translated
        logging.debug('Successfully translated timezone to %s.', local_tz)
      else:
        logging.error('Could not translate DHCP timezone.')
        logging.warning('Falling back to default timezone %s.', local_tz)
    else:
      logging.error(
          'Could not find timezone from DHCP after %d attempt(s).', attempt
      )
      logging.warning('Falling back to default timezone %s.', local_tz)
    logging.debug('Finalized timezone is %s.', local_tz)
    self._EditUnattend(local_tz)
