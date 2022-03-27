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

from typing import Iterator, List

# TODO: Instead of ValueError, print a legible error message.
# TODO: Include option to omit backup if run within some period of last backup.


def _times_str() -> str:
  now = datetime.datetime.now()
  return now.strftime('%Y%m%d_%H%M%S')


def _absolute_path(path: str) -> str:
  # This is more powerful than pathlib.Path.absolute(),
  # since it also works on "../thisdirectory".
  return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _process(source: str, target: str, max_to_keep: int, excludes: List[str],
             dryrun: bool) -> Iterator[str]:
  if not os.path.isdir(target):
    raise ValueError(f'{target!r} is not a valid directory')
  prefix = os.path.join(target, '_backup_')
  folders = [
      os.path.join(it.path)
      for it in os.scandir(target)
      if it.is_dir() and it.path.startswith(prefix)
  ]
  new_backup = os.path.join(target, prefix + _times_str())

  def _execute(command: str) -> str:
    """Optionally executes, and returns the command back."""
    if not dryrun:
      subprocess.run(command.split(' '), check=True)
    return command

  if folders:
    latest = max(folders)
    yield _execute(f'cp -al {latest} {new_backup}')
    # Rsync version, echoes the directories being copied.
    # commands.append(
    #     f'rsync -aAXHSv {latest}/ {new_backup}/ --link-dest={latest}')
  else:
    yield _execute(f'mkdir {new_backup}')

  # List that will be joined to get the final command.
  command_build = [
      f'rsync -aAXHSv {source}/ {new_backup}/payload',
      '--delete --progress --delete-excluded'
  ]
  for exclude in excludes:
    command_build.append(f'--exclude={exclude}')
  yield _execute(' '.join(command_build))

  if folders and max_to_keep >= 1:
    num_to_remove = len(folders) + 1 - max_to_keep
    if num_to_remove > 0:
      for folder in sorted(folders)[:num_to_remove]:
        yield _execute(f'rm -r {folder}')


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
  # Creates a list of strings.
  parser.add_argument('--exclude',
                      action='append',
                      help='Directories to exclude')
  args = parser.parse_args()
  source = _absolute_path(args.source)
  target = _absolute_path(args.backup_path)
  dryrun: bool = args.dry_run
  max_to_keep: int = args.max_to_keep
  exclude: List[str] = args.exclude or []

  _process(source, target, max_to_keep, exclude, dryrun)

  if dryrun:
    print('Called with --dry-run, nothing was changed.')


if __name__ == '__main__':
  main()
