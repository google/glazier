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
import subprocess
from typing import List, Optional

from glazier.lib import errors


def format_command(binary: str, args: Optional[List[str]] = None):
  """Format the command to execute.

  Args:
    binary: Full path the to binary.
    args: Additional commandline arguments.

  Returns:
    The command list required for subprocess and the formatted string for
    human-readable logging.
  """
  # If there is a quote in the binary, remove it.
  cmd = [binary.replace('"', '')]
  if args:
    cmd += args
  return cmd, ' '.join(map(str, cmd))


def execute_binary(binary: str, args: Optional[List[str]] = None,
                   return_codes: Optional[List[int]] = None,
                   shell: bool = False,
                   log: bool = True) -> int:
  """Execute a binary with optional parameters and return codes.

  Args:
    binary: Full path the to binary.
    args: Additional commandline arguments.
    return_codes: Acceptable exit/return codes. Defaults to 0.
    shell: Log to console only. Defaults to False and ignores log value.
    log: Display log messages. Defaults to True.

  Returns:
    Process return code if successfully exited.

  Raises:
    Error: Command returned invalid exit code.
  """
  cmd, string = format_command(binary, args)

  if not return_codes:
    return_codes = [0]

  if log:
    logging.info('Executing: %s', string)

  stdout = subprocess.PIPE
  stderr = subprocess.STDOUT
  if shell:
    stdout = None
    stderr = None
  try:
    process = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, shell=shell,
                               universal_newlines=True)
  except WindowsError as e:  # pylint: disable=undefined-variable
    raise errors.BinaryExecutionError(f'Failed to execute [{string}]') from e

  # Optionally log output to standard logger
  if not shell and log:
    for line in iter(process.stdout.readline, b''):
      # Break when empty newlines are detected
      if not line:
        break
      logging.info(line.strip())
    process.stdout.close()

  process.wait()

  if process.returncode not in return_codes:
    raise errors.BinaryExecutionError(
        f'Executing [{string}] returned invalid exit code [{process.returncode}]'
    )

  return process.returncode


def check_output(binary: str,
                 args: Optional[List[str]] = None,
                 return_codes: List[int] = None,
                 timeout: int = 300) -> str:
  """Executes a binary with optional parameters and checks the output.

  Args:
    binary: Full path the to binary.
    args: Additional commandline arguments.
    return_codes: Acceptable exit/return codes. Defaults to 0.
    timeout: How long, in seconds, to wait before exiting.

  Returns:
    Process stdout if the operation completed successfully.

  Raises:
    ExecReturnOutError
    ExecTimeoutError
  """
  cmd, string = format_command(binary, args)

  if not return_codes:
    return_codes = [0]

  logging.info('Executing: %s', string)
  try:
    process = subprocess.check_output(
        cmd,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        universal_newlines=True)
  except subprocess.CalledProcessError as e:
    # Process object does not exist if there was an error
    # Exception object contains the code and output
    out = e.output.strip()
    if e.returncode not in return_codes:
      raise errors.ExecReturnOutError(string, e.returncode, out)
    return out
  except subprocess.TimeoutExpired as e:
    raise errors.ExecTimeoutError(string, timeout) from e

  return process
