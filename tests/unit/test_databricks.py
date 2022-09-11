from viadot.sources import Databricks
import pandas as pd
import pytest
import copy

TEST_SCHEMA_ONEOFF = "viadot_test_schema_oneoff"
TEST_SCHEMA = "viadot_test_schema"
TEST_TABLE = "test_table"
FQN = f"{TEST_SCHEMA}.{TEST_TABLE}"

SOURCE_DATA = [
    {
        "Id": "wRACnHTeuw",
        "AccountId": 123,
        "Name": "Scott-Merritt",
        "FirstName": "Melody",
        "LastName": "Cook",
        "ContactEMail": "Melody.Cook@ScottMerritt.com",
        "MailingCity": "Elizabethfurt",
    },
    {
        "Id": "CFfTlqagNlpDu",
        "AccountId": 456,
        "Name": "Mann-Warren",
        "FirstName": "Wayne",
        "LastName": "Morrison",
        "ContactEMail": "Wayne.Morrison@MannWarren.com",
        "MailingCity": "Kathrynmouth",
    },
]
TEST_DF = pd.DataFrame(SOURCE_DATA)
ADDITIONAL_TEST_DATA = [
    {
        "Id": "UpsertTest2",
        "AccountId": 789,
        "Name": "new upsert-2",
        "FirstName": "Updated",
        "LastName": "Carter2",
        "ContactEMail": "Adam.Carter@TurnerBlack.com",
        "MailingCity": "Updated!Jamesport",
        "NewField": "New field vlaue",
    }
]
ADDITIONAL_DATA_NEW_FIELD_DF = pd.DataFrame(ADDITIONAL_TEST_DATA)
ADDITIONAL_DATA_DF = ADDITIONAL_DATA_NEW_FIELD_DF.copy().drop("NewField", axis=1)


@pytest.fixture(scope="session")
def databricks():

    databricks = Databricks(env="QA")
    databricks.create_schema(TEST_SCHEMA)

    yield databricks

    databricks.drop_table(schema=TEST_SCHEMA, table=TEST_TABLE)
    databricks.drop_schema(TEST_SCHEMA)
    databricks.session.stop()


@pytest.mark.dependency()
def test_create_schema(databricks):

    exists = databricks._check_if_schema_exists(TEST_SCHEMA_ONEOFF)
    assert exists is False

    created = databricks.create_schema(TEST_SCHEMA_ONEOFF)
    assert created is True

    exists = databricks._check_if_schema_exists(TEST_SCHEMA_ONEOFF)
    assert exists is True

    databricks.drop_schema(TEST_SCHEMA_ONEOFF)


@pytest.mark.dependency(depends=["test_create_schema"])
def test_drop_schema(databricks):

    exists = databricks._check_if_schema_exists(TEST_SCHEMA)
    assert exists is True

    dropped = databricks.drop_schema(TEST_SCHEMA)
    assert dropped is True

    exists = databricks._check_if_schema_exists(TEST_SCHEMA)
    assert exists is False

    databricks.create_schema(TEST_SCHEMA)


@pytest.mark.dependency()
def test_create_table(databricks):

    exists = databricks._check_if_table_exists(schema=TEST_SCHEMA, table=TEST_TABLE)
    assert exists is False

    created = databricks.create_table_from_pandas(
        schema=TEST_SCHEMA, table=TEST_TABLE, df=TEST_DF
    )
    assert created is True

    exists = databricks._check_if_table_exists(schema=TEST_SCHEMA, table=TEST_TABLE)
    assert exists is True


@pytest.mark.dependency(depends=["test_create_table"])
def test_drop_table(databricks):

    exists = databricks._check_if_table_exists(schema=TEST_SCHEMA, table=TEST_TABLE)
    assert exists is True

    dropped = databricks.drop_table(schema=TEST_SCHEMA, table=TEST_TABLE)
    assert dropped is True

    exists = databricks._check_if_table_exists(schema=TEST_SCHEMA, table=TEST_TABLE)
    assert exists is False


@pytest.mark.dependency(depends=["test_create_table", "test_drop_table"])
def test_to_df(databricks):

    databricks.create_table_from_pandas(
        schema=TEST_SCHEMA, table=TEST_TABLE, df=TEST_DF, if_exists="skip"
    )

    df = databricks.to_df(f"SELECT * FROM {FQN}")
    assert df.shape == TEST_DF.shape

    databricks.drop_table(schema=TEST_SCHEMA, table=TEST_TABLE)


@pytest.mark.dependency(depends=["test_create_table", "test_drop_table"])
def test_append(databricks):

    databricks.create_table_from_pandas(
        schema=TEST_SCHEMA, table=TEST_TABLE, df=TEST_DF, if_exists="skip"
    )

    appended = databricks.insert_into(
        schema=TEST_SCHEMA, table=TEST_TABLE, df=ADDITIONAL_DATA_DF
    )
    assert appended is True

    expected_result = TEST_DF.copy().append(ADDITIONAL_DATA_DF)
    result = databricks.to_df(f"SELECT * FROM {FQN}")
    assert result.shape == expected_result.shape

    databricks.drop_table(schema=TEST_SCHEMA, table=TEST_TABLE)


@pytest.mark.dependency(depends=["test_append"])
def test_insert_wrong_schema(databricks):
    with pytest.raises(ValueError):
        inserted = databricks.insert_into(
            schema="test_incorrect_schema",
            table=TEST_TABLE,
            df=ADDITIONAL_DATA_DF,
        )


@pytest.mark.dependency(depends=["test_append"])
def test_insert_non_existent_table(databricks):
    with pytest.raises(ValueError):
        inserted = databricks.insert_into(
            schema=TEST_SCHEMA,
            table="test_nonexistent_table",
            df=ADDITIONAL_DATA_DF,
            mode="append",
        )


# def test_full_refresh():
#     # Assert type and values returned after full refresh

#     table = "test_full_refresh_table"
#     fqn = f"{SCHEMA}.{table}"

#     databricks.create_table_from_pandas(schema=SCHEMA, table=table, df=df)

#     full_refresh_data = [
#         {
#             "Id": "wRACnHTeuw",
#             "AccountId": 123,
#             "Name": "Scott-Merritt",
#             "FirstName": "Melody",
#             "LastName": "Cook",
#             "ContactEMail": "Melody.Cook@ScottMerritt.com",
#             "MailingCity": "Elizabethfurt",
#         }
#     ]

#     full_refresh_df = pd.DataFrame(full_refresh_data)

#     did_insert = databricks.insert_into(
#         schema=SCHEMA, table=table, df=full_refresh_df, if_exists="replace"
#     )

#     assert did_insert

#     result = databricks.to_df(f"SELECT * FROM {fqn}")

#     assert result.shape == full_refresh_df.shape
#     databricks.drop_table(schema=SCHEMA, table=table)


def test_upsert(databricks):

    databricks.create_table_from_pandas(
        schema=TEST_SCHEMA, table=TEST_TABLE, df=TEST_DF
    )

    changed_record = copy.deepcopy(SOURCE_DATA[0])
    changed_record["ContactEMail"] = "new_email@new_domain.com"
    updated_data_df = pd.DataFrame(changed_record)
    primary_key = "Id"

    upserted = databricks.upsert(
        schema=TEST_SCHEMA,
        table=TEST_TABLE,
        df=updated_data_df,
        primary_key=primary_key,
    )
    assert upserted is True

    expected_result = df.append(upsert_df)
    result = databricks.to_df(f"SELECT * FROM {fqn}")
    assert result.shape == expected_result.shape

    databricks.drop_table(schema=SCHEMA, table=table)


@pytest.mark.dependency(depends=["test_create_table", "test_drop_table"])
def test_discover_schema(databricks):

    databricks.create_table_from_pandas(
        schema=TEST_SCHEMA, table=TEST_TABLE, df=TEST_DF, if_exists="skip"
    )

    expected_schema = {
        "Id": "string",
        "AccountId": "bigint",
        "Name": "string",
        "FirstName": "string",
        "LastName": "string",
        "ContactEMail": "string",
        "MailingCity": "string",
    }
    schema = databricks.discover_schema(schema=TEST_SCHEMA, table=TEST_TABLE)
    assert schema == expected_schema

    databricks.drop_table(schema=TEST_SCHEMA, table=TEST_TABLE)


# def test_rollback():
#     append_data = [
#         {
#             "Id": "UpsertTest2",
#             "AccountId": 789,
#             "Name": "new upsert-2",
#             "FirstName": "Updated",
#             "LastName": "Carter2",
#             "ContactEMail": "Adam.Carter@TurnerBlack.com",
#             "MailingCity": "Updated!Jamesport",
#         }
#     ]

#     table = "test_rollback"
#     fqn = f"{SCHEMA}.{table}"

#     databricks.create_table_from_pandas(schema=SCHEMA, table=table, df=df)

#     # Get the version of the table before applying any changes
#     version_number = databricks.get_table_version(schema=SCHEMA, table=table)

#     append_df = pd.DataFrame(append_data)

#     # Append to the table
#     did_insert = databricks.insert_into(
#         schema=SCHEMA, table=table, df=append_df, if_exists="append"
#     )
#     assert did_insert

#     # Rollback to the previous table version
#     databricks.rollback(schema=SCHEMA, table=table, version_number=version_number)
#     result = databricks.to_df(f"SELECT * FROM {fqn}")

#     assert df.shape == result.shape

#     databricks.drop_table(schema=SCHEMA, table=table)
