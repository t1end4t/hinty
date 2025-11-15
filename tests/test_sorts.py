from sorts import bead_sort
import pytest


def test_bead_sort_empty_list():
    assert bead_sort([]) == []


def test_bead_sort_single_element():
    assert bead_sort([5]) == [5]


def test_bead_sort_multiple_elements():
    assert bead_sort([3, 6, 1, 8, 2, 4]) == [1, 2, 3, 4, 6, 8]


def test_bead_sort_negative_number():
    with pytest.raises(ValueError):
        bead_sort([3, -6, 1, 8, 2, 4])
