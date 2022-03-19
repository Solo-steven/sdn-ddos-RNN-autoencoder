## Gateway
curl -X POST -d '{"gateway": "172.16.30.1"}' http://localhost:8080/router/0000000000000001
curl -X POST -d '{"gateway": "172.16.30.30"}' http://localhost:8080/router/0000000000000002
curl -X POST -d '{"gateway": "192.168.10.1"}' http://localhost:8080/router/0000000000000003

## Static Gateway
curl -X POST -d '{"destination": "192.168.30.0/24", "gateway": "192.168.10.20"}' http://localhost:8080/router/0000000000000002