#!/bin/bash

cat <<EOF > inventory.ini
[storage_server]
$ANSIBLE_HOST ansible_ssh_user=$ANSIBLE_SSH_USER ansible_ssh_private_key_file=$ANSIBLE_SSH_PRIVATE_KEY_FILE
EOF