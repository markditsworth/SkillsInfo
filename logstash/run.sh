#!/bin/bash
topic=$1
# template out pipeline file
sed "s/TOPIC/${topic}/g" pipeline_template.conf > pipeline_${topic}.conf

# spin up logstash container with new config file
docker run -it --name logstash_${topic} --network kafka-network -v $(pwd)/logstash.yml:/usr/share/logstash/config/logstash.yml -v $(pwd)/pipeline_${topic}.conf:/usr/share/logstash/pipeline/logstash.conf logstash
