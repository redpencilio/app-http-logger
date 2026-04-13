if [ -z "${ELASTIC_PASSWORD}" ]; then
    echo "Set the ELASTIC_PASSWORD environment variable in the .env file";
    exit 1
elif [ -z "${KIBANA_PASSWORD}" ]; then
    echo "Set the KIBANA_PASSWORD environment variable in the .env file";
    exit 1
elif [ -z "${LOGSTASH_PASSWORD}" ]; then
    echo "Set the LOGSTASH_PASSWORD environment variable in the .env file";
    exit 1
elif [ -z "${ELASTIC_HOST}" ]; then
    echo "Set the ELASTIC_HOST environment variable in the .env file";
    exit 1
fi

CERTS_DIR=config/certs

if [ ! -f ${CERTS_DIR}/ca/ca.crt ]; then
    echo "Creating CA"
    bin/elasticsearch-certutil ca --silent --pem -out ${CERTS_DIR}/ca.zip
    unzip ${CERTS_DIR}/ca.zip -d ${CERTS_DIR}
    rm ${CERTS_DIR}/ca.zip
fi

INSTANCES_FILE=${CERTS_DIR}/instances.yml

if [ ! -f ${CERTS_DIR}/es/es.crt ]; then
    echo "Creating certs"
    if [[ "${ELASTIC_HOST}" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        EXTRA_HOST_IP=$ELASTIC_HOST
        EXTRA_HOST_DNS=""
    elif [ "${ELASTIC_HOST}" = "elasticsearch" ]; then
        # "elasticsearch" is always included, so no extra needed here
        EXTRA_HOST_IP=""
        EXTRA_HOST_DNS=""
    else
        EXTRA_HOST_IP=""
        EXTRA_HOST_DNS=$ELASTIC_HOST
    fi
    cat << EOF > ${INSTANCES_FILE}
instances:
  - name: es
    ip:
      - 127.0.0.1
EOF
    if [ -n "${EXTRA_HOST_IP}" ]; then
        echo "      - ${EXTRA_HOST_IP}" >> ${INSTANCES_FILE}
    fi
    cat << EOF >> ${INSTANCES_FILE}
    dns:
      - elasticsearch
      - localhost
EOF
    if [ -n "${EXTRA_HOST_DNS}" ]; then
        echo "      - ${EXTRA_HOST_DNS}" >> ${INSTANCES_FILE}
    fi
    bin/elasticsearch-certutil cert --silent --pem \
        -out ${CERTS_DIR}/certs.zip \
        --in ${INSTANCES_FILE} \
        --ca-cert ${CERTS_DIR}/ca/ca.crt \
        --ca-key ${CERTS_DIR}/ca/ca.key
    unzip ${CERTS_DIR}/certs.zip -d ${CERTS_DIR}
    rm ${CERTS_DIR}/certs.zip
    rm ${INSTANCES_FILE}
fi

echo "Setting file permissions"
chown -R root:root ${CERTS_DIR}
find ${CERTS_DIR} -type d -exec chmod 755 \{\} \;
find ${CERTS_DIR} -type f -exec chmod 640 \{\} \;
find ${CERTS_DIR} -type f -name "*.crt" -exec chmod 644 \{\} \;

echo "Waiting for Elasticsearch availability"
until curl -s --cacert ${CERTS_DIR}/ca/ca.crt https://elasticsearch:9200 | grep -q "missing authentication credentials"; do
    sleep 5
done
echo "Setting kibana_system password"
until curl -s -X POST \
    --cacert ${CERTS_DIR}/ca/ca.crt \
    -u "elastic:${ELASTIC_PASSWORD}" \
    -H "Content-Type: application/json" \
    https://elasticsearch:9200/_security/user/kibana_system/_password \
    -d "{\"password\":\"${KIBANA_PASSWORD}\"}" | grep -q "^{}"; do
    sleep 5
done
echo "Creating logstash_writer role"
until curl -s -X POST \
    --cacert ${CERTS_DIR}/ca/ca.crt \
    -u "elastic:${ELASTIC_PASSWORD}" \
    -H "Content-Type: application/json" \
    https://elasticsearch:9200/_security/role/logstash_writer \
    -d "{\"cluster\": [\"manage_index_templates\", \"monitor\"], \"indices\": [{ \"names\": [\"http-log-*\", \"stats-*\"], \"privileges\": [\"write\", \"create\", \"create_index\"]}]}" | grep -q "^{\"role\":{\"created\":true}}"; do
    sleep 5
done
echo "Creating logstash_internal user"
until curl -s -X POST \
    --cacert ${CERTS_DIR}/ca/ca.crt \
    -u "elastic:${ELASTIC_PASSWORD}" \
    -H "Content-Type: application/json" \
    https://elasticsearch:9200/_security/user/logstash_internal \
    -d "{\"password\": \"${LOGSTASH_PASSWORD}\", \"roles\": [\"logstash_writer\"], \"full_name\": \"Logstash Internal User\"}" | grep -q "^{\"created\":true}"; do
    sleep 5
done
echo "Setup complete!"
