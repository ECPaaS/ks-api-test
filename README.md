ECPaaS自動化測試VM

1   INTRODUCTION

介紹如何使用python測試自動建立VM方法。

2   REFERENCE

2.1 參考文件

1.  https://pypi.org/project/paramiko/

3      測試自動建立VM的系統及檔案需求

3.1    前置作業

3.1.1  系統版本資訊

DISTRIB_ID=Ubuntu

DISTRIB_RELEASE=20.04

DISTRIB_CODENAME=focal

DISTRIB_DESCRIPTION="Ubuntu 20.04.6 LTS"

3.1.2	IMAGE

https://cloud-images.ubuntu.com/

可以在這邊找需要的官方版本 image 來作客製化，

按需求選擇下載適合版本的 IMAGE，EX:

wget https://cloud-images.ubuntu.com/releases/focal/release/ ubuntu-20.04-server-cloudimg-amd64.img

PS: 範例是用 20.04 版本。

3.1.3 工具程式
以下步驟會用到的工具程式，可以先裝好備用。

1.  Python 3.8.10
2.  pip 24.2 (python 3.8)
3.  paramiko 3.4.1 (pkg: python package)
4.  系統要有curl的指令


3.2 程式介紹和起動測試方法及參數
1.  先在本地目錄放置要上傳的 image及程式
Image:
ubuntu-20.04-server-cloudimg-amd64.img

單一建立VM的程式:
build_vm1.py

可配置建立VM參數的程式:

build_vm_many.py

清除所有虛擬化的template image, data volume, VM, upload image

remove_vm.py

build_vm_many.py可配置參數檔:

vm_config.ini

[vm]

cpu=1

ram=2

system_disk_size=20

template_name=t-name

host_name=h

namespace=def-vm

data_disk_name=data

data_disk_size=10

[host_num]

num=2

[host_disk_num]

num=2

2. 起動測試指令範例

python3 build_vm1.py admin:xxxxxxxx 192.168.42.212 bionic-server-cloudimg-i386.img

python3 build_vm_many.py admin:xxxxxxxx 192.168.42.212 bionic-server-cloudimg-i386.img

python3 remove_vm.py admin:xxxxxxxx 192.168.42.212 

起動測試參數:

測試程式名稱:    build_vm1.py

user:password: admin:xxxxxxxx(集群登入user/password)

Host IP(k8s):  192.168.42.212

上傳image file: bionic-server-cloudimg-i386.img

