#!/usr/bin/env python3
#
#  test_ast.py
"""
This is the module-level docstring

RST uses double asterisks for **strong**, which is
normally rendered as **bold**.

Here **strong is missing a closing double asterisk.

That is considered to be an error, and should fail::

	$ flake8 --select RST RST210/strong.py
	RST210/strong.py:7:1: RST210 Inline strong start-string without end-string.

"""
#
#  Copyright (c) 2020 Joe Bloggs
#
#  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi in luctus
#  eros, vitae malesuada velit. Aliquam erat volutpat. Quisque fringilla ligula
#  non tristique faucibus. Nulla eu libero nec metus viverra vehicula at mollis
#  libero. Suspendisse sollicitudin efficitur finibus. Praesent at feugiat
#  dolor, quis semper nunc. Pellentesque ornare porta volutpat. Morbi pulvinar
#  ultrices congue. Nullam eu est felis.
#


class MyClass(object):
	"""
	Long
	=====
	An overly long underline (here one extra equals sign)
	is considered acceptable.

	Short
	====
	There is a missing equals sign on the above underline,
	and that is considered an error. This should fail::

		$ flake8 --select RST RST212/short_underline.py
		RST212/short_underline.py:10:1: RST212 Title underline too short.

	Nice
	====
	Finally, this underline is just right.

	"""

	def __init__(self):
		"""
		RST uses single asterisks for *emphasis*, which is normally rendered as
		*italics*.

		Here *emphasis is missing a closing asterisk.

		That is considered to be an error, and should fail::

			$ flake8 --select RST RST213/emphasis.py
			RST213/emphasis.py:7:1: RST213 Inline emphasis start-string without end-string.
		"""

	class NestedClass:
		"""
		RST uses double backticks for ``literals`` like code
		snippets.

		Here ``literal is missing the closing backticks.

		That is considered to be an error, and should fail::

			$ flake8 --select RST RST214/literal.py
			RST214/literal.py:7:1: RST214 Inline emphasis start-string without end-string.
		"""

		@classmethod
		def create(cls):
			"""
			RST uses single backticks or back-quotes for various
			things including interpreted text roles and references.

			Here `example is missing a closing backtick.

			That is considered to be an error, and should fail::

				$ flake8 --select RST RST215/backticks.py
				RST215/backticks.py:7:1: RST215 Inline interpreted text or phrase reference start-string without end-string.
			"""


def my_function():
	"""
	RST uses single backticks or back-quotes for various things including
	interpreted text roles and references.

	Without a semi-colon prefix or suffix, `example` has the default role.
	A prefix like :code:`example` or a suffix like `example`:math: is allowed.

	However, :code:`example`:math: with both prefix and suffix is considered to be
	an error and should fail validation:

		$ flake8 --select RST RST216/roles.py
		RST216/roles.py:10:1: RST216 Multiple roles in interpreted text (both prefix and suffix present; only one allowed).
	"""

	a = 1+2
	print(a)

	def nested_function():
		"""
		RST uses single backticks or back-quotes for various things including
		interpreted text roles and references.

		Without a semi-colon prefix or suffix, `example` has the default role.
		A prefix like :code:`example` or a suffix like `example`:math: is allowed.

		However, trailing underscores have special meaning for referencing, thus
		`code`:example:_ is considered to be an error:

			$ flake8 --select RST RST217/roles.py
			RST217/roles.py:10:1: RST17 Mismatch: both interpreted text role suffix and reference suffix.
		"""

		pass

	def noqa_function():
		"""**My Docstring"""  # noqa
