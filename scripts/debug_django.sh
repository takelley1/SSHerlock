#!/usr/bin/env bash
# Open a Django debug shell for the SSHerlock project.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

main() {
  ssherlock::setup_environment

  if [[ ! -f "ssherlock/manage.py" ]]; then
    printf "%s\n" "Error: ssherlock/manage.py not found in repo root." >&2
    exit 1
  fi

  # Create a temporary Python startup script that sets up Django and pre-imports models.
  startup_py="$(mktemp -t ssherlock_django_startup_XXXX.py)"
  trap 'rm -f "${startup_py}"' EXIT

  cat >"${startup_py}" <<'PY'
import os
import sys

# Ensure Python can import the inner Django project package when run from repo root.
project_pkg_dir = os.path.join(os.getcwd(), "ssherlock")
if project_pkg_dir not in sys.path:
    sys.path.insert(0, project_pkg_dir)

# Ensure Django settings are configured and app registry is ready.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssherlock.settings")

try:
    import django  # noqa
    django.setup()
except Exception as exc:  # pylint: disable=broad-except
    print(f"Failed to set up Django: {exc}", file=sys.stderr)
    raise

# Pre-import commonly used models and utilities for convenience.
from django.contrib.auth.models import User  # noqa: E402
from django.utils import timezone  # noqa: E402
from django.conf import settings as dj_settings  # noqa: E402
from django.db import transaction  # noqa: E402
from django.db.models import Q, F, Count, Sum, Max, Min  # noqa: E402
from django.urls import reverse  # noqa: E402

import ssherlock_server.models as m  # noqa: E402
from ssherlock_server.models import (  # noqa: E402
    BastionHost,
    Credential,
    Job,
    LlmApi,
    TargetHost,
)
from ssherlock_server.utils import get_object_pretty_name  # noqa: E402

banner = (
    "Django shell with pre-imports:\n"
    " - User, timezone, dj_settings, transaction, Q/F/Count/Sum/Max/Min, reverse\n"
    " - ssherlock_server.models as m, BastionHost, Credential, Job, LlmApi, TargetHost\n"
    "Examples:\n"
    "  User.objects.count()\n"
    "  Job.objects.filter(status='Pending')\n"
    "  m.Job.objects.select_related('llm_api').last()\n"
)
print(banner)
PY

  # Launch an interactive Python session, keeping the TTY attached.
  python -i "${startup_py}"
}

main "$@"
