# FAQ

## Unable to connect to the ODKCentral server over http (i.e. insecure)

By default connections to the ODKCentral API verify the SSL certificate.

If you are running ODKCentral with a self-signed certificate, be sure to add the cert to your system trusted cert store. For Ubuntu/Debian, this would be:

```bash
sudo apt update && sudo apt install ca-certificates
sudo cp cert.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

If running ODKConvert within FMTM, this is handled for you.

As a last resort, you may disable SSL verification for the certificate, effectively connecting to ODKCentral insecurely. To do this add the `ODK_CENTRAL_SECURE=False` to your environment variables.
