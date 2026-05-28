# The expansion script is based on the modified start_instances.py file.
import time, os, sys, random, re
from os import environ as env
from novaclient import client
import keystoneclient.v3.client as ksclient
from keystoneauth1 import loading
from keystoneauth1 import session

flavor = "ssc.medium" 
private_net = "UPPMAX 2026/1-24 Internal IPv4 Network"
image_name = "Ubuntu 22.04 - 2023.01.07"
identifier = random.randint(1000,9999)

loader = loading.get_plugin_loader('password')
auth = loader.load_from_options(auth_url=env['OS_AUTH_URL'],
                                username=env['OS_USERNAME'],
                                password=env['OS_PASSWORD'],
                                project_name=env['OS_PROJECT_NAME'],
                                project_domain_id=env['OS_PROJECT_DOMAIN_ID'],
                                user_domain_name=env['OS_USER_DOMAIN_NAME'])
sess = session.Session(auth=auth)
nova = client.Client('2.1', session=sess)
print("User authorization completed.")

image = nova.glance.find_image(image_name)
flavor = nova.flavors.find(name=flavor)

if private_net != None:
    net = nova.neutron.find_network(private_net)
    nics = [{'net-id': net.id}]
else:
    sys.exit("private-net not defined.")

cfg_file_path = os.getcwd() + '/dev-cloud-cfg.txt'
if os.path.isfile(cfg_file_path):
    with open(cfg_file_path) as f:
        userdata_dev = f.read()
else:
    sys.exit("dev-cloud-cfg.txt is not in current working directory")    

secgroups = ['default']

new_vms = [f"group6_dev_server_2_{identifier}", f"group6_dev_server_3_{identifier}"]
created_instances = []

print("Creating extra Dev instances for Scalability testing...")
for vm_name in new_vms:
    instance = nova.servers.create(name=vm_name, image=image, flavor=flavor, key_name=None, userdata=userdata_dev, nics=nics, security_groups=secgroups)
    created_instances.append(instance)

print("Waiting for 10 seconds..")
time.sleep(10)

new_ips = []

for instance in created_instances:
    inst_status = instance.status
    while inst_status == 'BUILD':
        print(f"Instance: {instance.name} is in {inst_status} state, sleeping for 5 seconds more...")
        time.sleep(5)
        instance = nova.servers.get(instance.id)
        inst_status = instance.status
    
    ip_address = None
    for network in instance.networks[private_net]:
        if re.match(r'\d+\.\d+\.\d+\.\d+', network):
            ip_address = network
            break
    
    if ip_address:
        new_ips.append((instance.name, ip_address))
        print(f"Success! {instance.name} is ACTIVE at {ip_address}")

if new_ips:
    with open("hosts", "a") as f:
        for i, (name, ip) in enumerate(new_ips):
            node_alias = f"devserver_{i+2}_node"
            f.write(f"{node_alias} ansible_host={ip} ansible_user=appuser\n")
    print("\nAnsible hosts file updated automatically with new Dev IPs")