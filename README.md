# app-http-logger
Provide out-of-the-box automatic logging of your running docker containers, and make the data available on ElasticSearch + Kibana for further analysis and visualization.

## Usage
app-http-logger is structured as three docker-compose files:
* `docker-compose.yml`: provides common base functionality: services to capture HTTP traffic and docker stats for every container; logstash services to handle captured logs; database infrastructure.
* `docker-compose.encrypt.yml`: provides a Logstash pipeline that writes HTTP logs and stats to a file, and an encryption service that will periodically encrypt the written HTTP logs.
* `docker-compose.live.yml`: provides a Logstash pipeline that pushes HTTP logs and stats directly to Elasticsearch for indexing and visualization.
* `docker-compose.visualize.yml`: provides an ElasticSearch and Kibana container for indexing and visualization.

**Only containers with a label called `logging` (with any value) will be monitored**. Do not forget to set this label.

`docker-compose.encrypt.yml` and `docker-compose.live.yml` can at present not be used together, as they each create a separate Logstash pipeline that tries to listen on the same port for Packetbeat events.

### Logging traffic and directly visualizing it
This is the default mode of this project. To start logging containers, add the `logging` label to the containers you want to monitor.

Start the app-http-logger by running:
``` sh
docker-compose up -d
```

Logs will be visible in Kibana at `http://localhost:5601`. For a basic setup, add the index patterns `http-log*` and `stats*` and click on 'discover'.

### Logging traffic to (encrypted) files
In this mode, data is captured and written to files. HTTP logs get encrypted, stats remain unencrypted. Visualization is not running live on the data.

Update the `.env` file to use the following docker-compose files:
```
COMPOSE_FILE=docker-compose.yml:docker-compose.encrypt.yml
```

Make sure you have a public GPG key available in the `./keys` directory and configure the correct recipient (key id) in the `docker-compose.encrypt.yml` file. You can find the commands to generate a GPG key in [the README of the file-encryption-service](https://github.com/redpencilio/file-encryption-service).

Add the `logging` label to the containers you want to monitor.

Start the app-http-logger by running:
``` sh
docker-compose up -d
```

Plain text logs will be stored in `./data/logs`. Encrypted logs will be stored in the `./data/encrypted` directory.

### Visualizing (encrypted) logs from files
In this mode, only the services for visualization are started. Scripts are provided to import encrypted log files and unencrypted stats files in Elasticsearch. The stack doesn't need to run on the same server where the data is captured.

Update the `.env` file to use the following docker-compose files:
```
COMPOSE_FILE=docker-compose.visualize.yml
```

First, start the visualization stack:
``` sh
docker-compose up -d
```

Put the private GPG key `gpg.key` in `./keys`. This key will be used for decryption.

Put the encrypted logs files in `./data/encrypted/http`

Execute the following mu-script to import the encrypted logs files with the correct recipient (key id) for the GPG key:
``` sh
mu script visualize-scripts http $RECIPIENT
```

Put the unencrypted stats files in `./data/logs/stats`

Execute the following mu-script to import the stats files:
``` sh
mu script visualize-scripts stats
```

Logs will be visible in Kibana at `http://localhost:5601`. Add the index patterns `http-log*` and `stats*` and click on 'discover'.

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
#### capture
* `PACKETBEAT_LISTEN_PORTS` determines the ports on which traffic is logged.
* `PACKETBEAT_MAX_MESSAGE_SIZE` determines the maximum size of a message before its content is no longer logged.
* `CAPTURE_SYNC_INTERVAL` determines the interval in milliseconds between full syncs of monitor state from the database.
* `MONITOR_IMAGE` is the name of the image for monitor containers. Note that this image is *always pulled* and thus **must** be a remote image.

#### stats
* `QUERY_INTERVAL` Interval (in ms) by which the service should fetch new stats.


#### monitor
* `MONITOR_SYNC_INTERVAL` is the interval in milliseconds between syncs of the docker state to the database and sending of deltas (if any).

### docker-compose.encrypt.yml
#### logstash
* `LOGFILE_FORMAT_STRING` determines the name of the generated log files. `%{+YYYY-MM-dd}` is a time format string.

#### encrypt
* `ENCRYPT_RECIPIENT` is the e-mail address of the encryption key.
* `ENCRYPT_AFTER_MINUTES` determines how many minutes a file must be unmodified before it will be encrypted.
* `ENCRYPT_INTERVAL` determines how often the encrypt script runs.
* `ENCRYPT_GLOB` determines which files are encrypted using a standard shell glob.

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

## Components

* [docker-monitor-service](https://github.com/redpencilio/docker-monitor-service/): keeps track of running containers in the database.

* [docker-network-capture-service](https://github.com/redpencilio/docker-network-capture-service/): spawns packetbeat containers to monitor other containers.

* [docker-stats-service](https://github.com/redpencilio/docker-stats-service): fetches Docker stats and dumps them into logstash.

* [file-encryption-service](https://github.com/redpencilio/file-encryption-service/): encrypts logfiles.

* [http-logger-packetbeat-service](https://github.com/redpencilio/http-logger-packetbeat-service/): spawned by network capture service, monitors the traffic of the attached container.

* [elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html): search engine/database.

* [kibana](https://www.elastic.co/guide/en/kibana/current/index.html): dashboard .

* [logstash](https://www.elastic.co/guide/en/logstash/current/index.html): log processing.

* [packetbeat](https://www.elastic.co/guide/en/beats/packetbeat/current/index.html): network monitoring.

* [mu-authorization](https://github.com/mu-semtech/delta-notifier): abstraction layer for the database, create delta's from database state changes.

* [delta-notifier](https://github.com/mu-semtech/delta-notifier): notify network capture service of changes in docker state.
 
