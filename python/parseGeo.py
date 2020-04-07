#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 21:17:54 2020

@author: markd

To Do:
--- Kafka Consumer
-/- Add geo_point field (https://www.elastic.co/guide/en/elasticsearch/reference/7.6/geo-point.html)
-/- Kafka Producer
"""

import secret
import json
import requests
import argparse

from kafka import KafkaProducer
from kafka import KafkaConsumer

def argParse():
    parser = argparse.ArgumentParser(description='Parse LinkedIn Skills Data')
    parser.add_argument('--topic', type=str,
                        help='topic to read from')
    parser.add_argument('--host', type=str, default="localhost", help="Kafka hostname")
    parser.add_argument('--port', type=int, default=29092, help="Kafka port number")
    parser.add_argument('--from-file', action='store_true', help="Read from file instead of kafka")
    args = parser.parse_args()
    raw_topic = args.topic
    parsed_topic = 'parsed-' + raw_topic
    return args.topic, parsed_topic, args.host, args.port, args.from_file

def getLatLong(location, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": location, "key": api_key}
    r = requests.get(url, params=params)
    info = json.loads(r.text)
    lat = info['results'][0]['geometry']['location']['lat']
    long= info['results'][0]['geometry']['location']['lng']
    return lat, long

def enrichLocation(info, api_key):
    enriched_info = info.copy()
    if info['location'] != 'Other':
        lat, long = getLatLong(info['location'],api_key)
        enriched_info['coordinates'] = {'lat': lat, 'lon': long}
    else:
        enriched_info['coordinates'] = {'lat': 0, 'lon': 0}
    return enriched_info

def serialize(dictionary):
        return json.dumps(dictionary).encode('ascii')
    
if __name__ == '__main__':
    topic, parsed_topic, host, port, from_file = argParse()
    producer = KafkaProducer(bootstrap_servers=["{}:{}".format(host,port)])
    if not from_file:
        consumer = KafkaConsumer(topic, group_id='{}-consumer-group-1'.format(topic),
                                      bootstrap_servers=["{}:{}".format(host,port)],
                                      auto_offset_reset='earliest',
                                      value_deserializer=lambda m: json.loads(m.decode('ascii')))
        for m in consumer:
            message= m.value
            print(message)
            enriched_message = enrichLocation(message, secret.geocoder_api_key)
            producer.send(parsed_topic, serialize(enriched_message))
            
    else:
        path = "{}_output.json".format(topic)    
        with open(path,'r') as fObj:
            content = fObj.readlines()
        
        for x in content:
            data = json.loads(x)
            print(data['location'])
            enriched_data = enrichLocation(data, secret.geocoder_api_key)
            # send to kafka
            producer.send(parsed_topic, serialize(enriched_data))
        producer.flush()
        print("Messages from {} sent.".format(path))
