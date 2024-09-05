#!/usr/bin/env sh
#
# Removes docs, fonts, localization configurations, and other
#   non-essential files.
set -eu

output_file="$(mktemp)"

find \
    "/etc/multipath" \
    "/etc/pollinate" \
    "/etc/rsyslog.d" \
    "/usr/share/alsa" \
    "/usr/share/applications" \
    "/usr/share/awk" \
    "/usr/share/bug" \
    "/usr/share/common-licenses" \
    "/usr/share/doc-base" \
    "/usr/share/emacs" \
    "/usr/share/fonts" \
    "/usr/share/gitweb" \
    "/usr/share/icons" \
    "/usr/share/info" \
    "/usr/share/java" \
    "/usr/share/locale" \
    "/usr/share/man" \
    "/usr/share/pixmaps" \
    "/usr/share/sounds" \
    "/usr/share/zsh" \
    -type l -o \
    -type f \
    -print \
    -delete \
    >>"${output_file}"

find \
    "/usr/share/doc" \
    -type d \
    -print \
    -delete \
    >>"${output_file}"

if [ -r "/usr/share/i18n" ]; then
    find \
        "/usr/share/i18n" \
        -iname "en_US" -prune -o \
        -type f \
        -print \
        -exec rm -f -- '{}' \; \
        >>"${output_file}"
fi

if [ -r "/usr/share/zoneinfo" ]; then
    find \
        "/usr/share/zoneinfo" \
        \( \
        -ipath "*antarc*" -o \
        -ipath "*asia*" -o \
        -ipath "*atlan*" -o \
        -ipath "*aust*" -o \
        -ipath "*eur*" \
        \) \
        \( \
        -type f -o \
        -type l \
        \) \
        -print \
        -delete \
        >>"${output_file}"
fi

# Help Ansible determine if the task changed anything.
if [ -n "$(cat "${output_file}")" ]; then
    printf "%s\n" "RESULT-changed"
else
    printf "%s\n" "RESULT-ok"
fi
rm -f -- "${output_file}"
exit 0
