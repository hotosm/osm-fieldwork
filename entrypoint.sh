#!/bin/bash

set -eo pipefail

exec gosu appuser "$@"
