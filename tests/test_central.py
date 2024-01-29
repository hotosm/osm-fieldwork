# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     Underpass is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Underpass is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Test functionalty of OdkCentral.py."""

from pathlib import Path

import segno


def test_delete_appuser(appuser, appuser_details, project_details):
    """Create a QR Code for an appuser."""
    response = appuser.delete(
        project_details.get("id"),
        appuser_details.get("id"),
    )
    assert response.ok
    assert response.json().get("success") == True


# def test_update_role(appuser, project_details, appuser_details, xform_details):
#     """Test updating appuser role."""
#     response = appuser.updateRole(
#         projectId=project_details.get("id"), xform=xform_details.get("id"), actorId=appuser_details.get("id")
#     )
#     assert response.ok


# def test_grant_access(appuser, project_details, appuser_details, xform_details):
#     """Create granting appuser access to a form."""
#     response = appuser.grantAccess(
#         projectId=project_details.get("id"), xform=xform_details.get("id"), actorId=appuser_details.get("id")
#     )
#     assert response.ok


def test_create_qrcode(appuser, appuser_details):
    """Create a QR Code for an appuser."""
    qrcode = appuser.createQRCode(
        odk_id=1,
        project_name="test project",
        appuser_token=appuser_details.get("token"),
        basemap="osm",
        osm_username="svchotosm",
        # save_qrcode = False,
    )
    assert isinstance(qrcode, segno.QRCode)

    qrcode = appuser.createQRCode(
        odk_id=1,
        project_name="test project",
        appuser_token=appuser_details.get("token"),
        basemap="osm",
        osm_username="svchotosm",
        save_qrcode=True,
    )
    qrcode_file = Path("test project.png")
    assert qrcode_file.exists()
