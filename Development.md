# Developing TFBSDB2

## General Thoughts

TFBSDB2 is developed using services deployed in Docker containers

  * MySQL server
  * API server
  * Webapp server


## Docker setup

### Create application network

https://earthly.dev/blog/docker-mysql/#using-container-networks

```
$ docker network create bridge
```

We use a dedicated Docker network to stitch together our containers

## MySQL

### Run the database container

Hostname mysql

```
$ docker run --name mysql -e MYSQL_ROOT_PASSWORD=tfbsdb2 --network bridge -d mysql:5.7
```
  or

```
$ docker run --name mysql -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=tfbsdb2 --network bridge --restart unless-stopped mysql:latest
```

We can see the container by

```
$ docker network inspect bridge
```

### Populate database

```
$ docker exec -i <container-id> sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < schema.sql
```

### Run the mysql client

```
$ docker exec -it <container-id> mysql -uroot -p
```

### Troubleshooting

If we get errors like

```
ERROR 1045 (28000): Plugin caching_sha2_password could not be loaded: /usr/lib/x86_64-linux-gnu/mariadb19/plugin/caching_sha2_password.so: cannot open shared object file: No such file or directory
```
we should alter the password method

```
> alter user root@localhost identified with mysql_native_password by 'tfbsdb2';
> alter user root@'%' identified with mysql_native_password by 'tfbsdb2';
```

## API Server

We use Flask

```
$ cd api
$ docker build -t tfbsdb2 .
```

```
docker run -p 5000:5000 --network bridge tfbsdb2
```

## Pitfalls

creating Docker networks can cause problems with IT security.

E.g. at ISB we use network "bridge"

"172.17"
mysql --host 172.17.0.2 -u root -p tfbsdb2


## Solr Server

To create the Solr core

```
$ bin/solr create -c tfbsdb2
```

Add this to solrconfig.xml to enable auto suggester

```
  <!-- AutoSuggester component -->
  <searchComponent name="suggest" class="solr.SuggestComponent">
    <lst name="suggester">
      <str name="name">mySuggester</str>
      <str name="lookupImpl">FuzzyLookupFactory</str>
      <str name="dictionaryImpl">DocumentDictionaryFactory</str>
      <str name="field">names</str>
      <str name="suggestAnalyzerFieldType">string</str>
      <str name="buildOnStartup">false</str>
    </lst>
  </searchComponent>
  <requestHandler name="/suggest" class="solr.SearchHandler" startup="lazy">
    <lst name="defaults">
      <str name="suggest">true</str>
      <str name="suggest.count">10</str>
    </lst>
    <arr name="components">
      <str>suggest</str>
    </arr>
  </requestHandler>
```

### Post document to Solr

bin/post -c tfbsdb2 document.xml
