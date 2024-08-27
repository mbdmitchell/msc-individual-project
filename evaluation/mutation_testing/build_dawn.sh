# ./build_dawn.sh repo-name

# Check if the repo-name argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <repo-name>"
  exit 1
fi

repo_name=$1

git clone https://dawn.googlesource.com/dawn "$repo_name" && cd "$repo_name" || exit 1
cp scripts/standalone-with-node.gclient .gclient  # Copy the gclient configuration
gclient sync  # Synchronize dependencies
mkdir -p out/Debug && cd out/Debug || exit 1  # Create build directory and move into it
cmake ../.. -GNinja -DDAWN_BUILD_NODE_BINDINGS=1