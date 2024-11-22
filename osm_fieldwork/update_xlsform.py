"""Update an existing XLSForm with additional fields useful for field mapping."""

import logging
from datetime import datetime
from io import BytesIO
from uuid import uuid4

import pandas as pd
from python_calamine.pandas import pandas_monkeypatch

from osm_fieldwork.xlsforms import xlsforms_path

log = logging.getLogger(__name__)

# Monkeypatch pandas to add calamine driver
pandas_monkeypatch()

# Constants
FEATURE_COLUMN = "feature"
NAME_COLUMN = "name"
SURVEY_GROUP_NAME = "survey_questions"


def standardize_xlsform_sheets(xlsform: dict) -> dict:
    """Standardizes column headers in both the 'survey' and 'choices' sheets of an XLSForm.

    - Strips spaces and lowercases all column headers.
    - Fixes formatting for columns with '::' (e.g., multilingual labels).

    Args:
        xlsform (dict): A dictionary with keys 'survey' and 'choices', each containing a DataFrame.

    Returns:
        dict: The updated XLSForm dictionary with standardized column headers.
    """

    def clean_column_name(col_name):
        if col_name == "label":
            return "label::english(en)"
        if "::" in col_name:
            # Handle '::' columns (e.g., 'label::english (en)')
            parts = col_name.split("::")
            language_part = parts[1].replace(" ", "").lower()  # Remove spaces and lowercase
            return f"{parts[0]}::{language_part}"
        return col_name.strip().lower()  # General cleanup

    # Apply cleaning to each sheet
    for _sheet_name, sheet_df in xlsform.items():
        sheet_df.columns = [clean_column_name(col) for col in sheet_df.columns]

    return xlsform


def merge_dataframes(mandatory_df: pd.DataFrame, user_question_df: pd.DataFrame, digitisation_df: pd.DataFrame):
    """Merge multiple Pandas dataframes together, removing duplicate fields."""
    # Remove empty rows from dataframes
    mandatory_df = filter_df_empty_rows(mandatory_df)
    user_question_df = filter_df_empty_rows(user_question_df)
    digitisation_df = filter_df_empty_rows(digitisation_df)

    # Handle matching translation fields for label, hint, required_message, etc.
    # FIXME this isn't working properly yet
    # mandatory_df, user_question_df, digitisation_df = handle_translations(
    #     mandatory_df, user_question_df, digitisation_df, fields=["label", "hint", "required_message"]
    # )

    if "list_name" in user_question_df.columns:
        merged_df = pd.concat(
            [
                mandatory_df,
                user_question_df,
                digitisation_df,
            ],
            ignore_index=True,
        )
        # NOTE here we remove duplicate PAIRS based on `list_name` and the name column
        # we have `allow_duplicate_choices` set in the settings sheet, so it is possible
        # to have duplicate NAME_COLUMN entries, if they are in different a `list_name`.
        return merged_df.drop_duplicates(subset=["list_name", NAME_COLUMN], ignore_index=True)

    # Else we are processing the survey sheet, continue

    # Find common fields between user_question_df and mandatory_df or digitisation_df
    duplicate_fields = set(user_question_df[NAME_COLUMN]).intersection(
        set(mandatory_df[NAME_COLUMN]).union(set(digitisation_df[NAME_COLUMN]))
    )

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


def handle_translations(
    mandatory_df: pd.DataFrame, user_question_df: pd.DataFrame, digitisation_df: pd.DataFrame, fields: list[str]
):
    """Handle translations, defaulting to English if no translations are present.

    Handles all field types that can be translated, such as
    'label', 'hint', 'required_message'.
    """
    for field in fields:
        # Identify translation columns for this field in the user_question_df
        translation_columns = [col for col in user_question_df.columns if col.startswith(f"{field}::")]

        if field in user_question_df.columns and not translation_columns:
            # If user_question_df has only the base field (e.g., 'label'), map English translation from mandatory and digitisation
            mandatory_df[field] = mandatory_df.get(f"{field}::english(en)", mandatory_df.get(field))
            digitisation_df[field] = digitisation_df.get(f"{field}::english(en)", digitisation_df.get(field))

            # Then drop translation columns
            mandatory_df = mandatory_df.loc[:, ~mandatory_df.columns.str.startswith("label::")]
            digitisation_df = digitisation_df.loc[:, ~digitisation_df.columns.str.startswith("label::")]

        else:
            # If translation columns exist, match them for mandatory and digitisation dataframes
            for col in translation_columns:
                mandatory_col = mandatory_df.get(col)
                digitisation_col = digitisation_df.get(col)
                if mandatory_col is not None:
                    mandatory_df[col] = mandatory_col
                if digitisation_col is not None:
                    digitisation_df[col] = digitisation_col

    return mandatory_df, user_question_df, digitisation_df


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


def create_survey_group(name: str) -> dict[str, pd.DataFrame]:
    """Helper function to create a begin and end group for XLSForm."""
    begin_group = pd.DataFrame(
        {
            "type": ["begin group"],
            "name": [name],
            "label::english(en)": [name],
            "label::swahili(sw)": [name],
            "label::french(fr)": [name],
            "label::spanish(es)": [name],
            "relevant": "(${new_feature} != '') or (${building_exists} = 'yes')",
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

    additional_row = pd.DataFrame(
        {
            "type": [f"select_one_from_file {entity_name}.csv"],
            "name": [entity_name],
            "label::english(en)": [entity_name],
            "appearance": ["map"],
            "label::swahili(sw)": [entity_name],
            "label::french(fr)": [entity_name],
            "label::spanish(es)": [entity_name],
        }
    )

    # Prepare the row for calculating coordinates based on the additional entity
    coordinates_row = pd.DataFrame(
        {
            "type": ["calculate"],
            "name": ["additional_geometry"],
            "calculation": [f"instance('{entity_name}')/root/item[name=${entity_name}]/geometry"],
            "label::English(en)": ["additional_geometry"],
            "label::Swahili(sw)": ["additional_geometry"],
            "label::French(fr)": ["additional_geometry"],
            "label::Spanish(es)": ["additional_geometry"],
        }
    )
    # Insert the new row into the DataFrame
    top_df = df.iloc[:row_index_to_split_on]
    bottom_df = df.iloc[row_index_to_split_on:]
    return pd.concat([top_df, additional_row, coordinates_row, bottom_df], ignore_index=True)


async def append_mandatory_fields(
    custom_form: BytesIO,
    form_category: str,
    additional_entities: list[str] = None,
    existing_id: str = None,
) -> tuple[str, BytesIO]:
    """Append mandatory fields to the XLSForm for use in FMTM.

    Args:
        custom_form(BytesIO): the XLSForm data uploaded, wrapped in BytesIO.
        form_category(str): the form category name (in form_title and description).
        additional_entities(list[str]): add extra select_one_from_file fields to
            reference an additional Entity list (set of geometries).
            The values should be plural, so that 's' will be stripped in the
            field name.
        existing_id(str): an existing UUID to use for the form_id, else random uuid4.

    Returns:
        tuple(str, BytesIO): the xFormId + the update XLSForm wrapped in BytesIO.
    """
    log.info("Appending field mapping questions to XLSForm")
    custom_sheets = pd.read_excel(custom_form, sheet_name=None, engine="calamine")
    mandatory_sheets = pd.read_excel(f"{xlsforms_path}/common/mandatory_fields.xls", sheet_name=None, engine="calamine")
    digitisation_sheets = pd.read_excel(f"{xlsforms_path}/common/digitisation_fields.xls", sheet_name=None, engine="calamine")
    custom_sheets = standardize_xlsform_sheets(custom_sheets)

    # Merge 'survey' and 'choices' sheets
    if "survey" not in custom_sheets:
        msg = "Survey sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)

    log.debug("Merging survey sheet XLSForm data")
    custom_sheets["survey"] = merge_dataframes(
        mandatory_sheets.get("survey"), custom_sheets.get("survey"), digitisation_sheets.get("survey")
    )
    # Hardcode the form_category value for the start instructions
    if form_category.endswith("s"):
        # Plural to singular
        form_category = form_category[:-1]
    form_category_row = custom_sheets["survey"].loc[custom_sheets["survey"]["name"] == "form_category"]
    if not form_category_row.empty:
        custom_sheets["survey"].loc[custom_sheets["survey"]["name"] == "form_category", "calculation"] = f"once('{form_category}')"

    # Ensure the 'choices' sheet exists in custom_sheets
    if "choices" not in custom_sheets or custom_sheets["choices"] is None:
        custom_sheets["choices"] = pd.DataFrame(columns=["list_name", "name", "label::english(en)"])

    log.debug("Merging choices sheet XLSForm data")
    custom_sheets["choices"] = merge_dataframes(
        mandatory_sheets.get("choices"), custom_sheets.get("choices"), digitisation_sheets.get("choices")
    )

    # Append or overwrite 'entities' and 'settings' sheets
    log.debug("Overwriting entities and settings XLSForm sheets")
    custom_sheets.update({key: mandatory_sheets[key] for key in ["entities", "settings"] if key in mandatory_sheets})
    if "entities" not in custom_sheets:
        msg = "Entities sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)
    if "settings" not in custom_sheets:
        msg = "Settings sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)

    # Set the 'version' column to the current timestamp (if 'version' column exists in 'settings')
    xform_id = existing_id if existing_id else uuid4()
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.debug(f"Setting xFormId = {xform_id} | form title = {form_category} | version = {current_datetime}")
    custom_sheets["settings"]["version"] = current_datetime
    custom_sheets["settings"]["form_id"] = xform_id
    custom_sheets["settings"]["form_title"] = form_category

    # Append select_one_from_file for additional entities
    if additional_entities:
        log.debug("Adding additional entity list reference to XLSForm")
        for entity_name in additional_entities:
            custom_sheets["survey"] = append_select_one_from_file_row(custom_sheets["survey"], entity_name)

    # Return spreadsheet wrapped as BytesIO memory object
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in custom_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    return (xform_id, output)
