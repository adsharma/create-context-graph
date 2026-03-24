# Copyright 2026 Neo4j Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for ladybug_validator with mocked driver."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from create_context_graph.ladybug_validator import validate_connection


class TestValidateConnection:
    @patch("create_context_graph.ladybug_validator.lb")
    def test_successful_connection(self, mock_lb):
        mock_result = MagicMock()
        mock_result.has_next.side_effect = [True, False]
        mock_result.get_next.return_value = [1]
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_result
        mock_db = MagicMock()
        mock_lb.Database.return_value = mock_db
        mock_lb.Connection.return_value = mock_conn

        success, message = validate_connection("/tmp/test.db")

        assert success is True
        assert "Connected successfully" in message

    @patch("create_context_graph.ladybug_validator.lb")
    def test_connection_error(self, mock_lb):
        mock_lb.Database.side_effect = RuntimeError("Cannot open database")

        success, message = validate_connection("/tmp/bad.db")

        assert success is False
        assert "Connection error" in message
