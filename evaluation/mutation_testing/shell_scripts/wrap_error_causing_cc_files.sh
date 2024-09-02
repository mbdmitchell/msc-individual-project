#!/bin/zsh

if [ -z "$1" ]; then
  echo "Usage: $0 <file_path>"
  exit 1
fi

file_path="$1"

if [ ! -f "$file_path" ] || [[ "$file_path" != *.cc ]]; then
  echo "Error: File does not exist or is not a .cc file."
  exit 1
fi

temp_file=$(mktemp)

echo "#pragma clang diagnostic push" > "$temp_file"
echo "#pragma clang diagnostic ignored \"-Wkeyword-macro\"" >> "$temp_file"
cat "$file_path" >> "$temp_file"
echo "#pragma clang diagnostic pop" >> "$temp_file"

mv "$temp_file" "$file_path"

echo "Pragma directives added to $file_path"