"""
PE00 - Expression Evaluation
Evaluation module.

TEMPORARY STUB - replace with the real implementation from your groupmates.

The GUI calls exactly one function:

    run(lines: list[str]) -> str

    lines  : the input area's contents, already split into individual lines
    return : the complete output text, formatted and ready to display

Agree on this signature with your group before anyone writes the real version.
"""


def run(lines):
    out = []

    for line in lines:
        out.append(f"Line: {line}")
        out.append("Postfix: <pending>")
        out.append("Result: <pending>")
        out.append("")

    out.append("-------------------------------------------")
    out.append("Variables used:")
    out.append("<pending>")
    out.append("-------------------------------------------")
    out.append("Errors found:")
    out.append("<pending>")

    return "\n".join(out)
