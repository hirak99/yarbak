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

from . import backup_processor
from . import human_interval

from typing import List, Optional


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
  parser.add_argument('--minimum-wait',
                      type=str,
                      default='0s',
                      help=('Minimum time before next backup'
                            ' will be attempted. E.g. 2days.'))
  parser.add_argument('--min-ttl',
                      type=str,
                      default='',
                      help=('Guaranteed time to live. E.g. 7days, 1year, etc. '
                            'Takes priority over --max-to-keep. '
                            'Deletion will happen only if max-to-keep is >0.'))
  parser.add_argument('--max-to-keep',
                      type=int,
                      default=-1,
                      help=('How many backups to store. '
                            'A value of 0 or less disables this.'))
  parser.add_argument('--only-if-changed',
                      action='store_true',
                      help='Do not keep the backup if there is no change.')
  # This actually doesn't save much, ~150 bytes per file, or 15M for 100k files.
  parser.add_argument('--low-ram',
                      action='store_true',
                      help='Lowers memory usage a little. Can miss hard links.')
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
  low_ram: bool = args.low_ram
  dryrun: bool = args.dry_run
  verbose: bool = args.verbose
  min_ttl: Optional[float] = None
  if args.min_ttl:
    min_ttl = human_interval.parse_to_secs(args.min_ttl)
  max_to_keep: int = args.max_to_keep
  minimum_wait: float = human_interval.parse_to_secs(args.minimum_wait)
  exclude: List[str] = args.exclude or []

  processor = backup_processor.BackupProcessor(dryrun=dryrun,
                                               verbose=verbose,
                                               only_if_changed=only_if_changed,
                                               low_ram=low_ram,
                                               minimum_delay_secs=minimum_wait)
  processor.process(source=source,
                    target=target,
                    max_to_keep=max_to_keep,
                    excludes=exclude,
                    min_ttl=min_ttl)

  if dryrun:
    logging.info('Called with --dry-run, nothing was changed.')
  else:
    logging.info('Done')


if __name__ == '__main__':
  main()
