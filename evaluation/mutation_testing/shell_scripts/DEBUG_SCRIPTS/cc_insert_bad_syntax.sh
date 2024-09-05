#!/bin/zsh

# Used so that I can check if a file is being included in the build (as it'll throw an error)

if [ -z "$1" ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "File not found!"
  exit 1
fi

# Add "BAD_SYNTAX" to the end of 70th line of the file
sed -i '' '70s/$/BAD_SYNTAX/' "$1"


echo "File '$1' has been modified with 'BAD_SYNTAX' at the end of each line."