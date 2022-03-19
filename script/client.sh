#! /bin/bash

while [ 1 ]; do
    curl http://$1:3000
    sleep 1
    curl http://$2:3000
done