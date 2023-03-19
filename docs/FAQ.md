# FAQ
## For Users
Q: What is ODK Convert?
A: ODK Convert is a tool that allows users to convert survey forms created in different formats, such as XLSForm or Google Forms, to OpenDataKit (ODK) format. ODK is a free and open-source set of tools that allows users to create and deploy data collection forms on mobile devices.

Q: How do I install ODK Convert?
A: You can install ODK Convert either directly from the main branch using:

`pip install git+https://github.com/hotosm/odkconvert.git`

Or from PyPI using: `pip install ODKConvert`


Q: How do I convert my survey form to ODK format using ODK Convert?
A: To convert your survey form to ODK format using ODK Convert, you can run the command `odkconvert <input_file> <output_file>` in your terminal. Replace <input_file> with the path to your survey form file and <output_file> with the path to the output file in ODK format.

Q: Can ODK Convert convert survey forms created in any format to ODK format?

A: ODK Convert can convert survey forms created in XLSForm, Google Forms, and Kobo Toolbox format to ODK format. However, not all features and functions of the original form may be supported.

Q: What is the advantage of using ODK Convert?
A: Using ODK Convert allows users to easily convert their survey forms to ODK format, which can then be deployed on mobile devices using ODK Collect. ODK Collect allows for offline data collection, and the data can be easily aggregated and analyzed using ODK Aggregate.

Q: How do I update my ODK Convert version?
A: You can update your ODK Convert version by running the command `pip install odkconvert --upgrade` in your terminal. This will upgrade ODK Convert to the latest version.

Q: Can I use ODK Convert for free?
A: Yes, ODK Convert is free and open-source software, licensed under the AGPLv3.

## For Contributors
Q: What is ODKConvert?
A: ODKConvert is a command-line tool for converting data between various data formats commonly used in survey research, including XLSForm, ODK XForm, and JSON. The tool is built using Python and can be run on Windows, Mac, and Linux operating systems.

Q: How can I contribute to ODKConvert?
A: Contributions to ODKConvert are always welcome! You can contribute by fixing bugs, adding new features, improving the documentation, and testing the tool. To get started, you can check the ODKConvert repository on GitHub, review the open issues, and submit a pull request with your changes.

Q: What programming languages and technologies are used in ODKConvert?
A: ODKConvert is written in Python and uses several Python libraries, including PyYAML, Click, and xlrd. The tool can be run on any operating system that supports Python.

Q: How can I set up ODKConvert locally on my computer?
A: To set up ODKConvert locally, you need to have Python 3 installed on your system. You can then clone the ODKConvert repository from GitHub, install the required dependencies using pip, and run the tool using the command-line interface.

Q: How can I report a bug or suggest a new feature for ODKConvert?
A: You can report bugs or suggest new features by opening an issue on the ODKConvert repository on GitHub. Be sure to provide as much detail as possible, including steps to reproduce the bug and any relevant error messages.

Q: How can I test my changes to ODKConvert?
A: ODKConvert has a suite of automated tests that you can run to ensure that your changes do not introduce new bugs or break existing functionality. You can run the tests locally on your computer using the command-line interface or by setting up a continuous integration environment on a platform like Travis CI.

Q: Do I need to have prior experience with survey research or data formats to contribute to ODKConvert?
A: While prior experience with survey research or data formats is helpful, it is not required to contribute to ODKConvert. You can start by reviewing the documentation, exploring the codebase, and contributing to issues labeled as "good first issue."

Q: How can I get help or support with my contributions to ODKConvert?
A: If you need help or support, you can reach out to the ODK community on the ODK forum or Slack channel. You can also ask questions or seek feedback on your contributions by opening an issue on the ODKConvert repository.

Q: What are the benefits of contributing to ODKConvert?
A: Contributing to ODKConvert allows you to help improve a widely used tool in survey research, gain experience with Python programming and command-line tools, and connect with other contributors in the ODK community.


# Troubleshooting

## Unable to connect to the ODKCentral server over http (i.e. insecure)

By default, ODKCentral API connections are verified with SSL certificates. However, sometimes, users may encounter issues connecting to ODKCentral with self-signed certificates. Here are some steps to troubleshoot and resolve the issue:

- Add the certificate to your system trusted certificate store.

    If you are using a self-signed certificate, make sure to add it to your system's trusted certificate store. For Ubuntu/Debian users, follow the steps below:



    ```bash
    sudo apt update && sudo apt install ca-certificates
    sudo cp cert.crt /usr/local/share/ca-certificates/
    sudo update-ca-certificates
    ```

    If running ODKConvert within FMTM, this is handled for you.

- Disable SSL verification (not recommended)

    If you have tried the above step and still cannot connect to ODKCentral, you can disable SSL verification for the certificate. However, this is not recommended as it will connect to ODKCentral insecurely.

    To do this, add the environment variable `ODK_CENTRAL_SECURE=False` to your system.

### Here are some additional troubleshooting steps that may help if you are still unable to connect to the ODKCentral server over HTTP:

- Verify that the ODKCentral API URL is correct

    Make sure that you have entered the correct ODKCentral API URL in your ODKConvert configuration file. You can check the URL by logging into ODKCentral and navigating to the "Site Configuration" page.

- Check that the ODKCentral server is running

    Make sure that the ODKCentral server is running and accessible. You can check the server status by navigating to the ODKCentral API URL in your web browser.

- Check that the ODKCentral server is reachable from your network

    Make sure that your network is not blocking the connection to the ODKCentral server. You can try pinging the server from your computer to see if there is a network issue.

- Check that your firewall is not blocking the connection

    Make sure that your firewall is not blocking the connection to the ODKCentral server. You can try temporarily disabling your firewall to see if this resolves the issue.

- Check the ODKCentral server logs

    Check the ODKCentral server logs to see if there are any error messages related to the connection. This can help identify the root cause of the issue.

- Try using a different web browser

    If you are having trouble connecting to ODKCentral through a web browser, try using a different browser to see if the issue persists. It is possible that the issue is related to the browser or its settings.

- Update ODKConvert and ODKCentral to the latest version

    Make sure that you are using the latest version of ODKConvert and ODKCentral. Check the ODKConvert and ODKCentral release notes to see if any updates address the issue you are experiencing.
