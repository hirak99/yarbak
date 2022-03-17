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
"""Incremental backup creator

Example run -
  python yaribak.py \
    --source ~ \
    --backup-path /mnt/backup_drive/backup_home
"""
import argparse
import datetime
import os
import subprocess

from typing import List

# TODO: Move the backups to a payload/ subdirectory (so we can add metadata later).
# TODO: Instead of ValueError, print a legible error message.
# TODO: Include option to omit backup if run within some period of last backup.
# TODO: Add --exclude.


def _times_str() -> str:
  now = datetime.datetime.now()
  return now.strftime('%Y%m%d_%H%M%S')


def _absolute_path(path: str) -> str:
  # This is more powerful than pathlib.Path.absolute(),
  # since it also works on "../thisdirectory".
  return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _get_commands(source: str, target: str, max_to_keep: int) -> List[str]:
  commands = []
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
    commands.append(f'cp -al {latest} {new_backup}')
    # Rsync version, echoes the directories being copied.
    # commands.append(
    #     f'rsync -aAXHv {latest}/ {new_backup}/ --link-dest={latest}')

  commands.append(f'rsync -aAXHv --delete --progress {source}/ {new_backup}')

  if folders and max_to_keep >= 1:
    num_to_remove = len(folders) + 1 - max_to_keep
    if num_to_remove > 0:
      for folder in sorted(folders)[:num_to_remove]:
        commands.append(f'rm -r {folder}')

  return commands


def _execute(command: str) -> None:
  subprocess.run(command.split(' '), check=True)


def main():
  parser = argparse.ArgumentParser('yaribak')
  parser.add_argument('--source',
                      type=str,
                      required=True,
                      help='Source path to backup.')
  parser.add_argument('--backup-path',
                      type=str,
                      required=True,
                      help=('Destination path to backup to. '
                            'Backup directories will be created here.'))
  parser.add_argument(
      '--max-to-keep',
      type=int,
      default=-1,
      help='How many backups to store. A value of 0 or less disables this.')
  parser.add_argument('--dry-run',
                      action='store_true',
                      help='Do not make any change.')
  args = parser.parse_args()
  source = _absolute_path(args.source)
  target = _absolute_path(args.backup_path)
  dry_run: bool = args.dry_run
  max_to_keep: int = args.max_to_keep

  commands = _get_commands(source, target, max_to_keep)
  for i, command in enumerate(commands):
    print(f'# Command {i + 1}:')
    print(command)
    print()
    if not dry_run:
      _execute(command)
  if dry_run:
    print('Called with --dry-run, nothing was changed.')
  else:
    print(f'{len(commands)} commands executed.')


if __name__ == '__main__':
  main()
