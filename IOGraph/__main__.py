#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def iograph():
    """Generate Graphs for IOZone."""
    global _iograph
    if _iograph: return _iograph

import os
import codecs
import os.path
import socket
import sys
from cpuinfo import get_cpu_info
import struct
import datetime
#import csv
#import ast
#import re
#import json
import time
import math
import yaml
import xlrd
import itertools
import psutil
from psutil import virtual_memory
import xlwt
from xlutils.copy import copy as xl_copy
import argparse
import threading
import time
import distro
import pkg_resources
from shutil import which
from argparse import RawTextHelpFormatter
import pkg_resources
import appdirs
import platform
import subprocess
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pprint import pprint
#import pandas as pd
#import plotly.express as px
#import dash_core_components as dcc
#import dash_html_components as html
#from dash.dependencies import Input, Output
#from numpy.random import seed, rand
#from datetime import date
#from base64 import b64encode




## Get Version
version = pkg_resources.require("IOGraph")[0].version

##ArgumentParser
IOGraphMoTD='IOGraph\nVersion: '
IOGraphMoTD+=str(version)
IOGraphMoTD+='\nGenerate Graphs from IOZone Data'
parser = argparse.ArgumentParser(description=IOGraphMoTD, formatter_class=RawTextHelpFormatter
                   )
parser.add_argument('--version', action='version', version=version
                   )
parser.add_argument("-d","--dryrun",
                    help='Generate Graph from existing XLS file',nargs='+'
                   )
parser.add_argument("-v","--verbose",
                    help="increase output verbosity.",
                    action="store_true"
                   )
parser.add_argument("-a","--average", type=int,
                    help="run IOZone X times and average the results."
                   )
parser.add_argument("-c","--compare",
                    help="path to another IOzone generated XLS to compare results against."
                   )
parser.add_argument("-s","--settings",
                    help="the parameters that you want to run IOzone with."
                   )
parser.add_argument("-E","--executable",
                    help="path to the IOZone Executable."
                   )
parser.add_argument("-m","--mute",
                    help="mute all output.",
                    action="store_true"
                   )
parser.add_argument("-o","--outputfile",
                    help="specify the name of the output file, defaults to output."
                   )
parser.add_argument("-f","--filename",
                    help="specify the path and filename that IOzone Runs against."
                   )
parser.add_argument("-i","--testtype",
                    help='Test to run:\n\t0=write/rewrite, 1=read/re-read, 2=random-read/write\n\t3=Read-backwards, 4=Re-write-record, 5=stride-read, 6=fwrite/re-fwrite\n\t7=fread/Re-fread, 8=random_mix, 9=pwrite/Re-pwrite, 10=pread/Re-pread\n\t11=pwritev/Re-pwritev, 12=preadv/Re-preadv'
                   )
parser.add_argument("-I","--directio",
                    help='Use DIRECT IO if possible for all file operations. Tells the filesystem that all operations to the file are to bypass the buffer cache and go directly to disk. (not available on all platforms)'
                   )
parser.add_argument("-g","--maxfilesize",
                    help="Set maximum file size (in Kbytes) for auto mode. One may also specify -g #k (size in Kbytes) or -g #m (size in Mbytes) or -g #g (size in Gbytes). See -n for minimum file size."
                   )
parser.add_argument("-n","--minfilesize",
                    help="Override the minimum file size used for test to Bypass system buffer."
                   )                  
parser.add_argument("-q","--maxrecordsize",
                    help="Set maximum record size (in Kbytes) for auto mode. One may also specify -q #k (size in Kbytes) or -q #m (size in Mbytes) or -q #g (size in Gbytes). See -y for minimum record size."
                   )
parser.add_argument("-r","--recordsize",
                    help="Used to specify the record size, in Kbytes, to test. One may also specify -r #k (size in Kbytes) or -r #m (size in Mbytes) or -r #g (size in Gbytes)."
                   )
parser.add_argument("-y","--minrecordsize",
                    help="Set minimum record size (in Kbytes) for auto mode. One may also specify -y #k (size in Kbytes) or -y #m (size in Mbytes) or -y #g (size in Gbytes). See -q for maximum record size."
                   )
parser.add_argument("-F","--filesize",
                    help="Used to specify the size, in Kbytes, of the file to test. One may also specify -s #k (size in Kbytes) or -s #m (size in Mbytes) or -s #g (size in Gbytes).."
                   )
parser.add_argument("-U","--unmount",
                    help="Mount point to unmount and remount between tests. IOZone will unmount and remount this mount point before beginning each test. This guarantees that the buffer cache does not contain any of the file under test."
                   )                                    
parser.add_argument("-u","--cpu",
                    help="Include CPU results in Reports.",
                    action="store_true"
                   )
parser.add_argument("-z","--smallrecords",
                    help="Used in conjunction with -a to test all possible record sizes. Normally Iozone omits testing of small record sizes for very large files when used in full automatic mode. This option forces Iozone to include the small record sizes in the automatic tests also.",
                    action="store_true"
                   )
parser.add_argument("-e","--flush",
                    help="Include flush (fsync,fflush) in the timing calculations.",
                    action="store_true"
                   )
parser.add_argument("-M","--uname",
                    help="IOZone will call uname() and will put the string in the output file.",
                    action="store_true"
                   )

## Return all Argparse variables to args variable
args = parser.parse_args()
## End Argparse



## Configuration File
def get_config():
  ## Get User Config Dir
  cfg_dir = appdirs.user_config_dir('IOGraph')
  ## Get Conf file Path and Join it to the Dir
  cfg_file = os.path.join(cfg_dir, 'conf.yml')
  ## Check if it exists
  if not os.path.isfile(cfg_file):
      isDir = os.path.isdir(cfg_dir) 
      ## If the dir doesn't exist, create it
      if not isDir:
          os.mkdir(cfg_dir)
      ## Create the Config Dir
      create_user_config(cfg_file)
  ## Open and Return the Data
  with open(cfg_file) as f:
      config = yaml.load(f.read(), Loader=yaml.FullLoader)
      return config

## Create the configs if they don't exist in the users directory
def create_user_config(cfg_file):
    source = pkg_resources.resource_stream(__name__, 'conf.yml.dist')
    with open(cfg_file, 'wb') as dest:
        dest.writelines(source)

# Get the Configs
cfg = get_config()
## End of Configuration File

## Begin ZFS Detect Function
def zfs_detect(Array,OperatingSystem):
    poolconfigstart=False
    pool=Array
    command=""
    command+="zpool status "
    command+=pool
    config=[]
    import subprocess
    zpool = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    for line in zpool.stdout:
        cleanLine=line.rstrip().decode("utf-8")
        if "pool:" in cleanLine:
            poolname=cleanLine.split(':')[1].lstrip()
            poolconfigstart=False
        elif "state:" in cleanLine:
            poolstate=cleanLine.split(':')[1].lstrip()
            poolconfigstart=False
        elif "config:" in cleanLine:
            poolconfigstart=True
        elif "errors:" in cleanLine:
            poolconfigstart=False
            poolerrors=cleanLine.split(':')[1].lstrip()
        elif poolconfigstart:
            config.append(cleanLine)
    del config[0]
    del config[0]
    pool=config[0].lstrip().split(' ')[0]
    pooltype=config[1].lstrip().split(' ')[0]
    del config[0]
    del config[0]
    
    while("" in config) :
        config.remove("")
    
    newconfig=[]
    for entry in config:
        newconfig.append(entry.lstrip().split(' ')[0])
    diskType=[]
    disk=[]
    diskVendor=[]
    diskPartID=[]
    diskSize=[]
    
    
    if OperatingSystem == "omnios":
        #### OmniOS Specific  ####
        command=""
        command+="diskinfo"
        dconfig=[]
        import subprocess
        diskinfo = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        for line in diskinfo.stdout:
            dcleanLine=line.rstrip().decode("utf-8")
            dconfig.append(dcleanLine)
        
        diskConfs=[]
        del dconfig[0]
        for entry in dconfig:
            splentry=entry.split()
            if any(fs in splentry[1] for fs in newconfig):
                diskType=splentry[0]
                disk=splentry[1]
                diskVendor=splentry[2]
                diskPartID=splentry[3]
                diskSize=splentry[4]+" "+splentry[5]
                conf=[diskType,disk,diskVendor,diskPartID,diskSize]
                diskConfs.append(conf)
    
    
    #### Linux Specific ###
    if OperatingSystem == "ubuntu" or OperatingSystem == "centos":
        print("Some Linux Code to get Serial and Model and same info as above")
    
    ## Output
    finalConf=[]
    for conf in diskConfs:
        conf.append(pooltype)
        conf.append(pool)
        finalConf.append(conf)
    
    return finalConf      
## End ZFS Detect Function

## Detect Which System we are Running on
def osDetect():
  ## Small Animation Function
  osAnimatedone = False
  
  def animate():
      if not args.mute:
          print()
          for c in itertools.cycle(['.       ', '. .     ', '. . .   ', '. . . . ']):
              if osAnimatedone:
                  break
              sys.stdout.write('\rGathering System Information ' + c)
              sys.stdout.flush()
              time.sleep(0.1)
          sys.stdout.write('\rDone Gathering System Information!           ')
          print()
  ## End Animation Function
  System=os.name
  Platform=platform.system()
  PlatformRelease=platform.release()
  cpu=get_cpu_info()
  osAnimatedone = True
  osAnimatedone = False
  if not args.verbose:
      t = threading.Thread(target=animate)
      t.daemon=True
      t.start()
  rhel=False
  centos=False
  debian=False
  ubuntu=False
  omnios=False
  windows=False
  linux=False
  OperatingSystem=""
  hostname=socket.getfqdn()  
  today = datetime.datetime.now()
  today = str(today)
  SYSINF=[]
  SYSINF.append("System Information")
  Hostname=["Hostname",hostname]
  SYSINF.append(Hostname)
  Today=["Date",today]
  SYSINF.append(Today)
  system=["System",System]
  SYSINF.append(system)
  pdata=["Platform",Platform]
  SYSINF.append(pdata)
  platformrelease=["Release",PlatformRelease]
  SYSINF.append(platformrelease)

  if  args.verbose:
      print("System Information:")
      print("\tHostname:\t\t\t",hostname)
      print("\tDate:\t\t\t\t",today)
      print("\tSystem:\t\t\t\t",System)
      print("\tPlatform:\t\t\t",Platform)
      print("\tRelease:\t\t\t",PlatformRelease)
      print()
      print()
      print()


  if  args.verbose:
      print("CPU Information:")
  CPUINF=[]
  CPUINF.append("CPU Information")
  
  for x in cpu.keys():
      if x == "python_version":
          if  args.verbose: print("\t",x ,"\t\t" , cpu[x])
          python_version=["python_version",cpu[x]]
          CPUINF.append(python_version)
      if x == "cpuinfo_version":
          if  args.verbose: print("\t",x ,"\t\t" , cpu[x])
          value=str(cpu[x][0])+","+str(cpu[x][1])+","+str(cpu[x][2])
          cpuinfo_version=["cpuinfo_version",value]
          CPUINF.append(cpuinfo_version)
      if x == "cpuinfo_version_string":
          if  args.verbose: print("\t",x ,"\t" , cpu[x])
          cpuinfo_version_string=["cpuinfo_version_string",cpu[x]]
          CPUINF.append(cpuinfo_version_string)
      if x == "arch":
          if  args.verbose: print("\t",x ,"\t\t\t\t" , cpu[x])
          arch=["arch",cpu[x]]
          CPUINF.append(arch)
      if x == "bits":
          if  args.verbose: print("\t",x ,"\t\t\t\t" , cpu[x])
          bits=["bits",cpu[x]]
          CPUINF.append(bits)
      if x == "count":
          if  args.verbose: print("\t",x ,"\t\t\t\t" , cpu[x])
          count=["count",cpu[x]]
          CPUINF.append(count)
      if x == "arch_string_raw":
          if  args.verbose: print("\t",x ,"\t\t" , cpu[x])
          arch_string_raw=["arch_string_raw",cpu[x]]
          CPUINF.append(arch_string_raw)
      if x == "vendor_id_raw":
          if  args.verbose: print("\t",x ,"\t\t\t" , cpu[x])
          vendor_id_raw=["vendor_id_raw",cpu[x]]
          CPUINF.append(vendor_id_raw)
      if x == "brand_raw":
          if  args.verbose: print("\t",x ,"\t\t\t" , cpu[x])
          brand_raw=["brand_raw",cpu[x]]
          CPUINF.append(brand_raw)
      if x == "hz_advertised_friendly":
          if  args.verbose: print("\t",x ,"\t" , cpu[x])
          hz_advertised_friendly=["hz_advertised_friendly",cpu[x]]
          CPUINF.append(hz_advertised_friendly)
      if x == "hz_actual_friendly":
          if  args.verbose: print("\t",x ,"\t\t" , cpu[x])
          hz_actual_friendly=["hz_actual_friendly",cpu[x]]
          CPUINF.append(hz_actual_friendly)
      if x == "hz_advertised":
          if  args.verbose: print("\t",x ,"\t\t\t" , cpu[x])
          hz_advertised=["hz_advertised",cpu[x][0]]
          CPUINF.append(hz_advertised)
      if x == "hz_actual":
          if  args.verbose: print("\t",x ,"\t\t\t" , cpu[x])
          hz_actual=["hz_actual",cpu[x][0]]
          CPUINF.append(hz_actual)
      if x == "stepping":
          if  args.verbose: print("\t",x ,"\t\t\t" , cpu[x])
          stepping=["stepping",cpu[x]]
          CPUINF.append(stepping)
      if x == "model":
          if  args.verbose: print("\t",x ,"\t\t\t\t" , cpu[x])
          model=["model",cpu[x]]
          CPUINF.append(model)
      if x == "family":
          if  args.verbose: print("\t",x ,"\t\t\t" , cpu[x])
          family=["family",cpu[x]]
          CPUINF.append(family)
      if x == "flags":
          if  args.verbose: print("\t",x ,"\t\t\t\t" , cpu[x])
          flags=["flags",cpu[x]]
          CPUINF.append(flags)
      if x == "l2_cache_size":
          if  args.verbose: print("\t",x ,"\t\t\t" , cpu[x])
          l2_cache_size=["l2_cache_size",cpu[x]]
          CPUINF.append(l2_cache_size)
      if x == "l2_cache_line_size":
          if  args.verbose: print("\t",x ,"\t\t" , cpu[x])
          l2_cache_line_size=["l2_cache_line_size",cpu[x]]
          CPUINF.append(l2_cache_line_size)
      if x == "l2_cache_associativity":
          if  args.verbose: print("\t",x ,"\t" , cpu[x])
          l2_cache_associativity=["l2_cache_associativity",cpu[x]]
          CPUINF.append(l2_cache_associativity)


  significant_digits = 3

  MemConf=[]
  MemConf.append("Memory Configuration")
  
  vMem=virtual_memory().total / 1024 /1024
  Total=["Total",int(vMem)]
  MemConf.append(Total)
  
  vMem=virtual_memory().available / 1024 /1024
  Available=["Available",int(vMem)]
  MemConf.append(Available)
  
  vMem=virtual_memory().percent
  PUsed=["Percent Used",vMem]
  MemConf.append(PUsed)
  
  vMem=virtual_memory().used / 1024 /1024
  Used=["Used",int(vMem)]
  MemConf.append(Used)
  
  vMem=virtual_memory().free / 1024 /1024
  Free=["Free",int(vMem)]
  MemConf.append(Free)

## MemConf Ready to Pass Pack
  if  args.verbose:
      print()
      print()
      print()
      print("Memory Configuration:")
      vMem=virtual_memory().total / 1024 /1024
      print("\tTotal:\t\t\t\t",int(vMem),"MB")
      vMem=virtual_memory().available / 1024 /1024
      print("\tAvailable:\t\t\t",int(vMem),"MB")
      print("\tUsed:\t\t\t\t",virtual_memory().percent,"%")
      vMem=virtual_memory().used / 1024 /1024
      print("\tUsed:\t\t\t\t",int(vMem),"MB")
      vMem=virtual_memory().free / 1024 /1024
      print("\tFree:\t\t\t\t",int(vMem),"MB")
  
  ## Linux and OmniOS use Which to find path of IOZone
  def is_tool(name):
    return which(name)
    
  ## Windows Serach for the path to IOZone
  def find_files(filename, search_path):
     result = []
     for root, dir, files in os.walk(search_path):
        if filename in files:
           result.append(os.path.join(root, filename))
     return result[0]

  ## Detect Windows
  if os.name == "nt":
    windows=True
    os.environ['CYGWIN'] = 'nodosfilewarning'
  elif  os.name == "posix":
    if sys.platform == "cygwin":
      os.environ['CYGWIN'] = 'nodosfilewarning'
      windows=True
    elif sys.platform == "msys":
      os.environ['CYGWIN'] = 'nodosfilewarning'
      windows=True
  else:
    windows=False
    
  ## Detect OmniOS
  if  os.name == "posix":
    if Platform == "SunOS":
      if PlatformRelease == "5.11":
        omnios=True
        if os.geteuid() >  0:
            print("ERROR: Must be root to use")
            sys.exit(1)
  else:
    omnios=False
  
  ## Detect Linux
  if (Platform == "linux") or (Platform == "Linux"):
    if os.geteuid() >  0:
        print("ERROR: Must be root to use")
        sys.exit(1)
    ## Detect RHEL/CentOS
    if  (distro.linux_distribution(full_distribution_name=False)[0] == "CentOS Linux") or (distro.linux_distribution(full_distribution_name=False)[0] == "centos"):
      centos=True
    elif  (distro.linux_distribution(full_distribution_name=False)[0] == "Red Hat Enterprise Linux Server") or (distro.linux_distribution(full_distribution_name=False)[0] == "redhat"):
      rhel=True
    else:
      centos=False
    ## Detect if Ubuntu/Debian
    if (distro.linux_distribution(full_distribution_name=False)[0] == "Ubuntu") or (distro.linux_distribution(full_distribution_name=False)[0] == "ubuntu"):
      ubuntu=True
    elif  (distro.linux_distribution(full_distribution_name=False)[0] == "debian") or (distro.linux_distribution(full_distribution_name=False)[0] == "Debian"):
      debian=True
    else:
      ubuntu=False
      debian=False


  ## if Windows do
  if windows:
    executable = find_files("iozone.exe","C:\Program Files (x86)")
    OperatingSystem="windows"
  ## if OmniOS do  
  elif omnios:
    executable=is_tool("iozone")
    OperatingSystem="omnios"
  ## if CentOS do
  elif centos:
    executable=is_tool("iozone")  
    OperatingSystem="centos"
  ## if Ubuntu do
  elif ubuntu:
    executable=is_tool("iozone")
    OperatingSystem="ubuntu"
  elif args.executable:
    executable=args.executable
    OperatingSystem="na"
  else:
    print("IOZone not Detected, Please Specify path to IOZone with -E option")
    OperatingSystem="na"
    exit(1)
    
  # Check if Path is just the Root directory  
  path=cwd.rsplit('/', 1)
  if path[0] == "":
     path="/"
  else:
    path=cwd.rsplit('/', 1)[0]
  

  ## Get disk info from path
  ignoreFS=['hugetlbfs','cgroup','tmpfs','lofs','sysfs','proc','devtmpfs','securityfs','devpts','pstore','efivarfs','bpf','tracefs','configfs','mqueue','autofs','debugfs','fusectl','rpc_pipefs','binfmt_misc','devfs','dev','ctfs','sharefs','bootfs','objfs','mntfs','fd','vfat']


  STRGCONF=[] 
  #### Windows
  significant_digits = 5
  if OperatingSystem == "windows":
      import win32api, wmi
      drives = win32api.GetLogicalDriveStrings()
      drives = drives.split('\000')[:-1]
      driveInfo=[]
      for item in drives:
          diskName=win32api.GetVolumeInformation(item)[0]
          diskFS=win32api.GetVolumeInformation(item)[4]
          diskMount=item
          totalsize = psutil.disk_usage(item).total / 2**30
          finaltotalsize = round(totalsize,significant_digits - int(math.floor(math.log10(abs(totalsize)))) - 1)
          driveData=[diskMount,diskName,diskFS,finaltotalsize]
          driveInfo.append(driveData)


      def get_disk_info():
          tmplist = []
          c = wmi.WMI()
          for physical_disk in c.Win32_DiskDrive():
              tmpdict = [physical_disk.Model,physical_disk.DeviceID,physical_disk.SerialNumber,physical_disk.InterfaceType]
              tmplist.append(tmpdict)
          return tmplist
          
      def disk():
          c = wmi.WMI ()
          #Get hard disk partition
          disks=[]
          for physical_disk in c.Win32_DiskDrive ():
              for partition in physical_disk.associators ("Win32_DiskDriveToDiskPartition"):
                  for logical_disk in partition.associators ("Win32_LogicalDiskToPartition"):
                      disk=[physical_disk.Caption, partition.Caption, logical_disk.Caption]
                      disks.append(disk)
          return disks            
      diskdata=disk()
      dInfo=get_disk_info()
      driveanddiskdata=[]      
      for drive in driveInfo:
          for disk in diskdata:
              if disk[2] in drive[0]:
                  drive.append(disk[0])
    
      for ddData in driveInfo:
          if len(ddData) < 5: 
              ddData.append("fileshare")
      
      for di in dInfo:
          for drive in driveInfo:    
              if di[0] == drive[4]:
                  drive.append(di[1])
                  drive.append(di[2])
                  drive.append(di[3])
      
      for ddData in driveInfo:
          if len(ddData) < 8: 
              ddData.append("fileshare")
              ddData.append("fileshare")
              ddData.append("fileshare")

      for driveinfo in driveInfo:
          if driveinfo[0] in cwd:
              if  args.verbose:
                  print()
                  print()
                  print()
                  print("Storage Configuration: ")
                  print("\tDevice:\t\t\t\t", driveinfo[1])
                  print("\tMount Path:\t\t\t", driveinfo[0])
                  print("\tFS Type:\t\t\t", driveinfo[2])
                  print("\t-  Disk Model:\t\t\t", driveinfo[4])
                  print("\t   Disk Serial:\t\t\t", driveinfo[6])
                  print("\t   Disk Size:\t\t\t", driveinfo[3])
                  print("\t   Physiscal Disk Path:\t\t", driveinfo[5])
                  print("\t   Disk Interface Type:\t\t", driveinfo[7])
              STRGCONF.append("Storage Configuration")
              fDevice=["Device",driveinfo[1]]
              STRGCONF.append(fDevice)
              fMountPath=["Device",driveinfo[0]]
              STRGCONF.append(fMountPath)              
              fFSType=["Device",driveinfo[2]]
              STRGCONF.append(fFSType)
              fFModel=["Disk Model",driveinfo[4]]
              STRGCONF.append(fFModel)
              fFSerial=["Disk Serial",driveinfo[6]]
              STRGCONF.append(fFSerial)
              fDSize=["Disk Size",driveinfo[3]]
              STRGCONF.append(fDSize)
              fdPath=["Disk Path",driveinfo[5]]
              STRGCONF.append(fdPath)
              fIType=["Interface Type",driveinfo[7]]
              STRGCONF.append(fIType)
              
              
            
    ##### End Windows Disk Info


  XFSEXT4=False
  ZFS=False
  NFS=False
  rootXFSEXT4=False
  rootZFS=False
  rootNFS=False
  Device=""
  MountPath=""
  FSType=""
  DiskDeviceModel=""
  DiskDeviceSerial=""
  rootDevice=""
  rootMountPath=""
  rootFSType=""
  rootDiskDeviceModel=""
  rootDiskDeviceSerial=""
  finalDevice=""
  finalMountPath=""
  finalFSType=""
  finalDiskDeviceModel=""
  finalDiskDeviceSerial=""
  ## Linux and Solaris
   
  if OperatingSystem != "windows":
      for partition in psutil.disk_partitions(all=True):
          if partition[0] != "swap":
              if all(fs not in partition[2] for fs in ignoreFS):
                  if partition[1] != "/boot":
                      ## Get Disk Device Details
                      if partition[2] == "nfs":
                          if partition[1] in path:
                              Device=partition[0]
                              MountPath=partition[1]
                              FSType=partition[2]
                              NFS=True
                      ## if ZFS then        
                      if partition[2] == "zfs" :
                          if partition[0] != "rpool":
                              if partition[1] in path:
                                  if partition[1] == "/":
                                      rootDevice=partition[0]
                                      rootMountPath=partition[1]
                                      rootFSType=partition[2]
                                  else:
                                      Device=partition[0]
                                      MountPath=partition[1]
                                      FSType=partition[2]
                                      ## strip everything before and after first and second slah
                                      Array=MountPath.split("/")[1]
                                      Array=zfs_detect(Array,OperatingSystem)
                                      ZFS=True
                      if partition[2] == "xfs" or partition[2] == "ext4" :
                          import fcntl
                          ## if EXT or XFS
                          if partition[1] in path:
                              if partition[1] == "/":
                                  with open(partition[0][:-1], "rb") as fd:
                                      hd_driveid_format_str = "@ 10H 20s 3H 8s 40s 2B H 2B H 4B 6H 2B I 36H I Q 152H"
                                      HDIO_GET_IDENTITY = 0x030d
                                      sizeof_hd_driveid = struct.calcsize(hd_driveid_format_str)
                                      assert sizeof_hd_driveid == 512 
                                      buf = fcntl.ioctl(fd, HDIO_GET_IDENTITY, " " * sizeof_hd_driveid)
                                      fields = struct.unpack(hd_driveid_format_str, buf)
                                      serial_no = fields[10].strip()
                                      model = fields[15].strip()
                                      rootDiskDeviceModel=model.decode("utf-8")
                                      rootDiskDeviceSerial=serial_no.decode("utf-8")
                                  rootDevice=partition[0]
                                  rootMountPath=partition[1]
                                  rootFSType=partition[2]
                                  rootXFSEXT4=True
                              else:                          
                                  with open(partition[0][:-1], "rb") as fd:
                                      hd_driveid_format_str = "@ 10H 20s 3H 8s 40s 2B H 2B H 4B 6H 2B I 36H I Q 152H"
                                      HDIO_GET_IDENTITY = 0x030d
                                      sizeof_hd_driveid = struct.calcsize(hd_driveid_format_str)
                                      assert sizeof_hd_driveid == 512 
                                      buf = fcntl.ioctl(fd, HDIO_GET_IDENTITY, " " * sizeof_hd_driveid)
                                      fields = struct.unpack(hd_driveid_format_str, buf)
                                      serial_no = fields[10].strip()
                                      model = fields[15].strip()
                                      DiskDeviceModel=model.decode("utf-8")
                                      DiskDeviceSerial=serial_no.decode("utf-8")
                                  Device=partition[0]
                                  MountPath=partition[1]
                                  FSType=partition[2]
                                  XFSEXT4=True
      if Device == "":
          finalDevice = rootDevice
          if rootXFSEXT4:
              finalDiskDeviceModel = rootDiskDeviceModel
              finalDiskDeviceSerial = rootDiskDeviceSerial
      if Device != "":
          finalDevice = Device
          if XFSEXT4:
              finalDiskDeviceModel = DiskDeviceModel
              finalDiskDeviceSerial = DiskDeviceSerial
      if MountPath == "":
          finalMountPath = rootMountPath
      if MountPath != "":
          finalMountPath = MountPath
      if FSType == "":
          finalFSType = rootFSType
      if FSType != "":
          finalFSType = FSType
      if  args.verbose:
          print()
          print()
          print()
          print("Storage Configuration: ")
          print("\tDevice:\t\t\t\t", finalDevice)
          print("\tFS Type:\t\t\t", finalFSType)
          print("\tMount Path:\t\t\t", finalMountPath)
      
      STRGCONF.append("Storage Configuration")     
      fDevice=["Device",finalDevice]
      STRGCONF.append(fDevice)
      fMountPath=["Mount Path",finalMountPath]
      STRGCONF.append(fMountPath)
      fFSType=["FS Type",finalFSType]
      STRGCONF.append(fFSType)
      
      if (XFSEXT4 or rootXFSEXT4) and not NFS:
          if  args.verbose:
              print("\t-  Disk Model:\t\t\t", finalDiskDeviceModel)
              print("\t   Disk Serial:\t\t\t", finalDiskDeviceSerial)
          spacer=["",""]             
          STRGCONF.append(spacer)
          fDiskDeviceModel=["Disk Model",finalDiskDeviceModel]
          STRGCONF.append(fDiskDeviceModel)          
          fDiskDeviceSerial=["Disk Serial",finalDiskDeviceSerial]
          STRGCONF.append(fDiskDeviceSerial)
      if ZFS: 
          for disk in Array:
              if  args.verbose:
                  print("\t-  Disk Model:\t\t\t", disk[3])
                  print("\t   Disk Serial:\t\t\t", disk[1])
                  print("\t   Interface Type:\t\t", disk[0])
                  print("\t   Disk Size:\t\t\t", disk[4])
                  print("\t   ZFS Configuration:\t\t", disk[5])
                  print("\t   Zpool:\t\t\t", disk[6])
                  print("\t   Disk Vendor:\t\t\t", disk[2])
              spacer=["",""]             
              STRGCONF.append(spacer)
              dModel=["Disk Model",disk[3]]
              STRGCONF.append(dModel)
              dSerial=["Disk Serial",disk[1]]
              STRGCONF.append(dSerial)              
              dIType=["Interface Type",disk[0]]              
              STRGCONF.append(dIType)              
              dSize=["Disk Size",disk[4]]              
              STRGCONF.append(dSize)              
              dZC=["ZFS Configuration",disk[5]]              
              STRGCONF.append(dZC)              
              dZpool=["Zpool",disk[6]]             
              STRGCONF.append(dZpool)              
              dPN=["Disk Vendor",disk[2]]             
              STRGCONF.append(dPN)



  osData=[]
  osData.append(executable) #0
  osData.append(OperatingSystem) #1
  osData.append(System) #2
  osData.append(Platform) #3
  osData.append(PlatformRelease) #4
  osData.append(hostname) #5
  osData.append(SYSINF) #6
  osData.append(CPUINF) #7
  osData.append(MemConf) #8
  osData.append(STRGCONF) #9
  osAnimatedone = True
  if not args.verbose:
      if not args.mute: t.join()
  return osData
## End OS detection

## Get the Current Working Directory incase no path is specified by end user
def current_path():
    cwd=os.getcwd()
    return cwd

## Specify the filename ofthe test file if the user does not define it
if not args.filename:
    cwd=current_path()
    cwd+="IOZoneTestFile"
else:
    cwd=args.filename
    ## Do Sanitazation
    

OSData = osDetect()
executable=OSData[0]
OperatingSystem=OSData[1]
System=OSData[2]
Platform=OSData[3]
PlatformRelease=OSData[4]
hostname=OSData[5]
SystemInformation=OSData[6]
ProcessorInformation=OSData[7]
MemoryInformation=OSData[8]
DiskInformation=OSData[9]


## use data from Argparse to drive process
if args.dryrun:
    dryRun=args.dryrun
    
if not args.average:
    averageRun=1   
else:
    averageRun=args.average

if not args.outputfile:
    outputFile=hostname
else:
    outputFile=args.outputfile

if not args.settings:
    IOSettings="Rab"   
else:
    IOSettings=args.settings

if  args.verbose:
    print("Verbose:\t\t\t\t",args.verbose)
    print("Dry Run:\t\t\t\t",args.dryrun)
    print("Averaging Runs:\t\t\t\t",averageRun)
    print("Comparing Against:\t\t\t",args.compare)
    print("IOZone Settings:\t\t\t",IOSettings)
    print("IOzone is Running across the filename:\t",args.filename)
    print("IOZone is testing against the path:\t", cwd)

## Begin of Annot which helps wiht annotations on the Graph
def annot(xcrd,ycrd, zcrd, txt, yancr='bottom'):
    strng=dict(showarrow=False, x=xcrd, y=ycrd, z=zcrd, text=txt, yanchor=yancr, font=dict(color=cfg['plot']['annotation']['COLOR'],size=cfg['plot']['annotation']['SIZE']))
    return strng
## End of Annot

## Begin runIO Function
def runIO(runCount):
    ## Begin Animation Function
    Animatedone = False
    def animate():
        print()
        for c in itertools.cycle(['.       ', '. .     ', '. . .   ', '. . . . ']):
            if Animatedone:
                break
            sys.stdout.write('\rRunning IOZone ' + c)
            sys.stdout.flush()
            time.sleep(0.2)
        sys.stdout.write('\rDone Running IOZone!                  ')
        print()
    ## End Animation Function
    
    ## Run the Command to Grab the Data -- Add Flags Later for Different Reports
    loc=[]
    for x in range(0,1):
        if not args.dryrun:
            if not args.verbose:
                ## Define the location of the output file
                locfile=""
                locfile+=outputFile
                locfile+="-"
                locfile+=str(runCount+1)
                locfile+=".xls"
                if not args.mute:
                    print()
                    print("Run:",runCount+1," Filename: ",locfile)
                if not args.mute:
                    t = threading.Thread(target=animate)
                    t.daemon=True
                    t.start()
                command=""
                if OperatingSystem != "windows":
                  command="nohup "
                  command+=executable
                if OperatingSystem == "windows":
                  command+=f'"{executable}"'
                command+=" -"
                command+=IOSettings
                command+=" "
                command+=locfile
                if args.testtype:
                    command+=" -i "
                    command+=args.testtype
                    command+=" "
                if args.cpu:
                    command+=" -+u "
                if args.maxfilesize:
                    command+=" -g "
                    command+=args.maxfilesize
                    command+=" "
                if args.minfilesize:
                    command+=" -n "
                    command+=args.minfilesize
                    command+=" "
                if args.smallrecords:
                    command+=" -z "
                if cwd:
                    command+=" -f "
                    command+=cwd
                    command+=" "
                if OperatingSystem != "windows":
                    command+='> IO-output.log  2>&1'
                if OperatingSystem == "windows":
                    command+='> IO-output.log'

                iozonertndata = subprocess.Popen(command, shell=True)
                iozonertndata.wait()

                Animatedone = True
                if not args.mute: t.join()

                ## Open the Existing Worksheet
                rb = xlrd.open_workbook(locfile,  encoding_override='cp1252')
                # make a copy of it
                if rb.nsheets > 1: print("Already Has MetaData, Something smells Fishy")
                else:
                    wb = xl_copy(rb)
                    MetaData = wb.add_sheet('MetaData') 
                    row = 0
                    col = 0
                    entrycount = 0
                    for entry in SystemInformation:
                        if entrycount < 1:
                            MetaData.write(entrycount,col,entry)
                            col=1
                            entrycount+=1
                        elif entrycount > 0:
                            entrycount+=1
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            MetaData.write(entrycount,col,entry[1])
                            col=1
                    entrycount+=1
                    entrycount+=1   
                    col=0
                    for ecount,entry in enumerate(ProcessorInformation):
                        if ecount < 1:
                            MetaData.write(entrycount,col,entry)
                            col=1
                            entrycount+=1
                        elif ecount > 0:                              
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            if entry[0] == "flags":
                                for flag in entry[1]:
                                    MetaData.write(entrycount,col,flag)
                                    col+=1
                                col=1
                            else:
                                MetaData.write(entrycount,col,entry[1])
                                col=1
                            entrycount+=1
                    entrycount+=1   
                    col=0
                    for mcount,entry in enumerate(MemoryInformation):
                        if mcount < 1:
                            MetaData.write(entrycount,col,entry)
                            col=1
                            entrycount+=1
                        elif mcount > 0:                            
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            MetaData.write(entrycount,col,entry[1])
                            col=1
                            entrycount+=1
                    entrycount+=1
                    entrycount+=1   
                    col=0
                    for dcount,entry in enumerate(DiskInformation):
                        if dcount == 0:
                            MetaData.write(entrycount,col,entry)
                            col=1
                            entrycount+=1
                        elif 1 <= dcount <= 3:  
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            MetaData.write(entrycount,col,entry[1])
                            col=1
                            entrycount+=1
                        elif dcount > 3:
                            col=2
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            MetaData.write(entrycount,col,entry[1])
                            col=2
                            entrycount+=1
                    wb.save(locfile)
                loc=locfile
            else:
                ## Define the location of the output file
                locfile=""
                locfile+=outputFile
                locfile+="-"
                locfile+=str(runCount+1)
                locfile+=".xls"
                if not args.mute:
                    print()
                    print("Starting Run: ",runCount+1)
                command=""
                if OperatingSystem != "windows":
                   command+=executable
                if OperatingSystem == "windows":
                  command+=f'"{executable}"'
                command+=" -"
                command+=IOSettings
                command+=" "
                command+=outputFile
                command+="-"
                command+=str(runCount+1)
                command+='.xls'
                if args.testtype:
                    command+=" -i "
                    command+=args.testtype
                    command+=" "
                if args.maxfilesize:
                    command+=" -g "
                    command+=args.maxfilesize
                    command+=" "
                if args.minfilesize:
                    command+=" -n "
                    command+=args.minfilesize
                    command+=" "
                if args.cpu:
                    command+=" -+u "
                if args.smallrecords:
                    command+=" -z "
                if cwd:
                    command+=" -f "
                    command+=cwd
                print("Running Command:", command)
                iozonertndata = subprocess.Popen(command, shell=True)
                iozonertndata.wait()

                ## Open the Existing Worksheet
                rb = xlrd.open_workbook(locfile,  encoding_override='cp1252')
                # make a copy of it
                if rb.nsheets > 1: print("Already Has MetaData, Something smells Fishy")
                else:
                    wb = xl_copy(rb)
                    MetaData = wb.add_sheet('MetaData') 
                    row = 0
                    col = 0
                    entrycount = 0
                    for entry in SystemInformation:
                        if entrycount < 1:
                            MetaData.write(entrycount,col,entry)
                            col=1
                            entrycount+=1
                        elif entrycount > 0:
                            entrycount+=1
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            MetaData.write(entrycount,col,entry[1])
                            col=1
                    entrycount+=1
                    entrycount+=1   
                    col=0
                    for ecount,entry in enumerate(ProcessorInformation):
                        if ecount < 1:
                            MetaData.write(entrycount,col,entry)
                            col=1
                            entrycount+=1
                        elif ecount > 0:                              
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            if entry[0] == "flags":
                                for flag in entry[1]:
                                    MetaData.write(entrycount,col,flag)
                                    col+=1
                                col=1
                            else:
                                MetaData.write(entrycount,col,entry[1])
                                col=1
                            entrycount+=1
                    entrycount+=1   
                    col=0
                    for mcount,entry in enumerate(MemoryInformation):
                        if mcount < 1:
                            MetaData.write(entrycount,col,entry)
                            col=1
                            entrycount+=1
                        elif mcount > 0:                            
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            MetaData.write(entrycount,col,entry[1])
                            col=1
                            entrycount+=1
                    entrycount+=1
                    entrycount+=1   
                    col=0
                    for dcount,entry in enumerate(DiskInformation):
                        if dcount == 0:
                            MetaData.write(entrycount,col,entry)
                            col=1
                            entrycount+=1
                        elif 1 <= dcount <= 3:  
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            MetaData.write(entrycount,col,entry[1])
                            col=1
                            entrycount+=1
                        elif dcount > 3:
                            col=2
                            MetaData.write(entrycount,col,entry[0])
                            col+=1
                            MetaData.write(entrycount,col,entry[1])
                            col=2
                            entrycount+=1
                    wb.save(locfile)
                loc=locfile
                if not args.mute:
                    print()
                    print("Run:",runCount+1," Filename: ",loc)
        else:
            for arg in args.dryrun:
                loc=arg
    return loc    
## End runIO Function

## Begin of Trace
def Trace(clr,data):
    X = []
    Y = []
    Z = []
    for datum in data:
        X.append(float(datum[0]))
        Y.append(float(datum[1]))
        Z.append(float(datum[2]))
    if 'plot' in cfg:
        if 'trace' in cfg['plot']:
            if 'COLOR' in cfg['plot']['trace']:
                traceColor=cfg['plot']['trace']['COLOR']
            else:
                traceColor=Z
    if 'plot' in cfg:
        if 'trace' in cfg['plot']:
            if 'COLOR' in cfg['plot']['line']:
                lineColor=cfg['plot']['line']['COLOR']
            else:
                lineColor=Z
    ##Trace each Scatter 3d Trace
    trace=go.Scatter3d(
                       x=X,
                       y=Y,
                       z=Z, 
                       mode="lines+markers", 
                       marker = dict(
                           size = cfg['plot']['trace']['SIZE'],
                           color = traceColor,
                           #fill="toself",
                           showscale=True,
                           coloraxis="coloraxis",
                           colorscale = cfg['plot']['trace']['COLORSCALE']
                           ),
                       line=dict(
                           color=lineColor,
                           colorscale = cfg['plot']['line']['COLORSCALE'],
                           coloraxis="coloraxis",
                           width=cfg['plot']['line']['width']
                           )
                       )
    return trace   
## End of Trace

## Begin reportTrace Function
def reportTrace(reports):
    reportMatrix = []
    XData=[]
    YData=[]
    ZData=[]
    Data=[]
    dataCount = 0
    for reportData in reports[1:]:
        ## If the First Row start with Zero, then it is the Y Axis
        if dataCount == 0:
            YData=reportData[1:]
        ## The Remaing Rows are the X Axis and the Z Axis
        else:
            ## The First column is the X Axis Data
            XData.append(reportData[:1][0])
            ## remove any Empty Z values Not record as Zero
            ZDatarow=[float(i) if i.strip() else 0. for i in reportData[1:].tolist()]
            ## Change the Values to Strings for easier processing
            ZDatarow=[str(ZDatarow) for ZDatarow in ZDatarow]
            ## Save the Z Axis Data
            ZData.append(ZDatarow)
        ## Increment the Datacount so that we can get the Y data
        dataCount += 1	
    ## Create the Full Report Matrix
    for xcount, xvalue in enumerate(XData):
        for ycount, yvalue in enumerate(YData):
            reportMatrix.append([xvalue, YData[ycount], ZData[xcount][ycount]])
    Variables=[]
    Traces=LineUp(reportMatrix)    
    Variables.append(Traces)
    Variables.append(XData)
    Variables.append(YData)
    Variables.append(ZData)
    return Variables
## End of reportTrace

## Begin LineUp
def LineUp(reportMatrix):
    data=[]
    prevRow=[]
    Traces=[]
    trace=[]
    for row in reportMatrix:
        ## Setup The Trace Array 
        if not prevRow:
            pass
        elif prevRow != row[0]:
            ## New X detected, save the old one
            Traces.append(trace)            
        ## New Row Detected, Start new Trace to save to the Trace Array
        if prevRow != row[0]:
            trace=[]
            trace.append(row)
        else:
            ## Existing Row Detected, Keep in same loop
            trace.append(row)
        prevRow=row[0]
    Traces.append(trace)
    return Traces        
### End of LineUp Function

## Begin of ReportData Function
def ReportData(file):
    ## Open the Excel Spreadsheet
    if not args.mute:
        print()
        print("Working on File: ", file)
    workbook=xlrd.open_workbook(file, encoding_override='cp1252')

    ## Use the first Index (because IOZone doesn't give us any others that I know of)
    sheet = workbook.sheet_by_index(0)

    ## Each Report Header Contains the Word Report
    reportString="Report"  
    reportCount = 0
    rowsinreportCount = 0
    reports = []
    report = []
    PlotTitles=[]

    ## Seperate out each Report
    for i in range(3,sheet.nrows):
       npArray = np.array(sheet.row_values(i)).astype(str)
       if reportString in npArray[0]:
           PlotTitles.append(npArray[0])
           if not len(report) == 0:
               reports.append(report)
           report = []
           report.append(npArray[0])
           reportCount += 1
           rowsinreportCount = 0          
       else:
          report.append(npArray)
          rowsinreportCount += 1
    reports.append(report)

    ## Mute if unwanted
    if not args.mute:
        print()
        print("There are: ",reportCount," Reports")
        print()
    Variables=[]
    Variables.append(reports)
    Variables.append(reportCount)
    Variables.append(PlotTitles)
    return Variables
## End Report Data Function

## Begin Figures Function
def figures(reports,reportCount,PlotTitles):
    Reports = []
    ## Loop Through all reports and turn them into Traces
    rcount=0
    zMax=0
    zMin=0
    rData=[]
    rDataset=[]
    for report in reports:
        rcount+=1
        rData=reportTrace(report)
        rDataset.append(rData)
        LineTraces=[]

        ## For Each Line Trace, pass it to the Graphing function Trace
        for line in rData[0]:
            LineTraces.append(Trace(cfg['plot']['color'],line))
            for lineD in line:
                if  float(lineD[2]) > zMax:
                    zMax=float(lineD[2])
        Reports.append(LineTraces)
    Variables=[]
    zRange=[]
    zRange.append(zMin)
    zRange.append(zMax)
    Variables.append(reportCount)
    Variables.append(Reports)
    Variables.append(rData)
    Variables.append(PlotTitles)
    Variables.append(rDataset)
    Variables.append(zRange)
    return Variables
## End figures Function

## Begin graphReports Function
def graphReports(reportCount,Reports,rData,PlotTitles,Range):
    if not args.mute:
        print("Generating graph")

    Annot=[]
    ### Setup up the Canvas
    ## Set up the Camera
    camera = dict(
        up=dict(
                x=cfg['plot']['camera']['up']['X'],
                y=cfg['plot']['camera']['up']['Y'],
                z=cfg['plot']['camera']['up']['Z']
                ),
        center=dict(
                x=cfg['plot']['camera']['center']['X'],
                y=cfg['plot']['camera']['center']['Y'],
                z=cfg['plot']['camera']['center']['Z']),
        eye=dict(
                x=cfg['plot']['camera']['eye']['X'],
                y=cfg['plot']['camera']['eye']['Y'],
                z=cfg['plot']['camera']['eye']['Z']
                )
    )
    
    ## Specify the Scene type for each Trace
    spectale=[]
    scenestuff=[{'type': 'scatter3d'}]
    for i in range(reportCount):
        spectale.append(scenestuff)

    ## Configure to Figure to use the Layout Defined above
    if not args.verbose:
        fig = make_subplots( rows=reportCount, 
                        subplot_titles=(PlotTitles),
                        start_cell=cfg['plot']['startcell'],
                        horizontal_spacing = cfg['plot']['spacing']['horizontal'],
                        vertical_spacing = cfg['plot']['spacing']['vertical'],
                        shared_xaxes=cfg['plot']['shared_xaxes'],
                        shared_yaxes=cfg['plot']['shared_yaxes'],
                        specs=spectale
                        )
    else:     
        fig = make_subplots( rows=reportCount, 
                        subplot_titles=(PlotTitles),
                        start_cell=cfg['plot']['startcell'],
                        horizontal_spacing = cfg['plot']['spacing']['horizontal'],
                        vertical_spacing = cfg['plot']['spacing']['vertical'],
                        shared_xaxes=cfg['plot']['shared_xaxes'],
                        shared_yaxes=cfg['plot']['shared_xaxes'],
                        print_grid=True,
                        specs=spectale
                        )
    
    ##Setup the Layout
    if args.verbose:
        pprint(PlotTitles) 
    fig.update_layout(
                     margin=dict(
                                 l=cfg['plot']['margin']['l'],
                                 r=cfg['plot']['margin']['r'],
                                 t=cfg['plot']['margin']['t'],
                                 b=cfg['plot']['margin']['b'],
                                 pad=cfg['plot']['margin']['pad']
                                ),
                     height = cfg['plot']['height']*reportCount,
                     title = {
                         'text': cfg['plot']['title']['text'],
                         'y': cfg['plot']['title']['X'],
                         'x': cfg['plot']['title']['Y'],
                         'xanchor': cfg['plot']['title']['XANCHOR'],
                         'yanchor': cfg['plot']['title']['YANCHOR']},
                     showlegend=cfg['plot']['legend']['show'],
                     #legend=dict(traceorder="reversed"),
                     paper_bgcolor = cfg['plot']['paper']['COLOR']
                     )

    ##For each report, for each line in it's set of Traces, add the figure to the plot
    rscount=0
    for subReports in Reports:   
       rscount += 1
       for lineTraces in subReports:
            fig.add_trace(lineTraces,row=rscount, col=1)
        
    ## Setup The Scenes
    fig.update_scenes(            camera = camera,
                                  xaxis=dict(
                                             title=cfg['plot']['sector']['Title']['X'],
                                             type=cfg['plot']['lines']['type']['X'],
                                             zeroline=cfg['plot']['zeroline']['X'],
                                             autorange=cfg['plot']['lines']['autorange']['X'],
                                             zerolinecolor=cfg['plot']['zeroline']['COLOR']['X'],
                                             zerolinewidth=cfg['plot']['zeroline']['width']['X'],
                                             tickmode = 'array',
                                             tickvals = rData[1],
                                             ticktext = rData[1],
                                             showline=cfg['plot']['lines']['show']['X'],
                                             linewidth=cfg['plot']['lines']['width']['X'],
                                             linecolor=cfg['plot']['lines']['COLOR']['X'],
                                             ticks = cfg['plot']['tick']['ticks']['X'],
                                             showgrid = cfg['plot']['tick']['showgrid']['X'],
                                             tickprefix = cfg['plot']['tick']['prefix']['X'],
                                             tickcolor = cfg['plot']['tick']['COLOR']['X'],    
                                             tickwidth = cfg['plot']['tick']['width']['X'],
                                             ticklen = cfg['plot']['tick']['length']['X'],
                                             tickangle = cfg['plot']['tick']['angle']['X'],
                                             titlefont_color=cfg['plot']['sector']['COLOR']['X'],
                                             backgroundcolor=cfg['plot']['background']['COLOR']['X'],
                                             color=cfg['plot']['axis']['COLOR']['X'],
                                             gridcolor=cfg['plot']['grid']['COLOR']['X']
                                  ),
                                  yaxis=dict(
                                             title=cfg['plot']['sector']['Title']['Y'],
                                             type=cfg['plot']['lines']['type']['Y'],
                                             autorange=cfg['plot']['lines']['autorange']['Y'],
                                             zeroline=cfg['plot']['zeroline']['Y'],
                                             zerolinecolor=cfg['plot']['zeroline']['COLOR']['Y'],
                                             zerolinewidth=cfg['plot']['zeroline']['width']['Y'],
                                             tickmode = 'array',
                                             tickvals = rData[2],
                                             ticktext = rData[2],
                                             showline=cfg['plot']['lines']['show']['Y'],
                                             linewidth=cfg['plot']['lines']['width']['Y'],
                                             linecolor=cfg['plot']['lines']['COLOR']['Y'],
                                             ticks=cfg['plot']['tick']['ticks']['Y'],
                                             showgrid=cfg['plot']['tick']['showgrid']['Y'],
                                             tickprefix = cfg['plot']['tick']['prefix']['Y'],
                                             tickwidth = cfg['plot']['tick']['length']['Y'],
                                             tickcolor = cfg['plot']['tick']['COLOR']['Y'],                                              
                                             ticklen = cfg['plot']['tick']['width']['Y'],                                             
                                             tickangle = cfg['plot']['tick']['angle']['Y'],                                             
                                             titlefont_color=cfg['plot']['sector']['COLOR']['Y'],
                                             backgroundcolor=cfg['plot']['background']['COLOR']['Y'],
                                             color=cfg['plot']['axis']['COLOR']['Y'],
                                             gridcolor=cfg['plot']['grid']['COLOR']['Y']
                                   ),
                                  zaxis=dict(
                                             nticks=cfg['plot']['grid']['nticks']['Z'],
                                             tickformat="s3",
                                             autorange=cfg['plot']['lines']['autorange']['Z'],
                                             rangemode=cfg['plot']['lines']['rangemode']['Z'],
                                             showline=cfg['plot']['lines']['show']['Z'],
                                             linewidth=cfg['plot']['lines']['width']['Z'],
                                             linecolor=cfg['plot']['lines']['COLOR']['Z'],
                                             ticks=cfg['plot']['tick']['ticks']['Z'],
                                             showgrid=cfg['plot']['tick']['showgrid']['Z'],
                                             tickprefix = cfg['plot']['tick']['prefix']['Z'],
                                             tickcolor = cfg['plot']['tick']['COLOR']['Z'],    
                                             zeroline=cfg['plot']['zeroline']['Z'],
                                             zerolinecolor=cfg['plot']['zeroline']['COLOR']['Z'],
                                             zerolinewidth=cfg['plot']['zeroline']['width']['Z'],
                                             title=cfg['plot']['sector']['Title']['Z'],
                                             tickangle = cfg['plot']['tick']['angle']['Z'],                                             
                                             tickwidth = cfg['plot']['tick']['width']['Z'],
                                             ticklen = cfg['plot']['tick']['length']['Z'],
                                             titlefont_color=cfg['plot']['sector']['COLOR']['Z'],
                                             backgroundcolor=cfg['plot']['background']['COLOR']['Z'],
                                             color=cfg['plot']['axis']['COLOR']['Z'],
                                             gridcolor=cfg['plot']['grid']['COLOR']['Z'],
                                             range=[Range[0], Range[1]]
                                  ),
                     )
    return fig
## End graphReports Function

## Begin compare Function
def compare(figureData):
    ## Check if we need to Generate Figure Data to Compare against and Grab that data, assuming only one file
    comparativeData=[]   
    ## Grab the Report Data From the File
    if not args.mute:
        print("Pulling Comparative Data")

    compData=ReportData(args.compare)
    
  
    ## Save the Report data to ComparativeData and Generate it's Figures for later Graphing
    comparativeData.append(figures(compData[0],compData[1],compData[2]))  
    
    zipReports=zip(comparativeData[0][4],figureData[0][4])    


    ## use the rDataset from Figures function for both the current and the comparativedata
    zMax=0
    zMin=0
    allDifs=[]
    for zcompData,zRData  in zipReports:
        zcData=zcompData[3]
        zrData=zRData[3]
        xData=zRData[1]
        yData=zRData[2]
        zip_object = zip(zrData,zcData)
        differences=[]
        ## Zip up each row  and prepare to subtract it
        for compData,figData  in zip_object:                
            zobject=zip(compData,figData)
            difference=[]
            for c,f  in zobject:
                difference.append(float(c)-float(f))
                if  (float(c)-float(f) > zMax):
                    zMax=(float(c)-float(f))
                if  (float(c)-float(f)) < zMin:
                    zMin=(float(c)-float(f))
            differences.append(difference)
        allDifs.append(differences)
    zRange=[]
    zRange.append(zMin)
    zRange.append(zMax)
    allrX=[]
    Reports=[]

    for dif in allDifs:
        rX=[] 
        rDataset=[]
        rData=[]
        for xc, xv in enumerate(xData):   
            for yc, yv in enumerate(yData): 
                rX.append([ xv,  yData[yc], str(dif[xc][yc])])
        rData.append(LineUp(rX))
        rData.append(xData)
        rData.append(yData)
        rDataset.append(rData)
        LineTraces=[]
        ## For Each Line Trace, pass it to the Graphing function Trace
        for line in rData[0]:
            LineTraces.append(Trace(cfg['plot']['color'],line))
        Reports.append(LineTraces)
    Variables=[]
    Variables.append(figureData[0][0])
    Variables.append(Reports)
    Variables.append(rData)
    Variables.append(figureData[0][3])
    Variables.append(rDataset)
    Variables.append(zRange)
    return Variables
## End compare Function


## Begin average Function
def average(figureData):
    if not args.mute:
        print("Averaging Data")
    
    #zipReports=zip(comparativeData[0][4],figureData[0][4])    


    figDLenCount=len(figureData)
    zippedData=[]
    #for each averaging run
    zippedData=zip(figureData[0][4])
    zMax=0
    zMin=0
    
    oldrzcData=[]
    
    for x in range(0,figDLenCount):
        ## Print the rData for each Average, assuming three files
        rzcData=[]
        print("Run: ", x)
        if x == 0:
            for fadataCount,fadata in enumerate(figureData[0][4]):
                ## Get the Reports from the rData
                zcData=fadata[3] 
                oldrzcData.append(zcData)
        if x > 0:
            allDifs=[]
            for fadataCount,fadata in enumerate(figureData[x][4]):
                
                ## Get the Reports from the rData
                zcData=fadata[3] #
                rzcData.append(zcData) 
                xData=fadata[1]
                yData=fadata[2]                
            zip_object = zip(oldrzcData,rzcData)
            for compData,figData  in zip_object:
                zobject=zip(compData,figData)
                differences=[]
                for cd,fd in zobject:
                    rzobject=zip(cd,fd)
                    difference=[]
                    for c,f in rzobject:
                        difference.append((float(c) + float(f)) / 2 )
                        if  ((float(c) + float(f)) / 2) > zMax: zMax=((float(c) + float(f)) / 2)
                        if  ((float(c) + float(f)) / 2) < zMin: zMin=((float(c) + float(f)) / 2) 
                    differences.append(difference)
                allDifs.append(differences)
            oldrzcData=allDifs 
    zRange=[]
    zRange.append(zMin)
    zRange.append(zMax)
    allrX=[]
    Reports=[]
    
    for dif in allDifs:
        print(dif)
        rX=[] 
        rDataset=[]
        rData=[]
        for xc, xv in enumerate(xData):   
            for yc, yv in enumerate(yData): 
                rX.append([ xv,  yData[yc], str(dif[xc][yc])])
        rData.append(LineUp(rX))
        rData.append(xData)
        rData.append(yData)
        rDataset.append(rData)
        LineTraces=[]
        ## For Each Line Trace, pass it to the Graphing function Trace
        for line in rData[0]:
            LineTraces.append(Trace(cfg['plot']['color'],line))
        Reports.append(LineTraces)
    Variables=[]
    Variables.append(figureData[0][0])
    Variables.append(Reports)
    Variables.append(rData)
    Variables.append(figureData[0][3])
    Variables.append(rDataset)
    Variables.append(zRange)
    return Variables
## End average Function


## Begin Main
def main():
    ## Disable the Plotly Logo
    config = {'displaylogo': False} 
    
    loc=[]
    for x in range(0,averageRun):
        ## Generate or Gather XLS files
        loc.append(runIO(x))


    ## Generate a Figure for each File
    ffigureData=[]
    graphData=[]
    for file in loc:
        repData=ReportData(file)      
        ffigureData.append(figures(repData[0],repData[1],repData[2]))
    

    ## Check if we are doing an Average Calculation
    rCount = len(ffigureData)
    
    if rCount == averageRun:
        if rCount > 1:
            print("Detected Multiple Files, averaging each")
            ffigureData.append(average(ffigureData))
                
    

    
    
    ## Compare the Output with another
    if args.compare: 
        print()
        crepData=ReportData(args.compare)
        ## Create the Graph for the host we are comparing against
        ffigureData.append(figures(crepData[0],crepData[1],crepData[2]))
        ## Create the Graph for the Compared Data
        ffigureData.append(compare(ffigureData))
          
    ## Graph Each figure
    for figcount, figs in  enumerate(ffigureData):
        graphs=graphReports(figs[0],figs[1],figs[2],figs[3],figs[5])
        graphData.append(graphs)
        
    ## Write out the Visualization for each XLS file
    for graphcount, graph in  enumerate(graphData):
        htmloutputFile=""
        htmloutputFile=""
        htmloutputFile+=outputFile
        htmloutputFile+="-"
        htmloutputFile+=str(graphcount+1)
        htmloutputFile+=".html"      
        graph.write_html(htmloutputFile, config=config)           
## End Main

main()
