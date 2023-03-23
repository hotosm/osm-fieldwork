## ODK Client

odk_client.py is a command line utility for the ODK Central server. It
exposed many of the REST API calls supported by the server, including
uploading and downloading attachments and submissions.

# Server requests

All of the server-specific commands are accessible via the
_--server_ command. This command takes a single argument, and can only
access the global data about projects and users.

- --server projects - returns a list of project IDs and the project name

- --server users - returns a list of user IDs and their user name

# Project Requests

Projects contain all the Xforms and attachments for that project. To
access the data for a project, it is necessary to supply the project
ID. That can be retrieved using the above server command. In this
example, 1 is used.

- --id 1 --project forms - returns a list of all the XForms contained
  in this project
- --id 1 --project app-users - returns a list of all the app users who
  have access to this project.

# XForm Requests

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
