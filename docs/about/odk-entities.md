# ODK Entities

Entities are a concept introduced into ODK around 2022. The basic goal
of them is to allow updating of data using ODK, specifically by revisiting
specific things (features, people, whatever) and adding new data attached
to the same entity (data people refer to this as "longitudinal data"). For
example, revisiting the same patient in a clinical study, such that the
patient ID is constant and the new data from each visit is referenced to
the same person. For field mapping, the use-case is obvious: visit a
previously digitized building and add data from in-person observation or
surveying the people in it.

As of time of writing (March 2024), Entities in ODK are working and more
or less implemented, but not yet in wide use or well debugged.

# Use of Entities with FMTM

In FMTM, we want to:

- Be aware of features that have already been mapped
  - the ODK map views don't yet support styling features differently
    based on attributes like "already_field_mapped", so we're actually
    working on a navigation app within FMTM external to ODK, but we still
    hope that ODK Collect may support styling in the future, which will
    almost certainly be based on Entity attributes.
- Pre-fill questions in the form when features already have data attached
  to them (for example, if a building already has a "name" tag, the field
  mapper should see this pre-filled in the form, to be overwritted if wrong
  but otherwise swiped past).

The ODK core development team has strongly suggested that the FMTM team
use the Entities to achieve the above goals.

## Workflow Using Entities

The basic workflow would probably resemble:

- Create an Entity registration form.
  - In standard ODK settings, this simply means adding an `entities`
    tab to the XLSForm (as per
    [the example Entities form created by the ODK team](https://docs.google.com/spreadsheets/d/1xboXBJhIUlhs0wlblCxcQ3DB5Ubpx2AxLDuaXh_JYyw/edit#gid=2050654322).
    This seems to create what ODK refers to as a Dataset (in developer-facing documenation only;
    they avoid this word in user-facing documentation).
- Upload the Entities via the API:
  - There is currenltly no way to bulk upload Entities to a Dataset via the API.
  - Instead we must upload each Entity individually, including a geometry field
    in JavaRosa geometry format.
  - Until time of writing, FMTM creates geography attachments in GeoJSON,
    which does not work for Entities, which require a CSV file with a
    `geography` column (which must be in JavaRosa format, which no self-respecting
    GIS utility can export).
- Create a form for the data collection, referencing the `{dataset_name}.csv` for
  the `select_one_from_file` field.
- Dynamically insert the `task_id` field on the `choices` sheet, with `name` and
  `label` set to the task id (for filtering later).
- Create a field `task_id` in the survey, prior to the `select_one_from_file` field.
- Set `choice_filter` column to task_id=${task_id}, which links the selected task
  ID in the survey with the task_id field in the Entities (used for filtering).
- Load the form via intent, with `task_id` and `entity_id` fields in query params.
- On form completion we can update the Entity label and fields.
  - Set the field `status` to COMPLETE, IN_PROGRESS, INVALID.
  - Update the entity label to be prefixed with ✅ ❌ for a nicer visual cue.
    <https://docs.getodk.org/central-entities/#building-a-form-that-updates-an-entity>

# Resources

- [Here's the introductory page from ODK discussing the rationale for and use of Entities](https://docs.getodk.org/central-entities/). It has some example forms you can use to get started figuring out how to use Entities.
- [Here's the specification for Entities in the XForms language](https://getodk.github.io/xforms-spec/entities).
- [Here's the ODK Central API documentation for dealing with Entities](https://docs.getodk.org/central-api-entity-management/)
- [Here's the ODK Central API documentation for dealing with the "Datasets" they are part of](https://docs.getodk.org/central-api-form-management/#related-datasets)
- [Here's a discussion of how you can attach a draft form to an entity "dataset"](https://docs.getodk.org/central-api-form-management/#linking-a-dataset-to-a-draft-form-attachment)
