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
"""Unit tests for the stats_logger module."""

import logging

import pytest

from superset.stats_logger import BaseStatsLogger, DummyStatsLogger


# ---------------------------------------------------------------------------
# BaseStatsLogger.key()
# ---------------------------------------------------------------------------


def test_base_stats_logger_key_with_prefix() -> None:
    """key() should prepend the prefix to the given key."""
    logger = DummyStatsLogger(prefix="myapp")
    assert logger.key("some_metric") == "myappsome_metric"


def test_base_stats_logger_key_empty_prefix() -> None:
    """key() with an empty prefix should return the bare key."""
    logger = DummyStatsLogger(prefix="")
    assert logger.key("some_metric") == "some_metric"


def test_base_stats_logger_default_prefix() -> None:
    """Default prefix should be 'superset'."""
    logger = DummyStatsLogger()
    assert logger.prefix == "superset"


def test_base_stats_logger_incr_raises_not_implemented() -> None:
    """BaseStatsLogger.incr() must raise NotImplementedError."""

    class MinimalLogger(BaseStatsLogger):
        pass

    with pytest.raises(NotImplementedError):
        MinimalLogger().incr("metric")


def test_base_stats_logger_decr_raises_not_implemented() -> None:
    """BaseStatsLogger.decr() must raise NotImplementedError."""

    class MinimalLogger(BaseStatsLogger):
        pass

    with pytest.raises(NotImplementedError):
        MinimalLogger().decr("metric")


def test_base_stats_logger_timing_raises_not_implemented() -> None:
    """BaseStatsLogger.timing() must raise NotImplementedError."""

    class MinimalLogger(BaseStatsLogger):
        pass

    with pytest.raises(NotImplementedError):
        MinimalLogger().timing("metric", 1.5)


def test_base_stats_logger_gauge_raises_not_implemented() -> None:
    """BaseStatsLogger.gauge() must raise NotImplementedError."""

    class MinimalLogger(BaseStatsLogger):
        pass

    with pytest.raises(NotImplementedError):
        MinimalLogger().gauge("metric", 42.0)


# ---------------------------------------------------------------------------
# DummyStatsLogger
# ---------------------------------------------------------------------------


def test_dummy_stats_logger_incr_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    """DummyStatsLogger.incr() should log a debug message without raising."""
    logger = DummyStatsLogger()
    with caplog.at_level(logging.DEBUG):
        logger.incr("hits")
    assert "hits" in caplog.text


def test_dummy_stats_logger_decr_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    """DummyStatsLogger.decr() should log a debug message without raising."""
    logger = DummyStatsLogger()
    with caplog.at_level(logging.DEBUG):
        logger.decr("misses")
    assert "misses" in caplog.text


def test_dummy_stats_logger_timing_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    """DummyStatsLogger.timing() should log a debug message without raising."""
    logger = DummyStatsLogger()
    with caplog.at_level(logging.DEBUG):
        logger.timing("response_time", 0.123)
    assert "response_time" in caplog.text


def test_dummy_stats_logger_gauge_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    """DummyStatsLogger.gauge() should log a debug message without raising."""
    logger = DummyStatsLogger()
    with caplog.at_level(logging.DEBUG):
        logger.gauge("cpu_usage", 55.5)
    assert "cpu_usage" in caplog.text


def test_dummy_stats_logger_is_subclass_of_base() -> None:
    """DummyStatsLogger must be a subclass of BaseStatsLogger."""
    assert issubclass(DummyStatsLogger, BaseStatsLogger)
