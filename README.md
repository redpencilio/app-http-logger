# app-http-logger
Provide out-of-the-box automatic logging of your running docker containers, and make the data available on ElasticSearch + Kibana for further analysis and visualization.

## Usage 
app-http-logger is structured as three docker-compose files:
* `docker-compose.yml`: provides common base functionality: services to attach a Packetbeat monitor to every container, Logstash to send logs to, and database infrastructure.
* `docker-compose.visualize.yml`: provides an ElasticSearch and Kibana container, and a Logstash pipeline that will push logs to Elasticsearch.
* `docker-compose.encrypt.yml`: provides a Logstash pipeline that writes logs to a file, and an encryption service that will periodically encrypt the written logs.

**Only containers with a label called `logging` (with any value) will be monitored**. Do not forget to set this label.

`docker-compose.visualize.yml` and `docker-compose.encrypt.yml` can at present not be used together, as they each create a separate Logstash pipeline that tries to listen on the same port for Packetbeat events.

### Logging traffic and visualizing it
This is the default mode of this project, so to start logging containers, simply run:
```
docker-compose up -d
```

Logs will be visible in Kibana at `http://localhost:5601`. For a basic setup, add the index `http-log*` and click on 'discover'.

### Logging traffic and encrypting it

Make sure you have a public GPG key available in the `./keys` directory and configure the correct recipient in the `docker-compose.encrypt.yml` file.

Then run the following command to attach logging and visualization to your docker-compose project:
```
docker-compose -f docker-compose.yml -f docker-compose.encrypt.yml up -d
```

Encrypted logs will be stored in the `./encrypted` directory.

### Visualizing encrypted logs
A script is provided that will automatically decrypt and upload encrypted logs to ElasticSearch.

First, start the visualization stack:
```
docker-compose up -d
```
Now you can upload the files to ElasticSearch as such:
```
./scripts/visualize-audit.py $RECIPIENT <(echo "your_passphrase_here") http://localhost:9200 audit encrypted/*
```
Where `$RECIPIENT` is the identity used to encrypt the files.

This will make the decrypted files available in the "audit" index. Now go to http://localhost:5601, add the "audit" index and you can search it.

## Components

* [docker-monitor-service](https://github.com/redpencilio/docker-monitor-service/): keeps track of running containers in the database.

* [docker-network-capture-service](https://github.com/redpencilio/docker-network-capture-service/): spawns packetbeat containers to monitor other containers.

* [file-encryption-service](https://github.com/redpencilio/file-encryption-service/): encrypts logfiles.

* [http-logger-packetbeat-service](https://github.com/redpencilio/http-logger-packetbeat-service/): spawned by network capture service, monitors the traffic of the attached container.

* [elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html): search engine/database.

* [kibana](https://www.elastic.co/guide/en/kibana/current/index.html): dashboard .

* [logstash](https://www.elastic.co/guide/en/logstash/current/index.html): log processing.

* [packetbeat](https://www.elastic.co/guide/en/beats/packetbeat/current/index.html): network monitoring.

* [mu-authorization](https://github.com/mu-semtech/delta-notifier): abstraction layer for the database, create delta's from database state changes.

* [delta-notifier](https://github.com/mu-semtech/delta-notifier): notify network capture service of changes in docker state.
 
