# Troubleshooting

## Unable to connect to the ODKCentral server over http (i.e. insecure)

By default, ODKCentral API connections are verified with SSL
certificates. However, sometimes, users may encounter issues
connecting to [ODK Central](https://docs.getodk.org/central-intro/)
with self-signed certificates. This is common for developers if
running ODK Central in a local subnet without a public domain name.

Here are some steps to troubleshoot and resolve the issue:

- Add the certificate to your system trusted certificate store.

If you are using a self-signed certificate, make sure to add it to
your system's trusted certificate store. For Ubuntu/Debian users,
follow the steps below: 

    In a terminal:
    sudo apt update && sudo apt install ca-certificates
    sudo cp cert.crt /usr/local/share/ca-certificates/
    sudo update-ca-certificates


If running OSM Fieldwork within the
[Field Mapping Tasking Manager](https://github.com/hotosm/fmtm/wiki),
this is handled for you. 

**Q:** Can I disable SSL verification (not recommended)

**A:**  If you have tried the above step and still cannot connect to
	ODK Central, you can disable SSL verification for the
    certificate. However, this is not recommended as it will connect
    to ODK Central insecurely. To do this, add the environment
	variable **ODK_CENTRAL_SECURE=False** to your system.

### Additional Troubleshooting Steps

If you are still unable to connect to the ODKCentral server over HTTP: 

- Verify that the ODK Central API URL is correct

    Make sure that you have entered the correct ODK Central API URL in
    your OSM Fieldwork configuration file. You can check the URL by
    logging into ODK Central and navigating to the "Site
    Configuration" page.

- Check that the ODK Central server is running

    Make sure that the ODK Central server is running and
    accessible. You can check the server status by navigating to the
    ODK Central API URL in your web browser. 

- Check that the ODK Central server is reachable from your network

    Make sure that your network is not blocking the connection to the
    ODK Central server. You can try pinging the server from your
    computer to see if there is a network issue. 

- Check that your firewall is not blocking the connection

    Make sure that your firewall is not blocking the connection to the
    ODK Central server. You can try temporarily disabling your
    firewall to see if this resolves the issue. 

- Check the ODK Central server logs

    Check the ODK Central server logs to see if there are any error
    messages related to the connection. This can help identify the
    root cause of the issue. 

- Try using a different web browser

    If you are having trouble connecting to ODK Central through a web
    browser, try using a different browser to see if the issue
    persists. It is possible that the issue is related to the browser
    or its settings. 

- Update OSM Fieldwork and ODK Central to the latest version

    Make sure that you are using the latest version of OSM Fieldwork
    and ODK Central. Check the OSM Fieldwork and ODK Central release
    notes to see if any updates address the issue you are
    experiencing. 
