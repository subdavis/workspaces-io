#!/bin/bash

mc alias set local http://localhost:9000 minio minio1234
# Create user
mc admin user add local backend backend1234
# Give user access to all buckets
mc admin policy set local readwrite user=backend

mc alias set secondary http://localhost:9100 minio minio1234
# Create user
mc admin user add secondary backend backend1234
# Give user access to all buckets
mc admin policy set secondary readwrite user=backend

# wio register main@domain.com main --password pass
# wio register other@domain.com other --password pass
# wio login main@domain.com --password pass

wio node c default http://varrock:9000 backend backend1234
wio root c default-private default
wio root c public default --root-type public

wio node c secondary http://varrock:9100 backend backend1234
wio root c secondary-private secondary

wio w c first --public
wio w c second
wio w c third
