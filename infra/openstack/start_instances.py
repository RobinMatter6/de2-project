# http://docs.openstack.org/developer/python-novaclient/ref/v2/servers.html
import time, os, sys, random, re
from os import environ as env

from  novaclient import client
import keystoneclient.v3.client as ksclient
from keystoneauth1 import loading
from keystoneauth1 import session


flavor = "ssc.medium" 
private_net = "UPPMAX 2026/1-24 Internal IPv4 Network"
floating_ip_pool_name = None
floating_ip = None
image_name = "Ubuntu 22.04 - 2023.01.07"

identifier = random.randint(1000,9999)

loader = loading.get_plugin_loader('password')

auth = loader.load_from_options(auth_url=env['OS_AUTH_URL'],
                                username=env['OS_USERNAME'],
                                password=env['OS_PASSWORD'],
                                project_name=env['OS_PROJECT_NAME'],
                                project_domain_id=env['OS_PROJECT_DOMAIN_ID'],
                                #project_id=env['OS_PROJECT_ID'],
                                user_domain_name=env['OS_USER_DOMAIN_NAME'])

sess = session.Session(auth=auth)
nova = client.Client('2.1', session=sess)
print ("user authorization completed.")

image = nova.glance.find_image(image_name)

flavor = nova.flavors.find(name=flavor)

if private_net != None:
    net = nova.neutron.find_network(private_net)
    nics = [{'net-id': net.id}]
else:
    sys.exit("private-net not defined.")

cfg_file_path =  os.getcwd()+'/prod-cloud-cfg.txt'
if os.path.isfile(cfg_file_path):
    userdata_prod = open(cfg_file_path)
else:
    sys.exit("prod-cloud-cfg.txt is not in current working directory")

cfg_file_path =  os.getcwd()+'/dev-cloud-cfg.txt'
if os.path.isfile(cfg_file_path):
    userdata_dev = open(cfg_file_path)
else:
    sys.exit("dev-cloud-cfg.txt is not in current working directory")

# Workers reuse the same base cloud config as the dev server
cfg_file_path = os.getcwd()+'/dev-cloud-cfg.txt'
userdata_worker1 = open(cfg_file_path)
userdata_worker2 = open(cfg_file_path)

secgroups = ['default']

def get_ip(instance):
    for network in instance.networks[private_net]:
        if re.match(r'\d+\.\d+\.\d+\.\d+', network):
            return network
    raise RuntimeError(f'No IP address assigned to {instance.name}!')

# Find any already-running group6 instances
existing = nova.servers.list()
existing_prod  = next((s for s in existing if "group6_prod_server"  in s.name), None)
existing_dev   = next((s for s in existing if "group6_dev_server"   in s.name), None)
existing_w1    = next((s for s in existing if "group6_dev_worker_1" in s.name), None)
existing_w2    = next((s for s in existing if "group6_dev_worker_2" in s.name), None)

# Create only the instances that are missing
new_instances = []
print("Creating missing instances...")

if existing_prod:
    print(f"Skipping prod server — '{existing_prod.name}' already exists.")
    instance_prod = existing_prod
else:
    instance_prod = nova.servers.create(name="group6_prod_server_with_docker_"+str(identifier), image=image, flavor=flavor, key_name=None, userdata=userdata_prod, nics=nics, security_groups=secgroups)
    new_instances.append(instance_prod)

if existing_dev:
    print(f"Skipping dev server — '{existing_dev.name}' already exists.")
    instance_dev = existing_dev
else:
    instance_dev = nova.servers.create(name="group6_dev_server_"+str(identifier), image=image, flavor=flavor, key_name=None, userdata=userdata_dev, nics=nics, security_groups=secgroups)
    new_instances.append(instance_dev)

if existing_w1:
    print(f"Skipping dev worker 1 — '{existing_w1.name}' already exists.")
    instance_worker1 = existing_w1
else:
    instance_worker1 = nova.servers.create(name="group6_dev_worker_1_"+str(identifier), image=image, flavor=flavor, key_name=None, userdata=userdata_worker1, nics=nics, security_groups=secgroups)
    new_instances.append(instance_worker1)

if existing_w2:
    print(f"Skipping dev worker 2 — '{existing_w2.name}' already exists.")
    instance_worker2 = existing_w2
else:
    instance_worker2 = nova.servers.create(name="group6_dev_worker_2_"+str(identifier), image=image, flavor=flavor, key_name=None, userdata=userdata_worker2, nics=nics, security_groups=secgroups)
    new_instances.append(instance_worker2)

# Wait for newly created instances to finish building
if new_instances:
    print("waiting for 10 seconds...")
    time.sleep(10)
    building = list(new_instances)
    while building:
        still_building = []
        for inst in building:
            inst = nova.servers.get(inst.id)
            if inst.status == 'BUILD':
                print(f"Instance: {inst.name} is in BUILD state, sleeping for 5 seconds more...")
                still_building.append(inst)
            else:
                print(f"Instance: {inst.name} is now {inst.status}")
        if still_building:
            time.sleep(5)
        building = still_building

# Refresh all instance objects to get final state and IPs
instance_prod    = nova.servers.get(instance_prod.id)
instance_dev     = nova.servers.get(instance_dev.id)
instance_worker1 = nova.servers.get(instance_worker1.id)
instance_worker2 = nova.servers.get(instance_worker2.id)

ip_address_prod    = get_ip(instance_prod)
ip_address_dev     = get_ip(instance_dev)
ip_address_worker1 = get_ip(instance_worker1)
ip_address_worker2 = get_ip(instance_worker2)

print(f"Instance: {instance_prod.name} is in {instance_prod.status} state, ip address: {ip_address_prod}")
print(f"Instance: {instance_dev.name} is in {instance_dev.status} state, ip address: {ip_address_dev}")
print(f"Instance: {instance_worker1.name} is in {instance_worker1.status} state, ip address: {ip_address_worker1}")
print(f"Instance: {instance_worker2.name} is in {instance_worker2.status} state, ip address: {ip_address_worker2}")

# Automatically generate the Ansible hosts file with the fresh IPs
hosts_content = f"""[prodserver]
prodserver_node ansible_host={ip_address_prod} ansible_user=appuser

[devserver]
devserver_node ansible_host={ip_address_dev} ansible_user=appuser

[devworkers]
devworker1_node ansible_host={ip_address_worker1} ansible_user=appuser
devworker2_node ansible_host={ip_address_worker2} ansible_user=appuser
"""

with open("hosts", "w") as f:
    f.write(hosts_content)

print("Ansible hosts file updated automatically with new IPs!")