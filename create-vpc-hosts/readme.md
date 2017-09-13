Creates vPC hosts with switches, ports and policies.

Description: 
        Creates Leaf Interface Profile where provided does not exist. - Can be shared/contain N 'Access Port Selectors'
         A 'VPC Interface Policy Group' is created for the given single host. 
            - Policies cannot be shared between different hosts for PC/VPC
        Creates Access Port Selectors for given ports in a bundle and binds to a dedicated 'VPC Interface Policy Group'
        If switch Leaf Profile, Leaf Selectors do not exist for given switches - these are created.
     
        A leaf interface pofile [infraAccPortP] can be shared as long as the switches required are the same as 
        other host (policy) requirements.

        Switch Profiles ==> Interface Profiles ==>  Interface Selector ==> VPC Policy Group
             /\                                           \/
        Switch Selector                             Interface Block
             /\              
        Switch Block       

Notes: 
The ansible module is generic but some var names reflect VMware/ESXI. This was originally coded for a requirement to quickly add new VMware hosts by modifying the JSON file only. Specifics for VMware are in the playbook & json file where the AEP name suffix is named on the basis of the VMware DVS name. This could be easily changed to supply the full AEP name instead and change the param name from vcenter_dvs to aep_name. Again with the esxi_server_name var, this is only for the playbook and json file so could be changed to just server_name. The ansible module does not take /use these params. All other playbook references to ESXi in the value fields can be removed if require or change the HyperV for example.

The playbook provides the interface policies for CDp, LLDP,  MCP etc. These must exist and be valid in the playbook for the interface policy group to be valid. The ones in the playbook are provided in the aci_interface_policies.xml file but on production systems the playbook should be in sync with the exiwting policies if they exist.

Files: 
create-esxi-vpc-host.yml 
  - Ansible Playbook
  
create-esxi-vpc-host-params.json
  - Ansible Playbook Parameters in JSON Formay
	 
aci_vpc_policy_sw_int_setup.py
  - Ansible Module called by Playbook
  
aci_interface_policies.xml
  - Interface policies for Leaf Interface Policy Groups 
  
Use:
1. Save Ansible module in Ansible module directory (on Ubuntu the default would be /usr/lib/python2.7/dist-packages/ansible/modules/)
2. Adjust the json file for the static params for all hosts of this type - switch pairs/range, VMWare DVS (AEP Name), Leaf Interface Profile Name 
3. Adjust the json file for changes per host - server name (var named esxi-server-name but could be renamed) and the port ranges the server uses on all specified switches.
4. run the playbook as ansible-playbook create-esxi-vpc-host.yml --extra-vars "@create-esxi-vpc-host-params.json"

