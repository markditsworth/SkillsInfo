#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 22:49:38 2020

@author: markd
"""

import elasticsearch
import argparse

def parseArgs():
    parser = argparse.ArgumentParser(description='Use LinkedIn')
    parser.add_argument('--index', type=str, help="Name of index to create template for")
    
    args = parser.parse_args()
    return args.index

def main():
    index = parseArgs()
    index_file = "{}.json".format(index)
    with open(index_file, 'r') as fObj:
        body = fObj.read()
    template_name = "{}_template".format(index)
    es = elasticsearch.Elasticsearch(hosts=['localhost:9200'])
    es.indices.put_template(template_name, body)
    print("{} template applied.".format(index))