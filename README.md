# app-http-logger
Provide out-of-the-box automatic logging of your running docker containers, and make the data available on ElasticSearch + Kibana for further analysis and visualization.

## Components

* docker-monitor-service: keeps track of running containers in the database

* docker-network-capture-service: captures network traffic of docker containers as listed in the database. Optionally filters on a docker label.

* mu-har-transformation-service: converts the captured pcap files to har (a json structure)

* encryption-service: encrypts files

* elasticsearch-loader: loads har files into elasticsearch

* elasticsearch

* kibana

## Usage 

* Run ```docker-compose up```.
* After some traffic has been logged, visit *http://localhost:5601*, and in Kibana specify the index "**hars***" to start visualizing your data.

## Exporting Dashboard accross ElasticSearch & Kibana instances.

Kibana offers the possibility to save & export visualizations separately or together in dashboards to later import them in different instances of the **ElasticSearch & Kibana** stack. It is sometimes useful to have a predefined set of visualizations to be applied to different data sets, as long as they comply with the structure and parameters they visualizations require.

Instructions on to export & import the dashboards can be found in the [official documentation](https://www.elastic.co/guide/en/kibana/current/managing-saved-objects.html). Several remarks are important to be mentioned:

  * In order to export a dashboard, you must export both the dashboard & each one of the individual visualizations that conform it, otherwise they won't work. Luckily there is a *Export all* button in Kibana.
  * Visualizations are exported in JSON format, and they describe the way data is visualized, but they don't include the data itself, they will be run each time on the available data in **ElasticSearch**.
  * Following the previous bullet point, visualizing dashboards can be applied to different datasets over time.
