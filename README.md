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

Run the following -

```
sudo pip3 install yaribak
```

You can leave out the `sudo` in most distributions, or if you don't want to backup with super-user privileges.

## Example Usage

Backup home directory -

```bash
yaribak \
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

Each directory will have a full copy of the source.

_However_, any file that remains unchanged will be hard linked, preserving space.
