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


import concurrent.futures
import json
import logging
import os
import sys
import zlib
from base64 import b64encode
from datetime import datetime

import requests
import segno
from codetiming import Timer
from cpuinfo import get_cpu_info
from requests.auth import HTTPBasicAuth

# Set log level for urllib
log_level = os.getenv("LOG_LEVEL", default="INFO")
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
        url: str = None,
        user: str = None,
        passwd: str = None,
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

        # Authentication data
        self.auth = HTTPBasicAuth(self.user, self.passwd)

        # Use a persistant connect, better for multiple requests
        self.session = requests.Session()

        # These are just cached data from the queries
        self.projects = dict()
        self.users = list()
        # The number of threads is based on the CPU cores
        info = get_cpu_info()
        self.cores = info["count"]

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
            (HTTPBasicAuth): A session to the ODK Central server
        """
        if not self.url:
            self.url = url
        if not self.user:
            self.user = user
        if not self.passwd:
            self.passwd = passwd
        # Enable persistent connection, create a cookie for this session
        self.session.headers.update({"accept": "odkcentral"})

        # Connect to the server
        return self.session.get(self.url, auth=self.auth, verify=self.verify)

    def listProjects(self):
        """Fetch a list of projects from an ODK Central server, and
        store it as an indexed list.

        Returns:
            (list): A list of projects on a ODK Central server
        """
        log.info("Getting a list of projects from %s" % self.url)
        url = f"{self.base}projects"
        result = self.session.get(url, auth=self.auth, verify=self.verify)
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
    ):
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
                result = self.session.post(url, auth=self.auth, json={"name": name}, verify=self.verify, timeout=4)
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
        self.session.delete(url, auth=self.auth, verify=self.verify)
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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
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
        url: str = None,
        user: str = None,
        passwd: str = None,
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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
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


class OdkForm(OdkCentral):
    """Class to manipulate a from on an ODK Central server."""

    def __init__(
        self,
        url: str = None,
        user: str = None,
        passwd: str = None,
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
    ):
        """Get all the details for a form on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The data for this XForm
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}"
        result = self.session.get(url, auth=self.auth, verify=self.verify)
        self.data = result.json()
        return result

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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
        return result.json()

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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
        return result.json()

    def listSubmissions(self, projectId: int, xform: str, filters: dict = None):
        """Fetch a list of submission instances for a given form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (list): The list of Submissions
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}.svc/Submissions"
        result = self.session.get(url, auth=self.auth, params=filters, verify=self.verify)
        if result.ok:
            self.submissions = result.json()
            return self.submissions["value"]
        else:
            return list()

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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
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
            (list): The lit of submissions
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
        result = self.session.get(url, auth=self.auth, headers=headers, verify=self.verify)
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
            return list()

    def getSubmissionMedia(
        self,
        projectId: int,
        xform: str,
    ):
        """Fetch a ZIP file of the submissions with media to a survey form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (list): The media file
        """
        url = self.base + f"projects/{projectId}/forms/{xform}/submissions.csv.zip"
        result = self.session.get(url, auth=self.auth, verify=self.verify)
        return result

    def addMedia(
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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
        self.media = result.json()
        return self.media

    def uploadMedia(
        self,
        projectId: int,
        xform: str,
        filespec: str,
        convert_to_draft: bool = True,
    ):
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
            result = self.session.post(url, auth=self.auth, verify=self.verify)
            if result.status_code == 200:
                log.debug(f"Modified {title} to draft")
            else:
                status = eval(result._content)
                log.error(f"Couldn't modify {title} to draft: {status['message']}")

        url = f"{self.base}projects/{projectId}/forms/{xid}/draft/attachments/{datafile}"
        headers = {"Content-Type": "*/*"}
        file = open(filespec, "rb")
        media = file.read()
        file.close()
        result = self.session.post(url, auth=self.auth, data=media, headers=headers, verify=self.verify)
        if result.status_code == 200:
            log.debug(f"Uploaded {filespec} to Central")
        else:
            status = eval(result._content)
            log.error(f"Couldn't upload {filespec} to Central: {status['message']}")

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
        result = self.session.get(url, auth=self.auth, verify=self.verify)
        if result.status_code == 200:
            log.debug(f"fetched {filename} from Central")
        else:
            status = eval(result._content)
            log.error(f"Couldn't fetch {filename} from Central: {status['message']}")
        self.media = result.content
        return self.media

    def createForm(
        self,
        projectId: int,
        xform: str,
        filespec: str,
        draft: bool = False,
    ):
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

        result = self.session.post(url, auth=self.auth, data=xml, headers=headers, verify=self.verify)
        # epdb.st()
        # FIXME: should update self.forms with the new form
        if result.status_code != 200:
            if result.status_code == 409:
                log.error(f"{xform} already exists on Central")
            else:
                status = eval(result._content)
                log.error(f"Couldn't create {xform} on Central: {status['message']}")

        return result.status_code

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
            url = f"{self.base}projects/{projectId}/forms/{xform}/draft"
        else:
            url = f"{self.base}projects/{projectId}/forms/{xform}"
        result = self.session.delete(url, auth=self.auth, verify=self.verify)
        return result

    def publishForm(
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
        result = self.session.post(url, auth=self.auth, verify=self.verify)
        if result.status_code != 200:
            status = eval(result._content)
            log.error(f"Couldn't publish {xform} on Central: {status['message']}")
        else:
            log.info(f"Published {xform} on Central.")
        return result.status_code

    def dump(self):
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
        url: (str) = None,
        user: str = None,
        passwd: (str) = None,
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

        Args:
            projectId (int): The ID of the project on ODK Central
            name (str): The name of the XForm

        Returns:
            (bool): Whether it was created or not
        """
        url = f"{self.base}projects/{projectId}/app-users"
        result = self.session.post(url, auth=self.auth, json={"displayName": name}, verify=self.verify)
        self.user = name
        return result

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
        result = self.session.delete(url, auth=self.auth, verify=self.verify)
        return result

    def updateRole(
        self,
        projectId: int,
        xform: str,
        roleId: int = 2,
        actorId: int = None,
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
        result = self.session.post(url, auth=self.auth, verify=self.verify)
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
        result = self.session.post(url, auth=self.auth, verify=self.verify)
        return result

    def createQRCode(
        self,
        project_id: int,
        token: str,
        name: str,
    ):
        """Get the QR Code for an app-user.

        Args:
            project_id (int): The ID of the project on ODK Central
            token (str): The user's token
            name (str): The name of the project

        Returns:
            (bytes): The new QR code
        """
        log.info('Generating QR Code for app-user "%s" for project %s' % (name, project_id))
        self.settings = {
            "general": {
                "server_url": f"{self.base}key/{token}/projects/{project_id}",
                "form_update_mode": "manual",
                "basemap_source": "MapBox",
                "autosend": "wifi_and_cellular",
            },
            "project": {"name": f"{name}"},
            "admin": {},
        }
        qr_data = b64encode(zlib.compress(json.dumps(self.settings).encode("utf-8")))
        self.qrcode = segno.make(qr_data, micro=False)
        self.qrcode.save(f"{name}.png", scale=5)
        return qr_data


# This following code is only for debugging purposes, since this is easier
# to use a debugger with instead of pytest.
if __name__ == "__main__":
    """
    This main function lets this class be run standalone by a bash script
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
    x = form.createForm(4, "cemeteries", "cemeteries.xls", True)
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
