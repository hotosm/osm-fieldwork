#!/usr/bin/python3

# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
#
#     Odkconvert is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Odkconvert is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

# This uses https://github.com/kivy/python-for-android to produce apks for Android,
# and a zip file for python pip.

PACKAGE := org.odkconvert.py
NAME := ODKCOnvert
VERSION := 0.1
ARCH := armeabi-v7a
P4ABIN = /usr/local/bin/p4a

all: pip
	echo "Nothing to do..."

# Make a python2 apk for Android
apk2:
	${P4ABIN} apk ${DEFS} --requirements=${P2VER},${REQUIREMENTS}

# Make a python3 apk for Android
apk3:
	${P4ABIN} apk --private `pwd` --arch=${ARCH} --package=${PACKAGE} --name "${NAME}" --version ${VERSION} --bootstrap=${BOOTSTRAP} --requirements=${P3VER},${REQUIREMENTS}

# Make a python package for pip
pip:
	zip -r $(NAME).zip *.py

pip-install: pip
	pip3 install $(NAME).zip

pip-uninstall:
	pip3 uninstall $(NAME)

check:
	cd testsuite && pytest

#compile:
#    python3 -m nuitka --follow-imports shp2map.py

