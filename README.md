# Data Engineering 2 Project

## Start and Contextualize Dev and Prod VMs
Load OpenStack credentials. You will need your Swedish Science Cloud username and API password for this step:
```
source infra/openstack/openrc.sh
```

Next, start the VMs with:
```
python3 infra/openstack/start_instances.py
```

You can ssh into them with:
```
ssh -i /home/ubuntu/cluster-keys/cluster-key appuser@<dev/prod private IP>
```

Contextualize using ansible with:
```
ansible-playbook configuration.yml --private-key=/home/ubuntu/cluster-keys/cluster-key
```

## GitHub Actions Runner

Register a self-hosted runner. Get a fresh token from https://github.com/RobinMatter6/de2-project/settings/actions/runners/new:

```
./infra/actions_runner/setup-runner.sh <REGISTRATION_TOKEN>
```

To remove the runner, get the token by clicking remove runner at https://github.com/RobinMatter6/de2-project/settings/actions/runners:

```
./infra/actions_runner/teardown-runner.sh <REMOVAL_TOKEN>
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