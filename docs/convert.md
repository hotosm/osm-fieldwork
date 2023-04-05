## convert.py

The convert.py module is part of the osm_fieldwork package and
provides functionality for converting ODK forms between different
formats using a YAML configuration file.

### Usage:

To use convert.py, you'll need to create a YAML configuration file
that specifies the input and output formats for the conversion
process. Here's an example configuration file:

    input:
      type: xlsform
      path: path/to/form.xls

    output:
      type: odk
      path: path/to/converted/form

In this example, we're specifying that the input form is an XLSForm
located at 'path/to/form.xls', and that the output format should be
ODK, with the converted form saved to 'path/to/converted/form'.

Once you have a configuration file, you can use convert.py from the
command line by running the following command:

    [path]/convert.py path/to/config.yaml

This will start the conversion process using the specified
configuration file. The converted form will be saved to the path
specified in the configuration file.

### Supported Formats:

convert.py supports the following input and output formats:

- XLSForm: A format for creating ODK forms using a spreadsheet.
- ODK: The native format used by ODK Collect for storing forms and collected data.
- GeoJson: A lightweight data-interchange format.
- CSV: A common format for storing tabular data

Note that convert.py does not support all possible variations of these
formats. For example, some advanced features of XLSForm may not be
supported.

### Configuration File Options:

The following options are available in the configuration file:

- input:
    - type: The input format (e.g. xlsform, odk, json, csv).
    - path: The path to the input file.
- output:
    - type: The output format (e.g. odk, json, csv).
    - path: The path to save the converted output file.

### Example:
Here's an example of how to use convert.py to convert an XLSForm to ODK format:

    input:
      type: xlsform
      path: path/to/form.xls

    output:
      type: odk
      path: path/to/converted/form

And then run the following command:

    [path]/convert.py path/to/config.yaml

In this example, we're specifying that the input form is an XLSForm
located at 'path/to/form.xls', and that the output format should be
ODK, with the converted form saved to
'path/to/converted/form'. Running the command will start the
conversion process using the specified configuration file.

