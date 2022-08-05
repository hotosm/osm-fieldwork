# ODK Convert Utility Programs

ODK Convert contains a few standalone utility programs for converting
data from ODK Collect and the ODK Central server, and a few support
modules.

## CSVDump.py
convert CSV from ODK Central to OSM XML

	options:
		-h, --help            show this help message and exit
		-v [VERBOSE], --verbose [VERBOSE] - verbose output
		-i INFILE, --infile INFILE - The input file downloaded from ODK Central

## odk2csv.py
Convert ODK XML instance file to CSV format

	options:
		-h, --help            show this help message and exit
		-v [VERBOSE], --verbose [VERBOSE] - verbose output
		-i INSTANCE, --instance INSTANCE - The instance file from ODK Collect

These are the modules containing support functions. These need to be
loaded into the python package managber, pip, before they can be
used. For debugging purposes these can be run from the command line as
well.

	pip install -e .
	python setup.py install

## ODKDump.py
	options:
		-h, --help              - show this help message and exit
		-v, --verbose           - verbose output
		-i, --instance INSTANCE - The instance file from ODK Collect
		-x, --xform XFORM       - Load an alternal conversion file
		-o, --outdir            - The directory for the output file

## ODKForm.py
	options:
		-h, --help                           - show this help message and exit
		-v, --verbose,                       - verbose output
		-i, --infile XFORM, --instance XFORM - The definition file from ODK Collect

## ODKInstance.py
	options:
		-h, --help                       - show this help message and exit
		-v, --verbose                    - verbose output
		-i INSTANCE, --instance INSTANCE - The instance file from ODK Collect

## convert.py
This module uses the yaml config file to handle the conversion
process.

## osmfile.py
This module write OSM XML format output file.

## yamlfile.py
This reads in the yaml config file with all the conversion
information into a data structure that can be used when processing the
data conversion.
