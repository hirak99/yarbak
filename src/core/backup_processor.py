# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import subprocess
import time

from typing import Iterator, List

from . import metadata

# TODO: Include option to omit backup if run within some period of last backup.
# TODO: Implement safety by marking backup as .incomplete, and mv at the end.


def _times_str() -> str:
  now = datetime.datetime.now()
  return now.strftime('%Y%m%d_%H%M%S')


class BackupProcessor:

  def __init__(self, dryrun: bool):
    self._dryrun = dryrun

  def _execute_sh(self, command: str) -> Iterator[str]:
    """Optionally executes, and returns the command back for logging."""
    if not self._dryrun:
      print(f'Running {command}')
      subprocess.run(command.split(' '), check=True)
    yield command

  def _create_metadata(self, directory: str, source: str) -> Iterator[str]:
    data = metadata.Metadata(source=source, epoch=int(time.time()))
    fname = os.path.join(directory, 'metadata.json')
    if not self._dryrun:
      with open(fname, 'w') as f:
        f.write(data.asjson())
    yield f'Store metadata at {fname}'

  def _process_iterator(self, source: str, target: str, max_to_keep: int,
                        excludes: List[str]) -> Iterator[str]:
    """Creates an iterator of processes that need to be run for the backup."""
    if not os.path.isdir(target):
      raise ValueError(f'{target!r} is not a valid directory')
    prefix = os.path.join(target, '_backup_')
    folders = [
        os.path.join(it.path)
        for it in os.scandir(target)
        if it.is_dir() and it.path.startswith(prefix)
    ]
    new_backup = os.path.join(target, prefix + _times_str())

    if folders:
      latest = max(folders)
      yield from self._execute_sh(f'cp -al {latest} {new_backup}')
      # Rsync version, echoes the directories being copied.
      # yield from self._execute(
      #     f'rsync -aAXHSv {latest}/ {new_backup}/ --link-dest={latest}'))
    else:
      yield from self._execute_sh(f'mkdir {new_backup}')

    yield from self._create_metadata(directory=new_backup, source=source)

    # List that will be joined to get the final command.
    command_build = [
        f'rsync -aAXHSv {source}/ {new_backup}/payload',
        '--delete --progress --delete-excluded'
    ]
    for exclude in excludes:
      command_build.append(f'--exclude={exclude}')
    yield from self._execute_sh(' '.join(command_build))

    if folders and max_to_keep >= 1:
      num_to_remove = len(folders) + 1 - max_to_keep
      if num_to_remove > 0:
        for folder in sorted(folders)[:num_to_remove]:
          yield from self._execute_sh(f'rm -r {folder}')

  def process(self, *args, **kwargs) -> None:
    # Just runs through the iterator.
    # Without this, the iterator will be created but processes
    # may not be called.
    for i, step in enumerate(self._process_iterator(*args, **kwargs)):
      print(f'End of step #{i+1}. {step}')
