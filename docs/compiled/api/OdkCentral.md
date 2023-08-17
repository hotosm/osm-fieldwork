#


## OdkCentral
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L80)
```python 
OdkCentral(
   url: str = None, user: str = None, passwd: str = None
)
```




**Methods:**


### .authenticate
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L150)
```python
.authenticate(
   url: str = None, user: str = None, passwd: str = None
)
```

---
Setup authenticate to an ODK Central server

### .listProjects
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L168)
```python
.listProjects()
```

---
Fetch a list of projects from an ODK Central server, and
store it as an indexed list.

### .createProject
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L183)
```python
.createProject(
   name: str
)
```

---
Create a new project on an ODK Central server if it doesn't
already exist

### .deleteProject
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L210)
```python
.deleteProject(
   project_id: int
)
```

---
Delete a project on an ODK Central server

### .findProject
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L220)
```python
.findProject(
   project_id: int, name: str = None
)
```

---
Get the project data from Central

### .findAppUser
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L236)
```python
.findAppUser(
   user_id: int, name: str = None
)
```

---
Get the data for an app user

### .listUsers
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L258)
```python
.listUsers()
```

---
Fetch a list of users on the ODK Central server

### .dump
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L266)
```python
.dump()
```

---
Dump internal data structures, for debugging purposes only

----


## OdkProject
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L284)
```python 
OdkProject(
   url = None, user = None, passwd = None
)
```


---
Class to manipulate a project on an ODK Central server


**Methods:**


### .getData
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L295)
```python
.getData(
   keyword: str
)
```


### .listForms
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L300)
```python
.listForms(
   xform: str
)
```

---
Fetch a list of forms in a project on an ODK Central server.

### .getAllSubmissions
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L310)
```python
.getAllSubmissions(
   project_id: int, xforms: list = None
)
```

---
Fetch a list of submissions in a project on an ODK Central server.

### .listAppUsers
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L360)
```python
.listAppUsers(
   projectId: int
)
```

---
Fetch a list of app users for a project from an ODK Central server.

### .listAssignments
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L369)
```python
.listAssignments(
   projectId: int
)
```

---
List the Role & Actor assignments for users on a project

### .getDetails
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L377)
```python
.getDetails(
   projectId: int
)
```

---
Get all the details for a project on an ODK Central server

### .getFullDetails
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L386)
```python
.getFullDetails(
   projectId: int
)
```

---
Get extended details for a project on an ODK Central server

### .dump
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L396)
```python
.dump()
```

---
Dump internal data structures, for debugging purposes only

----


## OdkForm
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L415)
```python 
OdkForm(
   url: str = None, user: str = None, passwd: str = None
)
```


---
Class to manipulate a from on an ODK Central server


**Methods:**


### .getName
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L438)
```python
.getName()
```

---
Extract the name from a form on an ODK Central server

### .getFormId
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L445)
```python
.getFormId()
```

---
Extract the xmlFormId from a form on an ODK Central server

### .getDetails
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L452)
```python
.getDetails(
   projectId: int, xform: str
)
```

---
Get all the details for a form on an ODK Central server

### .getFullDetails
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L462)
```python
.getFullDetails(
   projectId: int, xform: str
)
```


### .listSubmissionBasicInfo
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L471)
```python
.listSubmissionBasicInfo(
   projectId: int, xform: str
)
```

---
Fetch a list of submission instances basic information for a given form.

### .listSubmissions
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L481)
```python
.listSubmissions(
   projectId: int, xform: str
)
```

---
Fetch a list of submission instances for a given form.

### .listAssignments
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L494)
```python
.listAssignments(
   projectId: int, xform: str
)
```

---
List the Role & Actor assignments for users on a project

### .getSubmissions
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L503)
```python
.getSubmissions(
   projectId: int, xform: str, submission_id: int, disk: bool = False, json: bool = True
)
```

---
Fetch a CSV file of the submissions without media to a survey form.

### .getSubmissionMedia
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L543)
```python
.getSubmissionMedia(
   projectId: int, xform: str
)
```

---
Fetch a ZIP file of the submissions with media to a survey form.

### .addMedia
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L552)
```python
.addMedia(
   media: str, filespec: str
)
```

---
Add a data file to this form

### .addXMLForm
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L560)
```python
.addXMLForm(
   projectId: int, xmlFormId: int, xform: str
)
```

---
Add an XML file to this form

### .listMedia
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L568)
```python
.listMedia(
   projectId: int, xform: str
)
```

---
List all the attchements for this form

### .uploadMedia
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L582)
```python
.uploadMedia(
   projectId: int, xform: str, filespec: str, convert_to_draft: bool = True
)
```

---
Upload an attachement to the ODK Central server

### .getMedia
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L618)
```python
.getMedia(
   projectId: int, xform: str, filename: str
)
```

---
Fetch a specific attachment by filename from a submission to a form.

### .createForm
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L637)
```python
.createForm(
   projectId: int, xform: str, filespec: str, draft: bool = False
)
```

---
Create a new form on an ODK Central server

### .deleteForm
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L670)
```python
.deleteForm(
   projectId: int, xform: str
)
```

---
Delete a form from an ODK Central server

### .publishForm
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L684)
```python
.publishForm(
   projectId: int, xform: str
)
```

---
Publish a draft form. When creating a form that isn't a draft, it can get publised then

### .dump
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L704)
```python
.dump()
```

---
Dump internal data structures, for debugging purposes only

----


## OdkAppUser
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L714)
```python 
OdkAppUser(
   url = None, user = None, passwd = None
)
```




**Methods:**


### .create
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L722)
```python
.create(
   projectId: int, name: str
)
```

---
Create a new app-user for a form

### .delete
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L734)
```python
.delete(
   projectId: int, userId: int
)
```

---
Create a new app-user for a form

### .updateRole
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L743)
```python
.updateRole(
   projectId: int, xform: str, roleId: int = 2, actorId: int = None
)
```

---
Update the role of an app user for a form

### .grantAccess
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L755)
```python
.grantAccess(
   projectId: int, roleId: int = 2, userId: int = None, xform: str = None,
   actorId: int = None
)
```

---
Grant access to an app user for a form

### .createQRCode
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L767)
```python
.createQRCode(
   project_id: int, token: str, name: str
)
```

---
Get the QR Code for an app-user

----


### downloadThread
[source](https://github.com/hotosm/osm-fieldwork/blob/main/../osm_fieldwork/OdkCentral.py/#L52)
```python
.downloadThread(
   project_id: int, xforms: list, odk_credentials: dict
)
```

---
Download a list of submissions from ODK Central
