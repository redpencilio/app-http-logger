#!/bin/env python3

import sys
import os.path
import logging
import tarfile
from string import Template
import requests
import gnupg

# when decrypting, ensure GPG_HOME_FOLDER exists
GPG_HOME_FOLDER = "/root/.gnupg"
UNENCRYPTED_LOGS_FOLDER = "/project/data/logs/http"

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
    filename = os.path.split(file_path)[1]
    extracted_filename = filename.replace('.tar.gz', '')
    dest_path = os.path.join(destination_folder, extracted_filename)
    if os.path.exists(dest_path):
        logging.info("An extracted version of '{}' already exists in '{}'. Skipping extraction ...".format(filename, destination_folder))
    else:
        logging.info("Starting extraction of {} ...".format(filename))
        with tarfile.open(source_path) as tar:
            tar.extract(extracted_filename, destination_folder)
    return dest_path

gpg_instance = None
def init_gpg():
    logging.info("Initializing Python gpg")
    return gnupg.GPG(gnupghome=GPG_HOME_FOLDER)

def decrypt_file(source_path, destination_folder, passphrase):
    global gpg_instance
    
    if gpg_instance is None:
        gpg_instance = init_gpg()
    
    filename = os.path.split(file_path)[1]
    unencrypted_filename = filename.replace('.json.gpg', '.json')
    output_path = os.path.join(destination_folder, unencrypted_filename)
    if os.path.exists(output_path):
        logging.info("An unencrypted version of '{}' already exists in '{}'. Skipping decryption ...".format(filename, destination_folder))
    else:
        logging.info("Starting decryption of {} ...".format(source_path))
        with open(source_path, "rb") as f:
            decryption_status = gpg_instance.decrypt_file(f, passphrase=passphrase, always_trust=True, output=output_path) # debug with `extra_args=["-v"]`
            if not decryption_status.ok:
                raise Exception("GPG Decryption failed: {}".format(decryption_status.status))
    return output_path

def es_ingest_file(file_path, es_host, es_index_name):
    with open(file_path, "rt") as file:
        # Streaming multiple GB's to the ES "/_bulk" endpoint in a single request causes memory issues in ES
        # Making one request per log-line on the other hand seems slow.
        for line in file:
            es_command = es_command_template.substitute(index_name=es_index_name, payload=line).encode('utf-8')
            headers = { 'content-type' : 'application/json' }
            response = requests.post("{}/_bulk".format(es_host), data=es_command, headers=headers)
            response.raise_for_status()

# https://www.elastic.co/guide/en/elasticsearch/reference/7.9/docs-bulk.html#docs-bulk-api-desc
es_command_template = Template("""
{ "index": { "_index": "$index_name" } }
$payload
""")

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # Args validation
    if len(sys.argv) < 6:
        logging.error("Usage: ./import-logs.py RECIPIENT PASSPHRASE URL INDEX FILE...")
        sys.exit(1)
    # recipient currently unused
    gpg_passphrase = sys.argv[2]
    es_host = sys.argv[3]
    es_index_name = sys.argv[4]

    for file_path in sys.argv[5:]:
        if os.path.isfile(file_path):
            if os.path.splitext(file_path) != ".json":
                logging.info("File '{}' needs preprocessing before being able to ingest in ES".format(file_path))
                ingest_path = preprocess_file(file_path, UNENCRYPTED_LOGS_FOLDER, gpg_passphrase)
            else:
                ingest_path = file_path

            logging.info("Ingesting file '{}' into ES".format(ingest_path))
            es_ingest_file(ingest_path, es_host, es_index_name)
            logging.info("Succesfully ingested file: {}".format(ingest_path))
        else:
            logging.error("'{}' is not a file. Skipping".format(file_path))
