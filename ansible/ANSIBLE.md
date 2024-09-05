# Ansible

## Running Ansible

The first time you run a playbook,
the following must be used:

ansible-playbook \
  pb-foo.yml \
  -kK \
  -e "user=akelley"

- Before running Ansible:
  ```
  apt install openssh sudo ansible -y
  echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
  systemctl start sshd
  ```
