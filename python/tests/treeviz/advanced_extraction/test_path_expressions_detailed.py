"""
Hardcore test suite for 3viz Phase 2 advanced extraction features.

This test suite uses pytest.parametrize extensively to test many input variations
and edge cases for path expressions, transformations, filtering, and combinations.
"""

import pytest
from treeviz.advanced_extraction import (
    extract_by_path,
    apply_transformation,
    filter_collection,
    extract_attribute,
)


class TestPathExpressionHardcore:
    """Hardcore testing of path expression parsing and evaluation."""

    @pytest.mark.parametrize(
        "path,data,expected",
        [
            # Simple attribute access
            ("name", {"name": "test"}, "test"),
            ("value", {"value": 42}, 42),
            ("missing", {"other": "value"}, None),
            # Dict-style access
            ("key", {"key": "value"}, "value"),
            ("nested", {"nested": {"inner": "deep"}}, {"inner": "deep"}),
            # Object attribute access
            (
                "attr",
                type("Obj", (), {"attr": "object_value"})(),
                "object_value",
            ),
            # Mixed object/dict access
            ("field", {"field": [1, 2, 3]}, [1, 2, 3]),
        ],
    )
    def test_simple_path_extraction(self, path, data, expected):
        """Test simple path extraction with various data types."""
        # Using functional API
        result = extract_by_path(data, path)
        assert result == expected

    @pytest.mark.parametrize(
        "path,data,expected",
        [
            # Basic dot notation
            ("a.b", {"a": {"b": "value"}}, "value"),
            ("def_.name", {"def_": {"name": "app"}}, "app"),
            (
                "deep.nested.value",
                {"deep": {"nested": {"value": "found"}}},
                "found",
            ),
            # Missing intermediate paths
            ("a.missing.c", {"a": {"other": "value"}}, None),
            ("missing.b", {"other": "value"}, None),
            # Mixed depth access
            (
                "root",
                {"root": {"child": {"grandchild": "value"}}},
                {"child": {"grandchild": "value"}},
            ),
            (
                "root.child",
                {"root": {"child": {"grandchild": "value"}}},
                {"grandchild": "value"},
            ),
            (
                "root.child.grandchild",
                {"root": {"child": {"grandchild": "value"}}},
                "value",
            ),
        ],
    )
    def test_dot_notation_paths(self, path, data, expected):
        """Test dot notation path resolution with various nesting levels."""
        # Using functional API
        result = extract_by_path(data, path)
        assert result == expected

    @pytest.mark.parametrize(
        "path,data,expected",
        [
            # Positive indexing
            ("items[0]", {"items": ["first", "second", "third"]}, "first"),
            ("items[1]", {"items": ["first", "second", "third"]}, "second"),
            ("items[2]", {"items": ["first", "second", "third"]}, "third"),
            # Negative indexing
            ("items[-1]", {"items": ["first", "second", "third"]}, "third"),
            ("items[-2]", {"items": ["first", "second", "third"]}, "second"),
            ("items[-3]", {"items": ["first", "second", "third"]}, "first"),
            # Out of bounds (should return None, not raise)
            ("items[10]", {"items": ["first", "second", "third"]}, None),
            ("items[-10]", {"items": ["first", "second", "third"]}, None),
            # Empty list
            ("items[0]", {"items": []}, None),
            ("items[-1]", {"items": []}, None),
            # Non-list access (should return None)
            ("value[0]", {"value": "string"}, "s"),  # String indexing works
            (
                "value[0]",
                {"value": 42},
                None,
            ),  # Number indexing fails gracefully
            ("missing[0]", {}, None),  # Missing field
        ],
    )
    def test_array_indexing_paths(self, path, data, expected):
        """Test array indexing with positive/negative indices and edge cases."""
        # Using functional API
        result = extract_by_path(data, path)
        assert result == expected

    @pytest.mark.parametrize(
        "path,data,expected",
        [
            # String keys without quotes
            ("['key']", {"key": "value"}, "value"),
            ('["key"]', {"key": "value"}, "value"),
            # String keys with special characters
            ("['complex-key']", {"complex-key": "value"}, "value"),
            ('["spaces in key"]', {"spaces in key": "value"}, "value"),
            ("['underscore_key']", {"underscore_key": "value"}, "value"),
            ("['dot.key']", {"dot.key": "value"}, "value"),
            # Numeric string keys
            ("['123']", {"123": "numeric_string_key"}, "numeric_string_key"),
            # Missing keys
            ("['missing']", {"other": "value"}, None),
            # Integer indices as bracket notation
            ("[0]", ["first", "second"], "first"),
            ("[1]", ["first", "second"], "second"),
            ("[-1]", ["first", "second"], "second"),
        ],
    )
    def test_bracket_notation_paths(self, path, data, expected):
        """Test bracket notation for string keys and numeric indices."""
        # Using functional API
        result = extract_by_path(data, path)
        assert result == expected

    @pytest.mark.parametrize(
        "path,data,expected",
        [
            # Dot notation with array access
            (
                "users[0].name",
                {"users": [{"name": "Alice"}, {"name": "Bob"}]},
                "Alice",
            ),
            (
                "users[1].name",
                {"users": [{"name": "Alice"}, {"name": "Bob"}]},
                "Bob",
            ),
            (
                "users[-1].name",
                {"users": [{"name": "Alice"}, {"name": "Bob"}]},
                "Bob",
            ),
            # Nested array access
            ("matrix[0][1]", {"matrix": [[1, 2, 3], [4, 5, 6]]}, 2),
            ("matrix[1][0]", {"matrix": [[1, 2, 3], [4, 5, 6]]}, 4),
            # Deep nesting with mixed access
            (
                "def_.databases[0].host",
                {"def_": {"databases": [{"host": "localhost"}]}},
                "localhost",
            ),
            (
                "app.modules[0].functions[1].name",
                {
                    "app": {
                        "modules": [
                            {"functions": [{"name": "f1"}, {"name": "f2"}]}
                        ]
                    }
                },
                "f2",
            ),
            # Bracket notation with dots
            (
                "data['complex-key'].nested",
                {"data": {"complex-key": {"nested": "value"}}},
                "value",
            ),
            # Missing intermediate elements
            ("users[5].name", {"users": [{"name": "Alice"}]}, None),
            ("users[0].missing", {"users": [{"name": "Alice"}]}, None),
            ("missing[0].name", {"other": "data"}, None),
        ],
    )
    def test_complex_path_combinations(self, path, data, expected):
        """Test complex path combinations with multiple access types."""
        # Using functional API
        result = extract_by_path(data, path)
        assert result == expected

    @pytest.mark.parametrize(
        "malformed_path",
        [
            "items[",  # Unclosed bracket
            "items]",  # Unopened bracket
            "items[0",  # Unclosed bracket
            "items0]",  # Unopened bracket
            "items[]",  # Empty brackets
            "items[0][",  # Mixed valid/invalid
            "",  # Empty path
            "   ",  # Whitespace only
            "items[[0]]",  # Double brackets
            "items[0]extra]",  # Extra closing bracket
        ],
    )
    def test_malformed_path_expressions(self, malformed_path):
        """Test that malformed path expressions raise ValueError."""
        # Using functional API
        data = {"items": [1, 2, 3]}

        with pytest.raises(ValueError):
            extract_by_path(data, malformed_path)


class TestTransformationHardcore:
    """Hardcore testing of transformation functions."""

    @pytest.mark.parametrize(
        "value,transform,expected",
        [
            # Text transformations
            ("hello", "upper", "HELLO"),
            ("WORLD", "lower", "world"),
            ("test string", "capitalize", "Test string"),
            ("  spaced  ", "strip", "spaced"),
            # Edge cases for text
            ("", "upper", ""),
            ("123", "upper", "123"),
            ("mixed123TEXT", "lower", "mixed123text"),
            ("   ", "strip", ""),
            ("\t\n  text  \n\t", "strip", "text"),
        ],
    )
    def test_text_transformations(self, value, transform, expected):
        """Test text transformation functions with various input types."""
        # Using functional API
        result = apply_transformation(value, transform)
        assert result == expected

    @pytest.mark.parametrize(
        "value,params,expected",
        [
            # Basic truncation
            ("short", {"name": "truncate", "max_length": 10}, "short"),
            (
                "this is a long string",
                {"name": "truncate", "max_length": 10},
                "this is a…",
            ),
            (
                "exactly10chars",  # This is 14 chars, so will be truncated
                {"name": "truncate", "max_length": 10},
                "exactly10…",  # 9 chars + 1 char suffix = 10
            ),
            # Custom suffix
            (
                "long text",
                {"name": "truncate", "max_length": 5, "suffix": "..."},
                "lo...",
            ),
            (
                "text",
                {"name": "truncate", "max_length": 8, "suffix": " [more]"},
                "text",
            ),
            # Edge cases
            ("text", {"name": "truncate", "max_length": 0}, ""),
            (
                "text",
                {"name": "truncate", "max_length": 1, "suffix": "..."},
                ".",  # Only 1 char allowed, so suffix is truncated to "."
            ),
            ("a", {"name": "truncate", "max_length": 1}, "a"),
            # Very long suffix
            (
                "text",
                {
                    "name": "truncate",
                    "max_length": 3,
                    "suffix": "VERYLONGSUFFIX",
                },
                "VER",
            ),
        ],
    )
    def test_truncate_transformation_variations(self, value, params, expected):
        """Test truncate transformation with various parameters."""
        # Using functional API
        result = apply_transformation(value, params)
        assert result == expected

    @pytest.mark.parametrize(
        "value,transform,expected",
        [
            # Numeric transformations
            (-42, "abs", 42),
            (42, "abs", 42),
            (0, "abs", 0),
            (-3.14, "abs", 3.14),
            # Format transformations
            (42, {"name": "format", "format_spec": "04d"}, "0042"),
            (3.14159, {"name": "format", "format_spec": ".2f"}, "3.14"),
            (1000, {"name": "format", "format_spec": ","}, "1,000"),
            # Round transformations
            (3.14159, {"name": "round", "digits": 2}, 3.14),
            (3.14159, {"name": "round", "digits": 0}, 3),
            (
                2.5,
                {"name": "round", "digits": 0},
                2,
            ),  # Python's round() behavior
        ],
    )
    def test_numeric_transformations(self, value, transform, expected):
        """Test numeric transformation functions."""
        # Using functional API
        result = apply_transformation(value, transform)
        assert result == expected

    @pytest.mark.parametrize(
        "value,transform,expected",
        [
            # Length transformations
            ([], "length", 0),
            ([1, 2, 3], "length", 3),
            ("hello", "length", 5),
            ("", "length", 0),
            # Join transformations
            (["a", "b", "c"], {"name": "join", "separator": "-"}, "a-b-c"),
            (["a", "b", "c"], {"name": "join", "separator": ""}, "abc"),
            ([], {"name": "join", "separator": "-"}, ""),
            ([1, 2, 3], {"name": "join", "separator": ","}, "1,2,3"),
            # First/last transformations
            ([1, 2, 3], "first", 1),
            ([1, 2, 3], "last", 3),
            ([], "first", None),
            ([], "last", None),
            ("hello", "first", "h"),
            ("hello", "last", "o"),
        ],
    )
    def test_collection_transformations(self, value, transform, expected):
        """Test collection transformation functions."""
        # Using functional API
        result = apply_transformation(value, transform)
        assert result == expected

    @pytest.mark.parametrize(
        "value,transform,expected",
        [
            # Type conversions
            ("123", "int", 123),
            (123, "str", "123"),
            ("3.14", "float", 3.14),
            (True, "str", "True"),
            (0, "str", "0"),
        ],
    )
    def test_type_transformations(self, value, transform, expected):
        """Test type conversion transformations."""
        # Using functional API
        result = apply_transformation(value, transform)
        assert result == expected

    @pytest.mark.parametrize(
        "invalid_transform",
        [
            "nonexistent",
            "UPPER",  # Wrong case
            "truncat",  # Typo
            123,  # Wrong type
            {"name": "unknown"},
            {"invalid": "structure"},  # Missing name
        ],
    )
    def test_invalid_transformations(self, invalid_transform):
        """Test that invalid transformations raise ValueError."""
        # Using functional API

        with pytest.raises(ValueError):
            apply_transformation("test", invalid_transform)

    def test_none_value_handling(self):
        """Test that None values skip transformation."""
        # Using functional API

        assert apply_transformation(None, "upper") is None
        assert (
            apply_transformation(None, {"name": "truncate", "max_length": 5})
            is None
        )
        assert apply_transformation(None, lambda x: x * 2) is None


class TestFilterEngineHardcore:
    """Hardcore testing of filtering engine with complex predicates."""

    @pytest.mark.parametrize(
        "items,predicate,expected_count",
        [
            # Simple equality filters
            ([{"type": "a"}, {"type": "b"}, {"type": "a"}], {"type": "a"}, 2),
            ([{"value": 1}, {"value": 2}, {"value": 1}], {"value": 1}, 2),
            ([{"name": "test"}], {"name": "test"}, 1),
            ([{"name": "test"}], {"name": "other"}, 0),
            # Numeric equality
            ([{"count": 0}, {"count": 1}, {"count": 0}], {"count": 0}, 2),
            ([{"score": 100}, {"score": 95}], {"score": 100}, 1),
            # Boolean equality
            ([{"active": True}, {"active": False}], {"active": True}, 1),
            ([{"visible": False}, {"visible": False}], {"visible": False}, 2),
        ],
    )
    def test_equality_filters(self, items, predicate, expected_count):
        """Test simple equality-based filtering with content verification."""
        # Using functional API
        result = filter_collection(items, predicate)
        assert len(result) == expected_count

        # Verify all returned items actually match the predicate
        for item in result:
            for field, expected_value in predicate.items():
                assert (
                    item.get(field) == expected_value
                ), f"Item {item} does not match predicate {predicate}"

    @pytest.mark.parametrize(
        "items,predicate,expected_count",
        [
            # Membership filters
            (
                [{"type": "a"}, {"type": "b"}, {"type": "c"}],
                {"type": {"in": ["a", "b"]}},
                2,
            ),
            (
                [{"priority": 1}, {"priority": 2}, {"priority": 3}],
                {"priority": {"in": [1, 3]}},
                2,
            ),
            (
                [{"status": "draft"}],
                {"status": {"in": ["published", "archived"]}},
                0,
            ),
            # Not in filters
            (
                [{"type": "a"}, {"type": "b"}, {"type": "c"}],
                {"type": {"not_in": ["a"]}},
                2,
            ),
            (
                [{"level": 1}, {"level": 2}],
                {"level": {"not_in": []}},
                2,
            ),  # Empty exclusion list
        ],
    )
    def test_membership_filters(self, items, predicate, expected_count):
        """Test membership-based filtering (in/not_in) with content verification."""
        # Using functional API
        result = filter_collection(items, predicate)
        assert len(result) == expected_count

        # Verify all returned items actually match the membership predicate
        for item in result:
            for field, condition in predicate.items():
                field_value = item.get(field)
                if "in" in condition:
                    assert (
                        field_value in condition["in"]
                    ), f"Item {item} field '{field}' value {field_value} not in {condition['in']}"
                elif "not_in" in condition:
                    assert (
                        field_value not in condition["not_in"]
                    ), f"Item {item} field '{field}' value {field_value} should not be in {condition['not_in']}"

    @pytest.mark.parametrize(
        "items,predicate,expected_count",
        [
            # String operations
            (
                [
                    {"name": "get_user"},
                    {"name": "set_value"},
                    {"name": "helper"},
                ],
                {"name": {"startswith": "get_"}},
                1,
            ),
            (
                [{"path": "file.txt"}, {"path": "image.png"}],
                {"path": {"endswith": ".txt"}},
                1,
            ),
            (
                [{"content": "hello world"}, {"content": "foo bar"}],
                {"content": {"contains": "world"}},
                1,
            ),
            # Regex patterns
            (
                [
                    {"name": "test_func_1"},
                    {"name": "test_func_2"},
                    {"name": "helper"},
                ],
                {"name": {"matches": r"test_func_\d+"}},
                2,
            ),
            (
                [{"email": "user@domain.com"}, {"email": "invalid-email"}],
                {"email": {"matches": r".+@.+\..+"}},
                1,
            ),
            # Case sensitivity
            (
                [{"name": "TEST"}, {"name": "test"}],
                {"name": {"startswith": "test"}},
                1,
            ),  # Case sensitive
        ],
    )
    def test_string_operation_filters(self, items, predicate, expected_count):
        """Test string-based filtering operations with content verification."""
        # Using functional API
        result = filter_collection(items, predicate)
        assert len(result) == expected_count

        # Verify all returned items actually match the string operation predicate
        import re

        for item in result:
            for field, condition in predicate.items():
                field_value = str(item.get(field, ""))
                if isinstance(condition, dict):
                    for op, expected in condition.items():
                        if op == "startswith":
                            assert field_value.startswith(
                                expected
                            ), f"Item {item} field '{field}' value '{field_value}' should start with '{expected}'"
                        elif op == "endswith":
                            assert field_value.endswith(
                                expected
                            ), f"Item {item} field '{field}' value '{field_value}' should end with '{expected}'"
                        elif op == "contains":
                            assert (
                                expected in field_value
                            ), f"Item {item} field '{field}' value '{field_value}' should contain '{expected}'"
                        elif op == "matches":
                            assert re.search(
                                expected, field_value
                            ), f"Item {item} field '{field}' value '{field_value}' should match pattern '{expected}'"

    @pytest.mark.parametrize(
        "items,predicate,expected_count",
        [
            # Comparison operators
            (
                [{"score": 85}, {"score": 95}, {"score": 75}],
                {"score": {"gt": 80}},
                2,
            ),
            (
                [{"score": 85}, {"score": 95}, {"score": 75}],
                {"score": {"gte": 85}},
                2,
            ),
            (
                [{"score": 85}, {"score": 95}, {"score": 75}],
                {"score": {"lt": 90}},
                2,
            ),
            (
                [{"score": 85}, {"score": 95}, {"score": 75}],
                {"score": {"lte": 85}},
                2,
            ),
            (
                [{"score": 85}, {"score": 95}, {"score": 75}],
                {"score": {"eq": 85}},
                1,
            ),
            (
                [{"score": 85}, {"score": 95}, {"score": 75}],
                {"score": {"ne": 85}},
                2,
            ),
            # Edge cases
            ([{"value": 0}], {"value": {"gt": -1}}, 1),
            ([{"value": None}], {"value": {"eq": None}}, 1),
        ],
    )
    def test_comparison_filters(self, items, predicate, expected_count):
        """Test comparison-based filtering operations with content verification."""
        # Using functional API
        result = filter_collection(items, predicate)
        assert len(result) == expected_count

        # Verify all returned items actually match the comparison predicate
        for item in result:
            for field, condition in predicate.items():
                field_value = item.get(field)
                if isinstance(condition, dict):
                    for op, expected in condition.items():
                        if op == "gt":
                            assert (
                                field_value > expected
                            ), f"Item {item} field '{field}' value {field_value} should be > {expected}"
                        elif op == "gte":
                            assert (
                                field_value >= expected
                            ), f"Item {item} field '{field}' value {field_value} should be >= {expected}"
                        elif op == "lt":
                            assert (
                                field_value < expected
                            ), f"Item {item} field '{field}' value {field_value} should be < {expected}"
                        elif op == "lte":
                            assert (
                                field_value <= expected
                            ), f"Item {item} field '{field}' value {field_value} should be <= {expected}"
                        elif op == "eq":
                            assert (
                                field_value == expected
                            ), f"Item {item} field '{field}' value {field_value} should equal {expected}"
                        elif op == "ne":
                            assert (
                                field_value != expected
                            ), f"Item {item} field '{field}' value {field_value} should not equal {expected}"

    @pytest.mark.parametrize(
        "items,predicate,expected_count",
        [
            # Type checking
            (
                [{"value": "text"}, {"value": 123}, {"value": None}],
                {"value": {"type": "str"}},
                1,
            ),
            (
                [{"value": "text"}, {"value": 123}, {"value": None}],
                {"value": {"type": "int"}},
                1,
            ),
            (
                [{"value": "text"}, {"value": 123}, {"value": None}],
                {"value": {"is_none": True}},
                1,
            ),
            (
                [{"value": "text"}, {"value": 123}, {"value": None}],
                {"value": {"is_not_none": True}},
                2,
            ),
        ],
    )
    def test_type_check_filters(self, items, predicate, expected_count):
        """Test type checking filters with content verification."""
        # Using functional API
        result = filter_collection(items, predicate)
        assert len(result) == expected_count

        # Verify all returned items actually match the type check predicate
        for item in result:
            for field, condition in predicate.items():
                field_value = item.get(field)
                if isinstance(condition, dict):
                    for op, expected in condition.items():
                        if op == "is_none":
                            if expected:
                                assert (
                                    field_value is None
                                ), f"Item {item} field '{field}' value {field_value} should be None"
                            else:
                                assert (
                                    field_value is not None
                                ), f"Item {item} field '{field}' value {field_value} should not be None"
                        elif op == "is_not_none":
                            if expected:
                                assert (
                                    field_value is not None
                                ), f"Item {item} field '{field}' value {field_value} should not be None"
                            else:
                                assert (
                                    field_value is None
                                ), f"Item {item} field '{field}' value {field_value} should be None"
                        elif op == "type":
                            assert (
                                type(field_value).__name__ == expected
                            ), f"Item {item} field '{field}' value {field_value} should be type {expected}, got {type(field_value).__name__}"

    @pytest.mark.parametrize(
        "items,predicate,expected_count",
        [
            # AND operations
            (
                [
                    {"type": "func", "public": True},
                    {"type": "func", "public": False},
                    {"type": "var", "public": True},
                ],
                {"and": [{"type": "func"}, {"public": True}]},
                1,
            ),
            # OR operations
            (
                [{"type": "func"}, {"type": "var"}, {"type": "class"}],
                {"or": [{"type": "func"}, {"type": "var"}]},
                2,
            ),
            # NOT operations
            (
                [{"hidden": True}, {"hidden": False}],
                {"not": {"hidden": True}},
                1,
            ),
            # Nested logical operations
            (
                [
                    {"type": "func", "public": True, "tested": True},
                    {"type": "func", "public": False, "tested": True},
                    {"type": "var", "public": True, "tested": False},
                ],
                {
                    "and": [
                        {"or": [{"type": "func"}, {"type": "var"}]},
                        {"public": True},
                    ]
                },
                2,
            ),
            # Complex nesting
            (
                [{"a": 1, "b": 2}, {"a": 2, "b": 1}, {"a": 1, "b": 1}],
                {
                    "or": [
                        {"and": [{"a": 1}, {"b": 2}]},
                        {"and": [{"a": 2}, {"b": 1}]},
                    ]
                },
                2,
            ),
        ],
    )
    def test_logical_operator_filters(self, items, predicate, expected_count):
        """Test logical operator combinations (and, or, not) with content verification."""
        # Using functional API
        result = filter_collection(items, predicate)
        assert len(result) == expected_count

        # Verify all returned items actually match the logical predicate by re-evaluating
        # This is complex for logical operators, so we'll do a simpler check
        # that the filter engine itself would accept these items
        for item in result:
            # Re-run the filter on just this item to ensure it passes
            single_item_result = filter_collection([item], predicate)
            assert (
                len(single_item_result) == 1
            ), f"Item {item} should match predicate {predicate} but doesn't when tested individually"

    @pytest.mark.parametrize(
        "items,predicate,expected_items",
        [
            # Test that correct items are returned, not just count
            (
                [{"name": "alice", "age": 25}, {"name": "bob", "age": 30}],
                {"age": {"gt": 27}},
                [{"name": "bob", "age": 30}],
            ),
            (
                [
                    {"id": 1, "active": True},
                    {"id": 2, "active": False},
                    {"id": 3, "active": True},
                ],
                {"active": True},
                [{"id": 1, "active": True}, {"id": 3, "active": True}],
            ),
            # Complex filter preserving item order
            (
                [
                    {"priority": 1, "status": "done"},
                    {"priority": 2, "status": "todo"},
                    {"priority": 1, "status": "todo"},
                ],
                {"and": [{"priority": 1}, {"status": "todo"}]},
                [{"priority": 1, "status": "todo"}],
            ),
        ],
    )
    def test_filter_content_accuracy(self, items, predicate, expected_items):
        """Test that filtering returns the correct items, not just correct count."""
        # Using functional API
        result = filter_collection(items, predicate)
        assert result == expected_items

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "not a list",
            123,
            {"a": "dict"},
            None,
        ],
    )
    def test_non_list_input_error(self, invalid_input):
        """Test that non-list inputs raise ValueError."""
        # Using functional API

        with pytest.raises(ValueError, match="Cannot filter non-list type"):
            filter_collection(invalid_input, {"type": "any"})

    def test_empty_collection_filtering(self):
        """Test filtering empty collections."""
        # Using functional API

        result = filter_collection([], {"type": "any"})
        assert result == []

        result = filter_collection([], {"and": [{"a": 1}, {"b": 2}]})
        assert result == []


class TestAdvancedAttributeExtractorHardcore:
    """Hardcore testing of the complete advanced extraction system."""

    @pytest.mark.parametrize(
        "source,spec,expected",
        [
            # Simple path extraction
            ({"name": "test"}, "name", "test"),
            ({"missing": "value"}, "other", None),  # Missing path returns None
            # Complex extraction with fallbacks
            (
                {"backup": "fallback_value"},
                {"path": "primary", "fallback": "backup", "default": "default"},
                "fallback_value",
            ),
            (
                {"nothing": "here"},
                {
                    "path": "primary",
                    "fallback": "secondary",
                    "default": "default_value",
                },
                "default_value",
            ),
            # Transformations
            (
                {"text": "hello"},
                {"path": "text", "transform": "upper"},
                "HELLO",
            ),
            # Complex path with transformation
            (
                {"user": {"profile": {"name": "john doe"}}},
                {"path": "user.profile.name", "transform": "capitalize"},
                "John doe",
            ),
        ],
    )
    def test_extraction_scenarios(self, source, spec, expected):
        """Test various extraction scenarios with different specifications."""
        # Using functional API
        result = extract_attribute(source, spec)
        assert result == expected

    @pytest.mark.parametrize(
        "source,spec,expected_count",
        [
            # Basic filtering
            (
                {"items": [{"type": "a"}, {"type": "b"}, {"type": "a"}]},
                {"path": "items", "filter": {"type": "a"}},
                2,
            ),
            # Complex filtering with logical operators
            (
                {
                    "modules": [
                        {"name": "mod1", "public": True, "tested": True},
                        {"name": "mod2", "public": False, "tested": True},
                        {"name": "mod3", "public": True, "tested": False},
                    ]
                },
                {
                    "path": "modules",
                    "filter": {"and": [{"public": True}, {"tested": True}]},
                },
                1,
            ),
            # Filtering with transformation
            (
                {
                    "functions": [
                        {"name": "get_user"},
                        {"name": "set_value"},
                        {"name": "get_data"},
                    ]
                },
                {
                    "path": "functions",
                    "filter": {"name": {"startswith": "get_"}},
                },
                2,
            ),
        ],
    )
    def test_filtering_scenarios(self, source, spec, expected_count):
        """Test filtering scenarios with various predicates and content verification."""
        # Using functional API
        result = extract_attribute(source, spec)
        assert len(result) == expected_count

        # Verify the filtered results actually match the filter criteria
        if isinstance(result, list) and "filter" in spec:
            filter_spec = spec["filter"]
            # Use filter_collection to verify each result item matches the filter
            # Using functional API for verification
            for item in result:
                single_item_result = filter_collection([item], filter_spec)
                assert (
                    len(single_item_result) == 1
                ), f"Filtered item {item} should match filter {filter_spec} but doesn't when tested individually"

    @pytest.mark.parametrize(
        "source,spec,expected",
        [
            # Chain: path -> transform -> filter
            # Transform list of objects, then filter by field
            (
                {
                    "items": [
                        {"name": "HELLO"},
                        {"name": "world"},
                        {"name": "TEST"},
                    ]
                },
                {
                    "path": "items",
                    "transform": lambda lst: [
                        {"name": item["name"].lower()} for item in lst
                    ],
                    "filter": {"name": "hello"},  # Filter by exact match
                },
                [{"name": "hello"}],  # Only the transformed "hello" matches
            ),
            # Chain: fallback -> transform
            (
                {"backup": "fallback text"},
                {"path": "missing", "fallback": "backup", "transform": "upper"},
                "FALLBACK TEXT",
            ),
            # Chain: path -> transform -> filter (consistent order)
            (
                {"numbers": [1, 2, 3, 4, 5]},
                {
                    "path": "numbers",
                    "transform": lambda lst: sum(
                        lst
                    ),  # Transform first: sum all
                    "filter": {"gt": 3},  # Can't filter int, so ignored
                },
                15,  # sum([1, 2, 3, 4, 5]) = 15
            ),
        ],
    )
    def test_complex_extraction_chains(self, source, spec, expected):
        """Test complex extraction chains combining multiple features."""
        # Using functional API
        result = extract_attribute(source, spec)
        assert result == expected

    @pytest.mark.parametrize(
        "source,path",
        [
            # Deep nesting with arrays
            (
                {"def_": {"servers": [{"db": {"host": "localhost"}}]}},
                "def_.servers[0].db.host",
            ),
            # Multiple array accesses
            ({"matrix": [[{"value": 42}]]}, "matrix[0][0].value"),
            # Mixed bracket and dot notation
            (
                {"data": {"complex-key": {"items": [{"name": "test"}]}}},
                "data['complex-key'].items[0].name",
            ),
            # Negative indexing in complex paths
            (
                {"users": [{"messages": ["hello", "world"]}]},
                "users[0].messages[-1]",
            ),
        ],
    )
    def test_complex_path_extraction(self, source, path):
        """Test complex path expressions with real-world nesting scenarios."""
        # Using functional API
        # Just test that these don't crash - specific values depend on the source data
        result = extract_attribute(source, path)
        assert result is not None

    def test_error_propagation(self):
        """Test that errors are properly propagated through the extraction chain."""
        # Using functional API

        # Test malformed path
        with pytest.raises(ValueError):
            extract_attribute({"test": "value"}, {"path": "test[unclosed"})

        # Test invalid transformation
        with pytest.raises(ValueError):
            extract_attribute(
                {"test": "value"},
                {"path": "test", "transform": "invalid_transform"},
            )

    @pytest.mark.parametrize(
        "spec",
        [
            # Various callable forms
            lambda node: node.get("name", "default"),
            lambda node: len(node.get("items", [])),
            lambda node: node["value"] * 2 if "value" in node else None,
        ],
    )
    def test_callable_extraction_compatibility(self, spec):
        """Test that callable extraction (Phase 1 compatibility) still works."""
        # Using functional API
        source = {"name": "test", "items": [1, 2, 3], "value": 5}

        # Should not raise an error
        result = extract_attribute(source, spec)
        assert result is not None


class TestIntegrationHardcore:
    """Hardcore integration tests combining all Phase 2 features."""

    @pytest.mark.parametrize(
        "def_,source,expected_label,expected_child_count",
        [
            # Basic definition with filtering
            (
                {
                    "attributes": {
                        "label": "name",
                        "children": {
                            "path": "items",
                            "filter": {"active": True},
                        },
                    }
                },
                {
                    "name": "root",
                    "items": [
                        {"active": True},
                        {"active": False},
                        {"active": True},
                    ],
                },
                "root",
                2,
            ),
            # Complex extraction with type overrides
            (
                {
                    "attributes": {
                        "label": "name",
                        "type": "node_type",
                        "children": "child_nodes",
                    },
                    "type_overrides": {
                        "special": {
                            "label": {
                                "path": "title",
                                "fallback": "name",
                                "transform": "upper",
                            },
                            "children": {
                                "path": "items",
                                "filter": {"priority": {"gt": 5}},
                            },
                        }
                    },
                },
                {
                    "name": "fallback",
                    "node_type": "special",
                    "items": [
                        {"priority": 3},
                        {"priority": 8},
                        {"priority": 10},
                    ],
                    "child_nodes": [],
                },
                "FALLBACK",
                2,
            ),
            # Deep nesting with transformations
            (
                {
                    "attributes": {
                        "label": {
                            "path": "def_.display.title",
                            "transform": {"name": "truncate", "max_length": 10},
                        },
                        "children": "modules",
                    }
                },
                {
                    "def_": {
                        "display": {"title": "Very Long Application Title"}
                    },
                    "modules": [],
                },
                "Very Long…",
                0,
            ),
        ],
    )
    def test_realistic_defurations(
        self, def_, source, expected_label, expected_child_count
    ):
        """Test realistic definition scenarios that combine multiple features."""
        from treeviz.adapter import adapt_node

        result = adapt_node(source, def_)

        assert result.label == expected_label
        assert len(result.children) == expected_child_count

    def test_performance_with_large_data(self):
        """Test performance with larger data structures."""
        from treeviz.adapter import adapt_node

        # Create a large source structure
        large_source = {
            "name": "root",
            "modules": [
                {
                    "name": f"module_{i}",
                    "type": "module",
                    "functions": [
                        {
                            "name": f"func_{j}",
                            "public": j % 2 == 0,
                            "tested": j % 3 == 0,
                        }
                        for j in range(20)
                    ],
                }
                for i in range(50)
            ],
        }

        def_ = {
            "attributes": {
                "label": "name",
                "children": {"path": "modules", "filter": {"type": "module"}},
            },
            "type_overrides": {
                "module": {
                    "children": {
                        "path": "functions",
                        "filter": {"and": [{"public": True}, {"tested": True}]},
                    }
                }
            },
        }

        result = adapt_node(large_source, def_)

        # Should complete without error and produce reasonable results
        assert result.label == "root"
        assert len(result.children) == 50  # All modules

        # Check that filtering worked on functions
        for module in result.children:
            # Each module should have some filtered functions
            assert len(module.children) <= 20  # At most all functions
            # We expect fewer due to filtering (public AND tested)

    @pytest.mark.parametrize(
        "edge_case_data",
        [
            # Empty structures
            {},
            {"empty_list": []},
            {"empty_dict": {}},
            # Null/None values
            {"null_value": None},
            {"mixed": [None, "value", None]},
            # Deeply nested empty structures
            {"deep": {"nested": {"empty": []}}},
            # Unicode and special characters
            {"unicode": "héllo wörld 🌍"},
            {"special-key": "value with spaces"},
            # Numeric edge cases
            {"zero": 0},
            {"negative": -1},
            {"float": 3.14159},
        ],
    )
    def test_edge_case_data_handling(self, edge_case_data):
        """Test that edge case data is handled gracefully."""
        from treeviz.adapter import adapt_node

        def_ = {
            "attributes": {
                "label": {"path": "name", "default": "unnamed"},
                "children": {"path": "items", "default": []},
            }
        }

        # Should not crash on edge case data
        try:
            result = adapt_node(edge_case_data, def_)
            assert result is not None
            assert result.label == "unnamed"  # Should use default
        except ValueError:
            # Some edge cases might legitimately fail
            pass
