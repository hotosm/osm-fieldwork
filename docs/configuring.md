# Configuring the Data Conversion

ODKConvert uses a YAML-based configuration file that controls the
conversion process. While ideally, the tags in the XForm are a match
for OSM tags, some survey questions generate very different primary
tags. All of the strings in this file are lowercase, as when
processing the CSV file, everything is forced to be lowercase.

YAML is a simple syntax, and most of the config options are simply
lists. For example:

    # All of the data that goes in a different non-OSM file
    private:
      - income
      - age
      - gender

There are 3 sections in the config file, _ignore_, _convert_, and
_private_. Anything in the _ignore_ section gets left out of all data
processing and output files. Anything in the _private_ section is kept
out of the OXM output file, but included in a separate GeoJson
formatted file. That file contains all the data from whoever is
organizing this mapping campaign. There are often data items like
_gender_ that don't belong in OSM, but that information is useful
to the organizers. Anything in the _convert_ section is the real
control of the conversion process.

### Here is an example of a configuration file with explanations of its different sections and options explained in detail:

    #ignore section
    ignore:
      - respondent_name
      - survey_date

    #private section
    private:
      - age
      - gender

    #convert section
    convert:
      #example of a simple conversion
      - waterpoint:
        - well: man_made=water_well
        - natural: natural=water
      #example of a conversion with multiple OSM tags
      - power:
        - solar: generator::source=solar,power=generator
        - wind: generator::source=wind,power=generator
        - hydro: generator::source=hydro,power=generator
        - geothermal: generator::source=geothermal,power=generator
        - grid: generator::source=electricity_network,power=generator

The configuration file has three sections: ignore, private, and convert.

The ignore section lists the names of data fields that should be ignored during the conversion process. These fields will not be included in any output files.

The private section lists the names of data fields that are considered private and should not be included in the OSM output file. However, they will be included in a separate GeoJson formatted file. This file contains all the data from whoever is organizing the mapping campaign. An example of private data is gender, which is useful to the organizers but not relevant to OSM.

The convert section is the real control of the conversion process. It lists the survey questions and their corresponding OSM tags and values. In this section, each survey question is represented by a tag name, and each answer to the survey question is represented by a value. If the answer matches the value, it returns both the tag and the value for OSM. An equal sign is used to delimit them.

For example, in the configuration file above, the survey question about waterpoints has two possible answers: "well" and "natural". If the answer is "well", the corresponding OSM tag and value is "man_made=water_well". If the answer is "natural", the corresponding OSM tag and value is "natural=water".

Another example in the same configuration file is the survey question about power sources. This survey question has five possible answers: "solar", "wind", "hydro", "geothermal", and "grid". Each answer corresponds to multiple OSM tags and values, which are separated by commas.

For example, if the answer is "solar", the corresponding OSM tags and values are "generator::source=solar" and "power=generator". The double colon is used to represent a hierarchy in the OSM tags. In this example, the generator source is solar, and the power source is a generator.

Both ODK and OSM use a _tag/value_ pair. In OSM, the tags and values
are documented, and the mapping community prefers people use the
commonly accepted values. In ODK, the tags and values can be anything
the developer of the XLSForm chooses. Depending on the answer to the
survey question, that may be converted to a variety of OSM tags and
values.

For this example, the value used in the **name** column of the XLSForm
_survey_ sheet is _waterpoint_. It has several values listed
underneath. Each of those is for the answer given to the waterpoint
survey question. If the answer matches the value, it returns both the
tag and the value for OSM. An equal sign is used to deliminate them.

    - waterpoint:
      - well: man_made=water_well
      - natural: natural=water

Some features have multiple OSM tags for a single survey question
answer. To handle this case, all entries are deliminated by a comma.

    - power:
      - solar: generator::source=solar,power=generator
      - wind: generator::source=wind,power=generator
      - hydro: generator::source=hydro,power=generator
      - geothermal: generator::source=geothermal,power=generator
      - grid: generator::source=electricity_network,power=generator

Overall, the configuration file is a powerful tool for customizing the conversion of ODK data into OSM tags and values. By carefully defining the ignore, private, and convert sections, you can control the output of the conversion process and ensure that it meets your needs.
