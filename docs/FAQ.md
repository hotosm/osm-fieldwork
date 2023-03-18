# FAQ

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
