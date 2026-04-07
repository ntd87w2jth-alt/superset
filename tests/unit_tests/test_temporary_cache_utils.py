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
"""Unit tests for the temporary_cache utility functions."""

import pytest

from superset.temporary_cache.utils import cache_key, SEPARATOR


def test_cache_key_single_arg() -> None:
    """cache_key with a single string argument should return the string unchanged."""
    assert cache_key("abc") == "abc"


def test_cache_key_multiple_string_args() -> None:
    """cache_key should join multiple string arguments with the SEPARATOR."""
    result = cache_key("dashboard", "42", "filter_state")
    assert result == f"dashboard{SEPARATOR}42{SEPARATOR}filter_state"


def test_cache_key_with_integer_args() -> None:
    """cache_key should convert integer arguments to strings via str()."""
    result = cache_key("prefix", 99, "suffix")
    assert result == f"prefix{SEPARATOR}99{SEPARATOR}suffix"


def test_cache_key_mixed_types() -> None:
    """cache_key should handle mixed argument types (str, int, None, bool)."""
    result = cache_key("key", 1, None, True)
    assert result == f"key{SEPARATOR}1{SEPARATOR}None{SEPARATOR}True"


def test_cache_key_no_args() -> None:
    """cache_key with no arguments should return an empty string."""
    assert cache_key() == ""


def test_cache_key_empty_string_arg() -> None:
    """cache_key should preserve empty strings as empty segments."""
    result = cache_key("a", "", "b")
    assert result == f"a{SEPARATOR}{SEPARATOR}b"


def test_cache_key_separator_constant() -> None:
    """SEPARATOR should be a semicolon."""
    assert SEPARATOR == ";"


def test_cache_key_produces_deterministic_output() -> None:
    """Calling cache_key with the same arguments twice should produce the same result."""
    args = ("chart", 7, "extra")
    assert cache_key(*args) == cache_key(*args)
