## 0.1.0 (2023-03-25)

### Feat

- set ssl verify via environment variable, default true
- option to configure standalone odkconvert via env vars
- index for xform files, plus path

### Fix

- update logging
- listProjects and findAppUser methods for OdkCentral, update logging
- relative imports --> absolute imports for packaging
- update verify=True for urllib to verify certs
- allow listProjects to fail gracefully if none exist
- typo for religious
- makefile zip bundle, pyproject version attr
- update paths for xforms.yaml, fix CSVDump.parse

### Refactor

- rename xforms to xlsforms throughout code
- rename xform dir to xlsform, more descriptive
- rename xforms path var for clarity
- remove redundant csv output files from xforms
- update refs to xforms dir and odk_client.py
- rename XForms dir to lowercase xforms
- add includes to pyproject to bundle odkconvert dir
- missed yaml file for restructure
- rename test dir to pytest default (tests)
- restructure, move .py files to odkconvert dir
