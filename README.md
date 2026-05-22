# Data Engineering 2 Project

## Start and Contextualize Dev and Prod VMs
Load OpenStack credentials. You will need your Swedish Science Cloud username and API password for this step:
```
source UPPMAX\ 2026_1-24-openrc
```

Next, start the VMs with:
```
python3 openstack-client/single_node_with_docker_ansible_client/start_instances.py
```

You can ssh into them with:
```
ssh -i /home/ubuntu/cluster-keys/cluster-key appuser@<dev/prod private IP>
```

Contextualize using ansible with:
```
ansible-playbook configuration.yml --private-key=/home/ubuntu/cluster-keys/cluster-key
```

## Git Hook

To activate the pre commit hook that scans staged changes for accidentally committed secrets. run once:

```
pip install pre-commit detect-secrets
pre-commit install
```

To re-scan the whole repo manually:

```
pre-commit run --all-files
```