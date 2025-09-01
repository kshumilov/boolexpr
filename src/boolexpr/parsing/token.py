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

Token types used by lex and parse operations

Interface Classes:
    Token
        EndToken
        KeywordToken
        NameToken
        LiteralToken
            StringToken
            NumberToken
                IntegerToken
                FloatToken
        OperatorToken
        PunctuationToken
"""

import collections

Token = collections.namedtuple("Token", ["value", "lineno", "offset"])


class EndToken(Token):
    """Special token for end of buffer"""


class KeywordToken(Token):
    """Base class for keyword tokens"""


class NameToken(Token):
    """Base class for name tokens"""


class LiteralToken(Token):
    """Base class for literal tokens"""


class StringToken(LiteralToken):
    """literal.string tokens, eg 'hello world'"""


class NumberToken(LiteralToken):
    """Base class for literal.number tokens"""


class IntegerToken(NumberToken):
    """literal.number.integer tokens, eg 42"""


class FloatToken(NumberToken):
    """literal.number.float tokens, eg 6.0221413e+23"""


class OperatorToken(Token):
    """literal.operator tokens, eg +-*/"""


class PunctuationToken(Token):
    """literal.punctuation tokens, eg !@#$"""
