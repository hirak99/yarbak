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
import logging
import os

from core import backup_processor

from typing import List


def _absolute_path(path: str) -> str:
  # This is more powerful than pathlib.Path.absolute(),
  # since it also works on "../thisdirectory".
  return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def main():
  logging.basicConfig(level=logging.INFO)

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
  parser.add_argument('--only-if-changed',
                      action='store_true',
                      help='Do not keep the backup if there is no change.')
  parser.add_argument('--verbose',
                      action='store_true',
                      help='Passes -v to rsync.')
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
  only_if_changed: bool = args.only_if_changed
  dryrun: bool = args.dry_run
  verbose: bool = args.verbose
  max_to_keep: int = args.max_to_keep
  exclude: List[str] = args.exclude or []

  processor = backup_processor.BackupProcessor(dryrun=dryrun,
                                               verbose=verbose,
                                               only_if_changed=only_if_changed)
  processor.process(source, target, max_to_keep, exclude)

  if dryrun:
    logging.info('Called with --dry-run, nothing was changed.')
  else:
    logging.info('Done')


if __name__ == '__main__':
  main()
