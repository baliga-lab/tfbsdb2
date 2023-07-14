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
$ docker network create tfbsdb2
```

We use a dedicated Docker network to stitch together our containers

## MySQL

### Run the database container

Hostname mysql

```
$ docker run --name mysql -e MYSQL_ROOT_PASSWORD=tfbsdb2 --network tfbsdb2 -d mysql:latest
```
  or

```
$ docker run --name mysql -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=tfbsdb2 --network tfbsdb2 --restart unless-stopped mysql:latest
```

We can see the container by

```
$ docker network inspect tfbsdb2
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
docker run -p 5000:5000 --network tfbsdb2 tfbsdb2
```
