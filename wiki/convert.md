# Convert.py

The convert.py module is part of the osm_fieldwork package and
provides functionality for converting ODK forms to OSM XML using a
YAML configuration file.

Even if an XLSForm is carefully designed to have a one to one match
between ODK and [OSM](https://www.openstreetmap.org), this is not
always possible, as not all survey questions are for OSM.

## The Config File Sections

There are several sections the config file. The default one is called
**xforms.yaml**, and is included in the sources and the python
package. It is possible to use a different config file.

### convert

This section supports one to one conversion of tags, as well as one to
many. This example shows all poossible conversion types. The simple
ones like _altitude_ just change the tag, and the value is used
unchanged. A more complicated conversion is changing the value in
addition to the tag. Anything with an equals sign is split into the
appropriate tag and value for OSM. The final one is where a singe
survey question creates multiple tahg and value pairs, deliminated by
a comma. Each of the pairs is handled as a separate tag and value in
OSM.
	
	convert:
		- latitude: lat
		- longitude: lon
		- altitude: ele
		- cemetery_services:
			- cemetery: amenity=grave_yard
			- cremation: amenity=crematorium
		- amenity:
			- coffee: amenity=cafe,cuisine=coffee_shop
	...

### private

Not all collected data is suitable for OSM. This may include data that
has no equivalant tag in OSM, or personal data. 

	private:
		- income
		- age
		- gender
		- education

### ignore

ODK supports many tags useful only internally. These go into the
ignore section of the config file. Any tag in this section gets
removed from from all output files. An example would be this:

	ignore:
		- attachmentsexpected
		- attachmentspresent
		- reviewstate
		- edits
		- gps_type
		- accuracy
		- deviceid
	...


### multiple

Not all survey questions have a single answer. Anything using
**select_multiple** may have more than one value. As the default
assumes one answer per question, this specifies the questions with
multiple answers since they have to be processed seperately. The
normal conversion process is applied to these too.

	multiple:
		- healthcare
		- amenity_type
		- specialty
