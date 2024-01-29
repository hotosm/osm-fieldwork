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

import pytest_asyncio

# from pyxform.xls2xform import xls2xform_convert
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject

logging.basicConfig(
    level="DEBUG",
    format=("%(asctime)s.%(msecs)03d [%(levelname)s] " "%(name)s | %(funcName)s:%(lineno)d | %(message)s"),
    datefmt="%y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)


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


@pytest_asyncio.fixture(scope="function")
def project():
    """Get persistent ODK Central requests session."""
    return OdkProject("https://proxy", "test@hotosm.org", "Password1234")


@pytest_asyncio.fixture(scope="function")
async def project_details(project):
    """Get persistent ODK Central requests session."""
    return await project.createProject("test project")


@pytest_asyncio.fixture(scope="function")
def appuser():
    """Get appuser for a project."""
    return OdkAppUser(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )


@pytest_asyncio.fixture(scope="function")
async def appuser_details(appuser, project_details):
    """Get appuser for a project."""
    appuser_name = f"test_appuser_{uuid.uuid4()}"
    response = await appuser.create(project_details.get("id"), appuser_name)

    assert response.get("projectId") == 1
    assert response.get("displayName") == appuser_name

    return response


@pytest_asyncio.fixture(scope="function")
async def xform():
    """Get appuser for a project."""
    return OdkForm(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )


# @pytest.fixture(scope="function")
# def xform_details(xform, project_details):
#     """Get appuser for a project."""
#     xlsform = xls2xform_convert(buildings)
#     response = xform.createForm(
#         projectId=project_details.get("id"),
#         xform="1",
#         filespec=xlsform,
#     )
