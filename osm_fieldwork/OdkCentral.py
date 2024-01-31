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


import asyncio
import concurrent.futures
import json
import logging
import os
import sys
import zlib
from base64 import b64encode
from datetime import datetime
from typing import Optional

from aiohttp import ClientError, ClientResponse, ClientSession
from codetiming import Timer
from cpuinfo import get_cpu_info
from segno import QRCode
from segno import make as make_qrcode

# Set log level for urllib
log_level = os.getenv("LOG_LEVEL", default="INFO")
logging.getLogger("urllib3").setLevel(log_level)

log = logging.getLogger(__name__)


async def downloadThread(project_id: int, xforms: list, odk_credentials: dict, filters: dict = None):
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
        subs = await form.listSubmissions(project_id, task, filters)
        if type(subs) == dict:
            log.error(f"{subs['message']}, {subs['code']} ")
            continue
        # log.debug(f"There are {len(subs)} submissions for {task}")
        if len(subs) > 0:
            data += subs
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
            self.verify = eval(verify)
        else:
            self.verify = verify
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
        self.session = ClientSession(raise_for_status=True)

        # Authentication with session token
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.authenticate())

        # These are just cached data from the queries
        self.projects = dict()
        self.users = list()
        # The number of threads is based on the CPU cores
        info = get_cpu_info()
        self.cores = info["count"]

    async def authenticate(
        self,
        url: str = None,
        user: str = None,
        passwd: str = None,
    ) -> ClientResponse:
        """Setup authenticate to an ODK Central server.

        Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central

        Returns:
            (ClientResponse): A response from ODK Central after auth
        """
        if not self.url:
            self.url = url
        if not self.user:
            self.user = user
        if not self.passwd:
            self.passwd = passwd
        # Enable persistent connection, create a cookie for this session
        self.session.headers.update({"accept": "odkcentral"})

        # Get a session token
        async with self.session.post(
            f"{self.base}sessions",
            json={
                "email": self.user,
                "password": self.passwd,
            },
            verify_ssl=self.verify,
        ) as response:
            token = (await response.json()).get("token")

            self.session.headers.update({"Authorization": f"Bearer {token}"})

            # Connect to the server
            async with self.session.get(f"{self.base}projects", verify_ssl=self.verify) as response:
                return await response.json()

    async def listProjects(self):
        """Fetch a list of projects from an ODK Central server, and
        store it as an indexed list.

        Returns:
            (list): A list of projects on a ODK Central server
        """
        log.info("Getting a list of projects from %s" % self.url)
        url = f"{self.base}projects"

        async with self.session.get(url, verify_ssl=self.verify) as response:
            projects = await response.json()

        for project in projects:
            if isinstance(project, dict):
                if project.get("id") is not None:
                    self.projects[project["id"]] = project
            else:
                log.info("No projects returned. Is this a first run?")
        return projects

    async def createProject(
        self,
        name: str,
    ):
        """Create a new project on an ODK Central server if it doesn't
        already exist.

        Args:
            name (str): The name for the new project

        Returns:
            (json): The response from ODK Central
        """
        log.debug(f"Checking if project named {name} exists already")
        exists = await self.findProject(name=name)
        if exists:
            log.debug(f"Project named {name} already exists.")
            return exists
        else:
            project_json = {}
            url = f"{self.base}projects"
            log.debug(f"POSTing project {name} to {url} with verify={self.verify}")
            try:
                async with self.session.post(url, json={"name": name}, verify_ssl=self.verify, timeout=4) as response:
                    project_json = await response.json()
            except ClientError as e:
                log.error(e)
                log.error("Failed to submit to ODKCentral")
            log.debug(f"Returned: {project_json}")
            # update the internal list of projects
            await self.listProjects()
            return project_json

    async def deleteProject(
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
        self.session.delete(url, verify_ssl=self.verify)
        async with self.session.delete(url, verify_ssl=self.verify):
            log.info(f"Deleted ODK project {project_id}")
        # update the internal list of projects
        await self.listProjects()
        return await self.findProject(project_id=project_id)

    async def findProject(
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
        await self.listProjects()

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

    async def findAppUser(
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

    async def listUsers(self):
        """Fetch a list of users on the ODK Central server.

        Returns:
            (list): A list of users on ODK Central, not app-users
        """
        log.info("Getting a list of users from %s" % self.url)
        url = self.base + "users"
        async with self.session.get(url, verify_ssl=self.verify) as response:
            self.users = await response.json()
        return self.users

    async def dump(self):
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
        self.appusers = list()
        self.id = None

    async def getData(
        self,
        keyword: str,
    ):
        """Args:
            keyword (str): The keyword to search for.

        Returns:
            (json): The data for the keyword
        """
        return self.data[keyword]

    async def listForms(self, project_id: int, metadata: bool = False):
        """Fetch a list of forms in a project on an ODK Central server.

        Args:
            project_id (int): The ID of the project on ODK Central

        Returns:
            (list): The list of XForms in this project
        """
        url = f"{self.base}projects/{project_id}/forms"
        if metadata:
            self.session.headers.update({"X-Extended-Metadata": "true"})
        async with self.session.get(url, verify_ssl=self.verify) as response:
            self.forms = await response.json()
        return self.forms

    async def getAllSubmissions(self, project_id: int, xforms: list = None, filters: dict = None):
        """Fetch a list of submissions in a project on an ODK Central server.

        Args:
            project_id (int): The ID of the project on ODK Central
            xforms (list): The list of XForms to get the submissions of

        Returns:
            (json): All of the submissions for all of the XForm in a project
        """
        timer = Timer(text="getAllSubmissions() took {seconds:.0f}s")
        timer.start()
        if not xforms:
            xforms_data = await self.listForms(project_id)
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

    async def listAppUsers(
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            self.appusers = await response.json()
        return self.appusers

    async def listAssignments(
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            return await response.json()

    async def getDetails(
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            self.data = await response.json()
        return self.data

    async def getFullDetails(
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            return await response.json()

    async def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        await super().dump()
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


class OdkForm(OdkCentral):
    """Class to manipulate a from on an ODK Central server."""

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
        self.draft = True
        # this is only populated if self.getDetails() is called first.
        self.data = dict()
        self.attach = list()
        self.publish = True
        self.media = list()
        self.xml = None
        self.submissions = list()
        self.appusers = dict()
        # self.xmlFormId = None
        # self.projectId = None

    # async def getName(self):
    #     """
    #     Extract the name from a form on an ODK Central server
    #
    #     Returns:
    #     """
    #     if "name" in self.data:
    #         return self.data["name"]
    #     else:
    #         log.warning("Execute OdkForm.getDetails() to get this data.")

    # async def getFormId(self):
    #     """Extract the xmlFormId from a form on an ODK Central server"""
    #     if "xmlFormId" in self.data:
    #         return self.data["xmlFormId"]
    #     else:
    #         log.warning("Execute OdkForm.getDetails() to get this data.")

    async def getDetails(
        self,
        projectId: int,
        xform: str,
    ):
        """Get all the details for a form on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The data for this XForm
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}"
        async with self.session.get(url, verify_ssl=self.verify) as response:
            self.data = await response.json()
        return self.data

    async def getFullDetails(
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            return await response.json()

    async def listSubmissionBasicInfo(
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            return await response.json()

    async def listSubmissions(self, projectId: int, xform: str, filters: dict = None):
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

        async with self.session.get(url, params=filters, verify_ssl=self.verify) as response:
            if response.ok:
                self.submissions = await response.json()
                return self.submissions

        return {}

    async def listAssignments(
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            return await response.json()

    async def getSubmissions(
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
        headers = {"Content-Type": "application/json"}
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
        async with self.session.get(url, headers=headers, verify_ssl=self.verify) as response:
            if response.status == 200:
                content = await response.read()
                if disk:
                    # id = self.forms[0]['xmlFormId']
                    try:
                        file = open(filespec, "xb")
                        file.write(content)
                    except FileExistsError:
                        file = open(filespec, "wb")
                        file.write(content)
                    log.info("Wrote output file %s" % filespec)
                    file.close()
                return content
            else:
                log.error(f"Submissions for {projectId}, Form {xform}" + " doesn't exist")
                return bytes()

    async def getSubmissionMedia(
        self,
        projectId: int,
        xform: str,
    ) -> bytes:
        """Fetch a ZIP file of the submissions with media to a survey form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (list): The media file
        """
        url = self.base + f"projects/{projectId}/forms/{xform}/submissions.csv.zip"
        async with self.session.get(url, verify_ssl=self.verify) as response:
            return await response.read()

    async def addMedia(
        self,
        media: str,
        filespec: str,
    ):
        """Add a data file to this form.

        Args:
            media (str): The media file
            filespec (str): the name of the media
        """
        # FIXME: this also needs the data
        self.media[filespec] = media

    async def addXMLForm(
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

    async def listMedia(
        self,
        projectId: int,
        xform: str,
    ) -> bytes:
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            self.media = await response.read()
        return self.media

    async def uploadMedia(
        self,
        projectId: int,
        xform: str,
        filespec: str,
        convert_to_draft: bool = True,
    ) -> dict:
        """Upload an attachement to the ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            filespec (str): The filespec of the media file
            convert_to_draft (bool): Whether to convert a published XForm to draft
        """
        title = os.path.basename(os.path.splitext(filespec)[0])
        datafile = f"{title}.geojson"
        xid = xform.split("_")[2]

        if convert_to_draft:
            url = f"{self.base}projects/{projectId}/forms/{xid}/draft"

            async with self.session.post(url, verify_ssl=self.verify) as response:
                if response.status == 200:
                    log.debug(f"Modified {title} to draft")
                else:
                    content = await response.json()
                    log.error(f"Couldn't modify {title} to draft: {content.get('message')}")

        url = f"{self.base}projects/{projectId}/forms/{xid}/draft/attachments/{datafile}"
        headers = {"Content-Type": "*/*"}
        file = open(filespec, "rb")
        media = file.read()
        file.close()
        async with self.session.post(url, data=media, headers=headers, verify_ssl=self.verify) as response:
            content = await response.json()
            if response.status == 200:
                log.debug(f"Uploaded {filespec} to Central")
            else:
                log.error(f"Couldn't upload {filespec} to Central: {content.get('message')}")
            return content

    async def getMedia(
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
        async with self.session.get(url, verify_ssl=self.verify) as response:
            content = await response.json()
            if response.status == 200:
                log.debug(f"fetched {filename} from Central")
            else:
                log.error(f"Couldn't fetch {filename} from Central: {content.get('message')}")
            self.media = content
            return self.media

    async def createForm(
        self,
        projectId: int,
        xform: str,
        filespec: str,
        draft: bool = False,
    ) -> int:
        """Create a new form on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            filespec (str): The name of the attachment for the XForm on ODK Central
            draft (bool): Whether to create the XForm in draft or published

        Returns:
            (int): The status code from ODK Central
        """
        if draft is not None:
            self.draft = draft
        headers = {"Content-Type": "application/xml"}
        if self.draft:
            url = f"{self.base}projects/{projectId}/forms/{xform}/draft?ignoreWarnings=true&publish=false"
        else:
            url = f"{self.base}projects/{projectId}/forms?ignoreWarnings=true&publish=true"

        # Read the XML or XLS file
        file = open(filespec, "rb")
        xml = file.read()
        file.close()
        log.info("Read %d bytes from %s" % (len(xml), filespec))

        async with self.session.post(url, data=xml, headers=headers, verify_ssl=self.verify) as response:
            # epdb.st()
            # FIXME: should update self.forms with the new form
            content = await response.json()
            if response.status != 200:
                if response.status == 409:
                    log.error(f"{xform} already exists on Central")
                else:
                    log.error(f"Couldn't create {xform} on Central: {content.get('message')}")

            return response.status

    async def deleteForm(
        self,
        projectId: int,
        xform: str,
    ) -> dict:
        """Delete a form from an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
        Returns:
            (dict): Response JSON.
        """
        # FIXME: If your goal is to prevent it from showing up on survey clients like ODK Collect, consider
        # setting its state to closing or closed
        if self.draft:
            url = f"{self.base}projects/{projectId}/forms/{xform}/draft"
        else:
            url = f"{self.base}projects/{projectId}/forms/{xform}"
        async with self.session.delete(url, verify_ssl=self.verify) as response:
            log.info(f"Deleted form ({xform}) from project ({projectId})")
        return await response.json()

    async def publishForm(
        self,
        projectId: int,
        xform: str,
    ):
        """Publish a draft form. When creating a form that isn't a draft, it can get publised then.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (int): The staus code from ODK Central
        """
        version = datetime.now().strftime("%Y-%m-%dT%TZ")
        if xform.find("_") > 0:
            xid = xform.split("_")[2]
        else:
            xid = xform

        url = f"{self.base}projects/{projectId}/forms/{xid}/draft/publish?version={version}"
        async with self.session.post(url, verify_ssl=self.verify) as response:
            content = await response.json()
            if response.status != 200:
                log.error(f"Couldn't publish {xform} on Central: {content.get('message')}")
            else:
                log.info(f"Published {xform} on Central.")
            return response.status

    async def form_fields(self, projectId: int, xform: str):
        """Retrieves the form fields for a xform from odk central.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            dict: A json object containing the form fields.

        """
        if xform.find("_") > 0:
            xid = xform.split("_")[2]
        else:
            xid = xform

        url = f"{self.base}projects/{projectId}/forms/{xid}/fields?odata=true"
        async with self.session.get(url, verify_ssl=self.verify) as response:
            return await response.json()

    async def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        # super().dump()
        entries = len(self.media)
        print("Form has %d attachments" % entries)
        for form in self.media:
            if "name" in form:
                print("Name: %s" % form["name"])


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

    async def create(
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
        async with self.session.post(url, json={"displayName": name}, verify_ssl=self.verify) as response:
            if response.status == 200:
                self.user = name
                return await response.json()
        return {}

    async def delete(
        self,
        projectId: int,
        userId: int,
    ) -> dict:
        """Delete an app user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            userId (int): The ID of the user on ODK Central to delete

        Returns:
            (dict): JSON response with success key
        """
        url = f"{self.base}projects/{projectId}/app-users/{userId}"
        async with self.session.delete(url, verify_ssl=self.verify) as response:
            log.info(f"Deleted appuser ({userId}) for project ({projectId})")
            return await response.json()

    async def updateRole(
        self,
        projectId: int,
        xform: str,
        roleId: int = 2,
        actorId: Optional[int] = None,
    ) -> dict:
        """Update the role of an app user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            roleId (int): The role for the user
            actorId (int): The ID of the user

        Returns:
            (dict): JSON response with success key
        """
        log.info("Update access to XForm %s for %s" % (xform, actorId))
        url = f"{self.base}projects/{projectId}/forms/{xform}/assignments/{roleId}/{actorId}"
        async with self.session.post(url, verify_ssl=self.verify) as response:
            return await response.json()

    async def grantAccess(self, projectId: int, roleId: int = 2, userId: int = None, xform: str = None, actorId: int = None):
        """Grant access to an app user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            roleId (int): The role ID
            userId (int): The user ID of the user on ODK Central
            xform (str):  The XForm to get the details of from ODK Central
            actorId (int): The actor ID of the user on ODK Central

        Returns:
            (dict): JSON response with success key
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/assignments/{roleId}/{actorId}"
        async with self.session.post(url, verify_ssl=self.verify) as response:
            return await response.json()

    async def createQRCode(
        self,
        odk_id: int,
        project_name: str,
        appuser_token: str,
        basemap: str = "osm",
        osm_username: str = "svchotosm",
        upstream_task_id: str = "",
        save_qrcode: bool = False,
    ) -> QRCode:
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
            QRCode: The new QR code object
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
        self.qrcode = make_qrcode(qr_data, micro=False)

        if save_qrcode:
            log.debug(f"Saving QR code to {project_name}.png")
            self.qrcode.save(f"{project_name}.png", scale=5)

        return self.qrcode


# This following code is only for debugging purposes, since this is easier
# to use a debugger with instead of pytest.
async def main():
    """This main function lets this class be run standalone by a bash script
    for development purposes. To use it, try the odk_client program instead.
    """
    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s.%(msecs)03d [%(levelname)s] " "%(name)s | %(funcName)s:%(lineno)d | %(message)s"),
        datefmt="%y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Gotta start somewhere...
    project = OdkProject()
    # Get a list of all the projects on this ODK Central server
    await project.listProjects()
    # List all the users on this ODK Central server
    await project.listUsers()
    # List all the forms for this project. FIXME: don't hardcode the project ID
    await project.listForms(4)
    # List all the app users for this project. FIXME: don't hardcode the project ID
    await project.listAppUsers(4)
    # List all the submissions for this project. FIXME: don't hardcode the project ID ad form name
    # project.listSubmissions(4, "cemeteries")
    # project.getSubmission(4, "cemeteries")
    # Dump all the internal data
    await project.dump()

    # Form management
    form = OdkForm()
    x = await form.getDetails(4, "cemeteries")
    # print(x.json())
    # x = form.listMedia(4, "waterpoints", 'uuid:fbe3ef41-6298-40c1-a694-6c9d25a8c476')
    # Make a new form
    # xml = "/home/rob/projects/HOT/osm_fieldwork.git/osm_fieldwork/xlsforms/cemeteries.xml"
    # form.addXMLForm(xml)
    # csv1 = "/home/rob/projects/HOT/osm_fieldwork.git/osm_fieldwork/xlsforms/municipality.csv"
    # csv2 = "/home/rob/projects/HOT/osm_fieldwork.git/osm_fieldwork/xlsforms/towns.csv"
    # form.addMedia(csv1)
    # form.addMedia(csv2)
    x = await form.createForm(4, "cemeteries", "cemeteries.xls", True)
    print(x)
    # x = form.publish(4, 'cemeteries', "cemeteries.xls")
    x = await form.uploadMedia(4, "cemeteries", "towns.csv")
    print(x)
    x = await form.uploadMedia(4, "cemeteries", "municipality.csv")
    print(x)
    x = await form.listMedia(4, "cemeteries")
    print(x)
    await form.dump()


if __name__ == "__main__":
    asyncio.run(main())
