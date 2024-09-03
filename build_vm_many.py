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

if len(sys.argv) < 4:
    print('no argument')
    sys.exit()

print("user:pw= "+sys.argv[1])
print("Host IP: " +sys.argv[2])
print("upload images: " + sys.argv[3])
user_pw=sys.argv[1]
host_ip = sys.argv[2]
upload_image = sys.argv[3]

vm_name_id = ""
vm_ip = ""


if vm_namespace != "default":
    cmd1 = "kubectl get ns"
    result = os.popen(cmd1).read()
    print("result= %s" % result)
    list_data = ",".join(result.split())
    list_data = list_data.split(",")
    #print(list_data)
    list_data_len = len(list_data)
    if vm_namespace not in list_data:
        cmd1 = "kubectl create namespace %s" % vm_namespace
        result = os.popen(cmd1).read()
        print("result= %s" % result)
        time.sleep(10)

        cmd1 = "kubectl get ns"
        result = os.popen(cmd1).read()
        print("result= %s" % result)
        list_data = ",".join(result.split())
        list_data = list_data.split(",")

    chk_make=0
    for data_loc in range(0, list_data_len):
        if vm_namespace in list_data[data_loc]:
            if "Active" not in list_data[data_loc+1]:
                print("Namespace not active ==> %s" % vm_namespace)
                sys.exit(0)
            else:
                chk_make=1
    if chk_make==0:
        print("Not found namespace %s" % vm_namespace)
        sys.exit(0)


show_step(1, "Check upload "+upload_image+ " file")
cmd1 = 'curl -X GET -u '+user_pw+' '+host_ip+':30880/kapis/virtualization.ecpaas.io/v1alpha1/minio/images'
print(cmd1)
result = os.popen(cmd1).read()
print("result= %s" % result)
result = json.loads(result)
result_list = result["items"]
file_mark=0
if result["items"] == None:
    print("Not found any body.. ")
else:
    print("File Length: "+ str(len(result_list)))
    for j in range(0, len(result_list)):
        if result_list[j]["name"] == upload_image and result_list[j]["size"] != 0:
            file_mark=1
            print("Found that the file already exists")
            break

if file_mark == 0:
    show_step(1.1, "Start upload "+upload_image+ " file")
    upload_file = "uploadfile=@"+upload_image
    url = "/kapis/virtualization.ecpaas.io/v1alpha1/minio/image"
    cmd1 = 'curl -X POST -u '+user_pw+' -H "Content-Type: multipart/form-data" --form "'+upload_file+'" '+host_ip+':30880'+url
    print(cmd1)
    result = os.popen(cmd1).read()
    print("result= %s" % result)

    show_step(1.2, "Check upload file size")
    for i in range(5):
        time.sleep (10)
        cmd1 = 'curl -X GET -u '+user_pw+' '+host_ip+':30880/kapis/virtualization.ecpaas.io/v1alpha1/minio/images'
        print(cmd1)
        result = os.popen(cmd1).read()
        print("result= %s" % result)
        result = json.loads(result)
        result_list = result["items"]
        if result["items"] == None:
            print("Not found any body.. ")
            continue
        print("File Length: "+ str(len(result_list)))
        loop_mark=1
        for j in range(0, len(result_list)):
            if result_list[j]["name"] == upload_image and result_list[j]["size"] != 0:
                loop_mark=0
                break
            else:
                continue
        if loop_mark == 0: break



show_step(2, "create template image with "+upload_image)
data = {
    "cpu_cores": vm_cpu,
    "description": "",
    "memory": vm_ram,
    "minio_image_name": upload_image,
    "name": vm_temp_name,
    "os_family": "ubuntu",
    "shared": False,
    "size": vm_system_disk_size,
    "type": "cloud",
    "version": "20.04_LTS_64bit"
}
url = "/kapis/virtualization.ecpaas.io/v1/namespaces/%s/images" % vm_namespace
cmd1 = 'curl -u '+user_pw+' -H "Content-Type: application/json" -X POST -d \''+json.dumps(data)+'\' '+host_ip+':30880'+url
result = os.popen(cmd1).read()
print("result= %s" % result)
result = json.loads(result)

show_step(2.1, "Check virtual machine status from "+result["id"])
if vm_namespace == "default":
    cmd1 = "kubectl get dv"
else:
    cmd1 = "kubectl get dv -n %s" % vm_namespace
print(cmd1)
for x in range(0, 36):
    time.sleep(20)
    result_vm_status = os.popen(cmd1).read()
    print(result_vm_status)
    if "100.0" in result_vm_status:
        break
    else:
        if x < 34: continue
        print("The virtual machine took too long to create. fail")
        sys.exit(0)



#result = {"id": "image-38031bd5"}
result_temp = {"id": result["id"]}
vm_name_id_list = []
show_step(3, "Create a virtual machine template by "+result_temp["id"])
for x in range(1, create_host_num+1):
    time.sleep(5)
    vm_host_name_id = vm_host_name+str(x)
    show_msg("Ceate VM name is "+str(vm_host_name_id))
    data = {
        "name": vm_host_name_id,
        "description": "",
        "cpu_cores": vm_cpu,
        "memory": vm_ram,
        "disk": [],
        "guest": {
            "username": "root",
            "password": "abc1234"
        },
        "image": {
            "id": result_temp["id"],
            "size": vm_system_disk_size,
            "namespace": vm_namespace
        },
        "namespace": vm_namespace
    }
    url = "/kapis/virtualization.ecpaas.io/v1/namespaces/%s/virtualmachines" % vm_namespace
    cmd1 = 'curl -u '+user_pw+' -H "Content-Type: application/json" -X POST -d \''+json.dumps(data)+'\' '+host_ip+':30880'+url
    result = os.popen(cmd1).read()
    print("result= %s" % result)
    result_dict = json.loads(result)
    vm_name_id_list.append(result_dict["id"])


show_step(4, "Check virtual machine status from list id")
vm_name_id_list_reg = vm_name_id_list.copy()
show_msg(", ".join(vm_name_id_list_reg))
for x in range(0, 25):
    time.sleep(10)
    vm_name_id_list_del = []
    for id in vm_name_id_list_reg:
        if vm_namespace == "default":
            cmd1 = "kubectl get vm " + id
        else:
            cmd1 = "kubectl get vm -n %s %s" % (vm_namespace, id)
        result_vm_status = os.popen(cmd1).read()
        print(result_vm_status)
        if "Running" in result_vm_status:
            vm_name_id_list_del.append(id)
            print("Found running status ... %s" % id)

    for id in vm_name_id_list_del: vm_name_id_list_reg.remove(id)
    if vm_name_id_list_reg == []: break
    if x < 24: continue
    print("The virtual machine took too long to create. fail")
    sys.exit(0)



show_step(5, "Get the virtual machine IP from list id")
vm_name_id_list_reg = vm_name_id_list.copy()
vm_ip_list = []
time.sleep(10)
if vm_namespace == "default":
    cmd1="kubectl get pods -o wide "
else:
    cmd1="kubectl get pods -o wide -n %s" % vm_namespace
result_k8s = os.popen(cmd1).read()
print("result= %s" % result_k8s)
list_data = ",".join(result_k8s.split())
list_data = list_data.split(",")
print(list_data)
list_data_len = len(list_data)
for data_loc in range(0, list_data_len):
    for data_reg in vm_name_id_list_reg:
        if data_reg in list_data[data_loc]:
            #print(list_data[data_loc+5])
            vm_ip_list.append(list_data[data_loc+5])
            vm_name_id_list_reg.remove(data_reg)
            break
    if vm_name_id_list_reg == []: break


#vm_ip="10.233.127.154"
show_step(6, "Test whether the PING of the virtual machine is passed")
show_msg("total list "+", ".join(vm_ip_list))
delay_time = 30
print("The virtual machine has been final start up, please wait for %d seconds." % delay_time)
time.sleep(delay_time)
vm_ip_pass_num = 0
for x in range(0, 10):
    for vm_ip in vm_ip_list:
        cmd1 = "ping -c 4 "+vm_ip
        result = os.popen(cmd1).read()
        print(result)
        if "0% packet loss" in result: vm_ip_pass_num+=1
    if vm_ip_pass_num == len(vm_ip_list):
        break
    elif x < 8:
        continue
    else:
        print("Ping Test Fail ...  Cannot connect vm host")

show_step(7, "SSH connection test")
for vm_ip in vm_ip_list:
    vm_cfg = {
        "mgmt_ip": vm_ip,
        "username": "root",
        "password": "abc1234"
    }
    vm_connect = SSH_CONNECT(vm_cfg)
    if("success" in vm_connect.ping("8.8.8.8", 4, True)):
        show_msg("ping test pass")
    else:
        print("Ping Test Fail ...  Cannot connect vm "+vm_ip)






show_step(8, "Get all PVC data ")
if vm_namespace == "default":
    cmd1="kubectl get pvc"
else:
    cmd1="kubectl get pvc -n %s" % vm_namespace
result_k8s = os.popen(cmd1).read()
print("result= %s" % result_k8s)

show_step(9, "Create Data disk of VM")
vm_data_disk_list = []
for x in range(1, create_host_num+1):
    data = {
        "description": "",
        "name": vm_data_disk_name+str(x),
        "namespace": vm_namespace,
        "size": vm_data_disk_size
    }
    url = "/kapis/virtualization.ecpaas.io/v1/namespaces/%s/disks" % vm_namespace
    cmd1 = 'curl -u '+user_pw+' -H "Content-Type: application/json" -X POST -d \''+json.dumps(data)+'\' '+host_ip+':30880'+url
    result = os.popen(cmd1).read()
    print("New disk id= %s" % result)
    # # # result_dict= {
    # # #  "id": "disk-7f43ef58"
    # # # }
    result_dict = json.loads(result)
    vm_data_disk_list.append(result_dict["id"])
    time.sleep(5)


show_step(10, "Check new PVC status ")
if vm_namespace == "default":
    cmd1="kubectl get pvc"
else:
    cmd1="kubectl get pvc -n %s" % vm_namespace
for x in range(0, 10):
    time.sleep(10)
    result_status = os.popen(cmd1).read()
    print("result= %s" % result_status)
    list_data = ",".join(result_status.split())
    list_data = list_data.split(",")
    list_data_len = len(list_data)
    loop_mark=1
    disk_pass_num=0
    for data_loc in range(0, list_data_len):
        for disk_data in vm_data_disk_list:
            if disk_data in list_data[data_loc] and "Bound" in list_data[data_loc+1]: disk_pass_num+=1
        if disk_pass_num == len(vm_data_disk_list): loop_mark=0

    if loop_mark == 0:
        msg = "The data disk of all has been bound"
        show_msg(msg)
        show_msg(", ".join(vm_data_disk_list))
        break
    if x < 9: continue
    print("Create new data disk. fail")
    sys.exit(0)





#vm_data_disk_list = ["disk-3ea4425f", "disk-550ea1e6"]
#vm_name_id_list = ["vm-3bc6379b", "vm-89981da3"]
show_step(11, "Check VM")
url = "/kapis/virtualization.ecpaas.io/v1/virtualmachines"
cmd1 = 'curl -u '+user_pw+' -H "Content-Type: application/json" -X GET '+host_ip+':30880'+url
result_status = os.popen(cmd1).read()
result_dict = json.loads(result_status)
vm_data = result_dict["items"]
loop_mark=1
vm_name_count = 0
for data_loc in range(0, len(vm_data)):
    print(vm_data[data_loc])
    for vm_name_id in vm_name_id_list:
        if vm_name_id in vm_data[data_loc]["id"]: vm_name_count+=1
    if vm_name_count == len(vm_name_id_list):
        loop_mark=0
        break
if loop_mark == 1:
    print("The %s of VM not exists. fail" % vm_name_id)
    sys.exit(0)

show_step(12, "Mount data dick on VM")
for i in range(0, len(vm_name_id_list)):
    data = {
        "disk": [
            {
                "action": "mount",
                "id": vm_data_disk_list[i],
                "namespace": vm_namespace
            }
        ]
    }
    url = "/kapis/virtualization.ecpaas.io/v1/namespaces/%s/virtualmachines/%s" % (vm_namespace, vm_name_id_list[i])
    cmd1 = 'curl -u '+user_pw+' -H "Content-Type: application/json" -X PUT -d \''+json.dumps(data)+'\' '+host_ip+':30880'+url
    result = os.popen(cmd1).read()
    show_msg(vm_name_id_list[i] + " mount result = "+result)
    time.sleep(3)

show_step(13, "Check vm mount disk status ")
for i in range(0, len(vm_name_id_list)):
    for x in range(0, 6):
        url = "/kapis/virtualization.ecpaas.io/v1/namespaces/%s/virtualmachines/%s" % (vm_namespace, vm_name_id_list[i])
        cmd1 = 'curl -u '+user_pw+' -H "Content-Type: application/json" -X GET '+host_ip+':30880'+url
        time.sleep(10)
        result_status = os.popen(cmd1).read()
        #print("result= %s" % result_status)
        result_dict = json.loads(result_status)
        disk_data = result_dict["disks"]
        loop_mark=1
        for data_loc in range(0, len(disk_data)):
            print(disk_data[data_loc])
            if vm_data_disk_list[i] in disk_data[data_loc]["id"]:
                loop_mark=0
                break
        if loop_mark == 0:
            msg = "The data disk of %s has been mount" % vm_data_disk_list[i]
            show_msg(msg)
            break
        if x <= 4: continue
        msg="Mount data disk of %s. fail" % vm_data_disk_list[i]
        show_msg(msg)
        sys.exit(0)


show_step(14, "Check data volume status")
if vm_namespace == "default":
    cmd1="kubectl get pods -o wide "
else:
    cmd1="kubectl get pods -o wide -n %s" % vm_namespace
for i in range(0, 10):
    time.sleep(10)
    result_k8s = os.popen(cmd1).read()
    print("result= %s" % result_k8s)
    list_data = ",".join(result_k8s.split())
    list_data = list_data.split(",")
    print(list_data)
    list_data_len = len(list_data)
    loop_count=0
    for data_loc in range(0, list_data_len):
        if "hp-volume" in list_data[data_loc]:
            if list_data[data_loc+2] in "Running": loop_count+=1
    if create_host_num == loop_count:
        break
    else:
        print("Found data volume is not ready..")
        continue

show_step(15, "Get the virtual machine IP from list id again")
vm_name_id_list_reg = vm_name_id_list.copy()
vm_ip_list = []
if vm_namespace == "default":
    cmd1="kubectl get pods -o wide "
else:
    cmd1="kubectl get pods -o wide -n %s" % vm_namespace
result_k8s = os.popen(cmd1).read()
print("result= %s" % result_k8s)
list_data = ",".join(result_k8s.split())
list_data = list_data.split(",")
print(list_data)
list_data_len = len(list_data)
for data_loc in range(0, list_data_len):
    for data_reg in vm_name_id_list_reg:
        if data_reg in list_data[data_loc]:
            #print(list_data[data_loc+5])
            vm_ip_list.append(list_data[data_loc+5])
            vm_name_id_list_reg.remove(data_reg)
            break
    if vm_name_id_list_reg == []: break


show_step(16, "Confirm whether the virtual machine has been mounted with PVC")
for i in range(0, len(vm_ip_list)):
    vm_cfg = {
        "mgmt_ip": vm_ip_list[i],
        "username": "root",
        "password": "abc1234"
    }
    pass_mark=0
    chk_size = str(vm_data_disk_size)+"G"
    for x in range(0, 6):
        time.sleep(10)
        vm_connect = SSH_CONNECT(vm_cfg)
        ssh_result = vm_connect.run_cmd("lsblk", False).decode().split("\n")
        for p in ssh_result:
            print(p)
            if chk_size in p: pass_mark=1
        if(pass_mark == 1):
            msg = "The virtual machine of IP %s have a data disk mounted => PASS" % vm_ip_list[i]
            show_msg(msg)
            break
    if pass_mark == 0: print("The virtual machine of IP %s does not have a data disk mounted => FAIL")
