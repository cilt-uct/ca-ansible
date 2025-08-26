# Capture Agent Ansible Playbooks

Deployment and update scripts for Galicaster, LectureSight, FFMpeg, VNC, DataPath, and other requirements onto a specified Capture Agent.

## Structure

The folder contains a ansible playbookk in the tasks folder.

| Name | Description| 
|----------|--------|
| playbook.yml | The main playbook to run the install for a CApture Agent |
| tasks/main.yml | Defines the standard task to be run |
| vars/main.yml | Defines the default variables used to install the required items |
| hosts | Define the DNS name of the capture agents |

## Run

Run the playbook for all capture agents:
```
ansible-playbook playbook.yml --limit ecolt1-ca 
```
Limit it to a single capture agent:
```
ansible-playbook playbook.yml --limit ecolt1-ca 
```
To check requirements before running a deploy/update:
```
ansible-playbook playbook.yml --check 
```

