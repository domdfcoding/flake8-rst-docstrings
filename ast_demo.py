import ast
import pathlib
import pprint

from flake8_rst_docstrings import Plugin

s = pathlib.Path("tests/test_ast.py").read_text()

pprint.pprint(list(Plugin(ast.parse(s)).run()))
