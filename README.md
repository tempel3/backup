# Simple backup scripts for nas etc.

Use at your own risk!

## Prerequisites

This scripts uses python3 and docker.

## Usage

Activate help:

`./local.py -h`

Backup locally:

`./local.py /etc /backup/etc`

Backup locally encrypted:

`./local.py /etc /backup/etc --passphrase=B4ckup`

Check for monitoring:

`./local.py /etc /backup/etc --check`

Restore files:

`./local.py /backup/etc /etc --restore`

Change cache directory with:

`./local.py /etc /backup/etc --cache_directory /var/lib/backup/`

## Thanks

Big thanks to
https://hub.docker.com/r/wernight/duplicity/

