"""
PE00 - Expression Evaluation
Evaluation module.

Responsibilities of this module:
  - Split each input code into its parts and tell an assignment statement
    (var = expression) apart from a plain expression
  - Convert the expression part from infix form into postfix form
  - Evaluate the postfix form for the +, -, *, / and % operators
  - Keep the running values of the variables and collect the errors found

The GUI calls exactly one function:

    run(lines: list[str]) -> str

    lines  : the input area's contents, already split into individual lines
    return : the complete output text, formatted and ready to display

Number model: a value is an integer unless the code contains a decimal
literal.  Integer / and % follow the C language (truncation toward zero),
which is the language the variable naming rules are borrowed from.

Error handling: every problem with an input code is raised as a CodeError and
handled per line, so one bad code never stops the rest of the input from being
processed.  run() never raises; whatever goes wrong ends up in the output.
"""

import math


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------

class CodeError(Exception):
    """An error in one input code.  Carries the message shown to the user."""
    pass


INVALID_CODE = "Invalid input code"
DIVISION_BY_ZERO = "Division by zero"


def undefined_variable(variable_name):
    return "Undefined variable " + variable_name


# --------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------

# The unary forms are what the tokenizer produces for a leading sign; they
# bind tighter than any binary operator and group from the right, so that
# - - 3 reads as -(-3).
UNARY_OPERATORS = ("u-", "u+")
RIGHT_ASSOCIATIVE_OPERATORS = UNARY_OPERATORS

OPERATOR_PRECEDENCE = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
    "%": 2,
    "u-": 3,
    "u+": 3,
}


def precedence(operator):
    return OPERATOR_PRECEDENCE[operator]


def is_right_associative(operator):
    return operator in RIGHT_ASSOCIATIVE_OPERATORS


# --------------------------------------------------------------------------
# Tokenizing
# --------------------------------------------------------------------------

def is_letter(character):
    return ("a" <= character <= "z") or ("A" <= character <= "Z")


def is_digit(character):
    return "0" <= character <= "9"


def is_valid_name(name):
    """C naming rules, without the underscore: letter, then letters/digits."""
    if not name:
        return False
    if not is_letter(name[0]):
        return False
    for character in name[1:]:
        if not (is_letter(character) or is_digit(character)):
            return False
    return True


def tokenize(expression):
    """Turn an expression string into a list of tokens.

    A token is a (kind, value) pair, one of:
        ("num", number)         numeric literal
        ("var", name)           variable name
        ("op",  symbol)         + - * / % (unary ones become u- and u+)
        ("lpar", "(")  /  ("rpar", ")")

    Raises CodeError for any character or literal that cannot be a token.
    """
    tokens = []
    position = 0
    length = len(expression)

    while position < length:
        character = expression[position]

        # whitespace simply separates tokens
        if character in " \t":
            position += 1
            continue

        # numeric literal
        starts_a_number = is_digit(character) or (
            character == "."
            and position + 1 < length
            and is_digit(expression[position + 1])
        )
        if starts_a_number:
            literal_start = position
            has_decimal_point = False
            while position < length and (is_digit(expression[position])
                                         or expression[position] == "."):
                if expression[position] == ".":
                    if has_decimal_point:
                        raise CodeError(INVALID_CODE)       # 1.2.3
                    has_decimal_point = True
                position += 1
            # a literal may not run straight into a name: 12abc
            if position < length and is_letter(expression[position]):
                raise CodeError(INVALID_CODE)
            literal = expression[literal_start:position]
            number = float(literal) if has_decimal_point else int(literal)
            tokens.append(("num", number))
            continue

        # variable name
        if is_letter(character):
            name_start = position
            while position < length and (is_letter(expression[position])
                                         or is_digit(expression[position])):
                position += 1
            tokens.append(("var", expression[name_start:position]))
            continue

        # operator
        if character in "+-*/%":
            previous_kind = tokens[-1][0] if tokens else None
            # A sign is unary when nothing that can end an operand precedes it.
            is_unary_sign = (character in "+-"
                             and previous_kind in (None, "op", "lpar"))
            if is_unary_sign:
                tokens.append(("op", "u" + character))
            else:
                tokens.append(("op", character))
            position += 1
            continue

        if character == "(":
            tokens.append(("lpar", character))
            position += 1
            continue

        if character == ")":
            tokens.append(("rpar", character))
            position += 1
            continue

        raise CodeError(INVALID_CODE)               # unknown character

    if not tokens:
        raise CodeError(INVALID_CODE)               # empty expression

    return tokens


def validate(tokens):
    """Check that the tokens form a well-formed infix expression.

    The check walks the tokens once and keeps track of whether the next token
    must be an operand (a value, a name, a sign or an opening parenthesis) or
    an operator (a binary operator or a closing parenthesis).
    """
    expecting_operand = True
    open_parenthesis_count = 0

    for token_kind, token_value in tokens:
        if token_kind in ("num", "var"):
            if not expecting_operand:
                raise CodeError(INVALID_CODE)       # 3 4
            if token_kind == "var" and not is_valid_name(token_value):
                raise CodeError(INVALID_CODE)
            expecting_operand = False

        elif token_kind == "lpar":
            if not expecting_operand:
                raise CodeError(INVALID_CODE)       # 3 (4)
            open_parenthesis_count += 1

        elif token_kind == "rpar":
            if expecting_operand or open_parenthesis_count == 0:
                raise CodeError(INVALID_CODE)       # (3 +)  or  3)
            open_parenthesis_count -= 1

        else:                                       # operator
            if token_value in UNARY_OPERATORS:
                if not expecting_operand:
                    raise CodeError(INVALID_CODE)   # 3 -u 4 cannot happen
            else:
                if expecting_operand:
                    raise CodeError(INVALID_CODE)   # 3 * * 4
                expecting_operand = True

    if expecting_operand or open_parenthesis_count != 0:
        raise CodeError(INVALID_CODE)               # 3 +   or   (3 + 4


# --------------------------------------------------------------------------
# Parsing an input code
# --------------------------------------------------------------------------

def parse_code(line):
    """Split one input code into (target_variable, expression_text).

    target_variable is the variable name for an assignment statement, or None
    when the code is a plain expression.  Raises CodeError when the code
    cannot be one of the two forms.
    """
    code = line.strip()

    if not code:
        raise CodeError(INVALID_CODE)

    # An '=' makes the code an assignment statement.  Only one is allowed, so
    # a comparison such as '==' is rejected here.
    if "=" in code:
        if code.count("=") > 1:
            raise CodeError(INVALID_CODE)

        equals_position = code.index("=")
        target_variable = code[:equals_position].strip()
        expression_text = code[equals_position + 1:].strip()

        if not is_valid_name(target_variable):
            raise CodeError(INVALID_CODE)
        if not expression_text:
            raise CodeError(INVALID_CODE)

        return target_variable, expression_text

    return None, code


# --------------------------------------------------------------------------
# Infix to postfix (shunting yard)
# --------------------------------------------------------------------------

def to_postfix(infix_tokens):
    """Convert validated infix tokens into a list of postfix tokens."""
    postfix_tokens = []
    operator_stack = []

    for token in infix_tokens:
        token_kind, token_value = token

        if token_kind in ("num", "var"):
            postfix_tokens.append(token)

        elif token_kind == "lpar":
            operator_stack.append(token)

        elif token_kind == "rpar":
            # Everything up to the matching '(' belongs to the output first.
            while operator_stack and operator_stack[-1][0] != "lpar":
                postfix_tokens.append(operator_stack.pop())
            operator_stack.pop()                    # discard the '('

        else:                                       # operator
            while operator_stack and operator_stack[-1][0] == "op":
                stacked_operator = operator_stack[-1][1]
                binds_tighter = (precedence(stacked_operator)
                                 > precedence(token_value))
                same_level_and_left_associative = (
                    precedence(stacked_operator) == precedence(token_value)
                    and not is_right_associative(token_value)
                )
                if binds_tighter or same_level_and_left_associative:
                    postfix_tokens.append(operator_stack.pop())
                else:
                    break
            operator_stack.append(token)

    while operator_stack:
        postfix_tokens.append(operator_stack.pop())

    return postfix_tokens


# --------------------------------------------------------------------------
# Postfix evaluation
# --------------------------------------------------------------------------

def integer_divide(dividend, divisor):
    """C-style integer division: the result is truncated toward zero."""
    quotient = abs(dividend) // abs(divisor)
    if (dividend < 0) != (divisor < 0):
        quotient = -quotient
    return quotient


def integer_modulo(dividend, divisor):
    """C-style remainder: it takes the sign of the dividend."""
    return dividend - integer_divide(dividend, divisor) * divisor


def apply_operator(operator, left_operand, right_operand):
    """Combine two operands with a binary operator."""
    if operator == "+":
        return left_operand + right_operand
    if operator == "-":
        return left_operand - right_operand
    if operator == "*":
        return left_operand * right_operand

    both_are_integers = (isinstance(left_operand, int)
                         and isinstance(right_operand, int))

    if operator == "/":
        if right_operand == 0:
            raise CodeError(DIVISION_BY_ZERO)
        if both_are_integers:
            return integer_divide(left_operand, right_operand)
        return left_operand / right_operand

    if operator == "%":
        if right_operand == 0:
            raise CodeError(DIVISION_BY_ZERO)
        if both_are_integers:
            return integer_modulo(left_operand, right_operand)
        raise CodeError(INVALID_CODE)               # % needs whole numbers

    raise CodeError(INVALID_CODE)


def evaluate_postfix(postfix_tokens, variable_values):
    """Evaluate postfix tokens and return the resulting value.

    variable_values maps a name to its most recently assigned value.

    validate() has already rejected malformed expressions, so the stack should
    always hold enough operands.  The checks below are there so that a gap in
    the validation shows up as a reported error instead of a crash.
    """
    operand_stack = []

    for token_kind, token_value in postfix_tokens:
        if token_kind == "num":
            operand_stack.append(token_value)

        elif token_kind == "var":
            if token_value not in variable_values:
                raise CodeError(undefined_variable(token_value))
            operand_stack.append(variable_values[token_value])

        elif token_value in UNARY_OPERATORS:
            if len(operand_stack) < 1:
                raise CodeError(INVALID_CODE)
            operand = operand_stack.pop()
            operand_stack.append(-operand if token_value == "u-" else operand)

        else:                                       # binary operator
            if len(operand_stack) < 2:
                raise CodeError(INVALID_CODE)
            right_operand = operand_stack.pop()
            left_operand = operand_stack.pop()
            operand_stack.append(
                apply_operator(token_value, left_operand, right_operand))

    # Exactly one value must be left: no operand went unused.
    if len(operand_stack) != 1:
        raise CodeError(INVALID_CODE)

    return operand_stack.pop()


# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------

def format_value(value):
    """Show whole numbers without a decimal part, others with one."""
    if isinstance(value, int):
        return str(value)
    if not math.isfinite(value):
        return "%g" % value             # inf / nan: int() would fail on these
    if value == int(value):
        return str(int(value))
    return "%g" % value


def format_postfix(postfix_tokens):
    """Render postfix tokens as a space-separated string."""
    rendered_tokens = []

    for token_kind, token_value in postfix_tokens:
        if token_kind == "num":
            rendered_tokens.append(format_value(token_value))
        elif token_value in UNARY_OPERATORS:
            # -u / +u, so a sign reads apart from the binary operator
            rendered_tokens.append(token_value[1] + "u")
        else:
            rendered_tokens.append(str(token_value))

    return " ".join(rendered_tokens)


# --------------------------------------------------------------------------
# Processing one code
# --------------------------------------------------------------------------

def process_code(line, variable_values, variables_used):
    """Process one input code and return (postfix_text, result_text).

    variable_values : name -> current value, updated in place by an assignment
    variables_used  : the variable names in the order they were first seen,
                      updated in place

    Both returned pieces are ready to be printed.  An error is raised so the
    caller can both show it as the result and list it at the end; the postfix
    form travels with the error whenever it is already known.
    """
    target_variable, expression_text = parse_code(line)

    infix_tokens = tokenize(expression_text)
    validate(infix_tokens)
    postfix_tokens = to_postfix(infix_tokens)
    postfix_text = format_postfix(postfix_tokens)

    # A variable is "used" whether it is read or assigned.
    for token_kind, token_value in postfix_tokens:
        if token_kind == "var" and token_value not in variables_used:
            variables_used.append(token_value)
    if target_variable is not None and target_variable not in variables_used:
        variables_used.append(target_variable)

    try:
        result_value = evaluate_postfix(postfix_tokens, variable_values)
    except CodeError as error:
        # Division by zero in a statement leaves the target variable alone,
        # so its previous value is kept simply by not assigning here.
        raise CodeError(error.args[0], postfix_text)

    if target_variable is None:
        return postfix_text, format_value(result_value)

    variable_values[target_variable] = result_value
    return postfix_text, target_variable + " = " + format_value(result_value)


# --------------------------------------------------------------------------
# Entry point used by the GUI
# --------------------------------------------------------------------------

SEPARATOR = "-------------------------------------------"


def run(lines):
    """Process every input code and build the complete output text.

    This function is the whole contract with the GUI, so it does not raise:
    a code that cannot be processed becomes an error in the output and the
    remaining codes are still processed.
    """
    variable_values = {}    # name -> most recently assigned value
    variables_used = []     # variable names, in order of first appearance
    errors_found = []       # one message per error found
    output_lines = []

    for line_number, line in enumerate(lines or [], start=1):
        if not line.strip():
            continue                                # blank lines carry no code

        try:
            postfix_text, result_text = process_code(
                line, variable_values, variables_used)
        except CodeError as error:
            error_message = error.args[0]
            # The postfix form is known unless the code failed before that.
            postfix_text = error.args[1] if len(error.args) > 1 else "-"
            result_text = error_message
            errors_found.append("Line %d: %s" % (line_number, error_message))
        except Exception as unexpected:
            # A fault in this module must not lose the rest of the output.
            # The type name is kept so the cause can still be tracked down.
            postfix_text = "-"
            result_text = INVALID_CODE
            errors_found.append("Line %d: %s (%s)" % (
                line_number, INVALID_CODE, type(unexpected).__name__))

        output_lines.append("Line: " + line.strip())
        output_lines.append("Postfix: " + postfix_text)
        output_lines.append("Result: " + result_text)
        output_lines.append("")

    output_lines.append(SEPARATOR)
    output_lines.append("Variables used:")
    if variables_used:
        for variable_name in variables_used:
            if variable_name in variable_values:
                output_lines.append(
                    variable_name + " = "
                    + format_value(variable_values[variable_name]))
            else:
                output_lines.append(variable_name + " = undefined")
    else:
        output_lines.append("(none)")

    output_lines.append("")
    output_lines.append(SEPARATOR)
    output_lines.append("Errors found:")
    if errors_found:
        output_lines.extend(errors_found)
    else:
        output_lines.append("(none)")

    return "\n".join(output_lines)
