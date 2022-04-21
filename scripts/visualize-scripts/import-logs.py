#!/bin/env python3

import sys
import time
from random import random
import os.path
import logging
import tarfile
from string import Template
import requests
import gnupg
import more_itertools
from joblib import Parallel, delayed

# when decrypting, ensure GPG_HOME_FOLDER exists
GPG_HOME_FOLDER = "/root/.gnupg"
UNENCRYPTED_LOGS_FOLDER = "/project/data/logs/http"

# utils
def strip_newlines(file):
    return list(line.rstrip('\n') for line in file)

def preprocess_file(file_path, destination_folder, passphrase):
    """ Yields file-like objects containing JSON.
        Since this functions also takes archive files, one filename can potentially yield multiple file-like objects
    """
    filename = os.path.split(file_path)[1]
    if filename.endswith(".json.tar.gz"): # Untar and then read the output
        return extract_file(file_path, destination_folder)
    elif filename.endswith(".json.gpg"): # Decrypt and then read the output
        return decrypt_file(file_path, destination_folder, passphrase)
    else:
        raise Exception("Unknown file type for file {}".format(filename))

def extract_file(source_path, destination_folder):
    filename = os.path.split(source_path)[1]
    extracted_filename = filename.replace('.tar.gz', '')
    dest_path = os.path.join(destination_folder, extracted_filename)
    if os.path.exists(dest_path):
        print("An extracted version of '{}' already exists in '{}'. Skipping extraction.".format(filename, destination_folder))
    else:
        print("Starting extraction of {}".format(filename))
        with tarfile.open(source_path) as tar:
            tar.extract(extracted_filename, destination_folder)
    return dest_path


def init_gpg():
    print("Initializing Python gpg")
    return gnupg.GPG(gnupghome=GPG_HOME_FOLDER, use_agent=True)


try:
    gpg_instance = init_gpg()
except:
    # The following happens when importing stats
    print("GPG not configured")


def decrypt_file(source_path, destination_folder, passphrase):
    filename = os.path.split(source_path)[1]
    unencrypted_filename = filename.replace('.json.gpg', '.json')
    output_path = os.path.join(destination_folder, unencrypted_filename)
    if os.path.exists(output_path):
        print("An unencrypted version of '{}' already exists in '{}'. Skipping decryption.".format(filename, destination_folder))
        return output_path
    else:
        retries = 10
        if do_decrypt_file(source_path, passphrase, output_path, retries):
            return output_path
        else:
            raise Exception("GPG Decryption failed {} times".format(retries))


def do_decrypt_file(source_path, passphrase, output_path, retries):
    with open(source_path, "rb") as f:
        try:
            decryption_status = gpg_instance.decrypt_file(f, passphrase=passphrase, always_trust=True, output=output_path)
            # debug with `extra_args=["-v"]`
            decryption_succeeded = decryption_status.ok
        except:
            decryption_succeeded = False
            print("Decryption process crashed for {}".format(source_path))

        if decryption_succeeded:
            return True
        else:
            if retries > 1:
                print("Failed to decrypt '{}' retrying {} more times".format(source_path, retries))
                time.sleep(1 + random())
                do_decrypt_file(source_path, passphrase, output_path, retries - 1)
            else:
                print("Exhausted retries to decrypt '{}'".format(source_path))
                return False


def es_ingest_file(file_path, es_host, es_index_name, batch_size):
    with open(file_path, "rt") as file:
        # Streaming multiple GB's to the ES "/_bulk" endpoint in a single request causes memory issues in ES
        # Making one request per log-line on the other hand seems slow.
        file_itor = more_itertools.ichunked(file, batch_size)

        for lines in file_itor:
            es_bulk_command = generate_bulk_index_command(es_index_name, lines)
            headers = { 'content-type' : 'application/json' }
            response = requests.post("{}/_bulk".format(es_host), data=es_bulk_command, headers=headers)

            if response.status_code == 429: # Too Many Requests
                print("Response status: 429 - Too Many Requests. Try to lower the batch size or increase Java's available memory.")

            response.raise_for_status()

def generate_bulk_index_command(es_index_name, lines):
    commands = []
    for line_str in lines:
        # line_str includes new line characters, like elastic search expects
        command = es_command_template.substitute(index_name=es_index_name, payload=line_str)
        commands.append(command)

    commands_str = "".join(commands).encode('utf-8')
    return commands_str


def ingest_path(gpg_passphrase, es_host, es_index_name, es_batch_size):
    def do_ingest_path(idx, file_path):
        if os.path.isfile(file_path):
            if os.path.splitext(file_path) != ".json":
                print("{}: Extracting and ingesting '{}'".format(idx, file_path))
                ingest_path = preprocess_file(file_path, UNENCRYPTED_LOGS_FOLDER, gpg_passphrase)
            else:
                print("{}: Ingesting '{}'".format(idx, file_path))
                ingest_path = file_path

            start_time = time.time()
            es_ingest_file(ingest_path, es_host, es_index_name, es_batch_size)
            duration = time.time() - start_time

            print("{}: Succesfully ingested file {} in {:.2f}s".format(idx, ingest_path, duration))
        else:
            print("{}: '{}' is not a file. Skipping".format(idx, file_path))
    return do_ingest_path

# https://www.elastic.co/guide/en/elasticsearch/reference/7.9/docs-bulk.html#docs-bulk-api-desc
es_command_template = Template("""
{ "index": { "_index": "$index_name" } }
$payload
""")

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # Args validation
    if len(sys.argv) < 7:
        logging.error("Usage: ./import-logs.py RECIPIENT PASSPHRASE URL INDEX BATCH_SIZE FILE...")
        sys.exit(1)
    # recipient currently unused
    gpg_passphrase = sys.argv[2]
    es_host = sys.argv[3]
    es_index_name = sys.argv[4]
    try:
        es_batch_size = int(sys.argv[5])
        parallelism = int(sys.argv[6])
    except:
        logging.error("Required argument BATCH_SIZE not provided.")
        sys.exit(1)

    p_engine = Parallel(n_jobs=parallelism)
    ingester = ingest_path(gpg_passphrase, es_host, es_index_name, es_batch_size)

    p_engine(delayed(ingester)(idx, file_path) for idx, file_path in enumerate(sys.argv[7:]))
