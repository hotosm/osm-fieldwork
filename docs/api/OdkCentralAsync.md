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

## Usage Example

- An async context manager must be used (`async with`).

```python
from osm_fieldwork.OdkCentralAsync import OdkProject

async with OdkProject(
    url="http://server.com",
    user="user@domain.com",
    passwd="password",
) as odk_central:
    projects = await odk_central.listProjects()
```
