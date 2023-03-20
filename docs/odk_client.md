## ODK Client

odk_client.py is a command line utility for  interacting with the ODK Central server. It
exposes many of the REST API calls supported by the server and allows users to perform various tasks, such as uploading and downloading attachments and submissions.

ODK Client provides several command-line options to interact with ODK Central. These commands are divided into three types: server requests, project requests, and XForm requests.

# Server requests

Server requests allow users to access global data about projects and users. 

For example:
- --server projects - returns a list of project IDs and the project name

- --server users - returns a list of user IDs and their user name

All of the server-specific commands are accessible via the
_--server_ command. This command takes a single argument, and can only
access the global data about projects and users.

# Project Requests

Project requests allow users to access data for a specific project, such as XForms, attachments, and app users. 
Projects contain all the Xforms and attachments for that project. To
access the data for a project, it is necessary to supply the project
ID. That can be retrieved using the above server command. In this
example, 1 is used.

- --id 1 --project forms - returns a list of all the XForms contained
  in this project
- --id 1 --project app-users - returns a list of all the app users who
  have access to this project.

# XForm Requests

XForm requests allow users to access data for a specific XForm within a project, such as attachments, submissions, and CSV data. 
An XForm has several components. The primary one is the XForm
description itself. In addition to that, there may be additional
attachments, usually a CSV file of external data to be used by the
XForm. If an XForm has been used to collect data, then it has
submissions for that XForm. These can be downloaded as CSV files.

To access the data for an XForm, it is necessary to supply the project
ID and the XForm ID. The XForm ID can be retrieved using the above
project command.

- --id 1 --form formid --xform attachments - returns a list of all the
  attachments for this XForm
- --id 1 --form formid -x download file1, file2,etc... - download the
  specified attachments for this XForm
- --id 1 --form formid --xform submissions - returns a list of all the
  submissions for this XForm
- --id 1 --form formid --xform csv - returns the data for the submissions
  submissions for this XForm
- --id 1 --form formid --xform upload file1,file2,.. - upload
  attachments for this XForm

# Create a new XForm, and upload these two attachments

These two attachments are input for _select_from_file_ in the survey
sheet. For odkconvert, they are usually a list of municipalities and
towns.

    ./odkconvert/odk_client.py --id 4 --form waterpoints --xform create odkconvert/xlsforms/waterpoints.xml odkconvert/xlsforms/towns.csv odkconvert/xlsforms/municipality.csv

# Project Requests

## List all the projects on an ODK Central server

    ./odkconvert/odk_client.py --server projects

## Delete a project from ODK Central

    ./odkconvert/odk_client.py --server delete --id 2

# App-user Requests

## Create a new app-user for a project

    ./odkconvert/odk_client.py --appuser create --id 4 foobar

## Create a QR code for the app-user to access ODK Central

    ./odkconvert/odk_client.py -i 4 -f waterpoints -a qrcode -u 'jhAbIwHmYCBObnR45l!I3yi$LbCL$q$saJHkDvgwgtKs2F6sso3eepySJ5tyyyAX'

## Delete an app-user from a project

    ./odkconvert/odk_client.py --appuser delete --id 4 378

## List all app-users for a project

    ./odkconvert/odk_client.py  --id 4 --project app-users

# Bulk operations

Some commands require multiple queries to ODK Central. As FMTM creates
many, many app-users and xforms, it's necessary to be able to clean up
the database sometimes, rather than go through Central for hundreds, or
thousands of app-users.

## Delete multiple app-users from a project

    ./odkconvert/odk_client.py --appuser delete --id 4 22-95

## Generate QRcodes for all registered app-users

    ./odkconvert/odk_client.py --id 4 --bulk qrcodes --form waterpoints

which generates a png file for each app-user, limited to that
project.
