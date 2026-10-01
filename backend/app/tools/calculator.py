import ast
import math
import operator

from langchain_core.tools import tool


_ALLOWED_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


_ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
}


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise ValueError("Boolean values are not allowed.")

        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError("Only numeric values are allowed.")

    if isinstance(node, ast.BinOp):
        operation = _ALLOWED_BINARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("This mathematical operator is not allowed.")

        left = _evaluate(node.left)
        right = _evaluate(node.right)

        if isinstance(node.op, ast.Pow):
            if abs(right) > 100:
                raise ValueError("Exponent is too large.")

        return operation(left, right)

    if isinstance(node, ast.UnaryOp):
        operation = _ALLOWED_UNARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("This unary operator is not allowed.")

        return operation(_evaluate(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only approved mathematical functions are allowed.")

        function = _ALLOWED_FUNCTIONS.get(node.func.id)

        if function is None:
            raise ValueError(
                f"Function '{node.func.id}' is not allowed."
            )

        if len(node.args) == 0:
            raise ValueError("A function requires an argument.")

        if len(node.args) > 1 and node.func.id != "round":
            raise ValueError("Too many arguments.")

        arguments = [_evaluate(argument) for argument in node.args]

        return function(*arguments)

    raise ValueError(
        f"Unsupported expression element: {type(node).__name__}"
    )


@tool
def calculator(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.

    Use this tool whenever the user asks for an exact mathematical
    calculation instead of doing arithmetic mentally.

    Supported operators:
    +, -, *, /, //, %, **

    Supported functions:
    sqrt(), abs(), round()

    Examples:
    25 * 17
    (100 + 50) / 3
    sqrt(144)
    2 ** 10
    round(10 / 3, 2)
    """

    expression = expression.strip()

    if not expression:
        return "Error: The mathematical expression is empty."

    if len(expression) > 500:
        return "Error: The mathematical expression is too long."

    try:
        tree = ast.parse(
            expression,
            mode="eval",
        )

        result = _evaluate(tree)

        if not math.isfinite(result):
            return "Error: The calculation produced a non-finite result."

        if isinstance(result, float) and result.is_integer():
            return str(int(result))

        return str(result)

    except ZeroDivisionError:
        return "Error: Division by zero is not allowed."

    except (SyntaxError, ValueError, TypeError, OverflowError) as error:
        return f"Error: Unable to calculate the expression. {error}"