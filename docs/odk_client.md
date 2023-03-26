# ODK Client

odk_client.py is a command line utility for  interacting with the ODK Central server. It
exposes many of the REST API calls supported by the server and allows users to perform various tasks, such as uploading and downloading attachments and submissions.

## Usage
`[-h] [-v] [-s {projects,users,delete}] [-p {forms,app-users,assignments,delete}] [-i ID] [-f FORM] [-u UUID]`

`[-x {attachments,csv,submissions,upload,download,create,assignments,delete,publish}] [-a {create,delete,update,qrcode,access}] [-d DATA] [-t TIMESTAMP]`

`[-b {qrcodes,update}]`

### command line client for ODK Central

### Options:

      -h, --help            show this help message and exit
      -v, --verbose         verbose output
      -s {projects,users,delete}, --server {projects,users,delete}
                            project operations
      -p {forms,app-users,assignments,delete}, --project {forms,app-users,assignments,delete}
                            project operations
      -i ID, --id ID        Project ID nunmber
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

  ### Example usage:

      python odk_client.py --server projects


- `--server users`

  This command returns a list of user IDs and their corresponding usernames.

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

  ### Example usage:

      python odk_client.py --id 1 --project forms

- `--id <project_id> --project app-users`

  This command returns a list of all the app users who have access to the specified project. Replace `"<project_id>"` with the actual ID of the project you want to retrieve the list of app users for.

  ### Example usage:

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

  ### Example usage:

      python odk_client.py --id 1 --form 1 --xform attachments

- `--id <project_id> --form <form_id> --xform download <attachment_1>,<attachment_2>,...`

  This command downloads the specified attachments for the specified XForm. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, "`<form_id>`" with the actual ID of the XForm you want to download the attachments for, and "`<attachment_1>`,`<attachment_2>`,`etc...`" with the actual names of the attachments you want to download.

  ### Example usage:

      python odk_client.py --id 1 --form 1 --xform download file1.csv,file2.pdf

- `--id <project_id> --form <form_id> --xform submissions`

  This command returns a list of all the submissions for the specified XForm. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, and "`<form_id>`" with the actual ID of the XForm you want to retrieve the submissions for.

  ### Example usage:

      python odk_client.py --id 1 --form 1 --xform submissions

- `--id <project_id> --form <form_id> --xform csv`

  This command returns the data for the submissions for the specified XForm in CSV format. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, and "`<form_id>`" with the actual ID of the XForm you want to retrieve the submission data for.

  ### Example usage:

      python odk_client.py --id 1 --form 1 --xform csv

- `--id <project_id> --form <form_id> --xform upload <attachment_1>,<attachment_2>,...`

  This command uploads the specified attachments for the specified XForm. Replace "`<project_id>`" with the actual ID of the project that contains the XForm, "`<form_id>`" with the actual ID of the XForm you want to upload the attachments for, and "`<attachment_1>,<attachment_2>,...`" with the actual names of the attachments you want to upload.

  ### Example usage:

      python odk_client.py --id 1 --form 1 --xform upload file1.csv,file2.pdf

Note: Replace "1" with the actual IDs of the project and XForm you want to access.

## Create a new XForm, and upload these two attachments

These two attachments are input for _select_from_file_ in the survey
sheet. For odkconvert, they are usually a list of municipalities and
towns.

### To create a new XForm and upload two attachments, follow these steps:

- Create a new XForm using the ODK XLSForm syntax. You can use any tool that supports this syntax, such as ODK Build or Excel. Save the XLSForm file as "`waterpoints.xml`".

- Next, prepare two CSV files: "`towns.csv`" and "`municipality.csv`". These CSV files should contain the list of municipalities and towns, respectively, that will be used as input for the "`select_from_file`" function in the survey sheet.

- Once you have these files ready, use the ODK Convert tool to convert the XLSForm and CSV files into an ODK form. To do this, open a terminal or command prompt and navigate to the "`odkconvert`" directory. Then, run the following command:

      ./odkconvert/odk_client.py --id 4 --form waterpoints --xform create odkconvert/xlsforms/waterpoints.xml odkconvert/xlsforms/towns.csv odkconvert/xlsforms/municipality.csv

This command will create a new form with the ID "4" and the name "waterpoints", using the XLSForm file and the two CSV files as input. The resulting ODK form can be uploaded to an ODK server for use in data collection.

Make sure to update the file paths in the command to match the actual location of your XLSForm and CSV files. Additionally, ensure that your CSV files are properly formatted according to the ODK specifications.

# Project Requests

## List all the projects on an ODK Central server
### To list all the projects, do the following
- Run the "`odk_client.py`" file located in the "`odkconvert`" folder.
- Use the "`--server`" flag to specify that you want to list all the projects on the ODK Central server. For example, use "`--server projects`".

### Example command:

    ./odkconvert/odk_client.py --server projects

Once you run the command, a list of all the projects on the ODK Central server will be displayed in the terminal or command prompt.

## Delete a project from ODK Central
### To the delete a project, do the following

- Run the "`odk_client.py`" file located in the "`odkconvert`" folder.
- Use the "`--server`" flag to specify that you want to delete a project from ODK Central. For example, use "`--server delete`".
- Use the "`--id`" flag to specify the ID number of the project you want to delete. For example, if the project ID number is 2, use "`--id 2`".

### Example command:

    ./odkconvert/odk_client.py --server delete --id 2

Once you run the command, the project with the specified ID number will be deleted from ODK Central. Please note that this action cannot be undone and all data associated with the project will be permanently deleted.

Note: Please use the delete option with great care, as it permanently removes the app-user and all associated data from the database. Unlike ODK Central, which merely archives projects, the deletion here removes it from the database completely. This option is primarily meant for debugging and administrative purposes and should rarely be used.

# App-user Requests

## Create a new app-user for a project
### To create a new app use, do the following
- Run the "`odk_client.py`" file located in the "`odkconvert`" folder.
- Use the "`--appuser`" flag to specify the action to perform, which is creating a new app-user. For example, use "--appuser create".
- Use the "`--id`" flag to specify the project ID for which you want to create the app-user. For example, use "`--id 4`".
- Use a username for the new app-user. For example, use "foobar".

### Example command:

    ./odkconvert/odk_client.py --appuser create --id 4 foobar

Once you run the command, a new app-user with the specified username will be created for the project with the specified ID number. The app-user will be assigned a unique ID number that you can use to perform other actions, such as assigning roles or deleting the app-user.

./odkconvert/odk_client.py --appuser create --id 4 foobar

## create a QR code for the app-user to access ODK Central
### To create the QR code, do the following

- Run the "`odk_client.py`" file located in the "`odkconvert`" folder.
- Use the "`-i`" flag to specify the server instance number. For example, if you're using the fourth server instance, use "`-i 4`".
- Use the "`-f`" flag to specify the form ID. For example, if you're using the "`waterpoints`" form, use "`-f waterpoints`".
- Use the "`-a`" flag to specify the action to perform. In this case, use "`-a qrcode`" to create a QR code.
- Use the "`-u`" flag to provide the API token for authentication. Forexample `jhAbIwHmYCBObnR45l!I3yi$LbCL$q$saJHkDvgwgtKs2F6sso3eepySJ5tyyyAX`

### Example command:

    ./odkconvert/odk_client.py -i 4 -f waterpoints -a qrcode -u 'your_api_token'

After running the command, the QR code will be displayed in the terminal. The app-user can then scan the QR code with their device's camera to access the specified ODK Central form.

## Delete an app-user from a project
### To delete the app-user, do the following
- Run the "`odk_client.py`" file located in the "`odkconvert`" folder.
- Use the "`--appuser`" flag to specify the action to perform, which is deleting an app-user. For example, use "`--appuser delete`".
- Use the "`--id`" flag to specify the project and app-user's ID number. For example, if the app-user's ID number is 378, use "`--id 4 378`".

### Example command:

    ./odkconvert/odk_client.py --appuser delete --id 4 378

Once you run the command, the app-user with the specified ID number will be deleted from the project.

Note: Please use the delete option with great care, as it permanently removes the app-user and all associated data from the database. Unlike ODK Central, which merely archives projects, the deletion here removes it from the database completely. This option is primarily meant for debugging and administrative purposes and should rarely be used.

## List all app-users for a project
### To list all app-users, do the following
- Run the "`odk_client.py`" file located in the "`odkconvert`" folder.
- Use the "`--id`" flag to specify the project. For example, if your project ID is 4, use "`--id 4`".
- Use the "`-- project app-users`" flag to specify the action to perform, which is listing all app-users. For example, use "`--project app-users`".

### Example command:

    ./odkconvert/odk_client.py  --id 4 --project app-users

Once you run the command, a list of all app-users for the specified project will be displayed in the terminal or command prompt.

# Bulk operations

Some commands require multiple queries to ODK Central. As FMTM creates
many, many app-users and xforms, it's necessary to be able to clean up
the database sometimes, rather than go through Central for hundreds, or
thousands of app-users.

## Delete multiple app-users from a project
### To delete mulitple app-users, do the following:
- Run the "`odk_client.py`" file located in the "`odkconvert`" folder.
- Use the "`--appuser`" flag to specify the action to perform, which is deleting app-users. For example, use "`--appuser delete`".
- Use the "`--id`" flag to specify the project's ID number. For example, if the project's ID  is 4, use "`--id 4`".
- Specify the project ID followed by the app-users ids seperated by a hyphen

### Example command:

    ./odkconvert/odk_client.py --appuser delete --id 4 22-95

Once you run the command, the app-users with the specified ID numbers and usernames or email addresses will be deleted from the project.

Note: Please use the delete option with great care, as it permanently removes the app-user and all associated data from the database. Unlike ODK Central, which merely archives projects, the deletion here removes it from the database completely. This option is primarily meant for debugging and administrative purposes and should rarely be used.

## Generate QRcodes for all registered app-users
### To generate QRcodes for all, do the following
- Run the "`odk_client.py`" file located in the "`odkconvert`" folder.
- Use the "`--id`" flag to specify the project ID for which you want to generate the QR codes. For example, use "`--id myproject`".
- Use the "`--bulk`" flag to specify that you want to generate QR codes for all registered app-users. For example, use "`--bulk qrcodes`".
Use the "`--form`" flag to specify the name of the form for which you want to generate the QR codes. For example, use "`--form myform`".

### Example command:

    ./odkconvert/odk_client.py --id myproject --bulk qrcodes --form myform

Once you run the command, QR codes for all registered app-users for the specified project and form will be generated and saved to a folder called "`qrcodes`" in the current directory.
which generates a png file for each app-user, limited to that
project.
