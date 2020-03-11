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
"""Common process execution function wrappers."""

import logging
import os
import subprocess
from typing import List, Optional, Text


class Error(Exception):
  pass


def execute_binary(binary: Text, args: Optional[List[Text]] = None,
                   return_codes: Optional[List[int]] = None,
                   log: bool = True) -> Optional[int]:
  """Execute a binary with optional parameters and return codes.

  Args:
    binary: Full path the to binary.
    args: Additional commandline arguments.
    return_codes: Acceptable exit/return codes. Defaults to 0.
    log: Display log messages. Defaults to True.

  Returns:
    Process return code if successfully exited.

  Raises:
    Error: Command returned invalid exit code.
  """
  if not os.path.exists(binary):
    raise Error('Failed to locate binary: {}'.format(binary))

  cmd = [binary]
  if args:
    cmd += args
  string = ' '.join(map(str, cmd))

  if not return_codes:
    return_codes = [0]
  logging.info('Executing: %s', string)

  try:
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True)
  except WindowsError as e:  # pylint: disable=undefined-variable
    raise Error('Failed to execute: %s (%s)' % (string, str(e)))

  # Log output to standard logger
  while True:
    output = process.stdout.readline()
    if not output and process.poll() is not None:
      break
    if output and log:
      logging.info(output.strip())

  if process.returncode not in return_codes:
    raise Error("Executing '{0}' returned invalid exit code: {1}".format(
        string, process.returncode))

  return process.returncode
