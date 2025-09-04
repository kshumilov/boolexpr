"""
Copyright (c) 2012, Chris Drake
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The :mod:`pyeda.util` module contains top-level utilities,
such as fundamental functions and decorators.

Interface Functions:

* :func:`bit_on` --- Return the value of a number's bit position
* :func:`clog2` --- Return the ceiling log base two of an integer
* :func:`parity` --- Return the parity of an integer
"""


def bit_on(num: int, bit: int) -> bool:
    """Return the value of a number's bit position.

    For example, since :math:`42 = 2^1 + 2^3 + 2^5`,
    this function will return 1 in bit positions 1, 3, 5:

    >>> [bit_on(42, i) for i in range(clog2(42))]
    [0, 1, 0, 1, 0, 1]
    """
    return bool((num >> bit) & 1)


def clog2(num: int) -> int:
    r"""Return the ceiling log base two of an integer :math:`\ge 1`.

    This function tells you the minimum dimension of a Boolean space with at
    least N points.

    For example, here are the values of ``clog2(N)`` for :math:`1 \le N < 18`:

    >>> [clog2(n) for n in range(1, 18)]
    [0, 1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 5]

    This function is undefined for non-positive integers:

    >>> clog2(0)
    Traceback (most recent call last):
        ...
    ValueError: expected num >= 1
    """
    if num < 1:
        raise ValueError("expected num >= 1")

    accum, shifter = 0, 1
    while num > shifter:
        shifter <<= 1
        accum += 1
    return accum


def parity(num: int) -> int:
    """Return the parity of a non-negative integer.

    For example, here are the parities of the first ten integers:

    >>> [parity(n) for n in range(10)]
    [0, 1, 1, 0, 1, 0, 0, 1, 1, 0]

    This function is undefined for negative integers:

    >>> parity(-1)
    Traceback (most recent call last):
        ...
    ValueError: expected num >= 0
    """
    if num < 0:
        raise ValueError("expected num >= 0")

    par = 0
    while num:
        par ^= num & 1
        num >>= 1
    return par
