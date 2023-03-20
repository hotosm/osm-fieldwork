# OdkCentral.py

OdkCentral.py is a Python module that provides a set of classes for interacting with an ODK Central server using its API. ODK Central is a server software for managing mobile data collection applications, such as ODK Collect, and provides a RESTful API for interacting with the data collected by those applications.

To use OdkCentral.py, you first need to initialize an OdkCentral object by passing in the URL of your ODK Central server and your authentication credentials. The object provides a set of methods for interacting with the server, such as creating or updating forms, fetching submissions, or managing users.

## Here are the classes provided by OdkCentral.py:

- ## OdkCentral:

    This is the base class for interacting with an ODK Central server. It provides methods for authentication and for sending HTTP requests to the server's REST API. You first need to initialize an OdkCentral object by passing in the URL of your ODK Central server and your authentication credentials. Once you have an OdkCentral object, you can use its methods to interact with the server.

    ### Example:

        from odkcentral import OdkCentral

        # Initialize an OdkCentral object with the server URL and credentials
        odkc = OdkCentral('https://my-odk-central-server.com', 'my-username', 'my-password')

        # Use the object's methods to interact with the server
        response = odkc.get('/projects')
        projects = response.json()
        for project in projects:
            print(project['name'])

    In this example, we first create an OdkCentral object by passing in the URL of our ODK Central server and our authentication credentials. We then use the object's `get()` method to send an HTTP GET request to the `/projects` endpoint of the server's REST API. The response is a JSON object containing information about the projects on the server, which we print to the console.

- ## OdkProject:

    This class represents a project on the server. It provides methods for fetching project metadata and for creating, updating, and deleting forms and users associated with the project.

    ### Example:

        from odkcentral import OdkCentral, OdkProject

        # Initialize an OdkCentral object with the server URL and credentials
        odkc = OdkCentral('https://my-odk-central-server.com', 'my-username', 'my-password')

        # Get a list of all projects on the server
        response = odkc.get('/projects')
        projects = response.json()

        # Choose a project to work with (in this example, we'll use the first project in the list)
        project = OdkProject(odkc, projects[0]['id'])

        # Fetch metadata about the project
        metadata = project.get_metadata()
        print(metadata)

        # Create a new form associated with the project
        form_data = {
            "name": "My New Form",
            "xmlFormId": "my-new-form",
            "formXml": "<xform><title>My New Form</title>...</xform>"
        }
        form = project.create_form(form_data)
        print(form)

        # Delete the form we just created
        project.delete_form(form['id'])


    In this example, we first create an OdkCentral object and use it to fetch a list of all projects on the server. We then choose a project to work with (in this example, we use the first project in the list) and create an OdkProject object by passing in the OdkCentral object and the project ID.

    We use the `get_metadata()` method to fetch metadata about the project, such as its name and description. We then use the `create_form()` method to create a new form associated with the project, passing in the form data as a dictionary. The method returns a JSON object containing information about the new form, which we print to the console.

    Finally, we use the `delete_form()` method to delete the form we just created, passing in the form ID.

- ## OdkForm:

    The OdkForm class represents a form on the ODK Central server. It provides methods for creating, updating, and deleting forms on the server, as well as fetching information about a specific form or a list of all forms.

    ### Here's an example of how to create a new form using the OdkForm class:

        from odkcentral import OdkForm

        # Initialize an OdkForm object with the server URL and credentials
        odkf = OdkForm('https://my-odk-central-server.com', 'my-username', 'my-password')

        # Define the form data
        form_data = {
            "name": "My New Form",
            "xmlFormId": "my-new-form",
            "formXml": "<xform><title>My New Form</title>...</xform>"
        }

        # Create the form on the server
        form = odkf.create(form_data)

    This will create a new form on the server with the specified name and XML form ID, and upload the form XML. You can also update an existing form using the `update()` method and delete a form using the `delete()` method.

    To fetch information about a specific form or a list of all forms, you can use the `get()` method. Here's an example of how to fetch information about a specific form:

        # Fetch information about a form with the ID 'my-form-id'
        form = odkf.get('my-form-id')

        # Print the name of the form
        print(form['name'])

    This will fetch information about the form with the ID 'my-form-id' and print its name.

    You can also fetch a list of all forms on the server using the `get_all()` method:

        # Fetch a list of all forms on the server
        forms = odkf.get_all()

        # Print the name of each form
        for form in forms:
            print(form['name'])

- ## OdkAppUser:

    The OdkAppUser class provides methods for creating, updating, deleting and retrieving ODK Central users. It has the following attributes:

    - id: The unique identifier for the user.
    - displayName: The display name of the user.
    - email: The email address of the user.
    - password: The user's password.

    ### Here is an example of how to use the OdkAppUser class to create a new user:

        from OdkCentral import OdkCentral, OdkAppUser

        # Connect to the ODK Central server
        central = OdkCentral('https://example.com', 'username', 'password')

        # Create a new user
        user_data = {
            "displayName": "Noah Droid",
            "email": "noahdroid@example.com",
            "password": "password123"
        }

        new_user = OdkAppUser.create(central, user_data)

    In the above example, we first create a new instance of the OdkCentral class and pass in the URL of the ODK Central server, as well as the username and password of a user with sufficient permissions to create new users.

    Next, we create a dictionary `user_data` containing the display name, email address, and password of the new user. We then call the `create` method on the OdkAppUser class, passing in the `central` object and the `user_data` dictionary. This creates a new user on the server and returns an instance of the OdkAppUser class representing the new user.

    We can also use the OdkAppUser class to retrieve information about existing users:

        # Get information about an existing user
        user_id = "abc123"
        existing_user = OdkAppUser.get(central, user_id)

        # Update the display name of an existing user
        existing_user.display_name = "Ndacyayisenga Doe"
        existing_user.save()

        # Delete an existing user
        existing_user.delete()

    In the above example, we first retrieve information about an existing user with the ID abc123 by calling the get method on the OdkAppUser class, passing in the central object and the user ID.

    We can then update the user's display name by modifying the display_name attribute of the existing_user object and calling the save method to save the changes to the server.

    Finally, we can delete the user from the server by calling the delete method on the existing_user object.