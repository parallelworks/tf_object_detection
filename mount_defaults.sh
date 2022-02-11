#!/bin/bash

vcinity_nfs=/pw/storage/vcinity_nfs_aws
direct_nfs=/pw/storage/direct_nfs_azure
gcp_bucket=/pw/storage/demoworkflows_bucket

#######################
# --- Vcinity NFS --- #
#######################
# Make directory:
mkdir -p ${vcinity_nfs}
# Mount if empty
if [ -z "$(ls -A ${vcinity_nfs})" ]; then
   cmd="sudo mount -vvv -o sync,nolock,vers=4 54.241.247.242:/ultxvfs2 ${vcinity_nfs}"
   echo ${cmd}
   ${cmd}
fi

######################
# --- Direct NFS --- #
######################
# Make directory:
mkdir -p ${direct_nfs}
# Mount if empty
if [ -z "$(ls -A ${direct_nfs})" ]; then
    cmd="sudo mount -vvv -o sync,nolock,vers=4 40.71.67.138:/ultxvfs2 ${direct_nfs}"
    echo ${cmd}
    ${cmd}
fi

######################
# --- GCP Bucket --- #
######################
# Make directory:
mkdir -p ${gcp_bucket}
# Mount if empty
if [ -z "$(ls -A ${gcp_bucket})" ]; then
   cmd="gcsfuse --file-mode 777 --dir-mode 777 --implicit-dirs demoworkflows ${gcp_bucket}"
   echo ${cmd}
   ${cmd}
fi
