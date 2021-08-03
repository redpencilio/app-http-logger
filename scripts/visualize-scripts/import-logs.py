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

# utils
def strip_newlines(file):
    return list(line.rstrip('\n') for line in file)

def batch_iterator(itor, batch_size):
    line_index = 0
    i_end = batch_size - 1
    while True:
        batches = []
        i = -1
        try:
            while i < i_end:
                it = next(itor)
                batches.append(it)
                # increment after next: keep track of i when iterator has advanced
                i = i + 1
        except StopIteration:
            return
        finally:
            is_present = i >= 0
            if is_present:
                # create batch result
                yield (batches, (line_index, line_index + i))

        line_index = line_index + batch_size

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

def es_ingest_file(file_path, es_host, es_index_name, batch_size):
    with open(file_path, "rt") as file:
        # Streaming multiple GB's to the ES "/_bulk" endpoint in a single request causes memory issues in ES
        # Making one request per log-line on the other hand seems slow.
        file_itor = batch_iterator(file, batch_size)

        for (lines, indices) in file_itor:
            es_bulk_command = generate_bulk_index_command(es_index_name, lines)
            headers = { 'content-type' : 'application/json' }
            response = requests.post("{}/_bulk".format(es_host), data=es_bulk_command, headers=headers)

            if response.status_code == 429: # Too Many Requests
                logging.error("Response status: 429 - Too Many Requests. Try to lower the batch size or increase Java's available memory.", file_path, indices)
            
            response.raise_for_status()

def generate_bulk_index_command(es_index_name, lines):
    commands = []
    for line_str in lines:
        # line_str includes new line characters, like elastic search expects
        command = es_command_template.substitute(index_name=es_index_name, payload=line_str)
        commands.append(command)

    commands_str = "".join(commands).encode('utf-8')
    return commands_str

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
    except:
        logging.error("Required argument BATCH_SIZE not provided.")
        sys.exit(1)

    for file_path in sys.argv[6:]:
        if os.path.isfile(file_path):
            if os.path.splitext(file_path) != ".json":
                logging.info("File '{}' needs preprocessing before being able to ingest in ES".format(file_path))
                ingest_path = preprocess_file(file_path, UNENCRYPTED_LOGS_FOLDER, gpg_passphrase)
            else:
                ingest_path = file_path

            logging.info("Ingesting file '{}' into ES".format(ingest_path))

            import time
            logging.info("Start ingestion: size {}".format(es_batch_size))
            start_time = time.time()
            es_ingest_file(ingest_path, es_host, es_index_name, es_batch_size)
            duration = time.time() - start_time
            logging.info("End ingestion  : time {}s".format(duration))

            logging.info("Succesfully ingested file: {}".format(ingest_path))
        else:
            logging.error("'{}' is not a file. Skipping".format(file_path))
