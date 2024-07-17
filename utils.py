def format_code(code: str, add_line_above=None, deliminators=('{', '}'), comment_marker=';;', ) -> str:
    if add_line_above is None:
        padded_lines = []

    open_delim = deliminators[0]
    closed_delim = deliminators[1]

    def bracket_count_difference(line: str):
        """Return the number of `(` minus the number of `)`, ignoring all characters after ';;'."""
        # Ignore characters after comment_marker
        comment_index = line.find(comment_marker)
        if comment_index != -1:
            line = line[:comment_index]
        return line.count(open_delim) - line.count(closed_delim)

    lines = code.split('\n')
    formatted_lines = []
    current_indent = 0

    for line in lines:
        stripped_line = line.lstrip()

        # Skip blank lines
        if not stripped_line:
            continue

        just_closed_bracket: bool = stripped_line[0] == closed_delim

        # Temp adjust indentation
        if just_closed_bracket:
            current_indent -= 1

        indented_line = '\t' * current_indent + stripped_line
        indented_line = indented_line.rstrip(' \t')

        if any(stripped_line.startswith(prefix) for prefix in add_line_above):
            indented_line = '\n' + indented_line


        formatted_lines.append(indented_line)

        # Update the current indentation level
        current_indent += bracket_count_difference(stripped_line)

        # Readjust indentation
        if just_closed_bracket:
            current_indent += 1

    return '\n'.join(formatted_lines)
