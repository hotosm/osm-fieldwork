## yamlfile.py

This reads in the yaml config file with all the conversion
information into a data structure that can be used when processing the
data conversion.

`yamlfile.py` is a module that reads in a YAML config file containing
information about how to convert data between different formats. The
config file contains a list of conversion rules, where each rule
specifies the source format, the target format, and any additional
information needed to perform the conversion. The module parses the
YAML file and creates a Python object representing the conversion
rules, which can be used by other code in the conversion process.

To use `yamlfile.py`, you first need to create a YAML config file
containing the conversion rules. Here's an example of a simple YAML
config file that converts CSV files to ODK Collect forms:

    - source: csv
    target: odk
    settings:
        form_id: my_form
        form_title: My Form
        form_version: 1.0
        csv_delimiter: ","

This rule specifies that CSV files should be converted to ODK Collect
forms, with the specified settings. The `settings` dictionary contains
additional information needed to perform the conversion, such as the
form ID, form title, form version, and the delimiter used in the CSV
file.

Once you have created the YAML config file, you can use `yamlfile.py`
to read it into a Python object. Here's an example of how to use the
`read_yaml_file()` function to read the YAML config file:

    import yamlfile

    config_file = 'my_config.yaml'
    conversion_rules = yamlfile.read_yaml_file(config_file)

This will read the `my_config.yaml` file and return a Python list
containing the conversion rules.

You can then use the conversion rules to perform the actual data
conversion. Here's an example of how to use the
`get_conversion_rule()` function to get the conversion rule for a
specific source and target format:

    import yamlfile

    config_file = 'my_config.yaml'
    conversion_rules = yamlfile.read_yaml_file(config_file)

    source_format = 'csv'
    target_format = 'odk'
    conversion_rule = yamlfile.get_conversion_rule(conversion_rules, source_format, target_format)

    # Perform the conversion using the conversion rule

This will search through the list of conversion rules for a rule that
matches the specified source and target format, and return the
matching rule. You can then use the conversion rule to perform the
actual data conversion.

Note that `yamlfile.py` relies on the PyYAML library to parse the YAML
file. If you don't have PyYAML installed, you will need to install it
using a package manager like `pip` before you can use `yamlfile.py`.

To handle errors when reading the YAML config file, `yamlfile.py`
raises a `YamlFileError` exception. This exception is raised if the
YAML file is not found, if the YAML file is malformed, or if a
required field is missing from the conversion rule. You can catch this
exception and handle it appropriately in your code.

Here's an example of how to catch the `YamlFileError` exception:

    import yamlfile

    config_file = 'my_config.yaml'

    try:
        conversion_rules = yamlfile.read_yaml_file(config_file)
    except yamlfile.YamlFileError as e:
        print(f"Error reading YAML file: {str(e)}")

This will catch any YamlFileError exceptions raised by
`read_yaml_file()` and print an error message.

In summary, `yamlfile.py` is a module that reads in a YAML config file
containing conversion rules and creates a Python object representing
the rules. This object can be used by other code in the data
conversion process. To use `yamlfile.py`, you need to create a YAML
config file containing conversion rules, and then use the
`read_yaml_file()` function to read the file into a Python object. You
can then use the object to get the conversion rule for a specific
source and target format, and perform the actual data conversion.
