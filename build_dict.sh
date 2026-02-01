#!/bin/bash

mkdir -p temp
mkdir -p build
mkdir -p ori

if [ ! -e ./ori/dict_data ]; then
  git clone "https://github.com/okxhfiweohi/dict_data.git" ./ori/dict_data
fi
python build_txt.py
echo "The Large Dict" >temp/title.html
mdict -a temp/dict.txt build/the_large_dict.mdx --title temp/title.html --description ./ori/the_large_dict/templates/description.j2
