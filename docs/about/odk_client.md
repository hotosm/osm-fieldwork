# ODK Client

odk_client.py is a command line utility for interacting with the ODK Central server. It
exposes many of the REST API calls supported by the server and allows users to perform various tasks, such as uploading and downloading attachments and submissions.

## Usage

`[-h] [-v] [-s {projects,users,delete}] [-p {forms,app-users,assignments,delete}] [-i ID] [-f FORM] [-u UUID]`

`[-x {attachments,csv,submissions,upload,download,create,assignments,delete,publish}] [-a {create,delete,update,qrcode,access}] [-d DATA] [-t TIMESTAMP]`

`[-b {qrcodes,update}]`

### command line client for ODK Central

### Options

      -h, --help            show this help message and exit
      -v, --verbose         verbose output
      -s {projects,users,delete}, --server {projects,users,delete}
                            project operations
      -p {forms,app-users,assignments,delete}, --project {forms,app-users,assignments,delete}
                            project operations
      -i ID, --id ID        Project ID number
      -f FORM, --form FORM  XForm name
      -u UUID, --uuid UUID  Submission UUID, needed to download the data
      -x {attachments,csv,submissions,upload,download,create,assignments,delete,publish}, --xform {attachments,csv,submissions,upload,download,create,assignments,delete,publish}
                            XForm ID for operations with data files
      -a {create,delete,update,qrcode,access}, --appuser {create,delete,update,qrcode,access}
                            App-User operations
      -d DATA, --data DATA  Data files for upload or download
      -t TIMESTAMP, --timestamp TIMESTAMP
                            Timestamp for submissions
      -b {qrcodes,update}, --bulk {qrcodes,update}
                            Bulk operations

## Server requests

Server requests allow users to access global data about projects and users.

### Usage

The following server-specific commands are supported by ODK Client:

- `--server projects`

  This command returns a list of project IDs and their corresponding project names.

### Example usage

      python odk_client.py --server projects

- `--server users`

  This command returns a list of user IDs and their corresponding usernames.

### Example usage

      python odk_client.py --server users

## Project Requests

Project requests allow users to access data for a specific project, such as XForms, attachments, and app users.
Projects contain all the Xforms and attachments for that project. To
access the data for a project, it is necessary to supply the project
ID. That can be retrieved using the above server command. In this
example, 1 is used.

### Usage

The following are the project-specific commands supported by ODK Client:

- `--id <project_id> --project forms`

  This command returns a list of all the XForms contained in the specified project. Replace `"<project_id>"` with the actual ID of the project you want to retrieve the forms for.

### Example usage

      python odk_client.py --id 1 --project forms

- `--id <project_id> --project app-users`

  This command returns a list of all the app users who have access to the specified project. Replace `"<project_id>"` with the actual ID of the project you want to retrieve the list of app users for.

### Example usage

      python odk_client.py --id 1 --project app-users

  Note: Replace "1" with the actual ID of the project you want to access.

## XForm Requests

XForm requests allow users to access data for a specific XForm within a project, such as attachments, submissions, and CSV data.
An XForm has several components. The primary one is the XForm
description itself. In addition to that, there may be additional
attachments, usually a CSV file of external data to be used by the
XForm. If an XForm has been used to collect data, then it has
submissions for that XForm. These can be downloaded as CSV files.

To access the data for an XForm, it is necessary to supply the project
ID and the XForm ID. The XForm ID can be retrieved using the above
project command.

### Usage

The following are the XForm-specific commands supported by ODK Client:

- `--id <project_id> --form <form_id> --xform attachments`

  This command returns a list of all the attachments for the specified XForm. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, and "`<form_id>`" with the actual ID of the XForm you want to retrieve the attachments for.

### Example usage

      python odk_client.py --id 1 --form 1 --xform attachments

- `--id <project_id> --form <form_id> --xform download <attachment_1>,<attachment_2>,...`

  This command downloads the specified attachments for the specified XForm. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, "`<form_id>`" with the actual ID of the XForm you want to download the attachments for, and "`<attachment_1>`,`<attachment_2>`,`etc...`" with the actual names of the attachments you want to download.

### Example usage

      python odk_client.py --id 1 --form 1 --xform download file1.csv,file2.pdf

- `--id <project_id> --form <form_id> --xform submissions`

  This command returns a list of all the submissions for the specified XForm. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, and "`<form_id>`" with the actual ID of the XForm you want to retrieve the submissions for.

### Example usage

      python odk_client.py --id 1 --form 1 --xform submissions

- `--id <project_id> --form <form_id> --xform csv`

  This command returns the data for the submissions for the specified XForm in CSV format. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, and "`<form_id>`" with the actual ID of the XForm you want to retrieve the submission data for.

### Example usage

      python odk_client.py --id 1 --form 1 --xform csv

- `--id <project_id> --form <form_id> --xform upload <attachment_1>,<attachment_2>,...`

  This command uploads the specified attachments for the specified XForm. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, "`<form_id>`" with the actual ID of the XForm you want to upload the attachments for, and "`<attachment_1>,<attachment_2>,...`" with the actual names of the attachments you want to upload.

### Example usage

      python odk_client.py --id 1 --form 1 --xform upload file1.csv,file2.pdf

Note: Replace "1" with the actual IDs of the project and XForm you want to access.

## Create a new XForm, and upload these two attachments

These two attachments are input for _select_from_file_ in the survey
sheet. For osm_fieldwork, they are usually a list of municipalities and
towns.

    ./osm_fieldwork/odk_client.py --id 4 --form waterpoints --xform create osm_fieldwork/xlsforms/waterpoints.xml osm_fieldwork/xlsforms/towns.csv osm_fieldwork/xlsforms/municipality.csv

### To create a new XForm and upload two attachments, follow these steps

- Create a new XForm using the ODK XLSForm syntax. You can use any tool that supports this syntax, such as ODK Build or Excel. Save the XLSForm file as "`waterpoints.xml`".

- Next, prepare two CSV files: "`towns.csv`" and "`municipality.csv`". These CSV files should contain the list of municipalities and towns, respectively, that will be used as input for the "`select_from_file`" function in the survey sheet.

- Once you have these files ready, use the osm-fieldwork tool to convert the XLSForm and CSV files into an ODK form. To do this, open a terminal or command prompt and navigate to the "`osm-fieldwork`" directory. Then, run the following command:

      ./osm-fieldwork/odk_client.py --id 4 --form waterpoints --xform create osm-fieldwork/xlsforms/waterpoints.xml osm-fieldwork/xlsforms/towns.csv osm-fieldwork/xlsforms/municipality.csv

This command will create a new form with the ID "4" and the name "waterpoints", using the XLSForm file and the two CSV files as input. The resulting ODK form can be uploaded to an ODK server for use in data collection.

Make sure to update the file paths in the command to match the actual location of your XLSForm and CSV files. Additionally, ensure that your CSV files are properly formatted according to the ODK specifications.

# Project Requests

## List all the projects on an ODK Central server

    ./osm_fieldwork/odk_client.py --server projects

## Delete a project from ODK Central

    ./osm_fieldwork/odk_client.py --server delete --id 2

# App-user Requests

## Create a new app-user for a project

    ./osm_fieldwork/odk_client.py --appuser create --id 4 foobar

## Create a QR code for the app-user to access ODK Central

    ./osm_fieldwork/odk_client.py -i 4 -f waterpoints -a qrcode -u 'jhAbIwHmYCBObnR45l!I3yi$LbCL$q$saJHkDvgwgtKs2F6sso3eepySJ5tyyyAX'

## Delete an app-user from a project

    ./osm_fieldwork/odk_client.py --appuser delete --id 4 378

## List all app-users for a project

    ./osm_fieldwork/odk_client.py  --id 4 --project app-users

# Bulk operations

Some commands require multiple queries to ODK Central. As FMTM creates
many, many app-users and xforms, it's necessary to be able to clean up
the database sometimes, rather than go through Central for hundreds, or
thousands of app-users.

## Delete multiple app-users from a project

    ./osm_fieldwork/odk_client.py --appuser delete --id 4 22-95

## Generate QRcodes for all registered app-users

    ./osm_fieldwork/odk_client.py --id 4 --bulk qrcodes --form waterpoints

which generates a png file for each app-user, limited to that
project.
