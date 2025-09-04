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

The :mod:`pyeda.boolalg.boolfunc` module implements the fundamentals of
Boolean space, variables and functions.

Data Types:

point
    A dictionary of ``Variable => {0, 1}`` mappings.
    For example, ``{a: 0, b: 1, c: 0, d: 1}``.
    An N-dimensional *point* corresponds to one vertex of an N-dimensional
    *cube*.

untyped point
    An untyped, immutable representation of a *point*,
    represented as ``(frozenset([int]), frozenset([int]))``.
    The integers are Variable uniqids.
    Index zero contains a frozenset of variables mapped to zero,
    and index one contains a frozenset of variables mapped to one.
    This representation is easier to manipulate than the *point*,
    and it is hashable for caching purposes.

term
    A tuple of :math:`N` Boolean functions,
    intended to be used as the input of either an OR or AND function.
    An OR term is called a *maxterm* (product of sums),
    and an AND term is called a *minterm* (sum of products).

Interface Functions:

* :func:`num2point` --- Convert an integer into a point in an N-dimensional
  Boolean space.
* :func:`num2upoint` --- Convert an integer into an untyped point in an
  N-dimensional Boolean space.
* :func:`num2term` --- Convert an integer into a min/max term in an
  N-dimensional Boolean space.

* :func:`point2upoint` --- Convert a point into an untyped point.
* :func:`point2term` --- Convert a point into a min/max term.

* :func:`iter_points` --- Iterate through all points in an N-dimensional
  Boolean space.
* :func:`iter_upoints` --- Iterate through all untyped points in an
  N-dimensional Boolean space.
* :func:`iter_terms` --- Iterate through all min/max terms in an N-dimensional
  Boolean space.

* :func:`vpoint2point` --- Convert a vector point into a point in an
  N-dimensional Boolean space.

Interface Classes:

* :class:`Variable`
* :class:`Function`
"""
