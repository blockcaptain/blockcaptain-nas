#!/bin/bash
set -ex
DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

useradd -M -s /sbin/nologin -u 2001 influx 

mkdir -p /var/local/influx
chown influx: /var/local/influx
cd "$DIR"
docker-compose up -d
tries=0
until $(curl --output /dev/null --max-time 3 --silent --fail http://localhost:9999/api/v2/setup); do
    sleep 1
    tries=$((tries+1)) 
    if [[ $tries -ge 30 ]]; then
        exit 1
    fi
done
container_id=$(docker-compose ps -q influx)
docker exec -u root $container_id influx setup -u admin -p 12345678 -o ParanoidNAS -b nas -r 0 -f 
docker exec -u root $container_id influx user create -n paranoid -p 12345678 -o ParanoidNAS 