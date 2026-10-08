"""Unit tests for the pure business logic functions."""
import pytest

from app import (bmi_category, calculate_bmi, calculate_calories,
                 validate_adherence)


@pytest.mark.parametrize("weight, program, expected", [
    (70, "FL", 1540),   # 70 x 22
    (70, "MG", 2450),   # 70 x 35
    (70, "BG", 1820),   # 70 x 26
    (82.5, "MG", 2887),  # decimals are truncated to int
])
def test_calculate_calories(weight, program, expected):
    assert calculate_calories(weight, program) == expected


def test_calories_unknown_program():
    with pytest.raises(ValueError):
        calculate_calories(70, "XYZ")


@pytest.mark.parametrize("weight", [0, -5, None])
def test_calories_invalid_weight(weight):
    with pytest.raises(ValueError):
        calculate_calories(weight, "FL")


def test_calculate_bmi():
    assert calculate_bmi(70, 175) == 22.9


@pytest.mark.parametrize("weight, height", [(0, 175), (70, 0), (-1, 170)])
def test_bmi_invalid_input(weight, height):
    with pytest.raises(ValueError):
        calculate_bmi(weight, height)


@pytest.mark.parametrize("bmi, category", [
    (17.0, "Underweight"),
    (18.5, "Normal"),
    (24.9, "Normal"),
    (25.0, "Overweight"),
    (30.0, "Obese"),
])
def test_bmi_category(bmi, category):
    assert bmi_category(bmi) == category


@pytest.mark.parametrize("value", [0, 50, 100])
def test_validate_adherence_ok(value):
    assert validate_adherence(value) == value


@pytest.mark.parametrize("value", [-1, 101, "80", None, True])
def test_validate_adherence_bad(value):
    with pytest.raises(ValueError):
        validate_adherence(value)
