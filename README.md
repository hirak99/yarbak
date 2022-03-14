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

## Example Call

Backup home directory -

```python
python rsync_incremental.py \
  --source ~ \
  --backup-path /mnt/backup/backup_home
```

