#!/bin/bash

mkdir -p temp
mkdir -p build
mkdir -p ori
if [ ! -e ./ori/the_large_dict ]; then
  git clone "https://github.com/okxhfiweohi/the_large_dict.git" ./ori/the_large_dict
fi
cd ./ori/the_large_dict
if command -v pnpm &>/dev/null; then
  pnpm install
  pnpm run build
else
  npm install
  npm run build
fi
cd ../..
cp -v ./ori/the_large_dict/dist/* build/
