#!/usr/bin/env bash

# Cat together the relevant code files from this repo so we can feed it all to ChatGPT.


files="$(git ls-files | grep -Ev ".*\.css|__init__|^conf\/|^\.git.*|.*\.(md|sh|txt)|(settings|asgi|wsgi|urls|manage)\.py|\/tests\/|runner")"

for i in ${files}; do
    printf "%s\n\n" "BELOW IS A NEW FILE. ITS PATH IS ${i}"
    cat "${i}"
    printf "%s\n\n" "END OF FILE"
done
