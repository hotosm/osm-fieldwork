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

"""This script creates a DataFrame for digitization-related fields in the survey form.

These fields focus on verifying the accuracy of digitized locations,
capturing any issues with digitization, and adding additional notes or
images if required. The fields include logic for relevance, mandatory
requirements, and conditions based on user responses.

Returns:
    pd.DataFrame: A DataFrame containing the digitization-related fields.
"""

import pandas as pd

digitisation_fields = [
    {
        "type": "begin group",
        "name": "verification",
        "label::english(en)": "Verification",
        "relevant": "(${new_feature} != '') or (${building_exists} = 'yes')",
    },
    {
        "type": "select_one yes_no",
        "name": "digitisation_correct",
        "label::english(en)": "Is the digitized location for this feature correct?",
        "relevant": "(${new_feature} != '') or (${building_exists} = 'yes')",
        "calculation": "once(if(${new_feature} != '', 'yes', ''))",
        "read_only": "${new_feature} != ''",
        "required": "yes",
    },
    {
        "type": "select_one digitisation_problem",
        "name": "digitisation_problem",
        "label::english(en)": "What is wrong with the digitization?",
        "relevant": "${digitisation_correct}='no'",
    },
    {
        "type": "text",
        "name": "digitisation_problem_other",
        "label::english(en)": "You said “Other.” Please tell us what went wrong with the digitization!",
        "relevant": "${digitisation_problem}='other' ",
    },
    {"type": "end group"},
    {
        "type": "image",
        "name": "image",
        "label::english(en)": "Take a Picture",
        "apperance": "minimal",
        "parameters": "max-pixels=1000",
    },
    {
        "type": "note",
        "name": "end_note",
        "label::english(en)": "You can't proceed with data acquisition, if the building doesn't exist.",
        "relevant": "${building_exists} = 'no'",
    },
]

digitisation_df = pd.DataFrame(digitisation_fields)
