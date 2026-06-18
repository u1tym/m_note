"""表（table）パーツ: 数式評価・表示値算出・参照調整。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Callable, Union

FormulaScalar = Union[float, str, date, time, datetime]
ResolveCellRaw = Callable[[int, int], FormulaScalar]

ERROR_CYCLE = "#CYCLE!"
ERROR_VALUE = "#VALUE!"
ERROR_ERROR = "#ERROR!"

CELL_TYPES = frozenset({"string", "date", "time", "datetime", "number"})

DISPLAY_FORMATS: dict[str, frozenset[str]] = {
    "date": frozenset({"YYYY/MM/DD", "MM/DD"}),
    "time": frozenset({"hh:mm", "hh:mm:ss"}),
    "datetime": frozenset({"YYYY/MM/DD hh:mm", "YYYY/MM/DD hh:mm:ss"}),
    "number": frozenset({"整数", "小数2桁", "カンマ付き整数", "カンマ付き小数2桁"}),
}

TEXT_ALIGNS = frozenset({"左寄せ", "中央寄せ", "右寄せ"})
DEFAULT_TEXT_ALIGN = "左寄せ"

CELL_REF_PATTERN = re.compile(r"Cell\((\$?)(\d+),\s*(\$?)(\d+)\)")


@dataclass
class CellData:
    x: int
    y: int
    cell_type: str
    input_value: str
    display_format: str
    display_value: str = ""
    text_align: str = DEFAULT_TEXT_ALIGN


@dataclass
class TableData:
    row_count: int
    col_count: int
    cells: dict[tuple[int, int], CellData]


def validate_cell_type(cell_type: str) -> bool:
    return cell_type in CELL_TYPES


def validate_display_format(cell_type: str, display_format: str) -> bool:
    if cell_type == "string":
        return True
    if not display_format:
        return False
    allowed = DISPLAY_FORMATS.get(cell_type)
    return allowed is not None and display_format in allowed


def validate_text_align(text_align: str) -> bool:
    return text_align in TEXT_ALIGNS


def _parse_date(text: str) -> date | None:
    normalized = text.strip().replace("-", "/")
    for fmt in ("%Y/%m/%d", "%m/%d"):
        try:
            parsed = datetime.strptime(normalized, fmt)
            if fmt == "%m/%d":
                return date(datetime.now().year, parsed.month, parsed.day)
            return parsed.date()
        except ValueError:
            continue
    return None


def _parse_time(text: str) -> time | None:
    normalized = text.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(normalized, fmt).time()
        except ValueError:
            continue
    parts = normalized.split(":")
    if len(parts) in (2, 3) and all(part.isdigit() for part in parts):
        try:
            hour = int(parts[0])
            minute = int(parts[1])
            second = int(parts[2]) if len(parts) == 3 else 0
            return time(hour, minute, second)
        except ValueError:
            return None
    return None


def _parse_datetime(text: str) -> datetime | None:
    normalized = text.strip().replace("-", "/")
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def _format_date(value: date, display_format: str) -> str:
    if display_format == "MM/DD":
        return value.strftime("%m/%d")
    return value.strftime("%Y/%m/%d")


def _format_time(value: time, display_format: str) -> str:
    if display_format == "hh:mm:ss":
        return value.strftime("%H:%M:%S")
    return value.strftime("%H:%M")


def _format_datetime(value: datetime, display_format: str) -> str:
    if display_format == "YYYY/MM/DD hh:mm:ss":
        return value.strftime("%Y/%m/%d %H:%M:%S")
    return value.strftime("%Y/%m/%d %H:%M")


def _format_number(value: float, display_format: str) -> str:
    if display_format == "整数":
        return str(int(round(value)))
    if display_format == "小数2桁":
        return f"{value:.2f}"
    if display_format == "カンマ付き整数":
        return f"{int(round(value)):,}"
    if display_format == "カンマ付き小数2桁":
        return f"{value:,.2f}"
    return str(value)


def _try_parse_number(text: str) -> float | None:
    cleaned = text.strip().replace(",", "")
    if not cleaned:
        return None
    try:
        return float(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        return None


def _scalar_kind(value: FormulaScalar) -> str:
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, date) and not isinstance(value, datetime):
        return "date"
    if isinstance(value, time):
        return "time"
    if isinstance(value, datetime):
        return "datetime"
    return "unknown"


def _normalize_scalar(value: FormulaScalar) -> FormulaScalar:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return 0.0
        number = _try_parse_number(stripped)
        if number is not None:
            return number
        parsed_date = _parse_date(stripped)
        if parsed_date is not None:
            return parsed_date
        parsed_datetime = _parse_datetime(stripped)
        if parsed_datetime is not None:
            return parsed_datetime
        parsed_time = _parse_time(stripped)
        if parsed_time is not None:
            return parsed_time
        return stripped
    return value


def _compare_scalars(left: FormulaScalar, op: str, right: FormulaScalar) -> bool:
    left_norm = _normalize_scalar(left)
    right_norm = _normalize_scalar(right)
    left_kind = _scalar_kind(left_norm)
    right_kind = _scalar_kind(right_norm)

    if left_kind != right_kind:
        raise ValueError(ERROR_VALUE)

    if left_kind == "number":
        if op == "=":
            return float(left_norm) == float(right_norm)
        if op == ">":
            return float(left_norm) > float(right_norm)
        if op == "<":
            return float(left_norm) < float(right_norm)
    elif left_kind == "string":
        if op == "=":
            return str(left_norm) == str(right_norm)
        if op == ">":
            return str(left_norm) > str(right_norm)
        if op == "<":
            return str(left_norm) < str(right_norm)
    elif left_kind == "date":
        if op == "=":
            return left_norm == right_norm
        if op == ">":
            return left_norm > right_norm
        if op == "<":
            return left_norm < right_norm
    elif left_kind == "time":
        if op == "=":
            return left_norm == right_norm
        if op == ">":
            return left_norm > right_norm
        if op == "<":
            return left_norm < right_norm
    elif left_kind == "datetime":
        if op == "=":
            return left_norm == right_norm
        if op == ">":
            return left_norm > right_norm
        if op == "<":
            return left_norm < right_norm

    raise ValueError(ERROR_VALUE)


def _to_arithmetic_number(value: FormulaScalar) -> float:
    normalized = _normalize_scalar(value)
    if isinstance(normalized, float):
        return normalized
    raise ValueError(ERROR_VALUE)


def _formula_scalar_to_number(value: FormulaScalar) -> float:
    normalized = _normalize_scalar(value)
    if isinstance(normalized, float):
        return normalized
    raise ValueError(ERROR_VALUE)


def _formula_scalar_to_string(value: FormulaScalar) -> str:
    if isinstance(value, str):
        return value
    raise ValueError(ERROR_VALUE)


def _canonical_time_string(value: time) -> str:
    if value.second:
        return value.strftime("%H:%M:%S")
    return value.strftime("%H:%M")


def _formula_scalar_to_time(value: FormulaScalar) -> str:
    normalized = _normalize_scalar(value)
    if isinstance(normalized, time):
        return _canonical_time_string(normalized)
    raise ValueError(ERROR_VALUE)


def _formula_scalar_to_date(value: FormulaScalar) -> str:
    normalized = _normalize_scalar(value)
    if isinstance(normalized, date) and not isinstance(normalized, datetime):
        return normalized.strftime("%Y/%m/%d")
    raise ValueError(ERROR_VALUE)


def _formula_scalar_to_datetime(value: FormulaScalar) -> str:
    normalized = _normalize_scalar(value)
    if isinstance(normalized, datetime):
        if normalized.second:
            return normalized.strftime("%Y/%m/%d %H:%M:%S")
        return normalized.strftime("%Y/%m/%d %H:%M")
    raise ValueError(ERROR_VALUE)


def _resolve_cell_raw_for_formula(
    table: TableData,
    stack: set[tuple[int, int]],
    cache: dict[tuple[int, int], str | float | None],
    x: int,
    y: int,
) -> FormulaScalar:
    ref = table.cells.get((x, y))
    if ref is None:
        return 0.0
    raw = _compute_raw_value(ref, table, stack, cache)
    if isinstance(raw, str):
        if raw in (ERROR_CYCLE, ERROR_VALUE, ERROR_ERROR):
            raise ValueError(raw)
        if not raw.strip():
            return 0.0
        return raw
    if raw is None:
        return 0.0
    if isinstance(raw, float):
        return raw
    raise ValueError(ERROR_VALUE)


def _evaluate_cell_formula(
    body: str,
    table: TableData,
    stack: set[tuple[int, int]],
    cache: dict[tuple[int, int], str | float | None],
    *,
    expect: str,
) -> str | float:
    resolve_cell_raw = lambda x, y: _resolve_cell_raw_for_formula(table, stack, cache, x, y)
    value = evaluate_formula(body, resolve_cell_raw)
    if expect == "number":
        return _formula_scalar_to_number(value)
    if expect == "string":
        return _formula_scalar_to_string(value)
    if expect == "time":
        return _formula_scalar_to_time(value)
    if expect == "date":
        return _formula_scalar_to_date(value)
    if expect == "datetime":
        return _formula_scalar_to_datetime(value)
    raise ValueError(ERROR_ERROR)


class _FormulaParser:
    def __init__(self, text: str, resolve_cell: ResolveCellRaw) -> None:
        self.text = text
        self.pos = 0
        self.resolve_cell = resolve_cell

    def parse(self) -> FormulaScalar:
        value = self._parse_value_expr()
        self._skip_ws()
        if self.pos < len(self.text):
            raise ValueError("invalid formula")
        return value

    def _peek(self) -> str:
        self._skip_ws()
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def _consume(self, ch: str) -> None:
        self._skip_ws()
        if self.pos >= len(self.text) or self.text[self.pos] != ch:
            raise ValueError(f"expected {ch}")
        self.pos += 1

    def _skip_ws(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def _peek_identifier(self) -> str | None:
        self._skip_ws()
        if self.pos >= len(self.text):
            return None
        if self.text[self.pos : self.pos + 4].lower() == "cell":
            return None
        start = self.pos
        while self.pos < len(self.text) and (
            self.text[self.pos].isalnum() or self.text[self.pos] == "_"
        ):
            self.pos += 1
        if start == self.pos:
            return None
        ident = self.text[start : self.pos]
        self.pos = start
        return ident

    def _consume_identifier(self, expected: str) -> None:
        ident = self._peek_identifier()
        if ident is None or ident.lower() != expected.lower():
            raise ValueError(f"expected {expected}")
        self.pos += len(ident)

    def _parse_number_literal(self) -> float:
        self._skip_ws()
        start = self.pos
        if self._peek() == "-":
            self.pos += 1
        while self.pos < len(self.text) and (
            self.text[self.pos].isdigit() or self.text[self.pos] in "."
        ):
            self.pos += 1
        token = self.text[start : self.pos]
        value = _try_parse_number(token)
        if value is None:
            raise ValueError("invalid number")
        return value

    def _parse_string_literal(self) -> str:
        self._skip_ws()
        if self._peek() != '"':
            raise ValueError("expected string")
        self.pos += 1
        chars: list[str] = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == '"':
                self.pos += 1
                return "".join(chars)
            if ch == "\\" and self.pos + 1 < len(self.text):
                self.pos += 1
                chars.append(self.text[self.pos])
                self.pos += 1
                continue
            chars.append(ch)
            self.pos += 1
        raise ValueError("unterminated string")

    def _parse_cell_ref(self) -> FormulaScalar:
        self._skip_ws()
        if not self.text[self.pos :].startswith("Cell("):
            raise ValueError("expected Cell(")
        match = CELL_REF_PATTERN.match(self.text, self.pos)
        if match is None:
            raise ValueError("invalid Cell()")
        x = int(match.group(2))
        y = int(match.group(4))
        self.pos = match.end()
        return self.resolve_cell(x, y)

    def _parse_if_call(self) -> FormulaScalar:
        self._consume_identifier("If")
        self._consume("(")
        condition = self._parse_condition()
        self._consume(",")
        true_value = self._parse_value_expr()
        self._consume(",")
        false_value = self._parse_value_expr()
        self._consume(")")
        return true_value if condition else false_value

    def _parse_condition(self) -> bool:
        return self._parse_or()

    def _parse_or(self) -> bool:
        ident = self._peek_identifier()
        if ident is not None and ident.lower() == "or":
            self._consume_identifier("Or")
            self._consume("(")
            values = [self._parse_condition()]
            while True:
                self._skip_ws()
                if self._peek() == ")":
                    break
                self._consume(",")
                values.append(self._parse_condition())
            self._consume(")")
            return any(values)

        return self._parse_and()

    def _parse_and(self) -> bool:
        ident = self._peek_identifier()
        if ident is not None and ident.lower() == "and":
            self._consume_identifier("And")
            self._consume("(")
            values = [self._parse_condition()]
            while True:
                self._skip_ws()
                if self._peek() == ")":
                    break
                self._consume(",")
                values.append(self._parse_condition())
            self._consume(")")
            return all(values)

        return self._parse_not()

    def _parse_not(self) -> bool:
        ident = self._peek_identifier()
        if ident is not None and ident.lower() == "not":
            self._consume_identifier("Not")
            self._consume("(")
            value = self._parse_condition()
            self._consume(")")
            return not value

        return self._parse_comparison()

    def _parse_comparison(self) -> bool:
        self._skip_ws()
        if self._peek() == "(":
            self.pos += 1
            value = self._parse_condition()
            self._consume(")")
            return value

        left = self._parse_value_expr()
        self._skip_ws()
        if self.pos >= len(self.text):
            raise ValueError("expected comparison")
        op = self.text[self.pos]
        if op not in "=><":
            raise ValueError("expected comparison")
        self.pos += 1
        right = self._parse_value_expr()
        return _compare_scalars(left, op, right)

    def _parse_if_or_value(self) -> FormulaScalar:
        ident = self._peek_identifier()
        if ident is not None and ident.lower() == "if":
            return self._parse_if_call()
        return self._parse_term()

    def _parse_value_expr(self) -> FormulaScalar:
        value = self._parse_if_or_value()
        while True:
            self._skip_ws()
            if self.pos >= len(self.text):
                break
            op = self.text[self.pos]
            if op not in "+-":
                break
            self.pos += 1
            rhs = self._parse_if_or_value()
            if op == "+":
                value = _to_arithmetic_number(value) + _to_arithmetic_number(rhs)
            else:
                value = _to_arithmetic_number(value) - _to_arithmetic_number(rhs)
        return value

    def _parse_factor(self) -> FormulaScalar:
        self._skip_ws()
        ch = self._peek()
        if ch == "-":
            self.pos += 1
            return -_to_arithmetic_number(self._parse_factor())
        if ch == "(":
            self.pos += 1
            value = self._parse_value_expr()
            self._consume(")")
            return value
        if ch == '"':
            return self._parse_string_literal()
        if self.text[self.pos :].startswith("Cell("):
            return self._parse_cell_ref()
        ident = self._peek_identifier()
        if ident is not None and ident.lower() == "if":
            return self._parse_if_call()
        return self._parse_number_literal()

    def _parse_term(self) -> FormulaScalar:
        value = self._parse_factor()
        while True:
            self._skip_ws()
            if self.pos >= len(self.text):
                break
            op = self.text[self.pos]
            if op not in "*/":
                break
            self.pos += 1
            rhs = self._parse_factor()
            left = _to_arithmetic_number(value)
            right = _to_arithmetic_number(rhs)
            if op == "*":
                value = left * right
            else:
                if right == 0:
                    raise ValueError("division by zero")
                value = left / right
        return value


def evaluate_formula(formula_body: str, resolve_cell: ResolveCellRaw) -> FormulaScalar:
    return _FormulaParser(formula_body, resolve_cell).parse()


def _compute_raw_value(
    cell: CellData,
    table: TableData,
    stack: set[tuple[int, int]],
    cache: dict[tuple[int, int], str | float | None],
) -> str | float | None:
    key = (cell.x, cell.y)
    if key in cache:
        cached = cache[key]
        if cached == ERROR_CYCLE:
            return ERROR_CYCLE
        return cached

    if key in stack:
        cache[key] = ERROR_CYCLE
        return ERROR_CYCLE

    stack.add(key)
    try:
        if cell.cell_type == "string":
            text = cell.input_value.strip()
            if text.startswith("="):
                result = _evaluate_cell_formula(
                    text[1:], table, stack, cache, expect="string"
                )
            else:
                result = cell.input_value
        elif cell.cell_type == "number":
            text = cell.input_value.strip()
            if text.startswith("="):
                result = _evaluate_cell_formula(
                    text[1:], table, stack, cache, expect="number"
                )
            else:
                parsed = _try_parse_number(text)
                if parsed is None and text:
                    result = ERROR_VALUE
                else:
                    result = parsed if parsed is not None else 0.0
        elif cell.cell_type == "date":
            text = cell.input_value.strip()
            if text.startswith("="):
                result = _evaluate_cell_formula(
                    text[1:], table, stack, cache, expect="date"
                )
            else:
                parsed = _parse_date(cell.input_value)
                result = cell.input_value if parsed else ERROR_VALUE if text else ""
        elif cell.cell_type == "time":
            text = cell.input_value.strip()
            if text.startswith("="):
                result = _evaluate_cell_formula(
                    text[1:], table, stack, cache, expect="time"
                )
            else:
                parsed = _parse_time(cell.input_value)
                result = cell.input_value if parsed else ERROR_VALUE if text else ""
        elif cell.cell_type == "datetime":
            text = cell.input_value.strip()
            if text.startswith("="):
                result = _evaluate_cell_formula(
                    text[1:], table, stack, cache, expect="datetime"
                )
            else:
                parsed = _parse_datetime(cell.input_value)
                result = cell.input_value if parsed else ERROR_VALUE if text else ""
        else:
            result = ERROR_ERROR
    except ValueError as exc:
        msg = str(exc)
        result = msg if msg in (ERROR_CYCLE, ERROR_VALUE, ERROR_ERROR) else ERROR_VALUE
    finally:
        stack.discard(key)

    cache[key] = result
    return result


def _format_raw_value(cell: CellData, raw: str | float | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        if raw in (ERROR_CYCLE, ERROR_VALUE, ERROR_ERROR):
            return raw
        if cell.cell_type == "string":
            return raw
        if cell.cell_type == "date":
            parsed = _parse_date(raw)
            return _format_date(parsed, cell.display_format) if parsed else ERROR_VALUE
        if cell.cell_type == "time":
            parsed = _parse_time(raw)
            return _format_time(parsed, cell.display_format) if parsed else ERROR_VALUE
        if cell.cell_type == "datetime":
            parsed = _parse_datetime(raw)
            return _format_datetime(parsed, cell.display_format) if parsed else ERROR_VALUE
        return raw

    if cell.cell_type == "number":
        if cell.display_format:
            return _format_number(float(raw), cell.display_format)
        return str(raw)

    if cell.cell_type == "date":
        if isinstance(raw, float):
            return ERROR_VALUE
        parsed = _parse_date(str(raw))
        return _format_date(parsed, cell.display_format) if parsed else ERROR_VALUE

    if cell.cell_type == "time":
        parsed = _parse_time(str(raw))
        return _format_time(parsed, cell.display_format) if parsed else ERROR_VALUE

    if cell.cell_type == "datetime":
        parsed = _parse_datetime(str(raw))
        return _format_datetime(parsed, cell.display_format) if parsed else ERROR_VALUE

    return str(raw)


def recalculate_display_values(table: TableData) -> None:
    cache: dict[tuple[int, int], str | float | None] = {}
    for cell in table.cells.values():
        raw = _compute_raw_value(cell, table, set(), cache)
        cell.display_value = _format_raw_value(cell, raw)


def shift_cell_references(
    input_value: str,
    dx: int,
    dy: int,
    *,
    adjust_relative_only: bool = True,
) -> str:
    if not input_value.startswith("="):
        return input_value

    def replacer(match: re.Match[str]) -> str:
        x_abs, x_str, y_abs, y_str = match.group(1), match.group(2), match.group(3), match.group(4)
        x = int(x_str)
        y = int(y_str)
        if not x_abs:
            x += dx
        if not y_abs:
            y += dy
        if adjust_relative_only and (x_abs and y_abs):
            return match.group(0)
        x_part = f"${x}" if x_abs else str(max(1, x))
        y_part = f"${y}" if y_abs else str(max(1, y))
        return f"Cell({x_part},{y_part})"

    return CELL_REF_PATTERN.sub(replacer, input_value)


def shift_cells_for_row_insert(cells: dict[tuple[int, int], CellData], at_row: int) -> None:
    for cell in cells.values():
        if cell.y >= at_row:
            cell.y += 1
        if cell.input_value.startswith("="):
            cell.input_value = _adjust_refs_for_row_insert(cell.input_value, at_row)


def _adjust_refs_for_row_insert(formula: str, at_row: int) -> str:
    def replacer(match: re.Match[str]) -> str:
        x_abs, x_str, y_abs, y_str = match.group(1), match.group(2), match.group(3), match.group(4)
        x = int(x_str)
        y = int(y_str)
        if not y_abs and y >= at_row:
            y += 1
        x_part = f"${x}" if x_abs else str(x)
        y_part = f"${y}" if y_abs else str(y)
        return f"Cell({x_part},{y_part})"

    return CELL_REF_PATTERN.sub(replacer, formula)


def adjust_formulas_for_row_delete(cells: dict[tuple[int, int], CellData], at_row: int) -> None:
    to_delete = [key for key, cell in cells.items() if cell.y == at_row]
    for key in to_delete:
        del cells[key]
    for cell in cells.values():
        if cell.y > at_row:
            cell.y -= 1
        if cell.input_value.startswith("="):
            cell.input_value = _adjust_refs_for_row_delete(cell.input_value, at_row)


def _adjust_refs_for_row_delete(formula: str, at_row: int) -> str:
    def replacer(match: re.Match[str]) -> str:
        x_abs, x_str, y_abs, y_str = match.group(1), match.group(2), match.group(3), match.group(4)
        x = int(x_str)
        y = int(y_str)
        if not y_abs:
            if y == at_row:
                return "#REF!"
            if y > at_row:
                y -= 1
        x_part = f"${x}" if x_abs else str(x)
        y_part = f"${y}" if y_abs else str(y)
        return f"Cell({x_part},{y_part})"

    return CELL_REF_PATTERN.sub(replacer, formula)


def shift_cells_for_col_insert(cells: dict[tuple[int, int], CellData], at_col: int) -> None:
    for cell in cells.values():
        if cell.x >= at_col:
            cell.x += 1
        if cell.input_value.startswith("="):
            cell.input_value = _adjust_refs_for_col_insert(cell.input_value, at_col)


def _adjust_refs_for_col_insert(formula: str, at_col: int) -> str:
    def replacer(match: re.Match[str]) -> str:
        x_abs, x_str, y_abs, y_str = match.group(1), match.group(2), match.group(3), match.group(4)
        x = int(x_str)
        y = int(y_str)
        if not x_abs and x >= at_col:
            x += 1
        x_part = f"${x}" if x_abs else str(x)
        y_part = f"${y}" if y_abs else str(y)
        return f"Cell({x_part},{y_part})"

    return CELL_REF_PATTERN.sub(replacer, formula)


def adjust_formulas_for_col_delete(cells: dict[tuple[int, int], CellData], at_col: int) -> None:
    to_delete = [key for key, cell in cells.items() if cell.x == at_col]
    for key in to_delete:
        del cells[key]
    for cell in cells.values():
        if cell.x > at_col:
            cell.x -= 1
        if cell.input_value.startswith("="):
            cell.input_value = _adjust_refs_for_col_delete(cell.input_value, at_col)


def _adjust_refs_for_col_delete(formula: str, at_col: int) -> str:
    def replacer(match: re.Match[str]) -> str:
        x_abs, x_str, y_abs, y_str = match.group(1), match.group(2), match.group(3), match.group(4)
        x = int(x_str)
        y = int(y_str)
        if not x_abs:
            if x == at_col:
                return "#REF!"
            if x > at_col:
                x -= 1
        x_part = f"${x}" if x_abs else str(x)
        y_part = f"${y}" if y_abs else str(y)
        return f"Cell({x_part},{y_part})"

    return CELL_REF_PATTERN.sub(replacer, formula)


def rebuild_cell_map(cells: dict[tuple[int, int], CellData]) -> dict[tuple[int, int], CellData]:
    rebuilt: dict[tuple[int, int], CellData] = {}
    for cell in cells.values():
        rebuilt[(cell.x, cell.y)] = cell
    return rebuilt
