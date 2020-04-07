#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 21:17:54 2020

@author: markd

"""

import secret
import json
import requests
import argparse

from kafka import KafkaProducer
from kafka import KafkaConsumer

def argParse():
    parser = argparse.ArgumentParser(description='Parse LinkedIn Skills Data')
    parser.add_argument('--topic', type=str, help='topic to read from')
    parser.add_argument('--host', type=str, default="localhost", help="Kafka hostname")
    parser.add_argument('--port', type=int, default=29092, help="Kafka port number")
    parser.add_argument('--from-file', action='store_true', help="Read from file instead of kafka")
    args = parser.parse_args()
    raw_topic = args.topic
    parsed_topic = 'parsed-' + raw_topic
    return args.topic, parsed_topic, args.host, args.port, args.from_file

'''
Queries Google Geocode API to convert addresses to latitude/longitude
  Requires the api_key from secret.py
'''
def getLatLong(location, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": location, "key": api_key}
    r = requests.get(url, params=params)
    info = json.loads(r.text)
    lat = info['results'][0]['geometry']['location']['lat']
    long= info['results'][0]['geometry']['location']['lng']
    return lat, long

'''
Accepts info dictionary, performs the conversion of address to coordinates, and
  returns new dictionary with the coordinates field, formatted for elasticsearch
  geo_point type. If not available, default coordinates to 0,0
'''
def enrichLocation(info, api_key):
    enriched_info = info.copy()
    if info['location'] != 'Other':
        lat, long = getLatLong(info['location'],api_key)
        enriched_info['coordinates'] = {'lat': lat, 'lon': long} # formatted for ES geo_point data type
    
    # if LinkedIn user put "Other" for location, default to (0,0)
    else:
        enriched_info['coordinates'] = {'lat': 0, 'lon': 0}
    return enriched_info

'''
Serializes dictionary for publishing to kafka
'''
def serialize(dictionary):
        return json.dumps(dictionary).encode('ascii')
    
if __name__ == '__main__':
    topic, parsed_topic, host, port, from_file = argParse()
    
    # Setup Kafka producer
    producer = KafkaProducer(bootstrap_servers=["{}:{}".format(host,port)])
    if not from_file:
        # Setup Kafka consumer
        consumer = KafkaConsumer(topic, group_id='{}-consumer-group-1'.format(topic),
                                      bootstrap_servers=["{}:{}".format(host,port)],
                                      auto_offset_reset='earliest',
                                      value_deserializer=lambda m: json.loads(m.decode('ascii')))
        
        # for each message in the kafka topic
        for m in consumer:
            message= m.value
            print(message)
            
            # add coordinates field to message
            enriched_message = enrichLocation(message, secret.geocoder_api_key)
            # send to parsed- topic
            producer.send(parsed_topic, serialize(enriched_message))
    
    # if reading from file instead of kafka
    else:
        # get file name
        path = "{}_output.json".format(topic)  
        
        # read contents of file, splitting by line
        with open(path,'r') as fObj:
            content = fObj.readlines()
        
        # for each document
        for x in content:
            # convert to dict
            data = json.loads(x)
            print(data['location'])
            # add coordinates field
            enriched_data = enrichLocation(data, secret.geocoder_api_key)
            # send to kafka
            producer.send(parsed_topic, serialize(enriched_data))
        
        # flush messages to ensure they are written to kafka
        producer.flush()
        print("Messages from {} sent.".format(path))
