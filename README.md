# app-http-logger
Provide out-of-the-box automatic logging of your running docker containers, and make the data available on ElasticSearch + Kibana for further analysis and visualization.

## Getting started
Add a `logging` label to all containers you want to monitor.

``` yaml
services:
  my-service:
    image: my/example:1.0.0
    labels:
      - "logging=true"
```

The stack can be started in different modes depending on the `docker-compose.*.yml` files that are taken into account. Some typical base scenarios are described below, but you can also combine them.

### Option 1: Logging traffic and directly visualizing it (development mode)
This is the default mode of this project. Logs are collected and immediately imported in the visualization stack. This is what you typically want to do during development. To start logging containers, add the `logging` label to the containers you want to monitor.

Ensure the `.env` file contains the following contents:
```
COMPOSE_FILE=docker-compose.yml:docker-compose.live.yml:docker-compose.visualize.yml
```

Start the app-http-logger by running:
``` sh
docker compose up -d
```

Logs will be visible in Kibana at `http://localhost:5601`. For a basic setup, add the index patterns `http-log*` and `stats*` and click on 'discover'.

_Note: the intermediate logs are not written to files. As a consequence in this setup no backups of the logs can be taken. This is probably not what you want in production._

### Option 2: Logging traffic to (encrypted) files
In this mode, data is captured and written to files. This is probably your prefered mode on production machines. HTTP logs get encrypted, stats remain unencrypted. Visualization is not running live on the data, but can be setup on any machine (see [option 3](#option-3-visualizing-encrypted-logs-from-files)).

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

Encrypted logs will be stored in the `./data/encrypted` directory. Compressed logs will be stored in `./data/compressed`. You probably want to backup these folders.

### Option 3: Visualizing (encrypted) logs from files
In this mode, only the services for visualization are started. Scripts are provided to import encrypted log files and compressed stats files in Elasticsearch. The visualization stack doesn't need to run on the same server where the data is captured. This is a typical scenario for viewing logs from the backups.

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

### Option 4: Logging traffic and sending it live to a remote visualization stack
In this mode, logs are captured on one host and sent live to a remote visualization stack for indexing and visualization. This means **two stacks will be running at the same time**: an **upstream** stack that collects the logs and sends them to the remote, and a **downstream** stack that receives the logs and visualizes them in Kibana. This is a typical scenario when the machine that captures the traffic is not the same machine that runs the visualization stack (e.g. capturing on a production host while visualizing on a separate, more powerful server).

Communication between the two stacks happens over HTTP(s) and is protected by a **shared secret**.
* On the **upstream** side it is configured through the `REMOTE_SECRET_KEY` environment variable on the `logstash` (and `stats-logstash`) service in `docker-compose.to-remote.yml`.
* On the **downstream** side it is configured through the `SECRET_KEY` environment variable on the `logstash` (and `stats-logstash`) service in `docker-compose.from-remote.yml`.

The upstream additionally needs to know where to send the logs. This is configured through the `REMOTE_HOST` environment variable, which must point to the URL of the downstream logstash endpoint.

#### Upstream stack (collecting and sending logs)

Update the `.env` file to use the following docker-compose files:
```
COMPOSE_FILE=docker-compose.yml:docker-compose.to-remote.yml
```

Edit `docker-compose.to-remote.yml` to configure the remote endpoint and the shared secret for both the HTTP and the stats logstash:
``` yaml
services:
  logstash:
    environment:
      REMOTE_HOST: "https://http-logs.example.com"
      REMOTE_SECRET_KEY: "your-shared-secret"
  stats-logstash:
    environment:
      REMOTE_HOST: "https://stats-logs.example.com"
      REMOTE_SECRET_KEY: "another-shared-secret"
```

Add the `logging` label to the containers you want to monitor.

Start the upstream app-http-logger by running:
``` sh
docker compose up -d
```

#### Downstream stack (receiving and visualizing logs)

Update the `.env` file to use the following docker-compose files:
```
COMPOSE_FILE=docker-compose.from-remote.yml:docker-compose.visualize.yml
```

Edit `docker-compose.from-remote.yml` to configure the shared secret. You should also configure the `logstash` and `stats-logstash` service to be available on the URL configured in the upstream stack. Logstash listens on port 8080.
``` yaml
services:
  logstash:
    environment:
      SECRET_KEY: "your-shared-secret"
  stats-logstash:
    environment:
      SECRET_KEY: "another-shared-secret"
```

_Start the downstream stack first_ so that it is ready to receive logs:
``` sh
docker compose up -d
```

Logs will be visible in Kibana of the downstream stack at `http://localhost:5601`. Add the index patterns `http-log*` and `stats*` and click on 'discover'.

## How-to guides
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

## Reference
### Operational modes
The stack can be started in different modes depending on the `docker-compose.*.yml` files that are taken into account. The different scenarios and their typical usage are described in the [Getting started guide](#getting-started).

The following docker-compose files are available.
* `docker-compose.yml`: provides common base functionality: services to capture HTTP traffic and docker stats for every container; logstash services to handle captured logs; database infrastructure.
* `docker-compose.encrypt.yml`: provides a Logstash pipeline that writes HTTP logs and stats to a file, and an encryption/compression service that will periodically encrypt/compress the written HTTP/stats logs.
* `docker-compose.live.yml`: provides a Logstash pipeline that pushes HTTP logs and stats directly to Elasticsearch for indexing and visualization.
* `docker-compose.to-remote.yml`: provides a Logstash pipeline that pushes HTTP logs and stats to a remote visualization stack.
* `docker-compose.from-remote.yml`: provides a Logstash pipeline that ingests HTTP logs and stats originating from a remote stack.
* `docker-compose.visualize.yml`: provides an ElasticSearch and Kibana container for indexing and visualization.


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
#### logstash | stats-logstash
* `LOGFILE_FORMAT_STRING` determines the name of the generated log files. `%{+YYYY-MM-dd}` is a time format string.

#### encrypt
* `ENCRYPT_RECIPIENT` is the e-mail address of the encryption key.
* Additional configuration is documented in the [README of the service](https://github.com/redpencilio/file-encryption-service)

### docker-compose.to-remote.yml
#### logstash | stats-logstash
* `REMOTE_HOST`: URL of the remote logstash to send logs to
* `REMOTE_SECRET_KEY`: Shared secret to send logs to a remote stack

### docker-compose.from-remote.yml
#### logstash | stats-logstash
* `SECRET_KEY`: Shared secret to receive logs from a remote stack

### docker-compose.visualize.yml
#### curator
* `LOG_RETENTION_DAYS`: Number of days to retain logs in Elasticsearch before they are automatically removed. Defaults to 3650 (10 years)."

### Components
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
* [mu-authorization](https://github.com/mu-semtech/sparql-parser): abstraction layer for the database, create delta's from database state changes.
* [delta-notifier](https://github.com/mu-semtech/delta-notifier): notify network capture service of changes in docker state.
