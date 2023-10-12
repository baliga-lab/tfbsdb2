# Utilities

## export2solr.py

### Export

./export2solr.py > document.xml

### Post to Solr

bin/post -c tfbsdb2 document.xml


### Delete existing documents

curl -X POST -H 'Content-Type: application/json' --data-binary '{"delete":{"query":"*:*" }}' http://localhost:8983/solr/tfbsdb2/update?commit=true
