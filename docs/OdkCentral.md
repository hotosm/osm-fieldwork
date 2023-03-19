# OdkCentral.py

`OdkCentral.py` is a Python module that provides a set of functions for interacting with an ODK Central server using its API. ODK Central is a server software for managing mobile data collection applications, such as ODK Collect, and provides a RESTful API for interacting with the data collected by those applications.

To use `OdkCentral.py`, you first need to initialize an `OdkCentral` object by passing in the URL of your ODK Central server and your authentication credentials. The object provides a set of methods for interacting with the server, such as creating or updating forms, fetching submissions, or managing users.

### Here's an example of how to create an OdkCentral object:

        from odkcentral import OdkCentral

        #Initialize an OdkCentral object with the server URL and credentials
        odkc = OdkCentral('https://my-odk-central-server.com', 'my-username', 'my-password')

Once you have an `OdkCentral` object, you can use its methods to interact with the server. For example, you can use the `get_forms()` method to fetch a list of all forms on the server:

        forms = odkc.get_forms()
        for form in forms:
            print(form['name'])

This will print out the name of each form on the server.

You can also use the `get_form_submissions()` method to fetch a list of all submissions for a particular form:

        submissions = odkc.get_form_submissions('my-form-id')
        for submission in submissions:
            print(submission['data'])

This will print out the data for each submission for the form with ID my-form-id.

Other methods provided by OdkCentral.py include `create_form()`, `update_form()`, `delete_form()`, `create_user()`, `update_user()`, `delete_user()`, and more.

## A few examples

### Creating and Updating Forms

You can use the `create_form()` method to create a new form on the server:

    form_data = {
        "name": "My New Form",
        "xmlFormId": "my-new-form",
        "formXml": "<xform><title>My New Form</title>...</xform>"
    }
    form = odkc.create_form(form_data)

This will create a new form on the server with the specified name and XML form ID, and upload the form XML.

You can use the `update_form()` method to update an existing form on the server:

    form_data = {
        "name": "My Updated Form",
        "xmlFormId": "my-updated-form",
        "formXml": "<xform><title>My Updated Form</title>...</xform>"
    }
    odkc.update_form('my-form-id', form_data)

This will update the form with ID `my-form-id` on the server with the specified name and XML form ID, and upload the updated form XML.

### Creating and Managing Users

You can use the `create_user()` method to create a new user on the server:

    user_data = {
        "email": "newuser@example.com",
        "password": "my-password",
        "displayName": "New User",
        "role": "data_viewer"
    }
    user = odkc.create_user(user_data)

This will create a new user on the server with the specified `email`, `password`, `display name`, and `role`.

You can use the `update_user()` method to update an existing user on the server:

    user_data = {
        "email": "updateduser@example.com",
        "password": "my-new-password",
        "displayName": "Updated User",
        "role": "data_manager"
    }
    updated_user = odkc.update_user(user_data)

If an error occurs while interacting with the server, `OdkCentral.py` raises an `OdkCentralError` exception. This exception contains a message describing the error. You can catch this exception and handle it appropriately in your code.

In short words, OdkCentral.py is a Python module that provides a set of functions for interacting with an ODK Central server using its API. To use OdkCentral.py, you first need to initialize an OdkCentral object with the server URL and your authentication credentials. You can then use the object's methods to interact with the server, such as creating or updating forms, fetching submissions, or managing users. If an error occurs, OdkCentral.py raises an OdkCentralError exception that you can catch and handle in your code.
