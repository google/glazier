# Lint as: python3
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
"""Takes a relative path and beyond_corp imaging seed to retrieve signed URL.

The BeyondCorp class will read the contents of a seed file and pass it along
with the path of the file being requested. The sign_endpoint will return
a signed URL, which will be returned to download new files.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import base64
import functools
import hashlib
import json
import logging

from absl import flags
from glazier.lib import constants
from glazier.lib import registry
import requests
from gwinpy.wmi import hw_info
from gwinpy.wmi import wmi_query

FLAGS = flags.FLAGS

flags.DEFINE_boolean('use_signed_url', False,
                     'Select whether or not to use signed urls')
flags.DEFINE_string('sign_endpoint', None, 'The signing URL endpoint to use')
flags.DEFINE_string('seed_path', None, 'Path to the seed file on disk')


class BCError(Exception):
  pass


class BeyondCorp(object):
  """Defines funtions needed to retrieve a signed URL."""

  def _ReadFile(self):
    """Reads the seed file and returns a json blob.

    Returns:
      contents of the file.
    """
    try:
      with open(FLAGS.seed_path) as p:
        return json.load(p)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
      raise BCError(e)

  @functools.lru_cache()
  def CheckBeyondCorp(self) -> bool:
    """Verify whether the image is running Beyond Corp.

    Returns:
      True if running beyond_corp.
      False if not running beyond_corp.
    """

    if FLAGS.use_signed_url:
      try:
        registry.set_value('beyond_corp', 'True', path=constants.REG_ROOT)
        return True
      except registry.Error as e:
        raise BCError(e)
    else:
      try:
        bc = registry.get_value('beyond_corp', path=constants.REG_ROOT)
        if bc:
          if bc.lower() == 'true':
            return True
          elif bc.lower() == 'false':
            return False
      except registry.Error as e:
        logging.warning(str(e))

    try:
      registry.set_value('beyond_corp', 'False', path=constants.REG_ROOT)
    except registry.Error as e:
      raise BCError(e)
    return False

  @functools.lru_cache()
  def _GetHash(self, file_path: str) -> bytes:
    """Calculates the hash of the boot wim.

    Args:
      file_path: path to the file to be hashed

    Returns:
      hash of boot wim in hex
    """
    block_size = 33554432  # define bytes to read at a time when hashing (32mb)
    hasher = hashlib.sha256()

    with open(file_path, 'rb') as f:
      fb = f.read(block_size)
      while fb:
        hasher.update(fb)
        fb = f.read(block_size)
    return base64.b64encode(hasher.digest())

  def _GetDisk(self, label: str) -> str:
    """Leverages the drive label to define the drive letter.

    The BeyondCorp USB device is not gaurenteed to be on a certain drive letter.

    Args:
      label: Drive label to use when querying for drive letter.

    Raises:
      BCError: Error executing WMI query.
      BCError: BeyondCorp drive letter was empty.

    Returns:
      Drive letter for the drive that contains the seed.
    """
    query = f'SELECT Name FROM win32_logicaldisk WHERE volumename="{label}"'
    try:
      drive_letter = wmi_query.WMIQuery().Query(query)[0].Name
    except wmi_query.WmiError as e:
      raise BCError(f'Failed to query WMI for BeyondCorp drive letter: {e}')

    if not drive_letter:
      raise BCError('BeyondCorp drive letter was empty.')

    logging.debug('BeyondCorp Drive letter = %s', drive_letter)

    return drive_letter

  def GetSignedUrl(self, relative_path: str) -> str:
    """Passes data the sign endpoint to retrieve signed URL.

    Args:
      relative_path: the relative path of the file being downloaded.

    Raises:
      BCError: Error with retrieving info from sign endpoint

    Returns:
      A signed_url string
    """
    if not FLAGS.use_signed_url:
      raise BCError('use_signed_url flag not configured.')

    if FLAGS.sign_endpoint is None or FLAGS.seed_path is None:
      raise BCError('sign_endpoint and seed_path cannot be None when using'
                    'Signed URL.')

    hwinfo = hw_info.HWInfo()
    drive_letter = self._GetDisk(constants.USB_VOLUME_LABEL).strip(':')

    data = self._ReadFile()
    data = {
        'Path':
            relative_path,
        'Mac':
            hwinfo.MacAddresses(),
        'Seed':
            data['Seed'],
        'Signature':
            data['Signature'],
        'Hash':
            self._GetHash(fr'{drive_letter}:\sources\boot.wim').decode('utf-8')
    }

    req = json.dumps(
        data,
        ensure_ascii=True,
        sort_keys=True,
        indent=None,
        separators=(',', ': '))
    try:
      res = requests.post(FLAGS.sign_endpoint, data=req)
    except requests.exceptions.ConnectionError as e:
      raise BCError(e)

    if res.status_code != 200 or res.json(
    )['Status'] != 'Success' or not res.json()['SignedURL']:
      raise BCError('Invalid response from signed url. Code: %s, Status: %s' %
                    (res.status_code, res.json()['Status']))
    return res.json()['SignedURL']
