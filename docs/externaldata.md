# Dealing with External Data in ODK

## External Datasets

[ODK Collect](https://www.getodk.org) has recently gained the ability
to load an external data file in GeoJson format of existing data. It's
now possible to select existing data and then import its values into
the XForm as default values. This lets the mapper use the XForm to
change the existing data, or add to it. Any changes will need to be
conflated later, that'll be another document.

**Why do I want to use ODK Collect to edit map data?** Much of what is
currently in [OpenStreetMap](https:www.openstreetmap.org) is lacking
metadata, or the data has changed, like when a restaurant changes
owners and gets a new name. Also most all remote mapping using
satellite imagery lacks tags beyond _building=yes_. When we are doing
a ground data collection project, we want to add useful tags like the
building material, or whether it's a cafe or a hospital.

Old imports also bring in problems, for example the infamous [TIGER
import](https://wiki.openstreetmap.org/wiki/TIGER). Mappers have been
cleaning that mess up for over a decade. But an old import may have a
weird value for an OSM tag, and it's usually better to update to a
more community approved data model. The beauty and the curse of OSM
data is its wonderful flexibility. People do invent new tags for a
specific mapping campaign or import that and escape being reviewed.
There are also typographical mistakes, weird capitalization, embedded
quote marks, and all sorts of weird values worth correcting.

## Creating the GeoJson file

When working with OSM data, there are multiple sources to obtain the required data. One option is to download a database dump from [GeoFabrik](http://download.geofabrik.de/index.html), which can be used as a flat file or imported into a database. Alternatively, Overpass Turbo can also be used to query the data directly. It's important to keep in mind that there is a translation between the column names obtained from querying the data and how ODK Collect views it. There is also a translation from ODK to OSM, and it's important to ensure that all translations work together seamlessly for a smooth data flow. To maintain clarity, it's best to keep all tags and values as similar as possible, with unique names. When using [ogr2ogr](https://gdal.org/programs/ogr2ogr.html) for data extraction from a Postgres database, there is more control than when using Overpass, and larger datasets can be processed.

To maintain consistency, the output column names can be redefined using the AS keyword in SQL queries, so that OSM standard names can be used in the survey and choices sheets. A technique for maintaining consistency is to append an _x_ to the end of each column name, so _healthcare_ becomes _healthcarex_. Then, in the XLSForm, _healthcarex_ can be used for the instance, and _xhealthcare_ can be used for the value in the calculation column in the survey sheet. The name column in the survey sheet can then be just _healthcare_, which will translate directly into its OSM tag equivalent.

It's possible to support almost any value using a text type in the XLSForm, but it's better to have an approved value for tag validation and completeness. If using a data model, the list of choices for a tag is defined, and anything outside of that will cause an error. Therefore, it's important to adhere to approved data models to avoid introducing errors or inconsistencies into the dataset. If the SQL query returns columns that aren't compatible with the XLSForm, XPATH errors will occur in ODK Collect.

If weird values are found in the data extract that continue to break ODK Collect, they must be removed manually. In that case, the weird values should be changed or deleted. At some point, it may be possible to write a filter program that uses the data model as defined in a YAML file, but this is not currently available.

## Debugging select_from file with GeoJson

Debugging complex interactions between the XLSForm, external data files, and ODK Collect can be a challenging task. Here are a few tricks to help debug what is going
on.

### Disable the map appearance

When working with external data, the _map value_ in the _appearance_ column of the survey sheet is often used. However, this can slow down the debugging process. To make it more efficient, you can turn off the map values and use the select menu instead. That works especially well
if you have a small data file for testing, because then it's easy to cycle between them.

To use the placement map, here's an example.

| type                                    | name     | label              | appearance |
| --------------------------------------- | -------- | ------------------ | ---------- |
| select_one_from_file camp_sites.geojson | existing | Existing Campsites | map        |

And an example where the values in the data file are an inline select
menu instead.

| type                                    | name     | label              | appearance |
| --------------------------------------- | -------- | ------------------ | ---------- |
| select_one_from_file camp_sites.geojson | existing | Existing Campsites | minimal    |

### Display calculated values

Often the bug you are trying to find is obscure, and you may not see any of the data file values being propagated into ODK Collect, even if it was working previously. In such cases, you can add a text survey question to display any of the values. Here's an example: 
| type      | name      | label            | calculation                                               | trigger     |
| --------- | --------- | ---------------- | --------------------------------------------------------- | ----------- |
| calculate | xid       | OSM ID           | instance(“camp_sites”)/root/item[id=${existing}]/id       |
| calculate | xlabel    | Get the label    | instance(“camp_sites”)/root/item[id=${existing}]/title    |             |
| calculate | xref      | Reference number | instance(“camp_sites”)/root/item[id=${existing}]/ref      |             |
| calculate | xlocation | Location         | instance(“camp_sites”)/root/item[id=${existing}]/geometry |             |
| calculate | xtourism  | camping type     | instance(“camp_sites”)/root/item[id=${existing}]/tourism  |             |
| calculate | xleisure  | leisure type     | instance(“camp_sites”)/root/item[id=${existing}]/leisure  |             |
| text      | debug1    | Leisure          | ${xleisure}                                               | ${existing} |
| text      | debug2    | OSM ID           | ${xid}                                                    | ${existing} |
| text      | debug3    | Ref number       | ${xref}                                                   | ${existing} |
| text      | debug4    | Tourism          | ${xtourism}                                               | ${existing} |

### Error Dialog

Assuming xls2xform is happy, sometimes you get this error message in
ODK Collect when switching screens. You'll see this when you have a
value in your data file for a _select_one_ survey question, but that
value is not in the list of values in the choices sheet for that tag. In
this example, there is no _doctor_ value in the _healthcare_
selection in the choices sheet.

![XPath Error](xlsimages/image1.jpg){width=500}
