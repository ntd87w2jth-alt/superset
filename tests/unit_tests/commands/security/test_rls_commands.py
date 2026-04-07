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
"""Unit tests for the RLS (Row Level Security) commands."""

from unittest.mock import MagicMock, patch

import pytest

from superset.commands.exceptions import DatasourceNotFoundValidationError
from superset.commands.security.create import CreateRLSRuleCommand
from superset.commands.security.delete import DeleteRLSRuleCommand
from superset.commands.security.exceptions import RLSRuleNotFoundError
from superset.commands.security.update import UpdateRLSRuleCommand


# ---------------------------------------------------------------------------
# CreateRLSRuleCommand
# ---------------------------------------------------------------------------


@patch("superset.commands.security.create.db")
@patch("superset.commands.security.create.populate_roles")
def test_create_rls_rule_validate_resolves_tables_and_roles(
    mock_populate_roles: MagicMock,
    mock_db: MagicMock,
) -> None:
    """CreateRLSRuleCommand.validate() should resolve tables and roles into model objects."""
    mock_role = MagicMock()
    mock_table = MagicMock()
    mock_populate_roles.return_value = [mock_role]
    mock_db.session.query.return_value.filter.return_value.all.return_value = [
        mock_table
    ]

    data = {
        "name": "test rule",
        "filter_type": "Regular",
        "clause": "id = 1",
        "tables": [42],
        "roles": [1],
    }
    command = CreateRLSRuleCommand(data)
    command.validate()

    assert command._properties["tables"] == [mock_table]
    assert command._properties["roles"] == [mock_role]


@patch("superset.commands.security.create.db")
@patch("superset.commands.security.create.populate_roles")
def test_create_rls_rule_table_not_found_raises(
    mock_populate_roles: MagicMock,
    mock_db: MagicMock,
) -> None:
    """CreateRLSRuleCommand.validate() should raise DatasourceNotFoundValidationError when a table is missing."""
    mock_populate_roles.return_value = [MagicMock()]
    # Query returns fewer tables than requested (none found for the given id)
    mock_db.session.query.return_value.filter.return_value.all.return_value = []

    data = {
        "name": "rule",
        "filter_type": "Regular",
        "clause": "id = 1",
        "tables": [99],
        "roles": [1],
    }
    command = CreateRLSRuleCommand(data)
    with pytest.raises(DatasourceNotFoundValidationError):
        command.validate()


@patch("superset.commands.security.create.db")
@patch("superset.commands.security.create.populate_roles")
def test_create_rls_rule_no_tables_succeeds(
    mock_populate_roles: MagicMock,
    mock_db: MagicMock,
) -> None:
    """CreateRLSRuleCommand.validate() should succeed when the tables list is empty."""
    mock_populate_roles.return_value = []
    mock_db.session.query.return_value.filter.return_value.all.return_value = []

    data = {
        "name": "global rule",
        "filter_type": "Base",
        "clause": "1=1",
        "tables": [],
        "roles": [],
    }
    command = CreateRLSRuleCommand(data)
    command.validate()  # should not raise

    assert command._properties["tables"] == []
    assert command._properties["roles"] == []


def test_create_rls_rule_works_on_copy_of_data() -> None:
    """CreateRLSRuleCommand should store a copy of the data, not a reference."""
    data = {"name": "r", "tables": [1, 2], "roles": []}
    command = CreateRLSRuleCommand(data)

    # Mutating the original dict should not affect the command's internal state
    data["name"] = "mutated"
    assert command._properties["name"] == "r"


# ---------------------------------------------------------------------------
# UpdateRLSRuleCommand
# ---------------------------------------------------------------------------


@patch("superset.commands.security.update.db")
@patch("superset.commands.security.update.populate_roles")
@patch("superset.commands.security.update.RLSDAO")
def test_update_rls_rule_validate_success(
    mock_dao: MagicMock,
    mock_populate_roles: MagicMock,
    mock_db: MagicMock,
) -> None:
    """UpdateRLSRuleCommand.validate() should resolve model, tables, and roles."""
    existing_model = MagicMock()
    existing_model.id = 10
    mock_dao.find_by_id.return_value = existing_model
    mock_table = MagicMock()
    mock_db.session.query.return_value.filter.return_value.all.return_value = [
        mock_table
    ]
    mock_populate_roles.return_value = [MagicMock()]

    data = {
        "name": "updated rule",
        "filter_type": "Regular",
        "clause": "id = 2",
        "tables": [5],
        "roles": [2],
    }
    command = UpdateRLSRuleCommand(10, data)
    command.validate()

    assert command._model is existing_model
    assert command._properties["tables"] == [mock_table]


@patch("superset.commands.security.update.RLSDAO")
def test_update_rls_rule_not_found_raises(
    mock_dao: MagicMock,
) -> None:
    """UpdateRLSRuleCommand.validate() should raise RLSRuleNotFoundError when the rule does not exist."""
    mock_dao.find_by_id.return_value = None

    command = UpdateRLSRuleCommand(999, {"tables": [], "roles": []})
    with pytest.raises(RLSRuleNotFoundError):
        command.validate()


@patch("superset.commands.security.update.db")
@patch("superset.commands.security.update.populate_roles")
@patch("superset.commands.security.update.RLSDAO")
def test_update_rls_rule_table_not_found_raises(
    mock_dao: MagicMock,
    mock_populate_roles: MagicMock,
    mock_db: MagicMock,
) -> None:
    """UpdateRLSRuleCommand.validate() should raise DatasourceNotFoundValidationError when a table is missing."""
    existing_model = MagicMock()
    mock_dao.find_by_id.return_value = existing_model
    mock_populate_roles.return_value = []
    # Return fewer tables than requested
    mock_db.session.query.return_value.filter.return_value.all.return_value = []

    data = {"tables": [77], "roles": []}
    command = UpdateRLSRuleCommand(1, data)
    with pytest.raises(DatasourceNotFoundValidationError):
        command.validate()


# ---------------------------------------------------------------------------
# DeleteRLSRuleCommand
# ---------------------------------------------------------------------------


@patch("superset.commands.security.delete.RLSDAO")
def test_delete_rls_rule_validate_success(mock_dao: MagicMock) -> None:
    """DeleteRLSRuleCommand.validate() should populate the models list when all IDs are found."""
    mock_model_1 = MagicMock()
    mock_model_2 = MagicMock()
    mock_dao.find_by_ids.return_value = [mock_model_1, mock_model_2]

    command = DeleteRLSRuleCommand([1, 2])
    command.validate()

    assert command._models == [mock_model_1, mock_model_2]


@patch("superset.commands.security.delete.RLSDAO")
def test_delete_rls_rule_not_found_raises(mock_dao: MagicMock) -> None:
    """DeleteRLSRuleCommand.validate() should raise RLSRuleNotFoundError when no models are returned."""
    mock_dao.find_by_ids.return_value = []

    command = DeleteRLSRuleCommand([42])
    with pytest.raises(RLSRuleNotFoundError):
        command.validate()


@patch("superset.commands.security.delete.RLSDAO")
def test_delete_rls_rule_partial_ids_raises(mock_dao: MagicMock) -> None:
    """DeleteRLSRuleCommand.validate() should raise RLSRuleNotFoundError when only a subset of IDs is found."""
    mock_dao.find_by_ids.return_value = [MagicMock()]  # only 1 of 2 requested

    command = DeleteRLSRuleCommand([1, 2])
    with pytest.raises(RLSRuleNotFoundError):
        command.validate()


@patch("superset.commands.security.delete.RLSDAO")
def test_delete_rls_rule_single_id_validates(mock_dao: MagicMock) -> None:
    """DeleteRLSRuleCommand should handle a single-element ID list."""
    model = MagicMock()
    mock_dao.find_by_ids.return_value = [model]

    command = DeleteRLSRuleCommand([7])
    command.validate()

    assert command._models == [model]
