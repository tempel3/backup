#!/usr/bin/env python3

__author__ = "Paul Stempel"
__copyright__ = "Copyright (C) 2018 Paul Stempel"
__license__ = "MIT"
__version__ = "1.0"

import subprocess
import argparse
import re
import os
import time

# https://hub.docker.com/r/wernight/duplicity/

parser = argparse.ArgumentParser(description='Backup locally.')
parser.add_argument('from_directory', help='Source directory for backup or restore.')
parser.add_argument('to_directory', help='Target directory for backup or restore.')
parser.add_argument('--info', help='Show only information about backup. No backup will be done.', action='store_true')
parser.add_argument('--check', help='Check backup age. For old backups script will exit with 2.', action='store_true')
parser.add_argument('--restore', help='Restore latest backup.', action='store_true')
parser.add_argument('--critical', type=int, dest='critical', default=14*24*3600,
                        help='Backup age considered as critical in seconds. (default: two weeks)')

parser.add_argument('--remove_older_than', default ="10Y",
                        help='Remove old backups after backup. Use for instance 6M, 2Y. (default: 10Y)' )

parser.add_argument('--cache_directory', default ="/var/lib/backup/", help="Directory for duplicity cache. (default: /var/lib/backup/)")

parser.add_argument('--passphrase', help="Use encryption with this passphrase.")

args = parser.parse_args()

from_directory = args.from_directory
to_directory = args.to_directory

cache_directory = args.cache_directory

if not os.path.exists(from_directory):
  raise Exception("{} directory not found.".format(from_directory))

if not os.path.exists(to_directory):
  raise Exception("{0} directory not found.".format(to_directory))

command = ["docker", "run", "--rm", "-it", "--user", "root"]

if args.passphrase:
  command = command + ["-e", "PASSPHRASE={0}".format(args.passphrase)]
  
command = command + ["-v", "{}/.cache:/home/duplicity/.cache/duplicity".format(cache_directory),
  "-v", "{}/.gnupg:/home/duplicity/.gnupg".format(cache_directory),
  "-v", "{}:/from_directory:ro".format(from_directory),
  "-v", "{}:/to_directory".format(to_directory),
  "wernight/duplicity",
  "duplicity"]

print(command)

def get_encyption_arguments():
  if args.passphrase:
    return []
  return ["--no-encryption"]

def print_collection_status():
  subprocess.check_call(command +
    ["collection-status",     
     "file:///to_directory"] + get_encyption_arguments())

def get_collection_status():
  out = subprocess.check_output(command +
    ["collection-status",     
     "file:///to_directory"] + get_encyption_arguments())
  return str(out)

def last_backup_time():
    status = get_collection_status()

    lastbackup = 0

    for line in status.split("\\r\\n"):
        parts = line.split()
        # Example line: Full         Wed May 18 21:47:38 2016              1113
        if parts[0] == "Full" or parts[0] == "Incremental":
          converted_time = " ".join(parts[1:6])
          backuptime = time.mktime(time.strptime(converted_time, "%a %b %d %H:%M:%S %Y"))

          if lastbackup < backuptime:
            lastbackup = backuptime            

    return lastbackup

def check_last_backup(max_age_in_seconds):
  try:
    lastbackup = last_backup_time()

    if lastbackup < time.time() - max_age_in_seconds:
      print("CRITICAL: Backup too old: {}".format(time.ctime(lastbackup)))
      exit(2)
    else:
      print("OK: Last backup is ok: {}".format(time.ctime(lastbackup)))
      exit(0)

  except Exception as e:
    print("CRITICAL: Caught exception - {}".format(str(e)))
    exit(2)  

# mein case
if args.check:
  check_last_backup(args.critical)

elif args.info:
  print_collection_status()

elif args.restore:
  print("Restoring from backup")
  subprocess.check_call(command +
    ["restore",     
    "--allow-source-mismatch",
    "file:///from_directory", 
    "/to_directory"]  + get_encyption_arguments())

else:
  print("Starting backup.")
  subprocess.check_call(command +
    ["--full-if-older-than=6M",
    "--allow-source-mismatch",
    "/from_directory", 
    "file:///to_directory"]  + get_encyption_arguments())

  if args.remove_older_than:
    print("Remove old backups.")
    subprocess.check_call(command +
      ["remove-older-than", 
      args.remove_older_than, 
      "--force", 
      "file:///to_directory"] + get_encyption_arguments())

  print("Cleanup backups.")
  subprocess.check_call(command +
      ["cleanup", 
      "--force", 
      "file:///to_directory"]  + get_encyption_arguments())