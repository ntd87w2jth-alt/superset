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
"""Unit tests for the PostgreSQLValidator."""

from unittest.mock import MagicMock, patch

import pytest

from superset.sql_validators.postgres import PostgreSQLValidator
from superset.sql_validators.base import SQLValidationAnnotation


@pytest.fixture
def mock_database() -> MagicMock:
    return MagicMock()


def test_postgres_validator_valid_sql(mock_database: MagicMock) -> None:
    """PostgreSQLValidator should return an empty list when pgsanity reports valid SQL."""
    with patch(
        "superset.sql_validators.postgres.check_string",
        return_value=(True, None),
    ):
        annotations = PostgreSQLValidator.validate(
            sql="SELECT 1",
            catalog=None,
            schema="public",
            database=mock_database,
        )
    assert annotations == []


def test_postgres_validator_invalid_sql_with_line_number(
    mock_database: MagicMock,
) -> None:
    """PostgreSQLValidator should parse the line number and message from pgsanity errors."""
    error_msg = "line 2: ERROR: syntax error at or near \"FROOOM\""
    with patch(
        "superset.sql_validators.postgres.check_string",
        return_value=(False, error_msg),
    ):
        annotations = PostgreSQLValidator.validate(
            sql="SELECT 1\nFROOOM table",
            catalog=None,
            schema="public",
            database=mock_database,
        )

    assert len(annotations) == 1
    annotation = annotations[0]
    assert annotation.line_number == 2
    assert annotation.message == 'ERROR: syntax error at or near "FROOOM"'
    assert annotation.start_column is None
    assert annotation.end_column is None


def test_postgres_validator_invalid_sql_without_line_number(
    mock_database: MagicMock,
) -> None:
    """PostgreSQLValidator should handle errors that don't contain a line number."""
    error_msg = "ERROR: some general parse failure"
    with patch(
        "superset.sql_validators.postgres.check_string",
        return_value=(False, error_msg),
    ):
        annotations = PostgreSQLValidator.validate(
            sql="bad sql",
            catalog=None,
            schema=None,
            database=mock_database,
        )

    assert len(annotations) == 1
    annotation = annotations[0]
    assert annotation.line_number is None
    assert annotation.message == error_msg


def test_postgres_validator_returns_single_annotation_per_call(
    mock_database: MagicMock,
) -> None:
    """PostgreSQLValidator should return exactly one annotation per invalid query."""
    with patch(
        "superset.sql_validators.postgres.check_string",
        return_value=(False, "line 1: ERROR: unexpected token"),
    ):
        annotations = PostgreSQLValidator.validate(
            sql="INVALID",
            catalog=None,
            schema="",
            database=mock_database,
        )
    assert len(annotations) == 1
    assert isinstance(annotations[0], SQLValidationAnnotation)


def test_postgres_validator_name() -> None:
    """PostgreSQLValidator should expose the correct validator name."""
    assert PostgreSQLValidator.name == "PostgreSQLValidator"
