"""Update an existing XLSForm with additional fields useful for field mapping."""

from datetime import datetime
from io import BytesIO
from uuid import uuid4

import pandas as pd
from python_calamine.pandas import pandas_monkeypatch

from osm_fieldwork.xlsforms import xlsforms_path

# Monkeypatch pandas to add calamine driver
pandas_monkeypatch()

# Constants
FEATURE_COLUMN = "feature"
NAME_COLUMN = "name"
SURVEY_GROUP_NAME = "survey_questions"


def filter_df_empty_rows(df: pd.DataFrame, column: str = NAME_COLUMN):
    """Remove rows with None values in the specified column.

    NOTE We retain 'end group' and 'end group' rows even if they have no name.
    NOTE A generic df.dropna(how="all") would not catch accidental spaces etc.
    """
    if column in df.columns:
        # Only retain 'begin group' and 'end group' if 'type' column exists
        if "type" in df.columns:
            return df[(df[column].notna()) | (df["type"].isin(["begin group", "end group", "begin_group", "end_group"]))]
        else:
            return df[df[column].notna()]
    return df


def merge_dataframes(mandatory_df: pd.DataFrame, user_question_df: pd.DataFrame, digitisation_df: pd.DataFrame):
    """Merge multiple Pandas dataframes together, removing duplicate fields."""
    # Remove empty rows from dataframes
    mandatory_df = filter_df_empty_rows(mandatory_df)
    user_question_df = filter_df_empty_rows(user_question_df)
    digitisation_df = filter_df_empty_rows(digitisation_df)

    # Find common fields between user_question_df and mandatory_df or digitisation_df
    # We use this to remove duplicates from the survey, giving our fields priority
    duplicate_fields = set(user_question_df[NAME_COLUMN]).intersection(
        set(mandatory_df[NAME_COLUMN]).union(set(digitisation_df[NAME_COLUMN]))
    )

    # Is choices sheet, return ordered merged choices
    if "list_name" in user_question_df.columns:
        user_question_df_filtered = user_question_df[~user_question_df[NAME_COLUMN].isin(duplicate_fields)]

        return pd.concat(
            [
                mandatory_df,
                user_question_df_filtered,
                digitisation_df,
            ],
            ignore_index=True,
        )

    # Else we are processing the survey sheet, continue

    # NOTE filter out 'end group' from duplicate check as they have empty NAME_COLUMN
    end_group_rows = user_question_df[user_question_df["type"].isin(["end group", "end_group"])]
    user_question_df_filtered = user_question_df[
        (~user_question_df[NAME_COLUMN].isin(duplicate_fields)) | (user_question_df.index.isin(end_group_rows.index))
    ]

    # Create survey group wrapper
    survey_group = create_survey_group(SURVEY_GROUP_NAME)

    # Concatenate dataframes in the desired order
    return pd.concat(
        [
            mandatory_df,
            # Wrap the survey question in a group
            survey_group["begin"],
            user_question_df_filtered,
            survey_group["end"],
            digitisation_df,
        ],
        ignore_index=True,
    )


def create_survey_group(name: str) -> dict[str, pd.DataFrame]:
    """Helper function to create a begin and end group for XLSForm."""
    begin_group = pd.DataFrame(
        {
            "type": ["begin group"],
            "name": [name],
            "label::English(en)": [name],
            "label::Swahili(sw)": [name],
            "label::French(fr)": [name],
            "label::Spanish(es)": [name],
            "relevant": "(${new_feature} = 'yes') or (${building_exists} = 'yes')",
        }
    )
    end_group = pd.DataFrame(
        {
            "type": ["end group"],
        }
    )
    return {"begin": begin_group, "end": end_group}


def append_select_one_from_file_row(df: pd.DataFrame, entity_name: str) -> pd.DataFrame:
    """Add a new select_one_from_file question to reference an Entity."""
    # Find the row index where name column = 'feature'
    select_one_from_file_index = df.index[df[NAME_COLUMN] == FEATURE_COLUMN].tolist()

    if not select_one_from_file_index:
        raise ValueError(f"Row with '{NAME_COLUMN}' == '{FEATURE_COLUMN}' not found in survey sheet.")

    # Find the row index after 'feature' row
    row_index_to_split_on = select_one_from_file_index[0] + 1
    # Strip the 's' from the end for singular form
    if entity_name.endswith("s"):
        # Plural to singular
        entity_name = entity_name[:-1]

    additional_row = pd.DataFrame(
        {
            "type": [f"select_one_from_file {entity_name}.csv"],
            "name": [entity_name],
            "label::English(en)": [entity_name],
            "appearance": ["map"],
            "choice_filter": ["selected(${task_filter}, '') or task_id=${task_filter}"],
            "trigger": ["${task_filter}"],
            "label::Swahili(sw)": [entity_name],
            "label::French(fr)": [entity_name],
            "label::Spanish(es)": [entity_name],
        }
    )

    # Insert the new row into the DataFrame
    top_df = df.iloc[:row_index_to_split_on]
    bottom_df = df.iloc[row_index_to_split_on:]
    return pd.concat([top_df, additional_row, bottom_df], ignore_index=True)


def append_task_ids_to_choices_sheet(df: pd.DataFrame, task_count: int) -> pd.DataFrame:
    """Add task id rows to choices sheet (for filtering Entity list)."""
    task_ids = list(range(1, task_count + 1))

    additional_rows = pd.DataFrame(
        {
            "list_name": ["task_filter"] * task_count,
            "name": task_ids,
            "label::English(en)": task_ids,
            "label::Swahili(sw)": task_ids,
            "label::French(fr)": task_ids,
            "label::Spanish(es)": task_ids,
        }
    )

    df = pd.concat([df, additional_rows], ignore_index=True)
    return df


async def append_mandatory_fields(
    custom_form: BytesIO,
    form_category: str,
    additional_entities: list[str] = None,
    task_count: int = None,
    existing_id: str = None,
) -> BytesIO:
    """Append mandatory fields to the XLSForm for use in FMTM.

    Args:
        custom_form(BytesIO): the XLSForm data uploaded, wrapped in BytesIO.
        form_category(str): the form category name (in form_title and description).
        additional_entities(list[str]): add extra select_one_from_file fields to
            reference an additional Entity list (set of geometries).
            The values should be plural, so that 's' will be stripped in the
            field name.
        task_count(int): number of tasks, used to generate task_id entries in choices
            sheet. These are used to filter Entities by task id in ODK Collect.
        existing_id(str): an existing UUID to use for the form_id, else random uuid4.

    Returns:
        BytesIO: the update XLSForm, wrapped in BytesIO.
    """
    custom_sheets = pd.read_excel(custom_form, sheet_name=None, engine="calamine")
    mandatory_sheets = pd.read_excel(f"{xlsforms_path}/common/mandatory_fields.xls", sheet_name=None, engine="calamine")
    digitisation_sheets = pd.read_excel(f"{xlsforms_path}/common/digitisation_fields.xls", sheet_name=None, engine="calamine")

    # Merge 'survey' and 'choices' sheets
    if "survey" in custom_sheets:
        custom_sheets["survey"] = merge_dataframes(
            mandatory_sheets.get("survey"), custom_sheets.get("survey"), digitisation_sheets.get("survey")
        )
        # Hardcode the form_category value for the start instructions
        if form_category.endswith("s"):
            # Plural to singular
            form_category = form_category[:-1]
        form_category_row = custom_sheets["survey"].loc[custom_sheets["survey"]["name"] == "form_category"]
        if not form_category_row.empty:
            custom_sheets["survey"].loc[custom_sheets["survey"]["name"] == "form_category", "calculation"] = (
                f"once('{form_category}')"
            )

    if "choices" in custom_sheets:
        custom_sheets["choices"] = merge_dataframes(
            mandatory_sheets.get("choices"), custom_sheets.get("choices"), digitisation_sheets.get("choices")
        )

    # Append or overwrite 'entities' and 'settings' sheets
    custom_sheets.update({key: mandatory_sheets[key] for key in ["entities", "settings"] if key in mandatory_sheets})

    # Set the 'version' column to the current timestamp (if 'version' column exists in 'settings')
    if "settings" in custom_sheets:
        custom_sheets["settings"]["version"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        custom_sheets["settings"]["form_id"] = existing_id if existing_id else uuid4()
        custom_sheets["settings"]["form_title"] = form_category

    # Append select_one_from_file for additional entities
    if additional_entities:
        for entity_name in additional_entities:
            custom_sheets["survey"] = append_select_one_from_file_row(custom_sheets["survey"], entity_name)

    # Append task id rows to choices sheet
    if task_count:
        custom_sheets["choices"] = append_task_ids_to_choices_sheet(custom_sheets["choices"], task_count)
    else:
        # NOTE here we must append a single task_id entry to make it a valid form
        custom_sheets["choices"] = append_task_ids_to_choices_sheet(custom_sheets["choices"], 1)

    # Return spreadsheet wrapped as BytesIO memory object
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in custom_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    return output
