#!/usr/bin/env sh
#
# Comments out all the uncommented "alias" lines in the provided file(s).
#
# Usage: ./unaliaser.sh <PATH-GLOB1> <PATH-GLOB2> ...
set -eu

output_file="$(mktemp)"
result_file="$(mktemp)"
IFS="$(printf '\n')"

# Loop through every relevant file in the given directories.
find "${@}" -type f | while read -r file; do

    # If the first non-whitespace string in the current line is "alias",
    #   comment it out. Also, print a "1" to the result_file, indicating
    #   that this script has made a change. This is used by Ansible.
    # Otherwise, print the line without modification.
    awk -v result_file="${result_file}" \
        '{
            if ($0 ~ /^[[:space:]]*alias/)
                {
                print "1" > result_file
                print "#",$0
                }
            else
                print $0
        }' "${file}" >"${output_file}"

    # Record file's original permissions.
    mode="$(stat --format=%a "${file}")"
    owner="$(stat --format=%U "${file}")"
    group="$(stat --format=%G "${file}")"

    mv -f -- "${output_file}" "${file}"

    # Restore file permissions.
    chmod "${mode}" "${file}"
    chown "${owner}:${group}" "${file}"

done

# Help Ansible determine if the task changed anything.
if grep -q "1" "${result_file}" 2>/dev/null; then
    printf "%s\n" "RESULT-changed"
else
    printf "%s\n" "RESULT-ok"
fi
rm -f -- "${result_file}"
exit 0
