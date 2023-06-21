# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of Osm-Fieldwork.
#
#     Osm-Fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Osm-Fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Osm-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

PACKAGE := org.osm_fieldwork.py
NAME := Osm-Fieldwork
VERSION := 0.3.1

# Make a python package for pip
pip:
	zip -r $(NAME).zip .

pip-install: pip
	pip3 install $(NAME).zip

pip-uninstall:
	pip3 uninstall $(NAME)

check:
	pytest
