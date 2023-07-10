# coding=UTF-8
# vim: tw=80
"""Generic logging template."""
import logging
import os

log = logging.getLogger()
console = logging.StreamHandler()

FORMAT_STR = "%(asctime)s\t[%(levelname)s] -- %(message)s"

console.setFormatter(logging.Formatter(FORMAT_STR))
# Prints logs to console
log.addHandler(console)
# Log INFO and above by default
if "LOG_LEVEL" in os.environ:
    log_level = os.getenv("LOG_LEVEL")
    if log_level is not None:
        log_level = log_level.upper()
    if log_level == "DEBUG":
        log.setLevel(logging.DEBUG)
    elif log_level == "INFO":
        log.setLevel(logging.INFO)
    elif log_level == "WARN":
        log.setLevel(logging.WARN)
    elif log_level == "CRITICAL":
        log.setLevel(logging.CRITICAL)
    else:
        print(f"Log level {log_level} not recognized, defaulting to INFO...")
else:
    log.setLevel(logging.INFO)
