# app-http-logger
Provide out-of-the-box automatic logging of your running docker containers, and make the data available on ElasticSearch + Kibana for further analysis and visualization.

## Usage
app-http-logger is structured as three docker-compose files:
* `docker-compose.yml`: provides common base functionality: services to capture HTTP traffic and docker stats for every container; logstash services to handle captured logs; database infrastructure.
* `docker-compose.encrypt.yml`: provides a Logstash pipeline that writes HTTP logs and stats to a file, and an encryption/compression service that will periodically encrypt/compress the written HTTP/stats logs.
* `docker-compose.live.yml`: provides a Logstash pipeline that pushes HTTP logs and stats directly to Elasticsearch for indexing and visualization.
* `docker-compose.visualize.yml`: provides an ElasticSearch and Kibana container for indexing and visualization, along with a security setup container that auto-generates TLS certificates.

**Only containers with a label called `logging` (with any value) will be monitored**. Do not forget to set this label.

The stack can be started in different modes depending on the `docker-compose.*.yml` files that are taken into account. The different options are described below.

### Option 1: Logging traffic and directly visualizing it
This is the default mode of this project. Logs are collected and immediately imported in the visualization stack. To start logging containers, add the `logging` label to the containers you want to monitor.

Ensure the `.env` file contains the following contents:
```
COMPOSE_FILE=docker-compose.yml:docker-compose.live.yml:docker-compose.visualize.yml
```

Start the app-http-logger by running:
``` sh
docker compose up -d
```

Logs will be visible in Kibana at `http://localhost:5601`. Log in with the `elastic` user and your `ELASTIC_PASSWORD`. For a basic setup, add the index patterns `http-log*` and `stats*` and click on 'discover'.

_Note: the intermediate logs are not written to files. As a consequence in this setup no backups of the logs can be taken. This is probably not what you want in production. To have both live visualization and backups of the logs use [Option 3: Logging traffic to (encrypted) files and directly visualizing it](#option-3-logging-traffic-to-encrypted-files-and-directly-visualizing-it) instead._

### Option 2: Logging traffic to (encrypted) files
In this mode, data is captured and written to files. This is probably your prefered mode on production machines. HTTP logs get encrypted, stats remain unencrypted. Visualization is not running live on the data, but can be setup on any machine (see option 3).

Update the `.env` file to use the following docker-compose files:
```
COMPOSE_FILE=docker-compose.yml:docker-compose.encrypt.yml
```

Make sure you have a public GPG key available in the `./keys` directory and configure the correct recipient (key id) in the `docker-compose.encrypt.yml` file. You can find the commands to generate a GPG key in [the README of the file-encryption-service](https://github.com/redpencilio/file-encryption-service).

Add the `logging` label to the containers you want to monitor.

Start the app-http-logger by running:
``` sh
docker compose up -d
```

Plain text logs will be stored in `./data/logs`. Encrypted logs will be stored in the `./data/encrypted` directory. Compressed logs will be stored in `./data/compressed`.

### Option 3: Logging traffic to (encrypted) files and directly visualizing it

This mode is a combination of [Option 1: Logging traffic and directly visualizing it](#option-1-logging-traffic-and-directly-visualizing-it) and [Option 2: Logging traffic to (encrypted) files](#option-2-logging-traffic-to-encrypted-files). It allows you to directly visualize logs as in option 1, but also log traffic to (encrypted) files as in option 2. This is useful for environments where you want to have both live visualization and backups of the logs.

Ensure the `.env` file contains the following contents:
```
COMPOSE_FILE=docker-compose.yml:docker-compose.live.yml:docker-compose.visualize.yml:docker-compose.encrypt.yml
```

Check that the `encrypt` service is configured as specified in [Logging traffic to (encrypted) files](#option-2-logging-traffic-to-encrypted-files).

Start the app-http-logger by running:
``` sh
docker compose up -d
```

For information on how to visualize the logs see [Logging traffic and directly visualizing it](#option-1-logging-traffic-and-directly-visualizing-it). For information on where to find the logs see [Logging traffic to (encrypted) files](#option-2-logging-traffic-to-encrypted-files).

### Option 4: Visualizing (encrypted) logs from files
In this mode, only the services for visualization are started. Scripts are provided to import encrypted log files and compressed stats files in Elasticsearch. The visualization stack doesn't need to run on the same server where the data is captured.

Update the `.env` file to use the following docker-compose files:
```
COMPOSE_FILE=docker-compose.visualize.yml
```

First, start the visualization stack:
``` sh
docker compose up -d
```

Put the private GPG key `gpg.key` in `./keys`. This key will be used for decryption.

Put the encrypted logs files in `./data/encrypted/http`

Execute the following mu-script to import the encrypted logs files with the correct recipient (key id) for the GPG key:
``` sh
RECIPIENT=johnny.bravo@example.com
mu script visualize-scripts http $RECIPIENT
```

Put the compressed stats files in `./data/compressed/stats`

Execute the following mu-script to import the stats files:
``` sh
mu script visualize-scripts stats
```

Logs will be visible in Kibana at `http://localhost:5601`. Add the index patterns `http-log*` and `stats*` and click on 'discover'.

_Note: the visualization scripts don't keep track which files have already been imported. Hence, running the script twice on the same set of files will result in duplicate entries._

## Option 5: Remote visualization
The stack can be split across two hosts:
- **Application host**: This host runs the application and forwards the logs to the visualization host.
- **Visualization host**: This host runs the visualization stack and receives the logs from the application host.

### Setup
#### Step 1 - Visualization host configuration
On the visualization host, create the `.env` file base on `.env.example`. Make sure the following variables are configured:
- `COMPOSE_FILE` is `docker-compose.yml:docker-compose.visualize.yml`
- `ELASTIC_HOST` is the visualization host's public IP or domain name
- All passwords have been set and are at least 6 characters long, alphanumeric, and don't contain special characters

Start the visualization part of app-http-logger by running:
```sh
docker compose up -d
```

The first time you start the stack you need to wait until the setup container has finished successfully. This can take a few minutes. You can check the status of the setup container by running:
```sh
docker compose logs -f setup
```

It should output `Setup complete!` when finished. During this process certificates and users are generated and configured.

#### Step 2 - Application host configuration
This step requires the certificates autogenerated in Step 1, so make sure the setup container on the visualization host has finished successfully before continuing.
Copy the CA cert from the visualization host to the application host. If you have access to both hosts from your local machine, you can do this with:
```sh
scp -3 visualization-host:/data/app-http-logger/config/certs/ca/ca.crt application-host:/data/app-http-logger/config/certs/ca/ca.crt
```

Create the `.env` file on the application host based on `.env.example`. Make sure the following variables are configured:
- `COMPOSE_FILE` is `docker-compose.yml:docker-compose.live.yml`
- `ELASTIC_HOST` is the visualization host's public IP or domain name, this is the same as on the visualization host
- `LOGSTASH_PASSWORD` is the same as on the visualization host

If you want to log traffic to (encrypted) files on the application host as well, add `docker-compose.encrypt.yml` to the `COMPOSE_FILE` variable:
```sh
COMPOSE_FILE=docker-compose.yml:docker-compose.live.yml:docker-compose.encrypt.yml
```

Start the log forwarding part of app-http-logger by running:
```sh
docker compose up -d
```

### Importing and exporting dashboards

If you create dashboards to visualize logs, you can export these to JSON files and load them again later. The Kibana service must be started and ready to use these scripts.

To export all of your dashboards, use:
``` sh
mu script kibana dashboard-export
```
This will create one JSON file per dashboard in the "dashboards" directory.

To import dashboards, put the JSON files as created by the export script in the "dashboards" directory and run:
``` sh
mu script kibana dashboard-import
```

## Configuration
### docker-compose.yml
#### monitor
* `MONITOR_SYNC_INTERVAL`: default: `10000` is the interval in milliseconds between syncs of the docker daemon container state to the database resulting in deltas being sent (if any update to the containers on the system occurred).

#### capture
* `PACKETBEAT_LISTEN_PORTS` determines the ports on which traffic is logged.
* `PACKETBEAT_MAX_MESSAGE_SIZE` determines the maximum size of a message before its content is no longer logged.
* `CAPTURE_SYNC_INTERVAL` determines the interval in milliseconds between full syncs of monitor state from the database.
* `MONITOR_IMAGE` is the name of the image for monitor containers. Note that this image is *always pulled* and thus **must** be a remote image.

#### stats
* `QUERY_INTERVAL` Interval (in ms) by which the service should fetch new stats.

### docker-compose.encrypt.yml
#### logstash
* `LOGFILE_FORMAT_STRING` determines the name of the generated log files. `%{+YYYY-MM-dd}` is a time format string.

#### encrypt
* `ENCRYPT_RECIPIENT` is the e-mail address of the encryption key.
* Additional configuration is documented in the [README of the service](https://github.com/redpencilio/file-encryption-service)

## Troubleshooting
### Elasticsearch and/or Virtuoso fail to start
This may be caused by a permissions problem in the mounted `data` directories, especially if Docker is running in a separate user namespace.

A solution is to set the permissions for these directories to 777:
``` sh
chmod -R a+rwx data
```
But note that this makes the data in these directories **readable to anybody with any access to your system**.

### Certain fields cannot be selected for aggregation or filtering
Kibana determines which fields are available in an index when it first creates that index. If documents featuring new fields are added, those will not be available for aggregation or filtering. To fix this, go to Settings -> Index Patterns -> select your index -> click on the "refresh" button. This should add any new fields to the index.

### Docker's rootless mode

Although not explicitly supported, app-http-logger can work on rootless docker with the following changes. app-http-logger communicates with the host's docker daemon through the `/var/run/docker.sock` volume which is mapped to the host's `/var/run/docker.sock` file by default. However, if you use docker's [rootless mode](https://docs.docker.com/engine/security/rootless/) this file doesn't exist and it lives at [`$XDG_RUNTIME_DIR/docker.sock` by default](https://docs.docker.com/engine/security/rootless/#daemon) instead. Update the volumes in the docker-compose.yml file to ensure communication with the docker daemon works as expected: 

```diff
    volumes:
-       - /var/run/docker.sock:/var/run/docker.sock
+       - /run/user/1000/docker.sock:/var/run/docker.sock
```

## Components

* [docker-monitor-service](https://github.com/redpencilio/docker-monitor-service/): keeps track of running containers in the database.

* [docker-network-capture-service](https://github.com/redpencilio/docker-network-capture-service/): spawns packetbeat containers to monitor other containers.

* [docker-stats-service](https://github.com/redpencilio/docker-stats-service): fetches Docker stats and dumps them into logstash.

* [file-encryption-service](https://github.com/redpencilio/file-encryption-service/): encrypts logfiles.

* [file-compression-service](https://github.com/redpencilio/file-compression-service/): compresses logfiles.

* [http-logger-packetbeat-service](https://github.com/redpencilio/http-logger-packetbeat-service/): spawned by network capture service, monitors the traffic of the attached container.

* [elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html): search engine/database.

* [kibana](https://www.elastic.co/guide/en/kibana/current/index.html): dashboard .

* [logstash](https://www.elastic.co/guide/en/logstash/current/index.html): log processing.

* [packetbeat](https://www.elastic.co/guide/en/beats/packetbeat/current/index.html): network monitoring.

* [mu-authorization](https://github.com/mu-semtech/delta-notifier): abstraction layer for the database, create delta's from database state changes.

* [delta-notifier](https://github.com/mu-semtech/delta-notifier): notify network capture service of changes in docker state.
