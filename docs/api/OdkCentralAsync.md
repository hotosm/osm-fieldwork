# OdkCentral

::: osm_fieldwork.OdkCentralAsync.OdkCentral
options:
show_source: false
heading_level: 3

::: osm_fieldwork.OdkCentralAsync.OdkProject
options:
show_source: false
heading_level: 3

::: osm_fieldwork.OdkCentralAsync.OdkEntity
options:
show_source: false
heading_level: 3

## Usage

- An async context manager must be used (`async with`).
- As of 2024-04 the session and authentication must be handled manually.

```python
from osm_fieldwork.OdkCentralAsync import OdkProject

async with OdkProject(
    url="http://server.com",
    user="user@domain.com",
    passwd="password",
) as odk_central:
    await odk_central.create_session()
    await odk_central.authenticate()

    projects = await odk_central.listProjects()
```
