#!/bin/bash

# Run from the /docs dir

pdm install -G docs
pdm run gendocs --config mkgendocs.yml
