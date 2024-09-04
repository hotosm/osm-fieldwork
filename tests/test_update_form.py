# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     osm-fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     osm-fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Test functionalty of update_form.py."""

from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from osm_fieldwork.update_form import update_xls_form


def test_merge_mandatory_fields():
    """Merge the mandatory fields XLSForm to a test survey form."""
    buildings_form = Path(__file__).parent.parent / "osm_fieldwork" / "xlsforms" / "buildings.xls"
    with open(buildings_form, "rb") as xlsform:
        form_bytes = BytesIO(xlsform.read())

    updated_form = update_xls_form(form_bytes)

    # Load the updated form using openpyxl
    workbook = load_workbook(filename=BytesIO(updated_form.getvalue()))
    if "survey" not in workbook.sheetnames:
        raise ValueError("The 'survey' sheet was not found in the workbook")
    sheet = workbook["survey"]

    # Find the index of the 'name' column
    name_col = None
    for col in sheet.iter_cols(1, sheet.max_column):
        if col[0].value == "name":
            name_col = col
            break

    assert name_col is not None, "The 'name' column was not found."

    # Check if 'existing' is present in the 'name' column (skip the header)
    existing_found = any(cell.value == "existing" for cell in name_col[1:])

    assert existing_found, "'existing' value not found in the 'name' column."
