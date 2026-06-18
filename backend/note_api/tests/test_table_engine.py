from datetime import date

from note_api.app.table_engine import (
    CellData,
    ERROR_VALUE,
    TableData,
    evaluate_formula,
    recalculate_display_values,
)


def _table(cells: dict[tuple[int, int], CellData]) -> TableData:
    return TableData(row_count=10, col_count=10, cells=cells)


def _number_cell(x: int, y: int, value: str) -> CellData:
    return CellData(
        x=x,
        y=y,
        cell_type="number",
        input_value=value,
        display_format="整数",
    )


def _string_cell(x: int, y: int, value: str) -> CellData:
    return CellData(x=x, y=y, cell_type="string", input_value=value, display_format="")


def _date_cell(x: int, y: int, value: str) -> CellData:
    return CellData(
        x=x,
        y=y,
        cell_type="date",
        input_value=value,
        display_format="YYYY/MM/DD",
    )


def test_if_numeric_condition() -> None:
    table = _table(
        {
            (1, 1): _number_cell(1, 1, "10"),
            (2, 1): _number_cell(2, 1, "=If(Cell(1,1)>5, 100, 200)"),
        }
    )
    recalculate_display_values(table)
    assert table.cells[(2, 1)].display_value == "100"


def test_if_string_equality() -> None:
    table = _table(
        {
            (1, 1): _string_cell(1, 1, "apple"),
            (2, 1): _number_cell(2, 1, '=If(Cell(1,1)="apple", 1, 0)'),
        }
    )
    recalculate_display_values(table)
    assert table.cells[(2, 1)].display_value == "1"


def test_if_string_lexicographic() -> None:
    table = _table(
        {
            (1, 1): _string_cell(1, 1, "banana"),
            (2, 1): _number_cell(2, 1, '=If(Cell(1,1)>"apple", 1, 0)'),
        }
    )
    recalculate_display_values(table)
    assert table.cells[(2, 1)].display_value == "1"


def test_if_date_comparison() -> None:
    table = _table(
        {
            (1, 1): _date_cell(1, 1, "2024/06/01"),
            (2, 1): _date_cell(2, 1, "2024/12/01"),
            (3, 1): _number_cell(3, 1, '=If(Cell(1,1)<Cell(2,1), 1, 0)'),
        }
    )
    recalculate_display_values(table)
    assert table.cells[(3, 1)].display_value == "1"


def test_and_or_not() -> None:
    table = _table(
        {
            (1, 1): _number_cell(1, 1, "8"),
            (2, 1): _number_cell(2, 1, "=If(And(Cell(1,1)>5, Cell(1,1)<10), 1, 0)"),
            (3, 1): _number_cell(3, 1, "=If(Or(Cell(1,1)<5, Cell(1,1)>7), 2, 0)"),
            (4, 1): _number_cell(4, 1, "=If(Not(Cell(1,1)=0), 3, 0)"),
        }
    )
    recalculate_display_values(table)
    assert table.cells[(2, 1)].display_value == "1"
    assert table.cells[(3, 1)].display_value == "2"
    assert table.cells[(4, 1)].display_value == "3"


def test_nested_if() -> None:
    table = _table({(1, 1): _number_cell(1, 1, "=If(1=2, 1, If(2=2, 9, 0))")})
    recalculate_display_values(table)
    assert table.cells[(1, 1)].display_value == "9"


def test_mixed_type_comparison_is_error() -> None:
    def resolve(_x: int, _y: int) -> str:
        return "abc"

    try:
        evaluate_formula('If("abc"=1, 1, 0)', resolve)
        assert False, "expected error"
    except ValueError as exc:
        assert str(exc) == ERROR_VALUE


def test_string_cell_formula() -> None:
    table = _table(
        {
            (1, 1): _string_cell(1, 1, "apple"),
            (2, 1): _string_cell(2, 1, '=If(Cell(1,1)="apple", "yes", "no")'),
            (3, 1): _string_cell(3, 1, "=Cell(1,1)"),
        }
    )
    recalculate_display_values(table)
    assert table.cells[(2, 1)].display_value == "yes"
    assert table.cells[(3, 1)].display_value == "apple"


def test_string_cell_formula_type_mismatch() -> None:
    table = _table(
        {
            (1, 1): _number_cell(1, 1, "42"),
            (2, 1): _string_cell(2, 1, "=Cell(1,1)"),
            (3, 1): _string_cell(3, 1, '=If(1=1, 5, "no")'),
        }
    )
    recalculate_display_values(table)
    assert table.cells[(2, 1)].display_value == ERROR_VALUE
    assert table.cells[(3, 1)].display_value == ERROR_VALUE


def test_arithmetic_with_if() -> None:
    table = _table({(1, 1): _number_cell(1, 1, "=If(2>1, 3, 0)+4")})
    recalculate_display_values(table)
    assert table.cells[(1, 1)].display_value == "7"
