"""Expression parsing, evaluation, state management, and output formatting."""

import math
import re


INVALID_CODE = "Invalid input code"
DIVISION_BY_ZERO = "Division by zero"
SEPARATOR = "-------------------------------------------"
OPERATORS = {"+", "-", "*", "/", "%"}
UNARY_OPERATORS = {"u+", "u-"}
PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "%": 2,
              "u+": 3, "u-": 3}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


class CodeError(Exception):
    """An expected error in one input code."""


def is_valid_name(name):
    return bool(IDENTIFIER_PATTERN.fullmatch(name))


def parse_code(line):
    code = line.strip()
    if not code:
        raise CodeError(INVALID_CODE)
    if "=" not in code:
        return None, code
    if code.count("=") != 1:
        raise CodeError(INVALID_CODE)
    target, expression = (part.strip() for part in code.split("=", 1))
    if not is_valid_name(target) or not expression:
        raise CodeError(INVALID_CODE)
    return target, expression


def tokenize(expression):
    tokens = []
    position = 0
    expecting_operand = True

    while position < len(expression):
        if expression[position].isspace():
            position += 1
            continue

        if number := re.match(r"(?:\d+(?:\.\d*)?|\.\d+)", expression[position:]):
            literal = number[0]
            position += len(literal)
            if position < len(expression) and expression[position].isalpha():
                raise CodeError(INVALID_CODE)
            value = float(literal) if "." in literal else int(literal)
            tokens.append(("num", value))
            expecting_operand = False
            continue

        if name := re.match(r"[A-Za-z][A-Za-z0-9]*", expression[position:]):
            value = name[0]
            position += len(value)
            tokens.append(("var", value))
            expecting_operand = False
            continue

        character = expression[position]
        if character in "+-":
            operator = f"u{character}" if expecting_operand else character
            tokens.append(("op", operator))
            position += 1
            expecting_operand = operator in UNARY_OPERATORS
            continue
        if character in "*/%":
            tokens.append(("op", character))
            position += 1
            expecting_operand = True
            continue
        if character == "(":
            tokens.append(("lpar", character))
            position += 1
            expecting_operand = True
            continue
        if character == ")":
            tokens.append(("rpar", character))
            position += 1
            expecting_operand = False
            continue
        raise CodeError(INVALID_CODE)

    if not tokens:
        raise CodeError(INVALID_CODE)
    return tokens


def validate(tokens):
    expecting_operand = True
    open_parentheses = 0

    for kind, value in tokens:
        if kind == "num":
            if not expecting_operand:
                raise CodeError(INVALID_CODE)
            expecting_operand = False
            continue
        if kind == "var":
            if not expecting_operand:
                raise CodeError(INVALID_CODE)
            expecting_operand = False
            continue
        if kind == "lpar":
            if not expecting_operand:
                raise CodeError(INVALID_CODE)
            open_parentheses += 1
        elif kind == "rpar":
            if expecting_operand or open_parentheses == 0:
                raise CodeError(INVALID_CODE)
            open_parentheses -= 1
        elif value in UNARY_OPERATORS:
            if not expecting_operand:
                raise CodeError(INVALID_CODE)
        else:
            if expecting_operand:
                raise CodeError(INVALID_CODE)
            expecting_operand = True

    if expecting_operand or open_parentheses:
        raise CodeError(INVALID_CODE)


def to_postfix(tokens):
    postfix = []
    stack = []

    for token in tokens:
        kind, value = token
        if kind in {"num", "var"}:
            postfix.append(token)
        elif kind == "lpar":
            stack.append(token)
        elif kind == "rpar":
            while stack and stack[-1][0] != "lpar":
                postfix.append(stack.pop())
            if not stack:
                raise CodeError(INVALID_CODE)
            stack.pop()
        else:
            while stack and stack[-1][0] == "op":
                top = stack[-1][1]
                left_associative = value not in UNARY_OPERATORS
                if PRECEDENCE[top] > PRECEDENCE[value] or (
                        PRECEDENCE[top] == PRECEDENCE[value]
                        and left_associative):
                    postfix.append(stack.pop())
                else:
                    break
            stack.append(token)

    while stack:
        if stack[-1][0] == "lpar":
            raise CodeError(INVALID_CODE)
        postfix.append(stack.pop())
    return postfix


def integer_divide(left, right):
    result = abs(left) // abs(right)
    return -result if (left < 0) != (right < 0) else result


def apply_operator(operator, left, right):
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator == "*":
        return left * right
    if right == 0 and operator in {"/", "%"}:
        raise CodeError(DIVISION_BY_ZERO)
    if operator == "/":
        if isinstance(left, int) and isinstance(right, int):
            return integer_divide(left, right)
        return left / right
    if operator == "%":
        if not isinstance(left, int) or not isinstance(right, int):
            raise CodeError(INVALID_CODE)
        return left - integer_divide(left, right) * right
    raise CodeError(INVALID_CODE)


def evaluate_postfix(postfix, variables):
    values = []
    for kind, value in postfix:
        if kind == "num":
            values.append(value)
        elif kind == "var":
            if value not in variables:
                raise CodeError(f"Undefined variable {value}")
            values.append(variables[value])
        elif value in UNARY_OPERATORS:
            if not values:
                raise CodeError(INVALID_CODE)
            operand = values.pop()
            values.append(-operand if value == "u-" else operand)
        else:
            if len(values) < 2:
                raise CodeError(INVALID_CODE)
            right = values.pop()
            left = values.pop()
            values.append(apply_operator(value, left, right))

    if len(values) != 1:
        raise CodeError(INVALID_CODE)
    return values[0]


def format_value(value):
    if isinstance(value, int):
        return str(value)
    if math.isfinite(value) and value == int(value):
        return str(int(value))
    return "%g" % value


def format_postfix(postfix):
    result = []
    for kind, value in postfix:
        if kind == "num":
            result.append(format_value(value))
        elif value in UNARY_OPERATORS:
            result.append(f"{value[1]}u")
        else:
            result.append(str(value))
    return " ".join(result)


def process_code(line, variables, variables_used):
    target, expression = parse_code(line)
    tokens = tokenize(expression)
    validate(tokens)
    postfix = to_postfix(tokens)
    postfix_text = format_postfix(postfix)

    for kind, value in postfix:
        if kind == "var" and value not in variables_used:
            variables_used.append(value)
    if target and target not in variables_used:
        variables_used.append(target)

    try:
        result = evaluate_postfix(postfix, variables)
    except CodeError as error:
        raise CodeError(error.args[0], postfix_text) from error

    if target:
        variables[target] = result
        return postfix_text, f"{target} = {format_value(result)}"
    return postfix_text, format_value(result)


def run(lines):
    variables = {}
    variables_used = []
    errors = []
    output = []

    for line_number, line in enumerate(lines or [], start=1):
        try:
            postfix, result = process_code(line, variables, variables_used)
        except CodeError as error:
            postfix = error.args[1] if len(error.args) > 1 else "-"
            result = error.args[0]
            errors.append(f"Line {line_number}: {result}")
        output.extend([f"Line: {line.strip()}", f"Postfix: {postfix}",
                       f"Result: {result}", ""])

    output.extend([SEPARATOR, "Variables used:"])
    if variables_used:
        for name in variables_used:
            if name in variables:
                output.append(f"{name} = {format_value(variables[name])}")
            else:
                output.append(f"{name} = undefined")
    else:
        output.append("(none)")
    output.extend(["", SEPARATOR, "Errors found:"])
    output.extend(errors or ["(none)"])
    return "\n".join(output)
