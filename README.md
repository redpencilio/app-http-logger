# app-http-logger
Provide out-of-the-box automatic logging of your running docker containers, and make the data available on ElasticSearch + Kibana for further analysis and visualization.

## Setup

This application depends on a `packetbeat-local` image available in the local Docker daemon. This is a simple open source packetbeat image with a custom configuration file. Build it with:

```
docker build -t packetbeat-local packetbeat/
```

## Usage 
app-http-logger is structured as three docker-compose files:
* `docker-compose.logging.yml`: provides common base functionality: services to attach a Packetbeat monitor to every container and a Logstash container to send the logs to.
* `docker-compose.logging.visualize.yml`: provides an ElasticSearch and Kibana container, and a Logstash pipeline that will push logs to Elasticsearch.
* `docker-compose.logging.encrypt.yml`: provides a Logstash pipeline that writes logs to a file, and an encryption service that will periodically encrypt the written logs.

This application is intended to **extend an existing docker-compose project** with logging functionality. `docker-compose.logging.yml` assumes that the original project has a Virtuoso triplestore available as a service called `database`. `docker-compose.logging.yml` should then in turn be extended by either `docker-compose.logging.visualize.yml` or `docker-compose.logging.encrypt.yml`.

**Only containers with a label called `logging` (with any value) will be monitored**. Do not forget to set this label.

`docker-compose.logging.visualize.yml` and `docker-compose.logging.encrypt.yml` can at present not be used together, as they each create a separate pipeline that tries to connect to port 5044 to read Packetbeat events.

### Logging traffic and visualizing it
Run the following command to attach logging and visualization to your docker-compose project:
```
docker-compose -f $YOUR_COMPOSE_FILE -f docker-compose.logging.yml -f docker.compose.logging.visualize.yml up -d
```

Requests will be visible on `http://localhost:5601` in Kibana. For a basic setup, add the index `http*` and click on 'discover'.

### Logging traffic and encrypting it

Make sure you have a public GPG key available in the `./keys` folder and configure the correct recipient in the `docker-compose.encrypt.yml` file.

Then run the following command to attach logging and visualization to your docker-compose project:
```
docker-compose -f $YOUR_COMPOSE_FILE -f docker-compose.logging.yml -f docker.compose.logging.encrypt.yml up -d
```

### Using a separate triplestore
In case the service you wish to monitor does not have a Virtuoso triplestore or you wish to separate the triplestores, you can include the `docker-compose.database.yml` file to start a separate database with service name `database`.

### Visualizing encrypted logs
To visualize encrypted logs from an application, first decrypt the encrypted files of interest:
```
for file in audit/*.json.gpg ; do
    mkdir -p "$target_dir/`dirname $file`"
    gpg --decrypt --recipient $recipient --trust-model always --passphrase-file $gpg_key_pwd -o "$target_dir/`dirname $file`/`basename $file ".gpg"`" $file
done
```

Next, start the visualisation stack (without a base project)
```
docker-compose -f docker-compose.database.yml -f docker-compose.logging.yml -f docker.compose.logging.visualize.yml up -d
```
Now you can upload the decrypted JSON files to ElasticSearch:
```
curl -XPOST 'http://localhost:9200/audit/_doc' -d @lane.json
```
This will make the decrypted files available in the "audit" index. Now go to http://localhost:5601, add the "audit" index and you can search it.

## Components

* [docker-monitor-service](https://github.com/lblod/docker-monitor-service/): keeps track of running containers in the database

* [docker-network-capture-service](https://github.com/lblod/docker-network-capture-service/): captures network traffic of docker containers as listed in the database. Optionally filters on a docker label.

* [encryption-service](https://github.com/lblod/encryption-service/): encrypts files

* [elasticsearch](https://www.docker.elastic.co/): search engine/database

* [kibana](https://www.docker.elastic.co/): dashboard 

* [logstash](https://www.docker.elastic.co): log processing

* [packetbeat](https://www.docker.elastic.co): network monitoring

## Known issues
 * packetbeat containers are not removed when logger is stopped, a quick way to remove them is running `docker ps | grep packetbeat | awk '{ print $1 }' | xargs docker rm -f`
 * crashed packetbeat containers are not restarted
 
