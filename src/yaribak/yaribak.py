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

# TODO: Include option to omit backup if run within some period of last backup.
# TODO: Add --exclude.
# TODO: Add tests.


def _times_str() -> str:
  now = datetime.datetime.now()
  return now.strftime('%Y%m%d_%H%M%S')


def _absolute_path(path: str) -> str:
  # This is more powerful than pathlib.Path.absolute(),
  # since it also works on "../thisdirectory".
  return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _get_commands(source: str, target: str) -> List[str]:
  if not os.path.isdir(target):
    # Do not proceed if destination does not exist.
    raise ValueError(f'Destination {target!r} does not exist')
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
  parser.add_argument('--dry-run',
                      action='store_true',
                      help='Do not make any change.')
  args = parser.parse_args()
  source = _absolute_path(args.source)
  target = _absolute_path(args.backup_path)
  dry_run: bool = args.dry_run
  commands = _get_commands(source, target)
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
