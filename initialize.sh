#!/bin/bash
mc alias set local http://localhost:9000 minio minio1234
# Create user
mc admin user add local backend backend1234
# Give user access to all buckets
mc admin policy set local readwrite user=backend

wio register main@domain.com main --password pass
wio register other@domain.com other --password pass
wio login main@domain.com --password pass

wio w c first --public
wio w c second
wio w c third

wio login other@domain.com --password pass

wio w c primary --pubic
wio w c secondary


wio index create
