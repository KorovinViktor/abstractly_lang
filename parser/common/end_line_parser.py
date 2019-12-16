from typing import Iterable

from line import Line
from parser.base import BaseParser, ParseError
from parser.parse_variant import ParseVariant
from parser.parser_wrapper import WrapperParser


class NotFoundEndLineError(ParseError):
    pass


class EndLineParser(WrapperParser):
    def _wrap(self, parser: BaseParser):
        return EndLineParser(parser)

    def parse(self, line: Line) -> Iterable[ParseVariant]:
        is_found = False
        for variant in super().parse(line):
            if variant.line == '':
                is_found = True
                yield variant

        if not is_found:
            raise NotFoundEndLineError("Not found variant with end line")

    def __eq__(self, other):
        _result = super().__eq__(other)
        if _result is not None:
            return _result

        if not isinstance(other, self.__class__):
            return False

        return self.parser == other.parser
