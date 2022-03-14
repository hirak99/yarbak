Yet another rsync based incremental backup utility.

# Purpose

A simple wrapper to use over rsync, to maintain incremental backups in differnet
directories.

## Comparison with Timeshift
This replicates part of timeshift's functionality.

Intendended to complement timeshift in backing up non-system directories.

Although this can be used to backup the root system, timeshift may be a better
option for that since it allows pretty safe restoring of the system.

Major differences from timeshift are -
* Allows you to choose destination directory
* Does not provide any automated restore functionality
* Can only be used from command line

Major similarities are -
* Does not require additional space when there is no change
* Uses hard links to replicate entire folder structure on any of the backups

# Setup and Usage

## Setup

Simply clone this repo, and use python3 to run the code.

## Example Usage

Backup home directory -

```bash
python3 path/to/yaribak.py \
  --source path/to/source \
  --backup-path path/to/backups
```

The following structure will be generated in the backup directory (for this example, after 3 calls) -
```
$ ls path/to/backups
_backup_20220306_232441
_backup_20220312_080749
_backup_20220314_110741
```

Any unchanged file between any two backups will be hard linked to the same inode. So overall space consumption between two successive backups will be small if there are no unchanged files.
