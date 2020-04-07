#!/bin/bash
index=$1
curl -X PUT "localhost:9200/_template/${index}_template?pretty" -H 'Content-Type: application/json' -d @${index}_template.json

echo "${index} template applied"
