import os
import sys
import time
import json
import re
import paramiko
import configparser

class SSH_CONNECT():
    def __init__(self, cfg):
        self._cfg = cfg

    def exec_host_cmd(self, content, debug=False):
        result = ""
        for x in range(5):
            print("SSH Connect IP %s ..." % self._cfg['mgmt_ip'])
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self._cfg['mgmt_ip'], 22, username=self._cfg['username'], password=self._cfg['password'], timeout=5)
                stdin, stdout, stderr = client.exec_command(content)
                result = stdout.read()
                client.close()
                break
            except Exception as err:
                print(err)
                print("Connect IP %s ...fail, Wait 30 seconds and reconnect" % self._cfg['mgmt_ip'])
                time.sleep(30)

        if debug == True: print(result)
        return result

    def ping(self, ip, count=15, debug=False):
        expected_str = '64 bytes from ' + ip

        result_ping = self.exec_host_cmd('ping -c {} {}'.format(count, ip), debug)
        if(expected_str in result_ping.decode()):
            return 'success'
        else:
            return 'failure'

    def run_cmd(self, cmd, debug=False):
        run_result = self.exec_host_cmd(cmd, debug)
        return run_result

def show_step(step, msg, sieve_len=40):
    str_len = (len(msg) + len( "Step"+str(step)+":"))/2
    both_len = sieve_len-int(str_len)
    if both_len < 0:
        left_right = int(str_len)
    else:
        left_right = int(str_len)*2+(int(both_len)*2)
    print()
    print("="*left_right)
    print("%s" % "="*both_len+"Step"+str(step)+":"+msg+"="*both_len)
    print("="*left_right)

def show_msg(msg, sieve_len=40):
    str_len = len(msg)/2
    both_len = sieve_len-int(str_len)
    if both_len < 0:
        left_right = int(str_len)
    else:
        left_right = int(str_len)*2+(int(both_len)*2)
    print()
    print("-"*left_right)
    print("%s" % "-"*both_len+msg+"-"*both_len)
    print("-"*left_right)

config = configparser.ConfigParser()
config.read('vm_config.ini')
vm_cpu = int(config['vm']['cpu'])
vm_ram = int(config['vm']['ram'])
vm_system_disk_size = int(config['vm']['system_disk_size'])
vm_temp_name = config['vm']['template_name']
vm_host_name = config['vm']['host_name']
vm_namespace = config['vm']['namespace']
vm_data_disk_name = config['vm']['data_disk_name']
vm_data_disk_size = int(config['vm']['data_disk_size'])
create_host_num = int(config['host_num']['num'])

if len(sys.argv) < 3:
    print('no argument')
    sys.exit()

user_pw=sys.argv[1]
host_ip = sys.argv[2]
print("user:pw= "+user_pw)
print("Host IP: " +host_ip)

vm_name_list = []
show_step(1, "Get all virtual machine")
url="/kapis/virtualization.ecpaas.io/v1/virtualmachines"
cmd1 = 'curl -X GET -u '+user_pw+' '+host_ip+':30880'+url
print(cmd1)
result = os.popen(cmd1).read()
#print("result= %s" % result)
result = json.loads(result)
result_list = result["items"]
if result["items"] == None:
    print("Not found any body.. ")
else:
    print("File Length: "+ str(len(result_list)))
    for j in range(0, len(result_list)):
        vm_name_list.append(result_list[j]["id"])
show_msg(", ".join(vm_name_list))


show_step(2, "Remove virtual machine")
for i in range(0, len(vm_name_list)):
    url="/kapis/virtualization.ecpaas.io/v1/namespaces/%s/virtualmachines/%s" % (vm_namespace, vm_name_list[i])
    cmd1 = 'curl -X DELETE -u '+user_pw+' '+host_ip+':30880'+url
    print(cmd1)
    result = os.popen(cmd1).read()
    print("result= %s" % result)
    time.sleep (5)

show_step(3, "Get all template image")
url="/kapis/virtualization.ecpaas.io/v1/images"
cmd1 = 'curl -X GET -u '+user_pw+' '+host_ip+':30880'+url
print(cmd1)
result = os.popen(cmd1).read()
#print("result= %s" % result)
result = json.loads(result)
result_list = result["items"]
vm_name_list = []
if result["items"] == None:
    print("Not found any body.. ")
else:
    print("File Length: "+ str(len(result_list)))
    for j in range(0, len(result_list)):
        vm_name_list.append(result_list[j]["id"])
show_msg(", ".join(vm_name_list))

show_step(4, "Remove template image")
for i in range(0, len(vm_name_list)):
    url="/kapis/virtualization.ecpaas.io/v1/namespaces/%s/images/%s"  % (vm_namespace, vm_name_list[i])
    cmd1 = 'curl -X DELETE -u '+user_pw+' '+host_ip+':30880'+url
    print(cmd1)
    result = os.popen(cmd1).read()
    print("result= %s" % result)
    time.sleep (5)


show_step(5, "Get all PVC disk")
url="/kapis/virtualization.ecpaas.io/v1/disks"
cmd1 = 'curl -X GET -u '+user_pw+' '+host_ip+':30880'+url
print(cmd1)
result = os.popen(cmd1).read()
#print("result= %s" % result)
result = json.loads(result)
result_list = result["items"]
vm_name_list = []
if result["items"] == None:
    print("Not found any body.. ")
else:
    print("File Length: "+ str(len(result_list)))
    for j in range(0, len(result_list)):
        vm_name_list.append(result_list[j]["id"])
show_msg(", ".join(vm_name_list))

show_step(6, "Remove all PVC disk")
for i in range(0, len(vm_name_list)):
    url="/kapis/virtualization.ecpaas.io/v1/namespaces/%s/disks/%s" % (vm_namespace, vm_name_list[i])
    cmd1 = 'curl -X DELETE -u '+user_pw+' '+host_ip+':30880'+url
    print(cmd1)
    result = os.popen(cmd1).read()
    print("result= %s" % result)
    time.sleep (5)


show_step(7, "Get all images file")
url="/kapis/virtualization.ecpaas.io/v1alpha1/minio/images"
cmd1 = 'curl -X GET -u '+user_pw+' '+host_ip+':30880'+url
print(cmd1)
result = os.popen(cmd1).read()
#print("result= %s" % result)
result = json.loads(result)
result_list = result["items"]
vm_name_list = []
if result["items"] == None:
    print("Not found any body.. ")
else:
    print("File Length: "+ str(len(result_list)))
    for j in range(0, len(result_list)):
        vm_name_list.append(result_list[j]["name"])
show_msg(", ".join(vm_name_list))

show_step(8, "Remove all images disk")
for i in range(0, len(vm_name_list)):
    url="/kapis/virtualization.ecpaas.io/v1alpha1/minio/image/"+vm_name_list[i]
    cmd1 = 'curl -X DELETE -u '+user_pw+' '+host_ip+':30880'+url
    print(cmd1)
    result = os.popen(cmd1).read()
    print("result= %s" % result)
    time.sleep (5)


if vm_namespace != "default":
    show_step(9, "Remove namespace %s" % vm_namespace)
    cmd1 = "kubectl delete namespace %s" % vm_namespace
    result = os.popen(cmd1).read()
    print("result= %s" % result)

