# Ansible playbooks for servers installation

The playbook are targeted for Ubuntu family machines: Ubuntu and Mint. They may work or not on Debian OS.

## Install Docker with Support for Nvidia

```shell
ansible-playbook docker-nvidia-container-setup.yaml --ask-become-pass
```

