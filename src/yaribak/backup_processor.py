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
import functools
import logging
import os
import pathlib
import shutil
import subprocess

from typing import Iterator, List, Optional

from . import metadata
from . import utils

# TODO: Include option to omit backup if run within some period of last backup.

_SNAPSHOT_DIR_PREFIX = 'ysnap_'

# Time in seconds to buffer for elapsed time computation.
# A backup will trigger even if elapsed time is short by this much.
_ELAPSED_TIME_BUFFER = 30.0


# Useful for injection and testing.
@functools.lru_cache(maxsize=None)
def _now() -> datetime.datetime:
  return datetime.datetime.now()


def _now_epoch() -> float:
  return _now().timestamp()


def _now_str() -> str:
  return _now().strftime('%Y%m%d_%H%M%S')


class BackupProcessor:

  def __init__(self,
               dryrun: bool,
               verbose: bool,
               only_if_changed: bool = False,
               minimum_delay_secs: float = 0):
    self._dryrun = dryrun
    self._rsync_flags = '-aAXHSv' if verbose else '-aAXHS'
    self._rsync_flags += ' --delete --delete-excluded'
    self._only_if_changed = only_if_changed
    self._minimum_delay_secs = minimum_delay_secs

  def _execute_sh(self, command: str) -> Iterator[str]:
    """Optionally executes, and returns the command back for logging."""
    if not self._dryrun:
      logging.info(f'Running {command}')
      subprocess.run(command.split(' '), check=True)
    yield command

  def _create_metadata(self, directory: str, source: str) -> Iterator[str]:
    data = metadata.Metadata(source=source,
                             epoch=int(_now_epoch()),
                             updated_epoch=int(_now_epoch()))
    fname = os.path.join(directory, 'backup_context.json')
    if not self._dryrun:
      data.save_to(fname)
    yield f'[Store metadata at {fname}]'

  def _process_iterator(self, source: str, target: str, max_to_keep: int,
                        excludes: List[str]) -> Iterator[str]:
    """Creates an iterator of processes that need to be run for the backup."""
    if not os.path.isdir(target):
      raise ValueError(f'{target!r} is not a valid directory')
    prefix = os.path.join(target, _SNAPSHOT_DIR_PREFIX)
    # This is a temporary directory, to use in case backup is stopped in the middle.
    new_backup = os.path.join(target, prefix + '_incomplete')
    if not self._dryrun and os.path.exists(new_backup):
      yield f'[Remove lingering {new_backup}]'
      shutil.rmtree(new_backup)

    folders = [
        os.path.join(it.path)
        for it in os.scandir(target)
        if it.is_dir() and it.path.startswith(prefix)
    ]

    # The directory with latest backup.
    latest: Optional[str] = None
    old_metadata: Optional[metadata.Metadata] = None
    if folders:
      latest = max(folders)
      # Load and store old metadata.
      meta_fname = os.path.join(latest, 'backup_context.json')
      old_metadata = metadata.Metadata.load_from(meta_fname)

      delay_since = _now_epoch() - old_metadata.last_updated() + _ELAPSED_TIME_BUFFER
      if delay_since < self._minimum_delay_secs:
        logging.info(f'Nothing to do since elapsed time {delay_since:0.2f} '
                     f'is less than {self._minimum_delay_secs}.')
        return

      yield from self._execute_sh(f'cp -al {latest} {new_backup}')
      # Rsync version, echoes the directories being copied.
      # yield from self._execute(
      #     f'rsync -aAXHSv {latest}/ {new_backup}/ --link-dest={latest}'))
    else:
      yield from self._execute_sh(f'mkdir {new_backup}')
      # While creating the first backup, ensure that owner is maintained.
      # This is useful as backups may be often run as root.
      source_path = pathlib.Path(source)
      owner, group = source_path.owner(), source_path.group()
      yield from self._execute_sh(f'chown {owner}:{group} {new_backup}')

    yield from self._create_metadata(directory=new_backup, source=source)

    # List that will be joined to get the final command.
    new_backup_payload = os.path.join(new_backup, 'payload')
    command_build = [
        f'rsync {self._rsync_flags} {source}/ {new_backup_payload}'
    ]
    for exclude in excludes:
      command_build.append(f'--exclude={exclude}')
    yield from self._execute_sh(' '.join(command_build))

    # Backup is done. Remaining steps are for cleaning up.

    # Check if there was no change.
    if not self._dryrun and self._only_if_changed and latest is not None:
      no_change = utils.is_hardlinked_replica(os.path.join(latest, 'payload'),
                                              new_backup_payload)
      # If no_change, remove new backup and update old metadata.
      if no_change:
        logging.info('There was no change. Removing the new backup.')
        yield from self._execute_sh(f'rm -r {new_backup}')
        # Update the $metadata.
        assert old_metadata is not None
        old_metadata.updated_epoch = int(_now_epoch())
        old_metadata.save_to(meta_fname)
        # Return early and do not remove older directories.
        return

    final_directory = os.path.join(target, prefix + _now_str())
    yield f'[Rename {new_backup} to {final_directory}]'
    if not self._dryrun:
      shutil.move(new_backup, final_directory)

    # Delete older backups.
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
      logging.info(f'End of step #{i+1}. {step}')
