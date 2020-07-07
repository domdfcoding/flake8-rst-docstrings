"""Check Python docstrings validate as reStructuredText (RST).

This is a plugin for the tool flake8 tool for checking Python
source code.
"""

import ast
import logging
import re
import sys
from typing import Any, Dict, Generator, List, Tuple, Type, Union

import restructuredtext_lint as rst_lint


__version__ = "0.0.13"

log = logging.getLogger(__name__)

rst_prefix = "RST"
rst_fail_load = 900
rst_fail_parse = 901
rst_fail_all = 902
rst_fail_lint = 903

# Level 1 - info
code_mapping_info = {
    "Possible title underline, too short for the title.": 1,
    "Unexpected possible title overline or transition.": 2,
}

# Level 2 - warning
code_mapping_warning = {
    # XXX ends without a blank line; unexpected unindent:
    "Block quote ends without a blank line; unexpected unindent.": 1,
    "Bullet list ends without a blank line; unexpected unindent.": 2,
    "Definition list ends without a blank line; unexpected unindent.": 3,
    "Enumerated list ends without a blank line; unexpected unindent.": 4,
    "Explicit markup ends without a blank line; unexpected unindent.": 5,
    "Field list ends without a blank line; unexpected unindent.": 6,
    "Literal block ends without a blank line; unexpected unindent.": 7,
    "Option list ends without a blank line; unexpected unindent.": 8,
    # Other:
    "Inline strong start-string without end-string.": 10,
    "Blank line required after table.": 11,
    "Title underline too short.": 12,
    "Inline emphasis start-string without end-string.": 13,
    "Inline literal start-string without end-string.": 14,
    "Inline interpreted text or phrase reference start-string without end-string.": 15,
    "Multiple roles in interpreted text (both prefix and suffix present; only one allowed).": 16,  # noqa: E501
    "Mismatch: both interpreted text role suffix and reference suffix.": 17,
    "Literal block expected; none found.": 18,
    "Inline substitution_reference start-string without end-string.": 19,
}

# Level 3 - error
code_mapping_error = {
    "Unexpected indentation.": 1,
    "Malformed table.": 2,
    # e.g. Unknown directive type "req".
    "Unknown directive type": 3,
    # e.g. Unknown interpreted text role "need".
    "Unknown interpreted text role": 4,
    # e.g. Undefined substitution referenced: "dict".
    "Undefined substitution referenced:": 5,
    # e.g. Unknown target name: "license_txt".
    "Unknown target name:": 6,
}

# Level 4 - severe
code_mapping_severe = {"Unexpected section title.": 1}

code_mappings_by_level = {
    1: code_mapping_info,
    2: code_mapping_warning,
    3: code_mapping_error,
    4: code_mapping_severe,
}


def code_mapping(level, msg, extra_directives, extra_roles, default=99):
    """Return an error code between 0 and 99."""
    try:
        return code_mappings_by_level[level][msg]
    except KeyError:
        pass
    # Following assumes any variable messages take the format
    # of 'Fixed text "variable text".' only:
    # e.g. 'Unknown directive type "req".'
    # ---> 'Unknown directive type'
    # e.g. 'Unknown interpreted text role "need".'
    # ---> 'Unknown interpreted text role'
    if msg.count('"') == 2 and ' "' in msg and msg.endswith('".'):
        txt = msg[: msg.index(' "')]
        value = msg.split('"', 2)[1]
        if txt == "Unknown directive type" and value in extra_directives:
            return 0
        if txt == "Unknown interpreted text role" and value in extra_roles:
            return 0
        return code_mappings_by_level[level].get(txt, default)
    return default


####################################
# Start of code copied from PEP257 #
####################################

# This is the reference implementation of the alogrithm
# in PEP257 for removing the indentation of a docstring,
# which has been placed in the public domain.
#
# This includes the minor change from sys.maxint to
# sys.maxsize for Python 3 compatibility.
#
# https://www.python.org/dev/peps/pep-0257/#handling-docstring-indentation


def trim(docstring):
    """PEP257 docstring indentation trim function."""
    if not docstring:
        return ""
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Stripping trailing and leading blank lines throws the line numbering off
    # Strip off trailing and leading blank lines:
    # while trimmed and not trimmed[-1]:
    #     trimmed.pop()
    # while trimmed and not trimmed[0]:
    #     trimmed.pop(0)
    # Return a single string:
    return "\n".join(trimmed)


##################################
# End of code copied from PEP257 #
##################################


def humanize(string):
    """Make a string human readable."""
    return re.compile(r"(.)([A-Z]+)").sub(r"\1 \2", string).lower()


class Visitor(ast.NodeVisitor):
    """
    Class to traverse an Abstract Syntax Tree (AST), extract docstrings and check them.
    """

    def __init__(self, extra_roles, extra_directives) -> None:
        """Initialise the AST NodeVisitor."""
        self.errors: List[Tuple[int, int, str]] = []
        self._from_imports: Dict[str, str] = {}

        if extra_roles is None:
            self.extra_roles = []
        else:
            self.extra_roles = extra_roles

        if extra_directives is None:
            self.extra_directives = []
        else:
            self.extra_directives = extra_directives

    def _check_docstring(self, node: Union[ast.ClassDef, ast.FunctionDef, ast.Module]):
        docstring = ast.get_docstring(node, clean=False)

        if docstring:
            if isinstance(node, ast.Module):
                # lineno = 0
                col_offset = -1
            else:
                # lineno = node.lineno
                col_offset = node.col_offset

            doc_end_lineno = node.body[0].value.lineno
            split_docstring = docstring.splitlines()
            doc_line_length = len(split_docstring)

            # Special casing for docstrings where the final line doesn't have indentation.
            # (Usually module docstring)
            if not re.match(r"^\s+$", split_docstring[-1]):
                doc_line_length += 1

            # Calculate the start line
            doc_start_lineno = doc_end_lineno - doc_line_length

            # If docstring is only a single line the start_lineno is 1 less than the end_lineno.
            # (-1 because docutils start counting at 1)
            if len(split_docstring) == 1:
                doc_start_lineno = doc_end_lineno - 1

            try:
                # Note we use the PEP257 trim algorithm to remove the
                # leading whitespace from each line - this avoids false
                # positive severe error "Unexpected section title."
                unindented = trim(docstring)
                # Off load RST validation to reStructuredText-lint
                # which calls docutils internally.
                # TODO: Should we pass the Python filename as filepath?

                for rst_error in rst_lint.lint(unindented):
                    # TODO - make this a configuration option?
                    if rst_error.level <= 1:
                        continue
                    # Levels:
                    #
                    # 0 - debug   --> we don't receive these
                    # 1 - info    --> RST1## codes
                    # 2 - warning --> RST2## codes
                    # 3 - error   --> RST3## codes
                    # 4 - severe  --> RST4## codes
                    #
                    # Map the string to a unique code:
                    msg = rst_error.message.split("\n", 1)[0]

                    code = code_mapping(
                            rst_error.level,
                            msg,
                            self.extra_directives,
                            self.extra_roles,
                            )

                    if not code:
                        # We ignored it, e.g. a known Sphinx role
                        continue

                    assert 0 < code < 100, code
                    code += 100 * rst_error.level
                    msg = "%s%03i %s" % (rst_prefix, code, msg)

                    # This will return the line number by combining the
                    # start of the docstring with the offset within it.
                    self.errors.append((doc_start_lineno + rst_error.line, col_offset, msg))

            except Exception as err:
                # e.g. UnicodeDecodeError
                msg = "%s%03i %s" % (
                        rst_prefix,
                        rst_fail_lint,
                        "Failed to lint docstring: %s - %s" % (node.name, err),
                        )

                self.errors.append((doc_start_lineno, col_offset, msg))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check the docstring of a function, or a method of a class."""
        self._check_docstring(node)
        super().generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check the docstring of a class."""
        self._check_docstring(node)
        super().generic_visit(node)

    def visit_Module(self, node: ast.Module) -> None:
        """Check the module-level docstring."""
        self._check_docstring(node)
        super().generic_visit(node)


class Plugin:
    """Checker of Python docstrings as reStructuredText."""

    name: str = "rst-docstrings"
    version: str = __version__
    extra_directives: List[str] = []
    extra_roles: List[str] = []

    def __init__(self, tree: ast.AST):
        """Initialise the flake8_rst_docstrings with an Abstract Syntax Tree (AST)."""
        self._tree = tree
        # self.extra_directives = None
        # self.extra_roles = None

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        """
        Traverse the Abstract Syntax Tree, extract docstrings and check them.

        Yields a tuple of (line number, column offset, error message, type(self))
        """
        visitor = Visitor(self.extra_roles, self.extra_directives)
        visitor.visit(self._tree)

        for line, col, msg in visitor.errors:
            yield line, col, msg, type(self)

    @classmethod
    def add_options(cls, parser):
        """Add RST directives and roles options."""
        parser.add_option(
                "--rst-directives",
                metavar="LIST",
                default="",
                parse_from_config=True,
                comma_separated_list=True,
                help="Comma-separated list of additional RST directives.",
                )
        parser.add_option(
                "--rst-roles",
                metavar="LIST",
                default="",
                parse_from_config=True,
                comma_separated_list=True,
                help="Comma-separated list of additional RST roles.",
                )

    @classmethod
    def parse_options(cls, options):
        """Adding black-config option."""
        cls.extra_directives = options.rst_directives
        cls.extra_roles = options.rst_roles
