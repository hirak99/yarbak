Yet another rsync based incremental backup utility.

# Purpose

A simple wrapper to use over rsync, to maintain incremental backups in differnet
directories.

# Alternatives

## Comparison with Timeshift
This replicates part of timeshift's functionality. This allows control over the
backup directory, while sacrificing GUI and cron integration.

Also, although this can be used to backup the root system, timeshift may be a
better option for that since it allows pretty safe restoring of the system.

# Setup and Usage

## Setup

Run the following -

```bash
sudo pip3 install yaribak
```

You can leave out the `sudo` in most distributions, or if you don't want to
backup with super-user privileges.

## Example Usage

Backup home directory -

```bash
yaribak \
  --source path/to/source \
  --backup-path path/to/backups
```

The following structure will be generated in the backup directory (for this
example, after 3 calls) -
```
$ ls path/to/backups
_backup_20220306_232441
_backup_20220312_080749
_backup_20220314_110741
```

Each directory will have a full copy of the source.

_However_, any file that remains unchanged will be hard linked, preserving space.

# Testing

From the package root, run -
```python
./runtests.sh
```