#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022, 2023, 2024 Humanitarian OpenStreetMap Team
#
# This file is part of OSM-Fieldwork.
#
#     This is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with OSM-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

"""This script generates an XLS form with mandatory fields.

For use in data collection and mapping tasks.
The generated form includes metadata, survey questions, and settings
required for compatibility with HOT's FMTM tools.
It programmatically organizes form sections into metadata,
mandatory fields, and entities, and outputs them in a structured format.

Modules and functionalities:
- **Metadata Sheet**: Includes default metadata fields
    such as `start`, `end`, `username`, and `deviceid`.
- **Survey Sheet**: Combines metadata with mandatory fields required for FMTM workflows.
    - `warmup` for collecting initial location.
    - `feature` for selecting map geometry from predefined options.
    - `new_feature` for capturing GPS coordinates of new map features.
    - Calculated fields such as `form_category`, `xid`, `xlocation`, `status`, and others.
- **Entities Sheet**: Defines entity management rules to handle mapping tasks dynamically.
    - Includes rules for entity creation and updates with user-friendly labels.
- **Settings Sheet**: Sets the form ID, version, and configuration options.
"""

from datetime import datetime

import pandas as pd

current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

meta_data = [
    {"type": "start", "name": "start"},
    {"type": "end", "name": "end"},
    {"type": "today", "name": "today"},
    {"type": "phonenumber", "name": "phonenumber"},
    {"type": "deviceid", "name": "deviceid"},
    {"type": "username", "name": "username"},
    {
        "type": "email",
        "name": "email",
    },
]

meta_df = pd.DataFrame(meta_data)

mandatory_data = [
    {
        "type": "note",
        "name": "instructions",
        "label::english(en)": """Welcome ${username}. This survey form was generated
                            by HOT's FMTM to record ${form_category} map features.""",
        "label::nepali(ne)": """स्वागत छ ${username}। ${form_category} नक्सा Data रेकर्ड गर्न HOT को FMTM द्वारा
                            यो सर्वेक्षण फारम उत्पन्न भएको थियो।""",
    },
    {"notes": "Fields essential to FMTM"},
    {"type": "start-geopoint", "name": "warmup", "notes": "collects location on form start"},
    {"type": "select_one_from_file features.csv", "name": "feature", "label::english(en)": "Geometry", "appearance": "map"},
    {
        "type": "geopoint",
        "name": "new_feature",
        "label::english(en)": "Alternatively, take a gps coordinates of a new feature",
        "label::nepali(ne)": "वैकल्पिक रूपमा, नयाँ सुविधाको GPS निर्देशांक लिनुहोस्।",
        "appearance": "placement-map",
        "relevant": "${feature}= ''",
        "required": "yes",
    },
    {
        "type": "calculate",
        "name": "form_category",
        "label::english(en)": "FMTM form category",
        "appearance": "minimal",
        "calculation": "once('Unkown')",
    },
    {
        "type": "calculate",
        "name": "xid",
        "notes": "e.g. OSM ID",
        "label::english(en)": "Feature ID",
        "appearance": "minimal",
        "calculation": "if(${feature} != '', instance('features')/root/item[name=${feature}]/osm_id, '')",
    },
    {
        "type": "calculate",
        "name": "xlocation",
        "notes": "e.g. OSM Geometry",
        "label::english(en)": "Feature Geometry",
        "appearance": "minimal",
        "calculation": "if(${feature} != '', instance('features')/root/item[name=${feature}]/geometry, ${new_feature})",
        "save_to": "geometry",
    },
    {
        "type": "calculate",
        "name": "task_id",
        "notes": "e.g. FMTM Task ID",
        "label::english(en)": "Task ID",
        "appearance": "minimal",
        "calculation": "if(${feature} != '', instance('features')/root/item[name=${feature}]/task_id, '')",
        "save_to": "task_id",
    },
    {
        "type": "calculate",
        "name": "status",
        "notes": "Update the Entity 'status' field",
        "label::english(en)": "Mapping Status",
        "appearance": "minimal",
        "calculation": """if(${new_feature} != '', 2,
                        if(${building_exists} = 'no', 5,
                        if(${digitisation_correct} = 'no', 6,
                        ${status})))""",
        "default": "2",
        "trigger": "${new_feature}",
        "save_to": "status",
    },
    {
        "type": "select_one yes_no",
        "name": "building_exists",
        "label::english(en)": "Does this feature exist?",
        "label::nepali(ne)": "के यो भवन अवस्थित छ?",
        "relevant": "${feature} != '' ",
    },
    {
        "type": "calculate",
        "name": "submission_ids",
        "notes": "Update the submission ids",
        "label::english(en)": "Submission ids",
        "appearance": "minimal",
        "calculation": """if(
    instance('features')/root/item[name=${feature}]/submission_ids = '',
    ${instanceID},
    concat(instance('features')/root/item[name=${feature}]/submission_ids, ',', ${instanceID})
    )""",
        "save_to": "submission_ids",
    },
]

mandatory_df = pd.DataFrame(mandatory_data)

# Define the survey sheet
survey_df = pd.concat([meta_df, mandatory_df])

# Define entities sheet
entities_data = [
    {
        "list_name": "features",
        "entity_id": "coalesce(${feature}, uuid())",
        "create_if": "if(${new_feature}, true(), false())",
        "update_if": "if(${new_feature}, false(), true())",
        "label": """concat(if(${status} = '1', "🔒 ",
        if(${status} = '2', "✅ ", if(${status} = '5', "❌ ",
        if(${status} = '6', "❌ ", '')))), "Task ", ${task_id},
        " Feature ", if(${xid} != ' ', ${xid}, ' '))""",
    }
]
entities_df = pd.DataFrame(entities_data)

# Define the settings sheet
settings_data = [
    {
        "form_id": "mandatory_fields",
        "version": current_datetime,
        "form_title": "Mandatory Fields Form",
        "allow_choice_duplicates": "yes",
    }
]

settings_df = pd.DataFrame(settings_data)
