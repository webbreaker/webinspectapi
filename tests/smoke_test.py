import sys
import pytest


def f(name):
    print("Hello {}".format(name))


def test_f(capfd):
    f("WebInspectApi")

    out, err = capfd.readouterr()
    assert out == "Hello WebInspectApi\n"
