import pytest
import pandas as pd
from viadot.tasks import SAPBWToDF
from viadot.task_utils import credentials_loader

CREDENTIALS = credentials_loader.run(credentials_secret="SAP")
sapbw_task = SAPBWToDF(sapbw_credentials=CREDENTIALS.get("BW"))


@pytest.fixture(scope="session")
def output_variable():
    output = (
        {
            "RETURN": {
                "TYPE": "",
                "ID": "",
                "NUMBER": "000",
                "MESSAGE": "",
                "LOG_NO": "",
                "LOG_MSG_NO": "000000",
                "MESSAGE_V1": "",
                "MESSAGE_V2": "",
                "MESSAGE_V3": "",
                "MESSAGE_V4": "",
                "PARAMETER": "",
                "ROW": 0,
                "FIELD": "",
                "SYSTEM": "",
            },
            "STATISTIC": {"STEP": "003YPR44RQTVS3BSMZTKDYBMD"},
            "DATA": [
                {
                    "COLUMN": 0,
                    "ROW": 0,
                    "DATA": "January 2023",
                    "VALUE_DATA_TYPE": "CHAR",
                    "CELL_STATUS": "",
                },
                {
                    "COLUMN": 1,
                    "ROW": 0,
                    "DATA": "202301",
                    "VALUE_DATA_TYPE": "NUMC",
                    "CELL_STATUS": "",
                },
            ],
            "HEADER": [
                {
                    "COLUMN": 0,
                    "ROW": 0,
                    "DATA": "[0CALMONTH].[LEVEL01].[DESCRIPTION]",
                    "VALUE_DATA_TYPE": "CHAR",
                    "CELL_STATUS": "",
                },
                {
                    "COLUMN": 1,
                    "ROW": 0,
                    "DATA": "[0CALMONTH].[LEVEL01].[MEMBER_NAME]",
                    "VALUE_DATA_TYPE": "CHAR",
                    "CELL_STATUS": "",
                },
            ],
        },
        {
            "RETURN": {
                "TYPE": "",
                "ID": "",
                "NUMBER": "000",
                "MESSAGE": "",
                "LOG_NO": "",
                "LOG_MSG_NO": "000000",
                "MESSAGE_V1": "",
                "MESSAGE_V2": "",
                "MESSAGE_V3": "",
                "MESSAGE_V4": "",
                "PARAMETER": "",
                "ROW": 0,
                "FIELD": "",
                "SYSTEM": "",
            },
            "ROWS": 1,
            "STATISTIC": {"STEP": "003YPR44RQTVS3BSMZTKE0FH1"},
            "DATA_INFO": [
                {
                    "COLUMN_ORDINAL": 1,
                    "FIELD_NAME": "DIM1",
                    "DATA_TYPE": "CHAR",
                    "LENGTH": "000060",
                    "DECIMALS": 0,
                },
                {
                    "COLUMN_ORDINAL": 2,
                    "FIELD_NAME": "DIM2",
                    "DATA_TYPE": "NUMC",
                    "LENGTH": "000006",
                    "DECIMALS": 0,
                },
            ],
            "HEADER": [
                {
                    "COLUMN_ORDINAL": 1,
                    "ROW_ORDINAL": 1,
                    "DATA": "[0CALMONTH].[LEVEL01].[DESCRIPTION]",
                },
                {
                    "COLUMN_ORDINAL": 2,
                    "ROW_ORDINAL": 1,
                    "DATA": "[0CALMONTH].[LEVEL01].[MEMBER_NAME]",
                },
            ],
        },
    )
    yield output


@pytest.fixture(scope="session")
def user_mapping():
    mapping = {
        "[0CALMONTH].[LEVEL01].[DESCRIPTION]": "Calendar Year/Month",
        "[0CALMONTH].[LEVEL01].[MEMBER_NAME]": "Calendar Year/Month key",
    }
    yield mapping


@pytest.fixture(scope="session")
def mdx_query_variable():
    mdx_query = """
        SELECT
                {
            }
                ON COLUMNS,
        NON EMPTY
                { 
                    { [0CALMONTH].[202301] } 
        } 
        DIMENSION PROPERTIES
        DESCRIPTION,
        MEMBER_NAME
        ON ROWS

        FROM ZCSALORD1/ZBW4_ZCSALORD1_006_BOA
    
                """
    yield mdx_query


df_to_test = pd.DataFrame(
    data={
        "[0CALMONTH].[LEVEL01].[DESCRIPTION]": ["January 2023"],
        "[0CALMONTH].[LEVEL01].[MEMBER_NAME]": ["202301"],
        "date": ["2023-06-19 11:12:43+00:00"],
    },
)


def test_get_columns(output_variable):
    df_cols = sapbw_task.get_columns(output_variable)
    assert isinstance(df_cols, list)


def test_apply_user_mapping(user_mapping):
    apply_mapping = sapbw_task.apply_user_mapping(df_to_test, user_mapping)
    print(user_mapping.values())
    assert list(apply_mapping.columns) == list(user_mapping.values())
    assert isinstance(apply_mapping, pd.DataFrame)


def test_to_df(output_variable):
    df = sapbw_task.to_df(output_variable)
    assert isinstance(df, pd.DataFrame)


def test_run(mdx_query_variable, user_mapping):
    df = sapbw_task.run(mdx_query_variable, user_mapping)
    assert isinstance(df, pd.DataFrame)
