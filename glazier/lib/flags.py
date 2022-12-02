# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Flags used by the Glazier imaging code."""

import threading
import typing
from absl import flags
from glazier.lib.spec import spec

FLAGS = flags.FLAGS
flags.DEFINE_string('binary_root_path', '/bin', 'Path to the binary storage.')
flags.DEFINE_string('binary_server', '', 'Root URL for binary build files.')
flags.DEFINE_boolean('config_branches', True,
                     'The configuration repository uses branched paths.')
flags.DEFINE_string('config_root_path', 'config',
                    'Path to the root of the configuration directory.')
flags.DEFINE_string('config_server', 'https://glazier-server.example.com',
                    'Root URL for configuration build data.')

flags.DEFINE_enum('environment', 'Host', ['Host', 'WinPE'],
                  'The running host environment.')
flags.DEFINE_string('ntp_server', 'time.google.com',
                    'Server to use for synchronizing the local system time.')
flags.DEFINE_list(
    'verify_urls', [
        'https://www.catalog.update.microsoft.com/Home.aspx',
    ], 'Comma-separated list of URLs to verify are reachable at start')
flags.DEFINE_enum(
    'glazier_spec', 'flag', list(spec.SPEC_OPTS.keys()),
    ('Which host specification module to use for determining host features '
     'like Hostname and OS.'))

cache = dict()
cache_lock = threading.Lock()


def _ReadFromCache(key: str) -> typing.Optional[str]:
  with cache_lock:
    return cache.get(key, None)


def _WriteToCache(key: str, value: typing.Optional[str]) -> None:
  with cache_lock:
    if value:
      cache[key] = value


# Clears the internal cache. Primarily used for testing.
def ClearCache():
  with cache_lock:
    cache.clear()


def GetBinaryPathFlag() -> str:
  """Determines the path to the folder containing all binaries for build.

  Returns:
    The versioned base path to the current build as a string.
  """
  server = GetBinaryServerFlag() or ''
  server = server.rstrip('/')
  path = FLAGS.binary_root_path.strip('/')
  path = '%s/%s/' % (server, path)
  return path


def GetBinaryServerFlag(set_to: str = '') -> str:
  """Get (or set) the binary server address.

  Args:
    set_to: Update the internal server address.

  Returns:
    The binary server without any trailing slashes.
  """
  _WriteToCache('binary_server', set_to)
  result = _ReadFromCache('binary_server')

  if not result:
    if FLAGS.binary_server:
      result = FLAGS.binary_server
    else:  # backward compatibility
      result = GetConfigServerFlag()
    _WriteToCache('binary_server', value=result)

  return result.rstrip('/')


def GetConfigServerFlag(set_to: str = '') -> str:
  """Get (or set) the config server address.

  Args:
    set_to: Update the internal server address.

  Returns:
    The config server without any trailing slashes.
  """
  _WriteToCache('config_server', value=set_to)
  result = _ReadFromCache('config_server')

  if not result:
    result = FLAGS.config_server
    _WriteToCache('config_server', value=result)

  return result.rstrip('/')
