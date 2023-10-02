# TFBSDB2 - New Transcription Factor Binding Site Database

## Description

For this update on tfbsdb we decided to migrate the application
from from Django to an API + Javascript frontend based web application.

## Update solr

curl http://localhost:8983/solr/tfbsdb2/update -H "Content-Type: text/xml" --data-binary @tfbsdb2_solr.xml

