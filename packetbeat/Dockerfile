FROM docker.elastic.co/beats/packetbeat-oss:7.8.1
COPY packetbeat.yml /usr/share/packetbeat/packetbeat.yml
USER root
RUN chown packetbeat:packetbeat /usr/share/packetbeat/packetbeat.yml
USER packetbeat
