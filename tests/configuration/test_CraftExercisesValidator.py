from pathlib import Path
from typing import List

import yaml

from craft_documents.configuration.CraftExercisesValidator import (
    CraftExercisesValidator,
    ExerciseConfiguration,
)
from tests.configuration.test_Configuration import Configuration


def test_yaml_typing_str():
    input = """
craft-exercises: intervals
"""
    y = yaml.safe_load(input)
    assert y == {"craft-exercises": "intervals"}
    assert isinstance(y["craft-exercises"], str)


def test_yaml_typing_list_str():
    input = """
craft-exercises:
    - intervals
    - chords
"""
    y = yaml.safe_load(input)
    assert y == {"craft-exercises": ["intervals", "chords"]}
    assert type(y["craft-exercises"]) == list

    match y["craft-exercises"]:
        case list():
            assert True
        case _:
            assert False


def test_yaml_typing_dict_one():
    input = """
craft-exercises:
    intervals:
        count: 2
        path: "intervals.tex"
"""
    y = yaml.safe_load(input)
    assert y == {
        "craft-exercises": {
            "intervals": {
                "count": 2,
                "path": "intervals.tex",
            },
        }
    }
    assert type(y["craft-exercises"]) == dict

    match y["craft-exercises"]:
        case dict(value):
            assert value == {"intervals": {"count": 2, "path": "intervals.tex"}}
        case _:
            assert False


def test_yaml_typing_list_of_dict():
    input = """
craft-exercises:
    - intervals: 1
    - chords:
        count: 2
    - melody
"""
    y = yaml.safe_load(input)
    assert y == {
        "craft-exercises": [{"intervals": 1}, {"chords": {"count": 2}}, "melody"]
    }

    match y["craft-exercises"]:
        case list(value):
            for element in value:
                match element:
                    case dict():
                        assert True
                    case str():
                        assert True
                    case _:
                        assert False
        case _:
            assert False


def test_yaml_typing_list_with_dict():
    input = """
craft-exercises:
    - intervals:
        count: 3
        path: blob
    - chords: 2
"""
    y = yaml.safe_load(input)
    assert y == {
        "craft-exercises": [
            {"intervals": {"count": 3, "path": "blob"}},
            {"chords": 2},
        ]
    }


def test_yaml_typing_dict():
    input = """
craft-exercises:
    intervals: 1
    chords:
        count: 3
"""
    y = yaml.safe_load(input)
    assert y == {"craft-exercises": {"intervals": 1, "chords": {"count": 3}}}


intervals = Path("config.craft/exercises/intervals.tex")


def test_ExerciseConfiguration(request):
    c = Configuration()
    e = ExerciseConfiguration(c, "intervals")
    assert e == {"count": 1, "path": request.config.rootdir / intervals}


def test_linter_str(request):
    v = CraftExercisesValidator()
    c = Configuration()
    v._configuration = c

    assert {"intervals": {"count": 1, "path": request.config.rootdir / intervals}} == v.lint("intervals.tex")


def test_linter_list_str(request):
    v = CraftExercisesValidator()
    c = Configuration()
    v._configuration = c

    assert {"intervals": {"count": 1, "path": request.config.rootdir / intervals}} == v.lint(["intervals"])


def test_linter_list_dict_str_int(request):
    v = CraftExercisesValidator()
    c = Configuration()
    v._configuration = c

    assert {"intervals": {"count": 2, "path": request.config.rootdir / intervals}} == v.lint(
        [{"intervals.tex": 2}]
    )


def test_linter_list_dict_str_dict(request):
    v = CraftExercisesValidator()
    c = Configuration()
    v._configuration = c

    assert {
        "intervals": {
            "count": 2,
            "path": request.config.rootdir / intervals.parent / "blob.tex",
            "blib": "blob",
        }
    } == v.lint(
        [
            {
                "intervals.tex": {
                    "count": 2,
                    "path": "blob",
                    "blib": "blob",
                }
            }
        ]
    )


def test_linter_dict_int(request):
    v = CraftExercisesValidator()
    c = Configuration()
    v._configuration = c

    assert {"intervals": {"count": 2, "path": request.config.rootdir / intervals}} == v.lint(
        {"intervals.tex": 2}
    )


def test_linter_dict_dict(request):
    v = CraftExercisesValidator()
    c = Configuration()
    v._configuration = c

    assert {"intervals": {"count": 3, "path": request.config.rootdir / intervals, "blib": "blob"}} == v.lint(
        {"intervals.tex": {"count": 3, "blib": "blob"}}
    )


def test_run_no_input():
    v = CraftExercisesValidator()
    c = Configuration()
    v.run(c)

    assert c == {}


def test_run_valid_input(request):
    v = CraftExercisesValidator()
    c = Configuration()
    c[v.key] = {"intervals": 2}
    v.run(c)

    assert c == {"craft-exercises": {"intervals": {"count": 2, "path": request.config.rootdir / intervals}}}


def test_run_multiple_valid_input(request):
    v = CraftExercisesValidator()
    c = Configuration()
    c[v.key] = {
        "intervals": 2,
        "chords": 1,
    }  # chords is removed because it doesn't exist yet
    v.run(c)

    assert c == {"craft-exercises": {"intervals": {"count": 2, "path": request.config.rootdir / intervals}}}


def test_run_invalid_input():
    v = CraftExercisesValidator()
    c = Configuration()
    c[v.key] = Path()
    v.run(c)

    assert c == {}


def test_run_invalid_path():
    v = CraftExercisesValidator()
    c = Configuration()
    c[v.key] = {"intervals": {"count": 1, "path": Path()}}
    v.run(c)

    assert c == {}


def test_run_invalid_count(request):
    v = CraftExercisesValidator()
    c = Configuration()
    c[v.key] = {"intervals": {"count": -1, "path": Path(request.config.rootdir / intervals)}}
    v.run(c)

    assert c == {}
