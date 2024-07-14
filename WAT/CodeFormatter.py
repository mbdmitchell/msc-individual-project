def format_code(code: str) -> str:

    def bracket_count_difference(line: str):
        """Return the number of `(` minus the number of `)`, ignoring all characters after ';;'."""
        # Ignore characters after ';;' (comments)
        comment_index = line.find(';;')
        if comment_index != -1:
            line = line[:comment_index]
        return line.count('(') - line.count(')')

    special_lines = [";; setup", ";; control flow code"]

    lines = code.split('\n')
    formatted_lines = []
    current_indent = 0

    for line in lines:
        stripped_line = line.lstrip()

        # Skip blank lines
        if not stripped_line:
            continue

        just_closed_bracket: bool = stripped_line[0] == ')'

        # Temp adjust indentation
        if just_closed_bracket:
            current_indent -= 1

        indented_line = '\t' * current_indent + stripped_line
        indented_line = indented_line.rstrip(' \t')

        if stripped_line in special_lines:
            indented_line = '\n' + indented_line

        formatted_lines.append(indented_line)

        # Update the current indentation level
        current_indent += bracket_count_difference(stripped_line)

        # Readjust indentation
        if just_closed_bracket:
            current_indent += 1

    return '\n'.join(formatted_lines)
