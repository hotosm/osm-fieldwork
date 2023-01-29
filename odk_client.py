#!/bin/python3

# Copyright (c) 2022 Humanitarian OpenStreetMap Team
#
#     This program is free software: you can redistribute it and/or modify
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

import logging
import epdb
import argparse
import sys, os
from datetime import tzinfo, datetime
import json
from OdkCentral import OdkCentral, OdkProject, OdkForm, OdkAppUser
from pathlib import Path
from pyodk.client import Client
import csv


class OdkClient(object):
    def __init__(self, id=None, name=None):
        """A Class for higher-level client side access to ODK Central"""
        self.id = id
        self.projects = dict()
        self.keys = dict()
        self.forms = list()
        if id:
            self.id = id
            self.client = Client(project_id=int(id))
            self.getForms(id)
        else:
            self.client = Client()
            self.id = self.client.config.central.default_project_id
        self.client.open()
        self.getProjects()
        self.submissions = list()

    def readCache(self, cache=".odkcentral"):
        """Read the cached submissions data, for debugging only!"""
        if os.path.exists(cache) and os.path.getsize(cache) > 0:
            file = open(cache, "rb")
            data = file.read()
            self.submissions = json.loads(data)
            file.close()
            logging.debug(f"Reading submissions cache from {cache}")
        return self.submissions

    def writeCache(self):
        """Cache submissions on disk, only used for debugging!"""
        cache = ".odkcentral"
        try:
            file = open(cache, "xb")
        except FileExistsError:
            file = open(cache, "wb")
        data = json.dumps(self.submissions, indent=0)
        file.write(bytes(data, encoding='utf8'))
        logging.info(f"Wrote to config file {cache}")
        file.close()

    def getProject(self, project_id=None):
        """Return the current project info"""
        if project_id:
            return self.projects[project_id]
        else:
            if self.id:
                return self.projects[self.id]
        return None

    def getProjects(self):
        """Query the Central server for a list of projects"""
        if len(self.projects) > 0:
            return self.projects()
        projects = self.client.projects.list()
        self.projects = dict()
        self.keys = dict()
        for project in projects:
            self.projects[project.dict()['id']] = project.dict()
        self.keys = list(projects[0].dict().keys())

    def getForms(self):
        """Query the Central server for a list of xforms for a project"""
        self.forms = self.client.forms.list()
        return self.forms

    def getSubmissions(self):
        """Query the Central server for the submissions of a XForm"""
        cache = self.readCache()
        if len(cache) > 0:
            self.submissions = cache
        else:
            for form in self.forms:
                # comments = self.client.submissions.list_comments(form_id=form.xmlFormId, instance_id="uuid:...")
                sub = self.client.submissions.list(form_id=form.xmlFormId, project_id=form.projectId)
                if len(sub) > 0:
                    for entry in sub:
                        data = self.client.submissions.get_table(form_id=form.xmlFormId)
                        self.submissions.append(data)
            self.writeCache()
            return self.submissions

    def makeCSV(self, filespec=None):
        data = list()
        if len(self.submissions) > 0:
            ignore = ['__id', 'start', 'end', 'today', 'phonenumber', 'deviceid', 'username', 'email', 'warmup', 'meta', '__system']
            keywords = list()
            for data in self.submissions:
                item = data['value'][0]
                keys = list(item.keys())
                for key in keys:
                    if not key in ignore:
                        # print(f"{key} = \t{item[key]}")
                        keywords += list(item[key].keys())
                # print(keywords)
            return data
        with open(filespec, 'w', newline='') as csvfile:
            csv = csv.DictWriter(csvfile, dialect='excel',fieldnames=keywords)
            csv.writeheader()
            for row in rows:
                csv.writerow(row)
        print("Wrote: %s" % filespec)

    def dump(self):
        """Dump internal data structuresm only for debugging by developers!"""
        for keyword in self.projects.keys():
            info = self.projects[keyword]
            for key, value in info.items():
                if value:
                    print(f"\t{key} = \"{value}\"")
            print("--------------------------")

        for form in self.forms:
            print(f"ID = {form.xmlFormId}, name = \"{form.name}\", hash = {form.hash}")
            print(f"There are {len(self.submissions)} submissions for XForm {form.xmlFormId}")
        # ignore = ['__id', 'start', 'end', 'today', 'phonenumber', 'deviceid', 'username', 'email', 'warmup', 'meta', '__system']
        # keywords = list()
        # for data in self.submissions:
        #     item = data['value'][0]
        #     keys = list(item.keys())
        #     for key in keys:
        #         if not key in ignore:
        #             print(f"{key} = \t{item[key]}")
        #             keywords += list(item[key].keys())
        #     print(keywords)

    def close(self):
        return self.client.close()

#
# The main entry point
#
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='command line client for ODK Central')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    # This is for server requests
    parser.add_argument("-s", "--server", choices=['projects', 'users'],
                        help="project operations")
    # This is for project specific requests
    parser.add_argument("-p", "--project", choices=['forms', 'app-users', 'assignments'],
                        help="project operations")
    parser.add_argument('-i', '--id', type=int, help = 'Project ID nunmber')
    parser.add_argument("-f", "--form", help="XForm name")
    parser.add_argument("-u", "--uuid", help="Submission UUID, needed to download the data")
    # This is for form specific requests
    parser.add_argument('-x', '--xform', choices=['attachments', "csv", 'submissions', 'upload', 'download', 'create', 'assignments', 'delete', 'publish'],
                        help = 'XForm ID for operations with data files')
    parser.add_argument("-a", "--appuser", choices=['create', 'delete', 'update', 'qrcode', 'access'], help="App-User operations")
    parser.add_argument("-d", "--data", help="Data files for upload or download")
    parser.add_argument("-t", "--timestamp", help="Timestamp for submissions")
    parser.add_argument("-b", "--bulk", choices=['qrcodes', 'update'], help="Bulk operations")

    # Caching isn't implemented yet. That's for fancier queries that require multiple
    # requests to the ODK server. Caching allows for data like names for IDs to
    # be more user friendly.
    # parser.add_argument('-c', '--cache', action="store_true", help = 'cache data from ODK Central')
    # For now read these from the $HOME/.odkcentral config file
    # parser.add_argument('-u', '--user', help = 'ODK Central username (usually email)')
    # parser.add_argument('-pw', '--password', help = 'ODK Central password')

    # parser.add_argument("-d", "--download", choices=['xml', 'xlsx', 'attach', 'submit', 'zip'], help="Download files from ODK Central")
    # parser.add_argument("-u", "--upload", choices=['xml', 'xlsx', 'attach', 'submit', 'zip'], help="Upload files to ODK Central")

    # Any files we want to use are specified on the command line with an argument.
    # Multiple files are stored in a list.
    args, unknown = parser.parse_known_args()

    # if verbose, dump to the terminal. Not that this enables logging output from
    # from any imported module, which is usewful for debugging, but may be a huge
    # amount of data.
    if args.verbose is not None and args.verbose:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
    
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

    files = list()
    if unknown:
        parser.print_help()
        # quit()

    odk = OdkClient(args.id)
    projects = odk.getProject()
    xforms = odk.getForms()
    submissions = odk.getSubmissions()
    odk.dump()
    outfile = odk.makeCSV('test.csv')
    odk.close()

# # Get any files for upload or download

# # Commands to the ODK Central server, which gets data that applies
# # to all projects on the server.
# if args.server:
#     central = OdkCentral()
#     # central.authenticate()
#     if args.server == "projects":
#         projects = central.listProjects()
#         print("There are %d projects on this ODK Central server" % len(projects))
#         ordered = sorted(projects, key=lambda item: item.get('id'))
#         for project in ordered:
#             print("\t%s: %s" % (project['id'], project['name']))
#     elif args.server == "users":
#         users = central.listUsers()
#         logging.info("There are %d users on this ODK Central server" % len(users))
#         ordered = sorted(users, key=lambda item: item.get('id'))
#         for user in ordered:
#             print("%s: %s (%s)" % (user['id'], user['displayName'], user['email']))

# # Commands to get data about a specific project on an ODK Central server.
# elif args.project:
#     project = OdkProject()
#     # project.authenticate()
#     if not args.id:
#         print("Need to specify a project ID using \"--id\"!")
#         print("You can use \"odk_client.-py --server projects\" to list all the projects!")
#         # parser.print_help()
#         quit()
#     if args.project == "forms":
#         forms = project.listForms(args.id)
#         ordered = sorted(forms, key=lambda item: item.get('xmlFormId'))
#         for form in ordered:
#             print("\t%r: %r" % (form['xmlFormId'], form['name']))
#     # if args.project == "submissions":
#     #     submit = project.listSubmissions(args.id, args.form)
#     #     # ordered = sorted(submit, key=lambda item: item.get('xmlFormId'))
#     #     for data in submit:
#     #         print("\t%s by user %s" % (data['instanceId'], data['submitterId']))
#     if args.project == "app-users":
#         users = project.listAppUsers(args.id)
#         logging.info("There are %d app users on this ODK Central server" % len(users))
#         ordered = sorted(users, key=lambda item: item.get('id'))
#         for user in ordered:
#             print("\t%r: %s (%s)" % (user['id'], user['displayName'], user['token']))
#     if args.project == "assignments":
#         assign = project.listAssignments(args.id)
#         logging.info("There are %d assignments  on this ODK Central server" % len(assign))
#         ordered = sorted(assign, key=lambda item: item.get('id'))
#         for role in ordered:
#             print("\t%r" % role)

# elif args.xform:
# # This downloads files from the ODK server
#     print("XForm ops %r" % files)
#     if not args.id:
#         print("Need to specify a project ID using \"--id\" and an XForm id using \"--\"!")
#         quit()
#     if not args.form:
#         print("Need to specify a XForm id using \"--form\"!")
#         quit()

#     form = OdkForm()
#     # form.authenticate()
#     # Note that uploading and downloading is only for the attachments, usually
#     # a CSV or GeoJson file used by the Form as an external data source for
#     # survey questions
#     if args.xform == "upload":
#         for file in files:
#             logging.info("Uploading file %r for XForm %s" % (file, args.form))
#             result = form.uploadMedia(args.id, args.form, file)

#     elif args.xform == "download":
#         logging.info("Downloading files %r for XForm %s" % (files, args.form))
#         for file in files:
#             logging.info("Downloading %r for XForm %s" % (file, args.form))
#             data = form.getMedia(args.id, args.form, file)
#             try:
#                 file = open(file, "xb")
#             except FileExistsError:
#                 file = open(file, "wb")
#             file.write(data)
#             file.close()
#     elif args.xform == "assignments":
#         assign = form.listAssignments(args.id, args.form)
#         logging.info("There are %d assignments  on this ODK Central server" % len(assign))
#         # ordered = sorted(assign, key=lambda item: item.get('id'))
#         for role in assign:
#             print("\t%r" % role)
#     elif args.xform == "submissions":
#         submissions = form.listSubmissions(args.id, args.form)
#         logging.info("There are %d submissions for XForm %s" % (len(submissions), args.form))
#         for file in submissions:
#             # form.submissions.append(file)
#             print("%s: %s" % (file['instanceId'], file['createdAt']))

#     elif args.xform == "csv":
#         submissions = form.getSubmission(args.id, args.form, True)
#         logging.info("There are %d submissions for XForm %s" % (len(submissions), args.form))
#         for file in submissions:
#             form.submissions.append(file)
#             print("%s: %s" % (file['instanceId'], file['createdAt']))

#     elif args.xform == "attachments":
#         attachments = form.listMedia(args.id, args.form)
#         logging.info("There are %d attachments for XForm %s" % (len(attachments), args.form))
#         for file in attachments:
#             print("\t%s exists ? %s" % (file['name'], file['exists']))

#     elif args.xform == "create":
#         for file in files:
#             path = Path(file)
#             if path.suffix == ".xml":
#                 logging.info("Creating XForm from %s" % file)
#                 result = form.createForm(args.id, args.form, file, True)
#             elif path.suffix == ".csv":
#                 logging.info("Uploading media file %r for XForm %s" % (file, file))
#                 result = form.uploadMedia(args.id, args.form, file)
#         result = form.publishForm(args.id, args.form)

#     elif args.xform == "delete":
#         logging.info("Deleting XForm from %s" % args.form)
#         result = form.deleteForm(args.id, args.form)

#     elif args.xform == "publish":
#         logging.info("Publishing XForm from %s" % args.form)
#         result = form.publishForm(args.id, args.form)

# elif args.appuser:
# # This handles app-users
#     print("App User ops %s" % args.appuser)
#     if not args.id:
#         print("Need to specify a project ID using \"--id\" and an XForm id using \"--\"!")
#         quit()
#     # if not args.form:
#     #     print("Need to specify a XForm id using \"--form\"!")
#     #     quit()

#     role = 2                # seems to be the default value
#     user = OdkAppUser()
#     if args.appuser == "create":
#         for appuser in files:
#             result = user.create(args.id, appuser)
#     elif args.appuser == "delete":
#         for appuser in files:
#             result = user.delete(args.id, appuser)
#     elif args.appuser == "update":
#         for appuser in files:
#             result = user.updateRole(args.id, args.form, role, appuser)
#     elif args.appuser == "qrcode":
#         result = user.getQRCode(args.id, args.uuid, args.form)
#     elif args.appuser == "access":
#         for appuser in files:
#             result = user.grantAccess(args.id, role, appuser, )
#     print(result)

# elif args.bulk:
#     central = OdkProject()
#     # project = central.getDetails(args.id)
#     appuser = OdkAppUser()
#     role = 2                    # thise seems to be the default value
#     if not args.form:
#         print("Need to specify a XForm id using \"--form\"!")
#         quit()
#     if args.bulk == "qrcodes":
#         users = central.listAppUsers(args.id)
#         for user in users:
#             # name = "%s-%s" % (project['name'], user['displayName'])
#             name = "%s-%s" % (args.form, user['displayName'])
#             result = appuser.getQRCode(args.id, user['token'], name)
#     elif args.bulk == "update":
#         users = central.listAppUsers(args.id)
#         for user in users:
#             result = appuser.updateRole(args.id, args.form, role, user['id'])
