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
"""Unit tests for the sql_validators base module."""

import pytest

from superset.sql_validators.base import BaseSQLValidator, SQLValidationAnnotation


def test_sql_validation_annotation_stores_all_fields() -> None:
    """SQLValidationAnnotation should retain all constructor arguments."""
    annotation = SQLValidationAnnotation(
        message="syntax error",
        line_number=5,
        start_column=10,
        end_column=20,
    )
    assert annotation.message == "syntax error"
    assert annotation.line_number == 5
    assert annotation.start_column == 10
    assert annotation.end_column == 20


def test_sql_validation_annotation_to_dict_full() -> None:
    """to_dict() should return a dict with all four keys populated."""
    annotation = SQLValidationAnnotation(
        message="unexpected token",
        line_number=3,
        start_column=1,
        end_column=7,
    )
    result = annotation.to_dict()
    assert result == {
        "line_number": 3,
        "start_column": 1,
        "end_column": 7,
        "message": "unexpected token",
    }


def test_sql_validation_annotation_to_dict_none_values() -> None:
    """to_dict() should include None for optional column/line fields."""
    annotation = SQLValidationAnnotation(
        message="unknown error",
        line_number=None,
        start_column=None,
        end_column=None,
    )
    result = annotation.to_dict()
    assert result == {
        "line_number": None,
        "start_column": None,
        "end_column": None,
        "message": "unknown error",
    }


def test_sql_validation_annotation_to_dict_keys() -> None:
    """to_dict() should always contain exactly the expected four keys."""
    annotation = SQLValidationAnnotation(
        message="msg",
        line_number=1,
        start_column=2,
        end_column=3,
    )
    assert set(annotation.to_dict().keys()) == {
        "line_number",
        "start_column",
        "end_column",
        "message",
    }


def test_base_sql_validator_validate_raises_not_implemented() -> None:
    """BaseSQLValidator.validate() should raise NotImplementedError."""
    from unittest.mock import MagicMock

    database = MagicMock()
    with pytest.raises(NotImplementedError):
        BaseSQLValidator.validate("SELECT 1", None, "public", database)
