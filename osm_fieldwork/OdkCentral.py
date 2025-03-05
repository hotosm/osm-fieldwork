#!/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     OSM-Fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with OSM-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

# The origins of this file was called odk_request.py, and gave me the
# idea to do a much enhanced version. Contributors to the original are:
# Author: hcwinsemius <h.c.winsemius@gmail.com>
# Author: Ivan Gayton <ivangayton@gmail.com>
# Author: Reetta Valimaki <reetta.valimaki8@gmail.com>

# NOTE while there is some unique functionality in this module not available
# NOTE in getodk/pyodk, for most use cases it would be recommended to use
# NOTE pyodk instead.
#
# NOTE If async functionality is required, then OdkCentralAsync is available,
# NOTE as pyodk does not support async workflows.

import concurrent.futures
import json
import logging
import os
import sys
import zlib
from base64 import b64encode
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4
from xml.etree import ElementTree

import requests
import segno
from codetiming import Timer
from cpuinfo import get_cpu_info

# Instantiate logger
log_level = os.getenv("LOG_LEVEL", default="INFO")
# Set log level for urllib
logging.getLogger("urllib3").setLevel(log_level)

log = logging.getLogger(__name__)


def downloadThread(project_id: int, xforms: list, odk_credentials: dict, filters: dict = None):
    """Download a list of submissions from ODK Central.

    Args:
        project_id (int): The ID of the project on ODK Central
        xforms (list): A list of the XForms to down the submissions from
        odk_credentials (dict): The authentication credentials for ODK Collect

    Returns:
        (list): The submissions in JSON format
    """
    timer = Timer(text="downloadThread() took {seconds:.0f}s")
    timer.start()
    data = list()
    # log.debug(f"downloadThread() called! {len(xforms)} xforms")
    for task in xforms:
        form = OdkForm(odk_credentials["url"], odk_credentials["user"], odk_credentials["passwd"])
        # submissions = form.getSubmissions(project_id, task, 0, False, True)
        subs = form.listSubmissions(project_id, task, filters)
        if not subs:
            log.error(f"Failed to get submissions for project ({project_id}) task ({task})")
            continue
        # log.debug(f"There are {len(subs)} submissions for {task}")
        if len(subs["value"]) > 0:
            data += subs["value"]
    # log.debug(f"There are {len(xforms)} Xforms, and {len(submissions)} submissions total")
    timer.stop()
    return data


class OdkCentral(object):
    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """A Class for accessing an ODK Central server via it's REST API.

        Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central

        Returns:
            (OdkCentral): An instance of this class
        """
        if not url:
            url = os.getenv("ODK_CENTRAL_URL", default=None)
        self.url = url
        if not user:
            user = os.getenv("ODK_CENTRAL_USER", default=None)
        self.user = user
        if not passwd:
            passwd = os.getenv("ODK_CENTRAL_PASSWD", default=None)
        self.passwd = passwd
        verify = os.getenv("ODK_CENTRAL_SECURE", default=True)
        if type(verify) == str:
            self.verify = verify.lower() in ("true", "1", "t")
        else:
            self.verify = verify
        # Set cert bundle path for requests in environment
        if self.verify:
            os.environ["REQUESTS_CA_BUNDLE"] = "/etc/ssl/certs/ca-certificates.crt"
        # These are settings used by ODK Collect
        self.general = {
            "form_update_mode": "match_exactly",
            "autosend": "wifi_and_cellular",
        }
        # If there is a config file with authentication setting, use that
        # so we don't have to supply this all the time. This is only used
        # when odk_client is used, and no parameters are passed in.
        if not self.url:
            # log.debug("Configuring ODKCentral from file .odkcentral")
            home = os.getenv("HOME")
            config = ".odkcentral"
            filespec = home + "/" + config
            if os.path.exists(filespec):
                file = open(filespec, "r")
                for line in file:
                    # Support embedded comments
                    if line[0] == "#":
                        continue
                    # Read the config file for authentication settings
                    tmp = line.split("=")
                    if tmp[0] == "url":
                        self.url = tmp[1].strip("\n")
                    if tmp[0] == "user":
                        self.user = tmp[1].strip("\n")
                    if tmp[0] == "passwd":
                        self.passwd = tmp[1].strip("\n")
            else:
                log.warning(f"Authentication settings missing from {filespec}")
        else:
            log.debug(f"ODKCentral configuration parsed: {self.url}")
        # Base URL for the REST API
        self.version = "v1"
        # log.debug(f"Using {self.version} API")
        self.base = self.url + "/" + self.version + "/"

        # Use a persistant connect, better for multiple requests
        self.session = requests.Session()

        # Authentication with session token
        self.authenticate()

        # These are just cached data from the queries
        self.projects = dict()
        self.users = list()

    def authenticate(
        self,
        url: str = None,
        user: str = None,
        passwd: str = None,
    ):
        """Setup authenticate to an ODK Central server.

        Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central

        Returns:
            (requests.Response): A response from ODK Central after auth
        """
        if not self.url:
            self.url = url
        if not self.user:
            self.user = user
        if not self.passwd:
            self.passwd = passwd

        # Get a session token
        try:
            response = self.session.post(
                f"{self.base}sessions",
                json={
                    "email": self.user,
                    "password": self.passwd,
                },
            )
        except requests.exceptions.ConnectionError as request_error:
            # URL does not exist
            raise ConnectionError("Failed to connect to Central. Is the URL valid?") from request_error

        if response.status_code == 401:
            # Unauthorized, invalid credentials
            raise ConnectionError("ODK credentials are invalid, or may have changed. Please update them.") from None
        elif not response.ok:
            # Handle other errors
            response.raise_for_status()

        self.session.headers.update({"Authorization": f"Bearer {response.json().get('token')}"})

        # Connect to the server
        return self.session.get(self.url, verify=self.verify)

    def listProjects(self):
        """Fetch a list of projects from an ODK Central server, and
        store it as an indexed list.

        Returns:
            (list): A list of projects on a ODK Central server
        """
        log.info("Getting a list of projects from %s" % self.url)
        url = f"{self.base}projects"
        result = self.session.get(url, verify=self.verify)
        projects = result.json()
        for project in projects:
            if isinstance(project, dict):
                if project.get("id") is not None:
                    self.projects[project["id"]] = project
            else:
                log.info("No projects returned. Is this a first run?")
        return projects

    def createProject(
        self,
        name: str,
    ) -> dict:
        """Create a new project on an ODK Central server if it doesn't
        already exist.

        Args:
            name (str): The name for the new project

        Returns:
            (json): The response from ODK Central
        """
        log.debug(f"Checking if project named {name} exists already")
        exists = self.findProject(name=name)
        if exists:
            log.debug(f"Project named {name} already exists.")
            return exists
        else:
            url = f"{self.base}projects"
            log.debug(f"POSTing project {name} to {url} with verify={self.verify}")
            try:
                result = self.session.post(url, json={"name": name}, verify=self.verify, timeout=4)
                result.raise_for_status()
            except requests.exceptions.RequestException as e:
                log.error(e)
                log.error("Failed to submit to ODKCentral")
            json_response = result.json()
            log.debug(f"Returned: {json_response}")
            # update the internal list of projects
            self.listProjects()
            return json_response

    def deleteProject(
        self,
        project_id: int,
    ):
        """Delete a project on an ODK Central server.

        Args:
            project_id (int): The ID of the project on ODK Central

        Returns:
            (str): The project name
        """
        url = f"{self.base}projects/{project_id}"
        self.session.delete(url, verify=self.verify)
        # update the internal list of projects
        self.listProjects()
        return self.findProject(project_id=project_id)

    def findProject(
        self,
        name: str = None,
        project_id: int = None,
    ):
        """Get the project data from Central.

        Args:
            name (str): The name of the project

        Returns:
            (dict): the project data from ODK Central
        """
        # First, populate self.projects
        self.listProjects()

        if self.projects:
            if name:
                log.debug(f"Finding project by name: {name}")
                for _key, value in self.projects.items():
                    if name == value["name"]:
                        log.info(f"ODK project found: {name}")
                        return value
            if project_id:
                log.debug(f"Finding project by id: {project_id}")
                for _key, value in self.projects.items():
                    if project_id == value["id"]:
                        log.info(f"ODK project found: {project_id}")
                        return value
        return None

    def findAppUser(
        self,
        user_id: int,
        name: str = None,
    ):
        """Get the data for an app user.

        Args:
            user_id (int): The user ID of the app-user on ODK Central
            name (str): The name of the app-user on ODK Central

        Returns:
            (dict): The data for an app-user on ODK Central
        """
        if self.appusers:
            if name is not None:
                result = [d for d in self.appusers if d["displayName"] == name]
                if result:
                    return result[0]
                else:
                    log.debug(f"No user found with name: {name}")
                    return None
            if user_id is not None:
                result = [d for d in self.appusers if d["id"] == user_id]
                if result:
                    return result[0]
                else:
                    log.debug(f"No user found with id: {user_id}")
                    return None
        return None

    def listUsers(self):
        """Fetch a list of users on the ODK Central server.

        Returns:
            (list): A list of users on ODK Central, not app-users
        """
        log.info("Getting a list of users from %s" % self.url)
        url = self.base + "users"
        result = self.session.get(url, verify=self.verify)
        self.users = result.json()
        return self.users

    def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        # print("URL: %s" % self.url)
        # print("User: %s" % self.user)
        # print("Passwd: %s" % self.passwd)
        print("REST URL: %s" % self.base)

        print("There are %d projects on this server" % len(self.projects))
        for id, data in self.projects.items():
            print("\t %s: %s" % (id, data["name"]))
        if self.users:
            print("There are %d users on this server" % len(self.users))
            for data in self.users:
                print("\t %s: %s" % (data["id"], data["email"]))
        else:
            print("There are no users on this server")


class OdkProject(OdkCentral):
    """Class to manipulate a project on an ODK Central server."""

    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central.

        Returns:
            (OdkProject): An instance of this object
        """
        super().__init__(url, user, passwd)
        self.forms = list()
        self.submissions = list()
        self.data = None
        self.appusers = None
        self.id = None

    def getData(
        self,
        keyword: str,
    ):
        """Args:
            keyword (str): The keyword to search for.

        Returns:
            (json): The data for the keyword
        """
        return self.data[keyword]

    def listForms(self, project_id: int, metadata: bool = False):
        """Fetch a list of forms in a project on an ODK Central server.

        Args:
            project_id (int): The ID of the project on ODK Central

        Returns:
            (list): The list of XForms in this project
        """
        url = f"{self.base}projects/{project_id}/forms"
        if metadata:
            self.session.headers.update({"X-Extended-Metadata": "true"})
        result = self.session.get(url, verify=self.verify)
        self.forms = result.json()
        return self.forms

    def getAllSubmissions(self, project_id: int, xforms: list = None, filters: dict = None):
        """Fetch a list of submissions in a project on an ODK Central server.

        Args:
            project_id (int): The ID of the project on ODK Central
            xforms (list): The list of XForms to get the submissions of

        Returns:
            (json): All of the submissions for all of the XForm in a project
        """
        # The number of threads is based on the CPU cores
        info = get_cpu_info()
        self.cores = info["count"]

        timer = Timer(text="getAllSubmissions() took {seconds:.0f}s")
        timer.start()
        if not xforms:
            xforms_data = self.listForms(project_id)
            xforms = [d["xmlFormId"] for d in xforms_data]

        chunk = round(len(xforms) / self.cores) if round(len(xforms) / self.cores) > 0 else 1
        last_slice = len(xforms) if len(xforms) % chunk == 0 else len(xforms) - 1
        cycle = range(0, (last_slice + chunk) + 1, chunk)
        future = None
        result = None
        previous = 0
        newdata = list()

        # single threaded for easier debugging
        # for current in cycle:
        #     if previous == current:
        #         continue
        #     result = downloadThread(project_id, xforms[previous:current])
        #     previous = current
        #     newdata += result

        odk_credentials = {"url": self.url, "user": self.user, "passwd": self.passwd}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.cores) as executor:
            futures = list()
            for current in cycle:
                if previous == current:
                    continue
                result = executor.submit(downloadThread, project_id, xforms[previous:current], odk_credentials, filters)
                previous = current
                futures.append(result)
            for future in concurrent.futures.as_completed(futures):
                log.debug("Waiting for thread to complete..")
                data = future.result(timeout=10)
                if len(data) > 0:
                    newdata += data
        timer.stop()
        return newdata

    def listAppUsers(
        self,
        projectId: int,
    ):
        """Fetch a list of app users for a project from an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central

        Returns:
            (list): A list of app-users on ODK Central for this project
        """
        url = f"{self.base}projects/{projectId}/app-users"
        result = self.session.get(url, verify=self.verify)
        self.appusers = result.json()
        return self.appusers

    def listAssignments(
        self,
        projectId: int,
    ):
        """List the Role & Actor assignments for users on a project.

        Args:
            projectId (int): The ID of the project on ODK Central

        Returns:
            (json): The list of assignments
        """
        url = f"{self.base}projects/{projectId}/assignments"
        result = self.session.get(url, verify=self.verify)
        return result.json()

    def getDetails(
        self,
        projectId: int,
    ):
        """Get all the details for a project on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central

        Returns:
            (json): Get the data about a project on ODK Central
        """
        url = f"{self.base}projects/{projectId}"
        result = self.session.get(url, verify=self.verify)
        self.data = result.json()
        return self.data

    def getFullDetails(
        self,
        projectId: int,
    ):
        """Get extended details for a project on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central

        Returns:
            (json): Get the data about a project on ODK Central
        """
        url = f"{self.base}projects/{projectId}"
        self.session.headers.update({"X-Extended-Metadata": "true"})
        result = self.session.get(url, verify=self.verify)
        return result.json()

    def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        super().dump()
        if self.forms:
            print("There are %d forms in this project" % len(self.forms))
            for data in self.forms:
                print("\t %s(%s): %s" % (data["xmlFormId"], data["version"], data["name"]))
        if self.data:
            print("Project ID: %s" % self.data["id"])
        print("There are %d submissions in this project" % len(self.submissions))
        for data in self.submissions:
            print("\t%s: %s" % (data["instanceId"], data["createdAt"]))
        print("There are %d app users in this project" % len(self.appusers))
        for data in self.appusers:
            print("\t%s: %s" % (data["id"], data["displayName"]))

    def updateReviewState(self, projectId: int, xmlFormId: str, instanceId: str, review_state: dict) -> dict:
        """Updates the review state of a submission in ODK Central.

        Args:
            projectId (int): The ID of the odk project.
            xmlFormId (str): The ID of the form.
            instanceId (str): The ID of the submission instance.
            review_state (dict): The updated review state.
        """
        try:
            url = f"{self.base}projects/{projectId}/forms/{xmlFormId}/submissions/{instanceId}"
            result = self.session.patch(url, json=review_state)
            result.raise_for_status()
            return result.json()
        except Exception as e:
            log.error(f"Error updating review state: {e}")
            return {}


class OdkForm(OdkCentral):
    """Class to manipulate a form on an ODK Central server."""

    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central.

        Returns:
            (OdkForm): An instance of this object
        """
        super().__init__(url, user, passwd)
        self.name = None
        # Draft is for a form that isn't published yet
        self.draft = False
        self.published = False
        # this is only populated if self.getDetails() is called first.
        self.data = {}
        self.attach = []
        self.media = {}
        self.xml = None
        self.submissions = []
        self.appusers = {}
        # self.xmlFormId = None
        # self.projectId = None

    # def getName(self):
    #     """
    #     Extract the name from a form on an ODK Central server
    #
    #     Returns:
    #     """
    #     if "name" in self.data:
    #         return self.data["name"]
    #     else:
    #         log.warning("Execute OdkForm.getDetails() to get this data.")

    # def getFormId(self):
    #     """Extract the xmlFormId from a form on an ODK Central server"""
    #     if "xmlFormId" in self.data:
    #         return self.data["xmlFormId"]
    #     else:
    #         log.warning("Execute OdkForm.getDetails() to get this data.")

    def getDetails(
        self,
        projectId: int,
        xform: str,
    ) -> dict:
        """Get all the details for a form on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The data for this XForm
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}"
        result = self.session.get(url, verify=self.verify)
        self.data = result.json()
        return result.json()

    def getFullDetails(
        self,
        projectId: int,
        xform: str,
    ):
        """Get the full details for a form on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The data for this XForm
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}"
        self.session.headers.update({"X-Extended-Metadata": "true"})
        result = self.session.get(url, verify=self.verify)
        return result.json()

    def getXml(
        self,
        projectId: int,
        xform: str,
    ):
        """Get the form XML from the ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central.
            xform (str): The XForm to get the details of from ODK Central.

        Returns:
            (str): The raw XML form.
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}.xml"
        result = self.session.get(url, verify=self.verify)

        if result.status_code != 200:
            result.raise_for_status()

        return result.text

    def listSubmissionBasicInfo(
        self,
        projectId: int,
        xform: str,
    ):
        """Fetch a list of submission instances basic information for a given form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The data for this XForm
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/submissions"
        result = self.session.get(url, verify=self.verify)
        return result.json()

    def listSubmissions(self, projectId: int, xform: str, filters: dict = None):
        """Fetch a list of submission instances for a given form.

        Returns data in format:

        {
            "value":[],
            "@odata.context": "URL/v1/projects/52/forms/103.svc/$metadata#Submissions",
            "@odata.count":0
        }

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The JSON of Submissions.
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}.svc/Submissions"
        try:
            result = self.session.get(url, params=filters, verify=self.verify)
            result.raise_for_status()  # Raise an error for non-2xx status codes
            self.submissions = result.json()
            return self.submissions
        except Exception as e:
            log.error(f"Error fetching submissions: {e}")
            return {}

    def listAssignments(
        self,
        projectId: int,
        xform: str,
    ):
        """List the Role & Actor assignments for users on a project.

        Fetch a list of submission instances basic information for a given form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The data for this XForm
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/assignments"
        result = self.session.get(url, verify=self.verify)
        return result.json()

    def getSubmissions(
        self,
        projectId: int,
        xform: str,
        submission_id: int,
        disk: bool = False,
        json: bool = True,
    ):
        """Fetch a CSV or JSON file of the submissions without media to a survey form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            submission_id (int): The ID of the submissions to download
            disk (bool): Whether to write the downloaded file to disk
            json (bool): Download JSON or CSV format

        Returns:
            (bytes): The list of submissions as JSON or CSV bytes object.
        """
        now = datetime.now()
        timestamp = f"{now.year}_{now.hour}_{now.minute}"

        if json:
            url = self.base + f"projects/{projectId}/forms/{xform}.svc/Submissions"
            filespec = f"{xform}_{timestamp}.json"
        else:
            url = self.base + f"projects/{projectId}/forms/{xform}/submissions"
            filespec = f"{xform}_{timestamp}.csv"

        if submission_id:
            url = url + f"('{submission_id}')"

        # log.debug(f'Getting submissions for {projectId}, Form {xform}')
        result = self.session.get(
            url,
            headers=dict({"Content-Type": "application/json"}, **self.session.headers),
            verify=self.verify,
        )
        if result.status_code == 200:
            if disk:
                # id = self.forms[0]['xmlFormId']
                try:
                    file = open(filespec, "xb")
                    file.write(result.content)
                except FileExistsError:
                    file = open(filespec, "wb")
                    file.write(result.content)
                log.info("Wrote output file %s" % filespec)
                file.close()
            return result.content
        else:
            log.error(f"Submissions for {projectId}, Form {xform}" + " doesn't exist")
            return bytes()

    def getSubmissionMedia(
        self,
        projectId: int,
        xform: str,
        filters: dict = {},
    ):
        """Fetch a ZIP file of the submissions with media to a survey form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (list): The media file
        """
        url = self.base + f"projects/{projectId}/forms/{xform}/submissions.csv.zip"
        result = self.session.get(url, params=filters, verify=self.verify)
        return result

    def getSubmissionPhoto(
        self,
        projectId: int,
        instanceID: str,
        xform: str,
        filename: str,
    ):
        """Fetch a specific attachment by filename from a submission to a form.

        NOTE this function expects the user has not configured external S3 storage.
        NOTE if S3 storage is configured, the response does not contain the
        NOTE photo content, but instead an S3 pre-signed URL.
        NOTE see OdkCentralAsync.OdkForm.getSubmissionAttachmentUrl

        Args:
            projectId (int): The ID of the project on ODK Central
            instanceID(str): The ID of the submission on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            filename (str): The name of the attachment for the XForm on ODK Central

        Returns:
            (bytes): The media data
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/submissions/{instanceID}/attachments/{filename}"
        result = self.session.get(url, verify=self.verify)
        if result.status_code == 200:
            log.debug(f"fetched {filename} from Central")
        else:
            status = result.json()
            log.error(f"Couldn't fetch {filename} from Central: {status['message']}")
        return result.content

    def addMedia(
        self,
        media: bytes,
        filespec: str,
    ):
        """Add a data file to this form.

        Args:
            media (str): The media file
            filespec (str): the name of the media
        """
        # FIXME: this also needs the data
        self.media[filespec] = media

    def addXMLForm(
        self,
        projectId: int,
        xmlFormId: int,
        xform: str,
    ):
        """Add an XML file to this form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
        """
        self.xml = xform

    def listMedia(
        self,
        projectId: int,
        xform: str,
    ):
        """List all the attchements for this form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (list): A list of al the media files for this project
        """
        if self.draft:
            url = f"{self.base}projects/{projectId}/forms/{xform}/draft/attachments"
        else:
            url = f"{self.base}projects/{projectId}/forms/{xform}/attachments"
        result = self.session.get(url, verify=self.verify)
        self.media = result.json()
        return self.media

    def validateMedia(self, filename: str):
        """Validate the specified filename is present in the XForm."""
        if not self.xml:
            return
        xform_filenames = []
        namespaces = {
            "h": "http://www.w3.org/1999/xhtml",
            "odk": "http://www.opendatakit.org/xforms",
            "xforms": "http://www.w3.org/2002/xforms",
        }

        root = ElementTree.fromstring(self.xml)
        instances = root.findall(".//xforms:model/xforms:instance[@src]", namespaces)

        for inst in instances:
            src_value = inst.attrib.get("src", "")
            if src_value.startswith("jr://"):
                src_value = src_value[len("jr://") :]  # Remove jr:// prefix
            if src_value.startswith("file/"):
                src_value = src_value[len("file/") :]  # Remove file/ prefix
            xform_filenames.append(src_value)

        if filename not in xform_filenames:
            log.error(f"Filename ({filename}) is not present in XForm media: {xform_filenames}")
            return False

        return True

    def uploadMedia(
        self,
        projectId: int,
        form_name: str,
        data: Union[str, Path, BytesIO],
        filename: Optional[str] = None,
    ) -> Optional[requests.Response]:
        """Upload an attachement to the ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            form_name (str): The XForm to get the details of from ODK Central
            data (str, Path, BytesIO): The file path or BytesIO media file
            filename (str): If BytesIO object used, provide a file name.

        Returns:
            result (requests.Response): The response object.
        """
        # BytesIO memory object
        if isinstance(data, BytesIO):
            if filename is None:
                log.error("Cannot pass BytesIO object and not include the filename arg")
                return None
            media = data.getvalue()
        # Filepath
        elif isinstance(data, str) or isinstance(data, Path):
            media_file_path = Path(data)
            if not media_file_path.exists():
                log.error(f"File does not exist on disk: {data}")
                return None
            with open(media_file_path, "rb") as file:
                media = file.read()
            filename = str(Path(data).name)

        # Validate filename present in XForm
        if self.xml:
            if not self.validateMedia(filename):
                return None

        # Must first convert to draft if already published
        if not self.draft or self.published:
            # TODO should this use self.createForm ?
            log.debug(f"Updating form ({form_name}) to draft")
            url = f"{self.base}projects/{projectId}/forms/{form_name}/draft?ignoreWarnings=true"
            result = self.session.post(url, verify=self.verify)
            if result.status_code != 200:
                status = result.json()
                log.error(f"Couldn't modify {form_name} to draft: {status['message']}")
                return None

        # Upload the media
        url = f"{self.base}projects/{projectId}/forms/{form_name}/draft/attachments/{filename}"
        log.debug(f"Uploading media to URL: {url}")
        result = self.session.post(
            url, data=media, headers=dict({"Content-Type": "*/*"}, **self.session.headers), verify=self.verify
        )

        if result.status_code == 200:
            log.debug(f"Uploaded {filename} to Central")
        else:
            status = result.json()
            log.error(f"Couldn't upload {filename} to Central: {status['message']}")
            return None

        # Publish the draft by default
        if self.published:
            self.publishForm(projectId, form_name)

        self.addMedia(media, filename)

        return result

    def getMedia(
        self,
        projectId: int,
        xform: str,
        filename: str,
    ):
        """Fetch a specific attachment by filename from a submission to a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            filename (str): The name of the attachment for the XForm on ODK Central

        Returns:
            (bytes): The media data
        """
        if self.draft:
            url = f"{self.base}projects/{projectId}/forms/{xform}/draft/attachments/{filename}"
        else:
            url = f"{self.base}projects/{projectId}/forms/{xform}/attachments/{filename}"
        result = self.session.get(url, verify=self.verify)
        if result.status_code == 200:
            log.debug(f"fetched {filename} from Central")
        else:
            status = result.json()
            log.error(f"Couldn't fetch {filename} from Central: {status['message']}")
        self.addMedia(result.content, filename)
        return self.media

    def createForm(
        self,
        projectId: int,
        data: Union[str, Path, BytesIO],
        form_name: Optional[str] = None,
        publish: Optional[bool] = False,
    ) -> Optional[str]:
        """Create a new form on an ODK Central server.

        - If no form_name is passed, the form name is generated by default in draft.
            If the publish param is also passed, then the form is published.
        - If form_name is passed, a new form is created from this in draft state.
            This copies across all attachments.

        Note:
            The form name (xmlFormId) is generated from the id="…" attribute
            immediately inside the <instance> tag of the XForm XML.

        Args:
            projectId (int): The ID of the project on ODK Central
            form_name (str): The user friendly name to provide the form
            data (str, Path, BytesIO): The XForm file path, or BytesIO memory obj
            publish (bool): If the new form should be published.
                Only valid if form_name is not passed, i.e. a new form.

        Returns:
            (str, Optional): The form name, else None if failure.
        """
        # BytesIO memory object
        if isinstance(data, BytesIO):
            self.xml = data.getvalue().decode("utf-8")
        # Filepath
        elif isinstance(data, str) or isinstance(data, Path):
            xml_path = Path(data)
            if not xml_path.exists():
                log.error(f"File does not exist on disk: {data}")
                return None
            # Read the XML or XLS file
            with open(xml_path, "rb") as xml_file:
                self.xml = xml_file.read()
            log.debug("Read %d bytes from %s" % (len(self.xml), data))

        if form_name or self.draft:
            self.draft = True
            log.debug(f"Creating draft from template form: {form_name}")
            url = f"{self.base}projects/{projectId}/forms/{form_name}/draft?ignoreWarnings=true"
        else:
            # This is not a draft form, its an entirely new form (even if publish=false)
            log.debug("Creating new form, with name determined from form_id field")
            self.published = True if publish else False
            url = f"{self.base}projects/{projectId}/forms?ignoreWarnings=true&{'publish=true' if publish else ''}"

        result = self.session.post(
            url, data=self.xml, headers=dict({"Content-Type": "application/xml"}, **self.session.headers), verify=self.verify
        )

        if result.status_code != 200:
            try:
                status = result.json()
                msg = status.get("message", "Unknown error")
                if result.status_code == 409:
                    log.warning(msg)
                    last_full_stop_index = msg.rfind(".")
                    last_comma_index = msg.rfind(",")
                    if last_full_stop_index != -1 and last_comma_index != -1:
                        # Extract xmlFormId from error msg
                        xmlFormId = msg[last_comma_index + 1 : last_full_stop_index].strip()
                        return xmlFormId
                    else:
                        log.warning("Unable to extract xmlFormId from error message")
                        return None
                else:
                    log.error(f"Couldn't create {form_name} on Central: {msg}")
                    return None
            except json.decoder.JSONDecodeError:
                log.error(f"Couldn't create {form_name} on Central: Error decoding JSON response")
                return None

        try:
            # Log response to terminal
            json_data = result.json()
        except json.decoder.JSONDecodeError:
            log.error("Could not parse response json during form creation")
            return None

        # epdb.st()
        # FIXME: should update self.forms with the new form

        if "success" in json_data:
            log.debug(f"Created draft XForm on ODK server: ({form_name})")
            return form_name

        new_form_name = json_data.get("xmlFormId")
        log.info(f"Created XForm on ODK server: ({new_form_name})")
        return new_form_name

    def deleteForm(
        self,
        projectId: int,
        xform: str,
    ):
        """Delete a form from an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
        Returns:
            (bool): did it get deleted
        """
        # FIXME: If your goal is to prevent it from showing up on survey clients like ODK Collect, consider
        # setting its state to closing or closed
        if self.draft:
            log.debug(f"Deleting draft form on ODK server: ({xform})")
            url = f"{self.base}projects/{projectId}/forms/{xform}/draft"
        else:
            log.debug(f"Deleting form on ODK server: ({xform})")
            url = f"{self.base}projects/{projectId}/forms/{xform}"

        result = self.session.delete(url, verify=self.verify)
        if not result.ok:
            try:
                # Log response to terminal
                json_data = result.json()
                log.warning(json_data)
                return False
            except json.decoder.JSONDecodeError:
                log.error(f"Could not parse response json during form deletion. status_code={result.status_code}")
            finally:
                return False

        self.draft = False
        self.published = False

        return True

    def publishForm(
        self,
        projectId: int,
        xform: str,
    ) -> int:
        """Publish a draft form. When creating a form that isn't a draft, it can get publised then.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (int): The staus code from ODK Central
        """
        version = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        url = f"{self.base}projects/{projectId}/forms/{xform}/draft/publish?version={version}"
        result = self.session.post(url, verify=self.verify)
        if result.status_code != 200:
            status = result.json()
            log.error(f"Couldn't publish {xform} on Central: {status['message']}")
        else:
            log.info(f"Published {xform} on Central.")

        self.draft = False
        self.published = True

        return result.status_code

    def formFields(self, projectId: int, xform: str):
        """Retrieves the form fields for a xform from odk central.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            dict: A json object containing the form fields.

        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/fields?odata=true"
        response = self.session.get(url, verify=self.verify)

        # TODO wrap this logic and put in every method requiring form name
        if response.status_code != 200:
            if response.status_code == 404:
                msg = f"The ODK form you referenced does not exist yet: {xform}"
                log.debug(msg)
                raise requests.exceptions.HTTPError(msg)
            log.debug(f"Failed to retrieve form fields. Status code: {response.status_code}")
            response.raise_for_status()

        return response.json()

    def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        # super().dump()
        entries = len(self.media.keys())
        print("Form has %d attachments" % entries)
        for filename, content in self.media:
            print("Filename: %s" % filename)
            print("Content length: %s" % len(content))
            print("")


class OdkAppUser(OdkCentral):
    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """A Class for app user data.

        Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central

        Returns:
            (OdkAppUser): An instance of this object
        """
        super().__init__(url, user, passwd)
        self.user = None
        self.qrcode = None
        self.id = None

    def create(
        self,
        projectId: int,
        name: str,
    ):
        """Create a new app-user for a form.

        Example response:

        {
        "createdAt": "2018-04-18T23:19:14.802Z",
        "displayName": "My Display Name",
        "id": 115,
        "type": "user",
        "updatedAt": "2018-04-18T23:42:11.406Z",
        "deletedAt": "2018-04-18T23:42:11.406Z",
        "token": "d1!E2GVHgpr4h9bpxxtqUJ7EVJ1Q$Dusm2RBXg8XyVJMCBCbvyE8cGacxUx3bcUT",
        "projectId": 1
        }

        Args:
            projectId (int): The ID of the project on ODK Central
            name (str): The name of the XForm

        Returns:
            (dict): The response JSON from ODK Central
        """
        url = f"{self.base}projects/{projectId}/app-users"
        response = self.session.post(url, json={"displayName": name}, verify=self.verify)
        self.user = name
        if response.ok:
            return response.json()
        return {}

    def delete(
        self,
        projectId: int,
        userId: int,
    ):
        """Create a new app-user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            userId (int): The ID of the user on ODK Central to delete

        Returns:
            (bool): Whether the user got deleted or not
        """
        url = f"{self.base}projects/{projectId}/app-users/{userId}"
        result = self.session.delete(url, verify=self.verify)
        return result

    def updateRole(
        self,
        projectId: int,
        xform: str,
        roleId: int = 2,
        actorId: Optional[int] = None,
    ):
        """Update the role of an app user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            roleId (int): The role for the user
            actorId (int): The ID of the user

        Returns:
            (bool): Whether it was update or not
        """
        log.info("Update access to XForm %s for %s" % (xform, actorId))
        url = f"{self.base}projects/{projectId}/forms/{xform}/assignments/{roleId}/{actorId}"
        result = self.session.post(url, verify=self.verify)
        return result

    def grantAccess(self, projectId: int, roleId: int = 2, userId: int = None, xform: str = None, actorId: int = None):
        """Grant access to an app user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            roleId (int): The role ID
            userId (int): The user ID of the user on ODK Central
            xform (str):  The XForm to get the details of from ODK Central
            actorId (int): The actor ID of the user on ODK Central

        Returns:
            (bool): Whether access was granted or not
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/assignments/{roleId}/{actorId}"
        result = self.session.post(url, verify=self.verify)
        return result

    def createQRCode(
        self,
        odk_id: int,
        project_name: str,
        appuser_token: str,
        basemap: str = "osm",
        osm_username: str = "svchotosm",
        upstream_task_id: str = "",
        save_qrcode: bool = False,
    ) -> segno.QRCode:
        """Get the QR Code for an app-user.

        Notes on QR code params:

        - form_update_mode: 'manual' allows for easier offline mapping, while
            if set to 'match_exactly', it will attempt sync with Central

        - metadata_email: we 'misuse' this field to add additional metadata,
            in this case a task id from an upstream application (FMTM).

        Args:
            odk_id (int): The ID of the project on ODK Central
            project_name (str): The name of the project to set
            appuser_token (str): The user's token
            basemap (str): Default basemap to use on Collect.
                Options: "google", "mapbox", "osm", "usgs", "stamen", "carto".
            osm_username (str): The OSM username to attribute to the mapping.
            save_qrcode (bool): Save the generated QR code to disk.

        Returns:
            segno.QRCode: The new QR code object
        """
        log.info(f"Generating QR Code for project ({odk_id}) {project_name}")

        self.settings = {
            "general": {
                "server_url": f"{self.base}key/{appuser_token}/projects/{odk_id}",
                "form_update_mode": "manual",
                "basemap_source": basemap,
                "autosend": "wifi_and_cellular",
                "metadata_username": osm_username,
                "metadata_email": upstream_task_id,
            },
            "project": {"name": f"{project_name}"},
            "admin": {},
        }

        # Base64 encode JSON params for QR code
        qr_data = b64encode(zlib.compress(json.dumps(self.settings).encode("utf-8")))
        # Generate QR code
        self.qrcode = segno.make(qr_data, micro=False)

        if save_qrcode:
            log.debug(f"Saving QR code to {project_name}.png")
            self.qrcode.save(f"{project_name}.png", scale=5)

        return self.qrcode


class OdkDataset(OdkCentral):
    """Class to manipulate a Entity on an ODK Central server."""

    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central.

        Returns:
            (OdkDataset): An instance of this object.
        """
        super().__init__(url, user, passwd)
        self.name = None

    def listDatasets(
        self,
        projectId: int,
    ):
        """Get all Entity datasets (entity lists) for a project.

        JSON response:
        [
            {
                "name": "people",
                "createdAt": "2018-01-19T23:58:03.395Z",
                "projectId": 1,
                "approvalRequired": true
            }
        ]

        Args:
            projectId (int): The ID of the project on ODK Central.

        Returns:
            list: a list of JSON dataset metadata.
        """
        url = f"{self.base}projects/{projectId}/datasets/"
        result = self.session.get(url, verify=self.verify)
        return result.json()

    # TODO add createDataset

    def listEntities(
        self,
        projectId: int,
        datasetName: str,
    ):
        """Get all Entities for a project dataset (entity list).

        JSON format:
        [
        {
            "uuid": "uuid:85cb9aff-005e-4edd-9739-dc9c1a829c44",
            "createdAt": "2018-01-19T23:58:03.395Z",
            "updatedAt": "2018-03-21T12:45:02.312Z",
            "deletedAt": "2018-03-21T12:45:02.312Z",
            "creatorId": 1,
            "currentVersion": {
            "label": "John (88)",
            "current": true,
            "createdAt": "2018-03-21T12:45:02.312Z",
            "creatorId": 1,
            "userAgent": "Enketo/3.0.4",
            "version": 1,
            "baseVersion": null,
            "conflictingProperties": null
            }
        }
        ]

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (str): The name of a dataset, specific to a project.

        Returns:
            list: a list of JSON entity metadata, for a dataset.
        """
        url = f"{self.base}projects/{projectId}/datasets/{datasetName}/entities"
        response = self.session.get(url, verify=self.verify)
        return response.json()

    def createEntity(
        self,
        projectId: int,
        datasetName: str,
        label: str,
        data: dict,
    ) -> dict:
        """Create a new Entity in a project dataset (entity list).

        JSON request:
        {
        "uuid": "54a405a0-53ce-4748-9788-d23a30cc3afa",
        "label": "John Doe (88)",
        "data": {
            "firstName": "John",
            "age": "88"
        }
        }

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (int): The name of a dataset, specific to a project.
            label (str): Label for the Entity.
            data (dict): Key:Value pairs to insert as Entity data.

        Returns:
            dict: JSON of entity details.
                The 'uuid' field includes the unique entity identifier.
        """
        # The CSV must contain a geometry field to work
        # TODO also add this validation to uploadMedia if CSV format
        required_fields = ["geometry"]
        if not all(key in data for key in required_fields):
            msg = "'geometry' data field is mandatory"
            log.debug(msg)
            raise ValueError(msg)

        url = f"{self.base}projects/{projectId}/datasets/{datasetName}/entities"
        response = self.session.post(
            url,
            verify=self.verify,
            json={
                "uuid": str(uuid4()),
                "label": label,
                "data": data,
            },
        )
        if not response.ok:
            if response.status_code == 404:
                msg = f"Does not exist: project ({projectId}) dataset ({datasetName})"
                log.debug(msg)
                raise requests.exceptions.HTTPError(msg)
            if response.status_code == 400:
                msg = response.json().get("message")
                log.debug(msg)
                raise requests.exceptions.HTTPError(msg)
            log.debug(f"Failed to create Entity. Status code: {response.status_code}")
            response.raise_for_status()
        return response.json()

    def updateEntity(
        self,
        projectId: int,
        datasetName: str,
        entityUuid: str,
        label: Optional[str] = None,
        data: Optional[dict] = None,
        newVersion: Optional[int] = None,
    ):
        """Update an existing Entity in a project dataset (entity list).

        The JSON request format is the same as creating, minus the 'uuid' field.
        The PATCH will only update the specific fields specified, leaving the
            remainder.

        If no 'newVersion' param is provided, the entity will be force updated
            in place.
        If 'newVersion' is provided, this must be a single integer increment
            from the current version.

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (int): The name of a dataset, specific to a project.
            entityUuid (str): Unique itentifier of the entity.
            label (str): Label for the Entity.
            data (dict): Key:Value pairs to insert as Entity data.
            newVersion (int): Integer version to increment to (current version + 1).

        Returns:
            dict: JSON of entity details.
                The 'uuid' field includes the unique entity identifier.
        """
        if not label and not data:
            msg = "One of either the 'label' or 'data' fields must be passed"
            log.debug(msg)
            raise requests.exceptions.HTTPError(msg)

        json_data = {}
        if data:
            json_data["data"] = data
        if label:
            json_data["label"] = label

        url = f"{self.base}projects/{projectId}/datasets/{datasetName}/entities/{entityUuid}"
        if newVersion:
            url = f"{url}?baseVersion={newVersion - 1}"
        else:
            url = f"{url}?force=true"

        log.debug(f"Calling {url} with params {json_data}")
        response = self.session.patch(
            url,
            verify=self.verify,
            json=json_data,
        )
        if not response.ok:
            if response.status_code == 404:
                msg = f"Does not exist: project ({projectId}) dataset ({datasetName})"
                log.debug(msg)
                raise requests.exceptions.HTTPError(msg)
            if response.status_code == 400:
                msg = response.json().get("message")
                log.debug(msg)
                raise requests.exceptions.HTTPError(msg)
            if response.status_code == 409:
                msg = response.json().get("message")
                log.debug(msg)
                raise requests.exceptions.HTTPError(msg)
            log.debug(f"Failed to create Entity. Status code: {response.status_code}")
            response.raise_for_status()
        return response.json()

    def deleteEntity(
        self,
        projectId: int,
        datasetName: str,
        entityUuid: str,
    ):
        """Delete an Entity in a project dataset (entity list).

        Only performs a soft deletion, so the Entity is actually archived.

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (int): The name of a dataset, specific to a project.
            entityUuid (str): Unique itentifier of the entity.

        Returns:
            bool: Deletion successful or not.
        """
        url = f"{self.base}projects/{projectId}/datasets/{datasetName}/entities/{entityUuid}"
        log.debug(f"Deleting dataset ({datasetName}) entity UUID ({entityUuid})")
        response = self.session.delete(url, verify=self.verify)

        if not response.ok:
            if response.status_code == 404:
                msg = f"Does not exist: project ({projectId}) dataset ({datasetName}) entity ({entityUuid})"
                log.debug(msg)
                raise requests.exceptions.HTTPError(msg)
            log.debug(f"Failed to delete Entity. Status code: {response.status_code}")
            response.raise_for_status()

        success = (response_msg := response.json()).get("success", False)

        if not success:
            log.debug(f"Server returned deletion unsuccessful: {response_msg}")

        return success

    def getEntityData(
        self,
        projectId: int,
        datasetName: str,
    ):
        """Get a lightweight JSON of the entity data fields in a dataset.

        Example response JSON:
        [
        {
            "0": {
                "__id": "523699d0-66ec-4cfc-a76b-4617c01c6b92",
                "label": "the_label_you_defined",
                "__system": {
                    "createdAt": "2024-03-24T06:30:31.219Z",
                    "creatorId": "7",
                    "creatorName": "fmtm@hotosm.org",
                    "updates": 4,
                    "updatedAt": "2024-03-24T07:12:55.871Z",
                    "version": 5,
                    "conflict": null
                },
                "geometry": "javarosa format geometry",
                "user_defined_field2": "text",
                "user_defined_field2": "text",
                "user_defined_field3": "test"
            }
        }
        ]

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (int): The name of a dataset, specific to a project.

        Returns:
            list: All entity data for a project dataset.
        """
        url = f"{self.base}projects/{projectId}/datasets/{datasetName}.svc/Entities"
        response = self.session.get(url, verify=self.verify)

        if not response.ok:
            if response.status_code == 404:
                msg = f"Does not exist: project ({projectId}) dataset ({datasetName})"
                log.debug(msg)
                raise requests.exceptions.HTTPError(msg)
            log.debug(f"Failed to get Entity data. Status code: {response.status_code}")
            response.raise_for_status()
        return response.json().get("value", {})


# This following code is only for debugging purposes, since this is easier
# to use a debugger with instead of pytest.
if __name__ == "__main__":
    """
    This main function lets this class be run standalone by a bash script
    for development purposes. To use it, try the odk_client program instead.
    """
    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s | %(funcName)s:%(lineno)d | %(message)s"),
        datefmt="%y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Gotta start somewhere...
    project = OdkProject()
    # Start the persistent HTTPS connection to the ODK Central server
    project.authenticate()
    # Get a list of all the projects on this ODK Central server
    project.listProjects()
    # List all the users on this ODK Central server
    project.listUsers()
    # List all the forms for this project. FIXME: don't hardcode the project ID
    project.listForms(4)
    # List all the app users for this project. FIXME: don't hardcode the project ID
    project.listAppUsers(4)
    # List all the submissions for this project. FIXME: don't hardcode the project ID ad form name
    # project.listSubmissions(4, "cemeteries")
    # project.getSubmission(4, "cemeteries")
    # Dump all the internal data
    project.dump()

    # Form management
    form = OdkForm()
    form.authenticate()
    x = form.getDetails(4, "cemeteries")
    # print(x.json())
    # x = form.listMedia(4, "waterpoints", 'uuid:fbe3ef41-6298-40c1-a694-6c9d25a8c476')
    # Make a new form
    # xml = "/home/rob/projects/HOT/osm_fieldwork.git/osm_fieldwork/xlsforms/cemeteries.xml"
    # form.addXMLForm(xml)
    # csv1 = "/home/rob/projects/HOT/osm_fieldwork.git/osm_fieldwork/xlsforms/municipality.csv"
    # csv2 = "/home/rob/projects/HOT/osm_fieldwork.git/osm_fieldwork/xlsforms/towns.csv"
    # form.addMedia(csv1)
    # form.addMedia(csv2)
    x = form.createForm(4, "cemeteries.xls", "cemeteries")
    print(x.json())
    # x = form.publish(4, 'cemeteries', "cemeteries.xls")
    print(x.json())
    x = form.uploadMedia(4, "cemeteries", "towns.csv")
    print(x.json())
    x = form.uploadMedia(4, "cemeteries", "municipality.csv")
    print(x.json())
    x = form.listMedia(4, "cemeteries")
    print(x.json())
    form.dump()
