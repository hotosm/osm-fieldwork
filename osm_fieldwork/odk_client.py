#!/bin/python3

# Copyright (c) 2022 Humanitarian OpenStreetMap Team
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

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from sys import argv

from codetiming import Timer

from osm_fieldwork.json2osm import JsonDump
from osm_fieldwork.OdkCentral import OdkAppUser, OdkCentral, OdkForm, OdkProject

# Set log level
log = logging.getLogger(__name__)


class OdkClient(object):
    def __init__(
        self,
        url: str = None,
        user: str = None,
        passwd: str = None,
    ):
        """A Class for higher-level client side access to ODK Central.

        Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central

        Returns:
            (OdkClient: An instance of this object
        """
        self.url = url
        self.user = user
        self.passwd = passwd
        self.cache = dict()

    # def readCache(self, cache=".odkcentral"):
    #     """FIXME: unimplemented"""
    #     file = open(cache, "rb")
    #     data = file.readline()
    #     print(json.load(data))
    #     file.close()

    # def writeCache(self, cache=".odkcentral", data=None):
    #     """FIXME: unimplemented"""
    #     if args.cache:
    #         try:
    #             file = open(cache, "xb")
    #         except FileExistsError:
    #             file = open(cache, "wb")
    #         file.write("projects\n")
    #         file.write(json.dump(data))
    #         file.close()
    #     logging.info("Wrote config file %s" % filespec)


def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="command line client for ODK Central")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    # This is for server requests
    parser.add_argument("-s", "--server", choices=["projects", "users", "delete"], help="project operations")
    # This is for project specific requests
    parser.add_argument(
        "-p",
        "--project",
        choices=["forms", "app-users", "assignments", "delete", "submissions"],
        help="project operations",
    )
    parser.add_argument("-i", "--id", type=int, help="Project ID nunmber")
    parser.add_argument("-f", "--form", help="XForm name")
    parser.add_argument("-u", "--uuid", help="Submission UUID, needed to download the data")
    # This is for form specific requests
    parser.add_argument(
        "-x",
        "--xform",
        choices=[
            "attachments",
            "csv",
            "json",
            "submissions",
            "upload",
            "download",
            "create",
            "assignments",
            "delete",
            "publish",
        ],
        help="XForm ID for operations with data files",
    )
    parser.add_argument(
        "-a",
        "--appuser",
        choices=["create", "delete", "update", "qrcode", "access"],
        help="App-User operations",
    )
    parser.add_argument("-d", "--data", help="Data files for upload or download")
    parser.add_argument("-t", "--timestamp", help="Timestamp for submissions")
    parser.add_argument("-b", "--bulk", choices=["qrcodes", "update"], help="Bulk operations")

    # logging.basicConfig(
    #     level=log_level,
    #     format=(
    #         "%(asctime)s.%(msecs)03d [%(levelname)s]"
    #         "%(name)s | %(funcName)s:%(lineno)d | %(message)s"
    #     ),
    #     datefmt="%y-%m-%d %H:%M:%S",
    #     stream=sys.stdout,
    # )

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

    if len(argv) <= 1:
        parser.print_help()
        quit()

    # Get any files for upload or download
    files = list()
    if unknown is not None:
        files = unknown

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    timer = Timer(text="odk_client() took {seconds:.0f}s")
    timer.start()
    # Commands to the ODK Central server, which gets data that applies
    # to all projects on the server.
    if args.server:
        central = OdkCentral()
        # central.authenticate()
        if args.server == "projects":
            projects = central.listProjects()
            if not projects:
                projects = list()
            elif "message" in projects:
                log.error(f"{projects['message']}, {projects['code']} ")
                quit()

            print("There are %d projects on this ODK Central server" % len(projects))
            ordered = sorted(projects, key=lambda item: item.get("id"))
            for project in ordered:
                print("\t%s: %s" % (project["id"], project["name"]))
        elif args.server == "users":
            users = central.listUsers()
            logging.info("There are %d users on this ODK Central server" % len(users))
            ordered = sorted(users, key=lambda item: item.get("id"))
            for user in ordered:
                print("%s: %s (%s)" % (user["id"], user["displayName"], user["email"]))
        elif args.server == "delete":
            central.deleteProject(args.id)

        # Commands to get data about a specific project on an ODK Central server.
    elif args.project:
        project = OdkProject()
        # project.authenticate()
        if not args.id:
            print('Need to specify a project ID using "--id"!')
            print('You can use "odk_client.-py --server projects" to list all the projects!')
            # parser.print_help()
            quit()
        if args.project == "forms":
            forms = project.listForms(args.id)
            if type(forms) == dict:
                log.error(f"{forms['message']}, {forms['code']} ")
                quit()
            if type(forms) != list:
                log.error(forms["message"])
                quit()
            ordered = sorted(forms, key=lambda item: item.get("xmlFormId"))
            for form in ordered:
                print("\t%r: %r" % (form["xmlFormId"], form["name"]))

        elif args.project == "submissions":
            submissions = project.getAllSubmissions(args.id)
            jsonin = JsonDump()
            now = datetime.now().strftime("%Y-%m-%dT%TZ")
            outfile = f"{args.project}_{now}"
            jsonin.createOSM(f"{outfile}.osm")
            # jsonin.createGeoJson(f"{outfile}.geojson")
            data = jsonin.parse(data=submissions)
            log.debug(f"There are a total of {len(submissions)} submissions")
            for entry in data:
                feature = jsonin.createEntry(entry)
                # Sometimes bad entries, usually from debugging XForm design, sneak in
                if len(feature) == 0:
                    continue
                if "lat" not in feature["attrs"]:
                    if "geometry" in feature["tags"]:
                        if type(feature["tags"]["geometry"]) == str:
                            coords = list(feature["tags"]["geometry"])
                            # del feature['tags']['geometry']
                    elif "coordinates" in feature["tags"]:
                        coords = feature["tags"]["coordinates"]
                        feature["attrs"] = {"lat": coords[1], "lon": coords[0]}
                    else:
                        log.warning("Bad record! %r" % feature)
                        continue
                jsonin.writeOSM(feature)
                log.info(f"Wrote {outfile}.osm")
                # This GeoJson file has all the data values
                # jsonin.writeGeoJson(feature)
                # log.info(f"Wrote {outfile}.geojson")

        elif args.project == "app-users":
            users = project.listAppUsers(args.id)
            logging.info("There are %d app users on this ODK Central server" % len(users))
            ordered = sorted(users, key=lambda item: item.get("id"))
            for user in ordered:
                print("\t%r: %s (%s)" % (user["id"], user["displayName"], user["token"]))
        elif args.project == "delete":
            tmp = files[0].split("-")
            if len(tmp) > 1:
                for id in range(int(tmp[0]), int(tmp[1])):
                    project.deleteProject(id)
            else:
                project.deleteProject(tmp[0])

            # logging.info("There are %d app users on this ODK Central server" %)
            if args.project == "assignments":
                assign = project.listAssignments(args.id)
                logging.info("There are %d assignments  on this ODK Central server" % len(assign))
            ordered = sorted(assign, key=lambda item: item.get("id"))
            for role in ordered:
                print("\t%r" % role)

    elif args.xform:
        # This downloads files from the ODK server
        if not args.id:
            print('Need to specify a project ID using "--id" and an XForm id using "--"!')
            quit()
        if not args.form:
            print('Need to specify a XForm id using "--form"!')
            quit()

        form = OdkForm()
        # form.authenticate()
        # Note that uploading and downloading is only for the attachments, usually
        # a CSV or GeoJson file used by the Form as an external data source for
        # survey questions
        if args.xform == "upload":
            for file in files:
                logging.info("Uploading file %r for XForm %s" % (file, args.form))
                result = form.uploadMedia(args.id, args.form, file)
        elif args.xform == "download":
            logging.info("Downloading files %r for XForm %s" % (files, args.form))
            for file in files:
                logging.info("Downloading %r for XForm %s" % (file, args.form))
                data = form.getMedia(args.id, args.form, file)
                try:
                    file = open(file, "xb")
                except FileExistsError:
                    file = open(file, "wb")
                    file.write(data)
                    file.close()
        elif args.xform == "assignments":
            assign = form.listAssignments(args.id, args.form)
            if type(assign) == dict:
                log.error(f"{assign['message']}, {assign['code']} ")
                quit()
            logging.info("There are %d assignments  on this ODK Central server" % len(assign))
            # ordered = sorted(assign, key=lambda item: item.get('id'))
            for role in assign:
                print("\t%r" % role)

        elif args.xform == "submissions":
            submissions = form.listSubmissions(args.id, args.form)
            if not submissions:
                submissions = list()
            elif "message" in submissions:
                log.error(f"{submissions['message']}, {submissions['code']} ")
                quit()

            logging.info("There are %d submissions for XForm %s" % (len(submissions), args.form))
            for file in submissions:
                # form.submissions.append(file)
                print("%s: %s" % (file["meta"]["instanceID"], file["end"]))

        elif args.xform == "csv":
            submissions = form.getSubmissions(args.id, args.form, True, False)
            if type(submissions) == dict:
                log.error(f"{submissions['message']}, {submissions['code']} ")
            logging.info("There are %d submissions for XForm %s" % (len(submissions), args.form))
            for file in submissions:
                form.submissions.append(file)
                print("%s: %s" % (file["meta"]["instanceID"], file["end"]))

        elif args.xform == "json":
            submissions = form.getSubmissions(args.id, args.form, False, True, True)
            if type(submissions) == dict:
                log.error(f"{submissions['message']}, {submissions['code']} ")
                quit()
            else:
                if submissions is None:
                    submissions = list()
            logging.info("There are %d submissions for XForm %s" % (len(submissions), args.form))
            for file in submissions:
                form.submissions.append(file)
                # print("%s: %s" % (file["instanceId"], file["createdAt"]))

        elif args.xform == "attachments":
            attachments = form.listMedia(args.id, args.form)
            if type(attachments) == dict:
                log.error(f"{attachments['message']}, {attachments['code']} ")
                quit()
            logging.info("There are %d attachments for XForm %s" % (len(attachments), args.form))
            for file in attachments:
                print("\t%s exists ? %s" % (file["name"], file["exists"]))

        elif args.xform == "create":
            for file in files:
                path = Path(file)
                if path.suffix == ".xml":
                    logging.info("Creating XForm from %s" % file)
                    result = form.createForm(args.id, file, args.form)
                elif path.suffix == ".csv":
                    logging.info("Uploading media file %r for XForm %s" % (file, file))
                    result = form.uploadMedia(args.id, args.form, file)
                    result = form.publishForm(args.id, args.form)

        elif args.xform == "delete":
            logging.info("Deleting XForm from %s" % args.form)
            result = form.deleteForm(args.id, args.form)

        elif args.xform == "publish":
            logging.info("Publishing XForm from %s" % args.form)
            result = form.publishForm(args.id, args.form)

    elif args.appuser:
        # This handles app-users
        print("App User ops %s" % args.appuser)
        if not args.id:
            print('Need to specify a project ID using "--id" and an XForm id using "--"!')
            quit()
            # if not args.form:
            #     print("Need to specify a XForm id using \"--form\"!")
            #     quit()

        role = 2  # seems to be the default value
        user = OdkAppUser()
        if args.appuser == "create":
            for appuser in files:
                result = user.create(args.id, appuser)
        elif args.appuser == "delete":
            tmp = files[0].split("-")
            if len(tmp) > 1:
                for id in range(int(tmp[0]), int(tmp[1])):
                    result = user.delete(args.id, id)
            else:
                result = user.delete(args.id, tmp[0])
        elif args.appuser == "update":
            for appuser in files:
                result = user.updateRole(args.id, args.form, role, appuser)
        elif args.appuser == "qrcode":
            result = user.getQRCode(args.id, args.uuid, args.form)
        elif args.appuser == "access":
            for appuser in files:
                result = user.grantAccess(
                    args.id,
                    role,
                    appuser,
                )
                print(result)

        elif args.bulk:
            central = OdkProject()
            # project = central.getDetails(args.id)
            appuser = OdkAppUser()
            role = 2  # thise seems to be the default value
            if not args.form:
                print('Need to specify a XForm id using "--form"!')
                quit()
            if args.bulk == "qrcodes":
                users = central.listAppUsers(args.id)
                for user in users:
                    # name = "%s-%s" % (project['name'], user['displayName'])
                    name = "%s-%s" % (args.form, user["displayName"])
                    result = appuser.getQRCode(args.id, user["token"], name)
            elif args.bulk == "update":
                users = central.listAppUsers(args.id)
                for user in users:
                    result = appuser.updateRole(args.id, args.form, role, user["id"])
    timer.stop()


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
