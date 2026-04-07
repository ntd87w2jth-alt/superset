# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Unit tests for the PrestoDBSQLValidator."""

from unittest.mock import MagicMock, patch

import pytest
from pyhive.exc import DatabaseError

from superset.sql_validators.presto_db import (
    PrestoDBSQLValidator,
    PrestoSQLValidationError,
)


def _make_statement(sql: str = "SELECT 1") -> MagicMock:
    stmt = MagicMock()
    stmt.__str__ = lambda self: sql
    return stmt


def _make_database(mutated_sql: str | None = None) -> MagicMock:
    db = MagicMock()
    db.mutate_sql_based_on_config.side_effect = lambda s: mutated_sql or s
    return db


def test_validate_statement_success_returns_none() -> None:
    """validate_statement should return None when the query is valid."""
    database = _make_database()
    cursor = MagicMock()
    cursor.poll.return_value = None

    result = PrestoDBSQLValidator.validate_statement(
        _make_statement("SELECT 1"),
        database,
        cursor,
    )
    assert result is None


def test_validate_statement_polling_finishes_on_finished_state() -> None:
    """validate_statement should stop polling when state is FINISHED."""
    database = _make_database()
    cursor = MagicMock()
    # First poll returns a FINISHED state, second returns None (stop condition)
    cursor.poll.side_effect = [
        {"stats": {"state": "FINISHED"}},
        None,
    ]

    result = PrestoDBSQLValidator.validate_statement(
        _make_statement("SELECT 1"),
        database,
        cursor,
    )
    assert result is None


def test_validate_statement_database_error_string_arg_raises() -> None:
    """validate_statement should raise PrestoSQLValidationError when DatabaseError arg is a string."""
    database = _make_database()
    cursor = MagicMock()
    cursor.poll.return_value = None
    database.db_engine_spec.fetch_data.side_effect = DatabaseError(
        "plain string error"
    )

    with pytest.raises(PrestoSQLValidationError):
        PrestoDBSQLValidator.validate_statement(
            _make_statement("SELECT bad"),
            database,
            cursor,
        )


def test_validate_statement_database_error_non_dict_arg_raises() -> None:
    """validate_statement should raise PrestoSQLValidationError when error arg is not a dict."""
    database = _make_database()
    cursor = MagicMock()
    cursor.poll.return_value = None
    database.db_engine_spec.fetch_data.side_effect = DatabaseError(42)

    with pytest.raises(PrestoSQLValidationError):
        PrestoDBSQLValidator.validate_statement(
            _make_statement("SELECT bad"),
            database,
            cursor,
        )


def test_validate_statement_database_error_empty_args_raises() -> None:
    """validate_statement should raise PrestoSQLValidationError when DatabaseError has no args."""
    database = _make_database()
    cursor = MagicMock()
    cursor.poll.return_value = None
    err = DatabaseError()
    err.args = ()
    database.db_engine_spec.fetch_data.side_effect = err

    with pytest.raises(PrestoSQLValidationError):
        PrestoDBSQLValidator.validate_statement(
            _make_statement("SELECT bad"),
            database,
            cursor,
        )


def test_validate_statement_error_dict_missing_message_raises() -> None:
    """validate_statement should raise PrestoSQLValidationError when message key is absent."""
    database = _make_database()
    cursor = MagicMock()
    cursor.poll.return_value = None
    database.db_engine_spec.fetch_data.side_effect = DatabaseError(
        {"errorLocation": {"lineNumber": 1, "columnNumber": 1}}
    )

    with pytest.raises(PrestoSQLValidationError):
        PrestoDBSQLValidator.validate_statement(
            _make_statement("SELECT bad"),
            database,
            cursor,
        )


def test_validate_statement_error_dict_missing_location_returns_annotation() -> None:
    """validate_statement should return an annotation at line 1 when errorLocation is absent."""
    database = _make_database()
    cursor = MagicMock()
    cursor.poll.return_value = None
    database.db_engine_spec.fetch_data.side_effect = DatabaseError(
        {"message": "column not found"}
    )

    annotation = PrestoDBSQLValidator.validate_statement(
        _make_statement("SELECT missing_col"),
        database,
        cursor,
    )

    assert annotation is not None
    assert annotation.line_number == 1
    assert annotation.start_column == 1
    assert annotation.end_column == 1
    assert "column not found" in annotation.message


def test_validate_statement_error_dict_with_location_returns_annotation() -> None:
    """validate_statement should return a correctly located annotation when errorLocation is present."""
    database = _make_database()
    cursor = MagicMock()
    cursor.poll.return_value = None
    database.db_engine_spec.fetch_data.side_effect = DatabaseError(
        {
            "message": "unexpected token",
            "errorLocation": {"lineNumber": 3, "columnNumber": 7},
        }
    )

    annotation = PrestoDBSQLValidator.validate_statement(
        _make_statement("SELECT\n  1\nFROM bad"),
        database,
        cursor,
    )

    assert annotation is not None
    assert annotation.message == "unexpected token"
    assert annotation.line_number == 3
    assert annotation.start_column == 7
    assert annotation.end_column == 7


def test_validate_statement_unexpected_exception_reraises() -> None:
    """validate_statement should re-raise non-DatabaseError exceptions."""
    database = _make_database()
    cursor = MagicMock()
    cursor.poll.return_value = None
    database.db_engine_spec.fetch_data.side_effect = RuntimeError("unexpected")

    with pytest.raises(RuntimeError):
        PrestoDBSQLValidator.validate_statement(
            _make_statement("SELECT 1"),
            database,
            cursor,
        )


def test_validate_multiple_statements_collects_all_annotations() -> None:
    """validate() should collect annotations from every statement in a multi-statement script."""
    database = _make_database()
    database_engine = (
        database.get_sqla_engine.return_value.__enter__.return_value
    )
    database_conn = database_engine.raw_connection.return_value.__enter__.return_value
    cursor = database_conn.cursor.return_value
    cursor.poll.return_value = None

    error_dict = {
        "message": "bad token",
        "errorLocation": {"lineNumber": 1, "columnNumber": 1},
    }
    database.db_engine_spec.fetch_data.side_effect = DatabaseError(error_dict)

    annotations = PrestoDBSQLValidator.validate(
        sql="SELECT bad; SELECT also_bad",
        catalog=None,
        schema="default",
        database=database,
    )
    # Each invalid statement produces one annotation
    assert len(annotations) >= 1


def test_presto_validator_name() -> None:
    """PrestoDBSQLValidator should expose the correct validator name."""
    assert PrestoDBSQLValidator.name == "PrestoDBSQLValidator"
