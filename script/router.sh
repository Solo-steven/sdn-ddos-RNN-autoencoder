#! /bin/bash

echo "Start Setting up S1"
curl -X POST -d '{"address":"172.16.20.1/24"}' http://localhost:8080/router/0000000000000001
curl -X POST -d '{"address": "172.16.30.30/24"}' http://localhost:8080/router/0000000000000001

echo "Start Setting up S2"
curl -X POST -d '{"address":"172.16.10.1/24"}' http://localhost:8080/router/0000000000000002
curl -X POST -d '{"address": "172.16.30.1/24"}' http://localhost:8080/router/0000000000000002
curl -X POST -d '{"address": "192.168.10.1/24"}' http://localhost:8080/router/0000000000000002

echo "Start Setting up S3"
curl -X POST -d '{"address": "192.168.30.1/24"}' http://localhost:8080/router/0000000000000003
curl -X POST -d '{"address": "192.168.10.20/24"}' http://localhost:8080/router/0000000000000003
