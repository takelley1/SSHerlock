#!/usr/bin/env bash
#
# Invoked during CI to prepare the repository for deployment to the application
# server with Ansible.
set -euo pipefail

# Ensure we start at the root of the git repo.
cd "$(git rev-parse --show-toplevel)" || exit 1

# Generate a long random key for SECRET_KEY.
SECRET_KEY=$(openssl rand -base64 64)

# Update settings.py with deployment configurations.
sed -E -i 's/DEBUG = [tT]rue/DEBUG = False/g' "ssherlock/ssherlock/settings.py"
sed -E -i 's/HTML_MINIFY = False/HTML_MINIFY = True/g' "ssherlock/ssherlock/settings.py"
sed -E -i "s/SECRET_KEY = .+/SECRET_KEY = '${SECRET_KEY}'/g" "ssherlock/ssherlock/settings.py"
sed -E -i 's/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ["yourdomain.com", "127.0.0.1", ".localhost"]/g' "ssherlock/ssherlock/settings.py"

# Ensure secure settings for production.
cat <<EOL >> "ssherlock/ssherlock/settings.py"

# Security settings for production
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
EOL

# Run final check.
python "./ssherlock_server/manage.py" check --deploy

# Copy application directory into a place Ansible can find it.
cp -rav "ssherlock" "ansible/roles/ssherlock/files/"
# Copy other miscellaneous files that are necessary.
cp -rav "requirements.txt" "ansible/roles/ssherlock/files/"

# Run Ansible to finally deploy the server.
cd ansible || exit 1
ansible-playbook pb-deploy-ssherlock.yml
