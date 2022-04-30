#! /bin/bash

OSMNBI_URL="https://10.0.12.98:9999/osm"

for item in sdns nsrs vnfrs nslcmops pdus nsts nsis nsilcmops # vims
do
    curl --insecure ${OSMNBI_URL}/test/db-clear/${item}
done
