#!/bin/bash

echo -n "Building Kafka and Zookeeper container..."
cd ./kafka
./init.sh
echo "     Done."
echo

echo -n "Building Elasticsearch container..."
cd ../elasticsearch
./init.sh
sleep 5
echo "     Done."
echo

echo -n "Building Kibana container..."
cd ../kibana
./init.sh
echo "     Done."
echo

echo -n "Building Logstash container..."
cd ../logstash
./init.sh
echo "     Done."
echo "Ready for tweets!"
