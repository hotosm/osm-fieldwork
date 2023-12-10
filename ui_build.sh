#!/bin/bash

# Build the app
docker build . --target ui-build \
    --tag ghcr.io/hotosm/osm-fieldwork/ui:latest

# Remove container if exists and exited
docker rm kivy-ui-build || true

docker run --rm --name kivy-ui-build \
    -v $PWD/dist:/app/bin \
    ghcr.io/hotosm/osm-fieldwork/ui:latest
