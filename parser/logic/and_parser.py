from typing import Iterable, List

from line import Line
from parser.base import ParseError
from parser.logic._multi_parser import MultiParser
from parser.parse_variant import ParseVariant


class AndParserError(ParseError):
    def __init__(self, msg, errors):
        super().__init__(msg)
        self.errors = errors


class AndParser(MultiParser):
    STR_SYM = '&'

    def parse(self, line: Line) -> Iterable[ParseVariant]:
        variants: List[ParseVariant] = []
        all_errors: List[List] = []

        for i, parser in enumerate(self.parsers):
            errors = []
            all_errors.append(errors)
            try:
                if i == 0:
                    variants = list(parser.parse(line))
                else:
                    child_variants = []
                    for variant in variants:
                        p, cur_line = variant.parser, variant.line
                        try:
                            for sub_variant in parser.parse(cur_line):
                                child_variants.append(ParseVariant(
                                    AndParser(p, sub_variant.parser),
                                    sub_variant.line
                                ))
                        except ParseError as e:
                            # Dublicated code
                            # TODO: Commond add context with or
                            errors.append(e)

                    variants = child_variants

            except ParseError as e:
                # TODO: Commond add context with or
                errors.append(e)

        if variants:
            yield from variants
        else:
            raise AndParserError("No variants :(", all_errors)
