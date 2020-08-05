# app-http-logger
Provide out-of-the-box automatic logging of your running docker containers, and make the data available on ElasticSearch + Kibana for further analysis and visualization.

## Usage 
app-http-logger is structured as three docker-compose files:
* `docker-compose.logging.yml`: provides common base functionality: services to attach a Packetbeat monitor to every container and a Logstash container to send the logs to.
* `docker-compose.logging.visualize.yml`: provides an ElasticSearch and Kibana container, and a Logstash pipeline that will push logs to Elasticsearch.
* `docker-compose.logging.encrypt.yml`: provides a Logstash pipeline that writes logs to a file, and an encryption service that will periodically encrypt the written logs.
* `docker-compose.database.yml`: provides a Virtuoso database to store information about running Docker containers and network monitors.

**Only containers with a label called `logging` (with any value) will be monitored**. Do not forget to set this label.

`docker-compose.logging.visualize.yml` and `docker-compose.logging.encrypt.yml` can at present not be used together, as they each create a separate pipeline that tries to listen on port 5044 for Packetbeat events.

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
docker-compose -f docker-compose.database.yml -f docker-compose.logging.yml -f docker-compose.logging.encrypt.yml up -d
```

Encrypted logs will be stored in the `./encrypted` directory.

### Visualizing encrypted logs
To visualize encrypted logs, first decrypt the encrypted logs of interest:
```
for file in encrypted/*.json.gpg ; do
    gpg --decrypt --recipient $recipient --trust-model always --passphrase-file $gpg_key_pwd -o "encrypted/$(basename $file ".gpg")" $file
done
```

Next, start the visualization stack (without a base project):
```
docker-compose up -d
```
Now you can upload the decrypted JSON files to ElasticSearch:
```
./scripts/visualize-audit.py http://localhost:9200 audit encrypted/*.json
```
This will make the decrypted files available in the "audit" index. Now go to http://localhost:5601, add the "audit" index and you can search it.

### Using the project's triplestore
If the project you wish to monitor has its own Virtuoso database, you can also use that database instead of using a separate one. Simply add the docker-compose files of this project to your project, and make sure the Virtuoso database is available with the hostname `database`.

For visualization:
```
docker-compose -f $YOUR_COMPOSE_FILE -f docker-compose.logging.yml -f docker-compose.logging.visualize.yml up -d
```

For encryption:
```
docker-compose -f $YOUR_COMPOSE_FILE -f docker-compose.logging.yml -f docker-compose.logging.encrypt.yml up -d
```

## Components

* [docker-monitor-service](https://github.com/redpencilio/docker-monitor-service/): keeps track of running containers in the database

* [docker-network-capture-service](https://github.com/redpencilio/docker-network-capture-service/): captures network traffic of docker containers as listed in the database. Optionally filters on a docker label.

* [file-encryption-service](https://github.com/redpencilio/file-encryption-service/): encrypts files

* [http-logger-packetbeat-service](https://github.com/redpencilio/http-logger-packetbeat-service/): spawned by network capture service, monitors the traffic of the attached container.

* [elasticsearch](https://www.docker.elastic.co/): search engine/database

* [kibana](https://www.docker.elastic.co/): dashboard 

* [logstash](https://www.docker.elastic.co): log processing

* [packetbeat](https://www.docker.elastic.co): network monitoring
 
