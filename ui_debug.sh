#!/bin/bash

docker build . --target ui-debug \
    --tag ghcr.io/hotosm/osm-fieldwork/ui:debug

# Remove container if exists and exited
docker rm kivy-ui-debug || true

docker run --rm --name kivy-ui-debug \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e "DISPLAY=$DISPLAY" \
    ghcr.io/hotosm/osm-fieldwork/ui:debug
