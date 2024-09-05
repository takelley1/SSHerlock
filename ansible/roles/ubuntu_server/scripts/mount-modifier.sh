#!/usr/bin/env sh
#
# Adds "noatime" to all fstab mounts.

output_file="$(mktemp)"
result_file="$(mktemp)"

awk -v result_file="${result_file}" \
    '
    # The following conditions must be met for awk to modify the line:
    #   - The line must not be commented or empty
    #   - The mountpoint must not be none
    #   - The filesystem must not be swap or a FAT variant
    #   - The mount options must not already contain "noatime"
    {
        if ($0 !~ /[[:space:]]*#|^[[:space:]]*$/ && $2 !~ /none/ && $3 !~ /swap|fat/ && $4 !~ /noatime/)
            {
            print $1, $2, $3, $4",noatime", $5, $6
            print "1" > result_file
            }
        else
            print $0

    }' "/etc/fstab" > "${output_file}"

# Record file's original permissions.
mode="$(stat --format=%a "/etc/fstab")"
owner="$(stat --format=%U "/etc/fstab")"
group="$(stat --format=%G "/etc/fstab")"

mv -f -- "${output_file}" "/etc/fstab"

# Restore file permissions.
chmod "${mode}" "/etc/fstab"
chown "${owner}:${group}" "/etc/fstab"

# Help Ansible determine if the task changed anything.
if grep -q "1" "${result_file}" 2>/dev/null; then
    printf "%s\n" "RESULT-changed"
else
    printf "%s\n" "RESULT-ok"
fi
rm -f -- "${result_file}"
exit 0
