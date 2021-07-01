#!/bin/env python3

import sys
import os.path
import logging
import tarfile
import codecs
import requests
import gnupg

GPG_HOME_FOLDER = "/root/.gnupg"
UNENCRYPTED_LOGS_FOLDER = "/project/data/logs/http"

def strip_newlines(file):
    return list(line.rstrip('\n') for line in file)

def yield_files_from_filename(file_path, gpg_instance, passphrase):
    """ Yields file-like objects containing JSON.
        Since this functions also takes archive files, one filename can potentially yield multiple file-like objects
    """
    filename = os.path.split(file_path)[1]
    if filename.endswith(".json.tar.gz"): # Untar and then read the output
        with tarfile.open(file_path) as tar:
            reader = codecs.getreader("utf-8")
            for member in tar.getmembers():
                memberfile = tar.extractfile(member)
                yield reader(memberfile)
    elif filename.endswith(".json"):
        with open(file_path) as f:
            yield f
    elif filename.endswith(".json.gpg"): # Decrypt and then read the output
        unencrypted_filename = filename.replace('.json.gpg', '.json')
        output_path = os.path.join(UNENCRYPTED_LOGS_FOLDER, unencrypted_filename)
        with open(file_path, "rb") as f:
            logging.info("Starting decryption for {} ...".format(file_path))
            decryption_status = gpg_instance.decrypt_file(f, passphrase=passphrase, always_trust=True, output=output_path)
            if not decryption_status.ok:
                raise Exception("GPG Decryption failed: {}".format(decryption_status.status))
            yield yield_files_from_filename(output_path, gpg_instance, passphrase)

# Check input
if len(sys.argv) < 6:
    print("Usage: ./import-logs.py RECIPIENT PASSPHRASE_FILE URL INDEX FILE...")
    exit(1)

for arg in sys.argv[5:]:
    if not os.path.isfile(arg):
        print("{0:s} is not a file.".format(arg))
        print("Usage: ./import-logs.py RECIPIENT PASSPHRASE_FILE URL INDEX FILE...")
        exit(1)

# Assign variables
url = sys.argv[3]

index = sys.argv[4]

command = '{{ "index" : {{ "_index" : "{0:s}" }} }}'.format(index)
def to_bulk_query(events):
    for event in events:
        yield command + '\n'
        yield event + '\n'

logging.info("Initializing Python gpg")
gpg = gnupg.GPG(gnupghome=GPG_HOME_FOLDER)

# Send input to Bulk API file-per-file
for filename in sys.argv[5:]:
    print("Ingesting file: {0:s}".format(filename))
    try:
        for file in yield_files_from_filename(filename, gpg, sys.argv[2]):
            bulkdata = to_bulk_query(file)

            # Send request to Bulk API
            headers = { 'content-type' : 'application/json' }
            print("Started streaming")

            response = requests.post("{0:s}/_bulk".format(url), data=bulkdata, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Print result
            print("Ingested file: {0:s}".format(filename))
            print("Response: {0:d}".format(response.status_code))
    except Exception as e:
        print("Skipped file: {0:s}".format(filename))
        raise e
