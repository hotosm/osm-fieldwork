# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm-fieldwork.
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
#     along with osm-fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Configuration and fixtures for PyTest."""

import logging
import sys
import uuid
from pathlib import Path

import pytest

# from pyxform.xls2xform import xls2xform_convert
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject

logging.basicConfig(
    level="DEBUG",
    format=("%(asctime)s.%(msecs)03d [%(levelname)s] " "%(name)s | %(funcName)s:%(lineno)d | %(message)s"),
    datefmt="%y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

testdata_dir = Path(__file__).parent / "testdata"


# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy_utils import create_database, database_exists


# engine = create_engine("postgres://")
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base.metadata.create_all(bind=engine)


# def pytest_configure(config):
#     """Configure pytest runs."""
#     # Stop sqlalchemy logs
#     sqlalchemy_log = logging.getLogger("sqlalchemy")
#     sqlalchemy_log.propagate = False


# @pytest.fixture(scope="session")
# def db_engine():
#     """The SQLAlchemy database engine to init."""
#     engine = create_engine(settings.FMTM_DB_URL.unicode_string())
#     if not database_exists:
#         create_database(engine.url)

#     Base.metadata.create_all(bind=engine)
#     yield engine


# @pytest.fixture(scope="function")
# def db(db_engine):
#     """Database session using db_engine."""
#     connection = db_engine.connect()

#     # begin a non-ORM transaction
#     connection.begin()

#     # bind an individual Session to the connection
#     db = TestingSessionLocal(bind=connection)

#     yield db

#     db.rollback()
#     connection.close()


# @pytest.fixture(scope="function")
# def token():
#     """Get persistent ODK Central requests session."""
#     response = requests.post("http://central:8383/v1/sessions", json={
#         "email": "test@hotosm.org",
#         "password": "Password1234"
#     })
#     return response.json().get("token")


@pytest.fixture(scope="session")
def project():
    """Get persistent ODK Central requests session."""
    return OdkProject("https://proxy", "test@hotosm.org", "Password1234")


@pytest.fixture(scope="session")
def project_details(project):
    """Get persistent ODK Central requests session."""
    return project.createProject("test project")


@pytest.fixture(scope="function")
def appuser():
    """Get appuser for a project."""
    return OdkAppUser(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )


@pytest.fixture(scope="function")
def appuser_details(appuser, project_details):
    """Get appuser for a project."""
    appuser_name = f"test_appuser_{uuid.uuid4()}"
    response = appuser.create(project_details.get("id"), appuser_name)

    assert response.get("displayName") == appuser_name

    return response


@pytest.fixture(scope="function")
def odk_form(project_details) -> tuple:
    """Get appuser for a project."""
    odk_id = project_details.get("id")
    form = OdkForm(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )
    return odk_id, form


@pytest.fixture(scope="function")
def odk_form_cleanup(odk_form):
    """Get xform for project, with automatic cleanup after."""
    odk_id, xform = odk_form
    test_xform = testdata_dir / "buildings.xml"

    # Create form
    form_name = xform.createForm(odk_id, str(test_xform))
    assert form_name == "test_form"

    # Before yield is used in tests
    yield odk_id, form_name, xform
    # After yield is test cleanup

    # Delete form
    success = xform.deleteForm(odk_id, "test_form")
    assert success


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Cleanup projects and forms after all tests (session)."""
    project = OdkProject(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )

    for item in project.listProjects():
        project_id = item.get("id")
        project.deleteProject(project_id)


# @pytest.fixture(scope="function")
# def xform_details(xform, project_details):
#     """Get appuser for a project."""
#     xlsform = xls2xform_convert(buildings)
#     response = xform.createForm(
#         projectId=project_details.get("id"),
#         filespec=xlsform,
#         xform="1",
#     )
