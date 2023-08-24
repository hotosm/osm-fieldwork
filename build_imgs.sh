#!/bin/bash

set -eo pipefail

PKG_VERSION=0.3.5

docker build . --push \
    -t "ghcr.io/hotosm/osm-fieldwork:${PKG_VERSION}" \
    --target prod \
    --build-arg PKG_VERSION="${PKG_VERSION}"

docker build . --push \
    -t ghcr.io/hotosm/osm-fieldwork:ci \
    --target ci \
    --build-arg PKG_VERSION="${PKG_VERSION}"
