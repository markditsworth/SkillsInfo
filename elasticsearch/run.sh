#!/bin/bash
docker run -d -p 9200:9200 -p 9300:9300 --network kafka-network -e "discovery.type=single-node" -v $(pwd)/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml --name elasticsearch elasticsearch
