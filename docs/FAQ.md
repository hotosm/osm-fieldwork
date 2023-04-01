# FAQ

**Q:** What is OSM Fieldwork?

**A:** OSM Fieldwork is a project to support field data collection using
[OpenDataKit](https://opendatakit.org/software/) and
[OpenStreetMap](https://www.openstreetmap.org). The primary
functionality is the ability to convert data collected with ODK
Collect into OSM XML. In addition it can also create satellite imagery
basemaps for [ODK Collect](https://docs.getodk.org/collect-intro/) and
[Osmand](https://osmand.net/). In addition there is a library of
[XLSForms](https://xlsform.org/en/) focused on humanitarian data
collection.

**Q:** How do I install OSM Fieldwork ?

**A:** You can install OSM Fieldwork using **pip install osm-fieldwork**

**Q:** Where can I find the source code and the XLSForm library ?

**A:** The git repository [is here](https://github.com/hotosm/osm-fieldwork)

**Q:** What language is Osm Fieldwork written in ?

**A:** OSM Fieldwork is written in Python and uses other modules like
[shapely](https://pypi.org/project/shapely/),
[pyxform](https://pypi.org/project/pyxform/),
[xmltodict](https://pypi.org/project/xmltodict/),
[psycopg2](https://pypi.org/project/psycopg/), and
[pandas](https://pypi.org/project/pandas/)

**Q:** What is the XLSForm library ?

**A:** The library of XLSForms are primarily focused on humanitarian
data collection, and follow data models designed by the [Humanitarian
Openstreetmap Team](https://www.hotosm.org) with consultation with
other [humanitarian
NGOs](https://en.wikipedia.org/wiki/Non-governmental_organization). These
are designed for efficient data collection and conversion to OSM XML
format to allow for easy and high quality contributions to the map.

**Q:** How can I report a bug or suggest a new feature for OSM
  Fieldwork ?

**A:** You can report bugs or suggest new features by opening an issue
  on the [OSM Fieldwork
  repository](https://github.com/hotosm/osm-fieldwork/issues) on
  GitHub. Be sure to provide as  much detail as possible, including
  steps to reproduce the bug and any relevant error messages.

**Q:** Do I need to have prior experience with XLSForms or python to
contribute to OSM Fieldwork ?

**A:** While prior experience with the various data formats usd by OSM
  Fieldwork is  helpful, it is not required to contribute to OSM
  Fieldwork. You can  start by reviewing the documentation, exploring
  the codebase, and contributing to issues labeled as **good first issue**.

**Q:** What types of contributions are needed ?

**A:** OSM Field is currently lacking a collection of test cases, which
will help maintain good quality. We would also like to have
[sphinx](https://www.sphinx-doc.org/) based documentation addd to the
code base.

**Q:** How can I get help or support for OSM Fieldwork ?

**A:** If you need help or support with XLSForms, you can reach out to the
  ODK community on the [ODK Forum](https://forum.getodk.org/). For
  questions on OSM Fieldwork you can open an issue on the OSM
  Fieldwork repository.

**Q:** What are the benefits of contributing to OSM Fieldwork?

**A:** Contributing to OSM Fieldwork allows you to help improve a widely
used tools for data collection.

**Q:** What is the license for OSM Fieldwork ?

**A:** OSM Fieldwork is
[AGPLv3](https://www.fsf.org/bulletin/2021/fall/the-fundamentals-of-the-agplv3),
because it encourages us to all work together. The XLSForms themselves
are under the [CC 4.0](https://creativecommons.org/licenses/by/4.0/)

**Q:** How can I test my changes to OSM Fieldwork ?

**A:** OSM Fieldwork has a suite of automated tests that you can run to
ensure that your changes do not introduce new bugs or break existing
functionality. You can run the tests locally on your computer using
the command-line interface or by setting up a continuous integration
environment on a platform like Travis CI.
