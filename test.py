from unittest.mock import patch

from converter import (parse_expression, parse_scene, calculate_adjectives,
    convert_scene_to_sentences, ON_STAGE, VARIABLE_MAP)

def test_calculate_adjectives_simple():
    assert calculate_adjectives("handsome rich brave hero", 1) == 8


def test_calculate_adjectives_negative():
    assert calculate_adjectives("stupid fatherless big smelly half-witted coward", -1) == -32


def test_convert_scene_to_sentences():
    assert convert_scene_to_sentences(["""this is a sentence. some other stuff.
        and then wow! you can ask questions? I guess so
        guys. and more.
    """, " and more sentences in another item"]) == [
        "this is a sentence.",
        "some other stuff.",
        "and then wow!",
        "you can ask questions?",
        "I guess so guys.",
        "and more.",
    ]

def test_parse_expression_variable():
    VARIABLE_MAP.reset({"romeo": 65})
    assert parse_expression(
        "you",
        "",
        "romeo",
    ) == 65


def test_parse_expression_variable_phrase():
    VARIABLE_MAP.reset({"romeo": 65})
    assert parse_expression(
        "of yourself",
        "",
        "romeo",
    ) == 65


@patch('converter.say_output')
def test_parse_expression_speak(say_output):
    VARIABLE_MAP.reset({"romeo": 65})
    parse_expression(
        "speak your mind",
        "",
        "romeo",
    )
    say_output.assert_called_with("A")


def test_parse_expression_with_variable():
    VARIABLE_MAP.reset({"romeo": 3})
    assert parse_expression(
        "you are as stupid as the difference between a handsome rich brave hero and thyself",
        "",
        "romeo",
    ) == 5  # The first part evaluates to 8, then subtract romeo (3) to get 5


def test_parse_expression_with_difference_and_sum():
    VARIABLE_MAP.reset({"romeo": 20})
    assert parse_expression(
        "you are as healthy as the difference between the sum of the sweetest reddest rose and my father and yourself",
        "",
        "romeo",
    ) == -15  # (4 + 1) - romeo => -15


def test_parse_expression_with_sum_and_difference():
    VARIABLE_MAP.reset({"romeo": 20})
    # assert parse_expression("difference between a big mighty proud kingdom and a horse", "") == 7
    assert parse_expression(
        "you are as cowardly as the sum of yourself and the difference between a big mighty proud kingdom and a horse",
        "",
        "romeo",
    ) == 27  # romeo + (8 - 1) => 27


def test_parse_expression_with_sum_and_sum():
    VARIABLE_MAP.reset({"romeo": 20})
    assert parse_expression(
        "thou art as sweet as the sum of the sum of romeo and his horse and his black cat",
        "",
        "romeo",
    ) == 23  # (romeo + 1) + 2 => 23


def test_parse_expression_with_product():
    assert parse_expression(
        "the product of a large rural town and my amazing bottomless embroidered purse",
        "",
        "",
    ) == 32  # 4 * 8


def test_parse_expression_with_cube():
    assert parse_expression(
        "are as small as the difference between the square of the difference between my little pony"
        + " and your big hairy hound and the cube of your sorry little codpiece",
        "",
        "",
    ) == 100  # (2 - -4)^2 - (-4)^3 => 36 - -64 => 100 


def test_parse_expression_with_quotient():
    VARIABLE_MAP.reset({"romeo": 100})
    assert parse_expression(
        "as good as the quotient between romeo and the sum of a small furry animal and a leech",
        "",
        "",
    ) == 33  # Romeo / (4 + -1)


def test_parse_expression_with_quotient_and_diff():
    VARIABLE_MAP.reset({"romeo": 100})
    assert parse_expression(
        "as disgusting as the quotient between romeo and twice the " + 
        "difference between a mistletoe and an oozing infected blister",
        "",
        "romeo",
    ) == 10  # Romeo / (2 * (1 - -4)) => 100 / 10


def test_parse_expression_with_remainder():
    VARIABLE_MAP.reset({"romeo": 5})
    assert parse_expression(
        "is the remainder of the quotient between romeo and a fine flower",
        "",
        "",
    ) == 1  # Romeo % 2 => 1


def test_parse_expression_with_square_root():
    VARIABLE_MAP.reset({"romeo": 16})
    assert parse_expression(
        "the square root of romeo",
        "",
        "",
    ) == 4  # sqrt(16) => 4


def test_parse_expression_with_as_as():
    assert parse_expression(
        "art as sweet as a sunny summers day",
        "",
        "",
    ) == 2  # sqrt(16) => 4


def test_parse_expression_with_nothing():
    VARIABLE_MAP.reset({"romeo": 5})
    assert parse_expression(
        "difference between nothing and romeo",
        "",
        "",
    ) == -5  # sqrt(16) => 4


def test_scene_enter_and_exit():
    parse_scene(["[enter romeo and juliet]"])
    assert ON_STAGE == {"romeo", "juliet"}

    parse_scene(["[exit romeo]"])
    assert ON_STAGE == {"juliet"}
