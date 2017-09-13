#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_vpc_policy_sw_int_setup

short_description: 
        Creates Leaf Interface Profile where provided does not exist. - Can be shared/contain N 'Access Port Selectors'
         A 'VPC Interface Policy Group' is created for the given single host. 
            - Policies cannot be shared between different hosts for PC/VPC
        Creates Access Port Selectors for given ports in a bundle and binds to a dedicated 'VPC Interface Policy Group'
        If switch Leaf Profile, Leaf Selectors do not exist for given switches - these are created.
       
 


description:

        A leaf interface pofile [infraAccPortP] can be shared as long as the switches required are the same as 
        other host (policy) requirements.

        Switch Profiles ==> Interface Profiles ==>  Interface Selector ==> VPC Policy Group
             /\                                           \/
        Switch Selector                             Interface Block
             /\              
        Switch Block       

version_added: "2.3.2.0"

author: Simon Birtles (@simonbirtles)

requirements: ACI Version >=2.0

notes:

options:

    interface_profile_name
        description: Generic Interface Policy For VMware ESXi Hosts where same switches are used for selected ports for these ESXi hosts

    interface_profile_description
        description: description

    access_port_selector_name
        description: Specific ESXi Host Interface Selector Policy Name

    access_port_selector_description
        description: Specific ESXi Host Interface Selector Policy Desc

    access_port_selector_type=
        description: Does this Access Interface/Port Selector specify a range of ports or ALL ports on the switches
        choices: [ range, ALL ]
        default: range

    access_policy_group_name
        description: The Access Policy Group name. For PC/VPC configurations, this is per Host (ESXi in this case)

    access_policy_group_fexid
        description: The FEX ID, set to 101, no need to modify, but available for future.
        default: 101



    port_block_from_card
        description: Port Range - Chassis Card Number Start In Range

    port_block_from_port
        description: Port Range - Chassis Port Number Start In Range

    port_block_to_card
        description: Port Range - Chassis Card Number End In Range

    port_block_to_port
        description: Port Range - Chassis Port Number End In Range



    switch_profile_name
        description: Switch Leaf Profile Name 

    switch_selector_name
        description: Switch Leaf Selector Name

    switch_selector_type
        description: Does this Switch Selector specify a range of switches or ALL switches
        choices: [ range, ALL ]
        default: range

    switch_block_from
        description: Switch Port Range Start Switch Node ID

    switch_block_to
        description: Switch Port Range End Switch Node ID



    infraRsLacpPol
        description: Interface LACP Policy Name

    infraRsHIfPol
        description: Interface Link Negotiation Policy Name

    infraRsCdpIfPol
        description: Interface CDP Policy Name

    infraRsMcpIfPol
        description: Interface Mis-cabling Protocol (MCP) Name

    infraRsLldpIfPol
        description: Interface LLDP Policy Name

    infraRsStpIfPol
        description: Interface STP Policy Name

    infraRsStormctrlIfPol
        description: Interface Traffic Storm Control (Traffic Suppression) Policy Name 

    infraRsL2IfPol
        description: Interface VLAN Scope (Global/PortLocal) Policy Name

    infraRsL2PortSecurityPol
        description: Interface Port Security Policy Name

    infraRsQosDppIfPol
        description: Unused 

    infraRsQosEgressDppIfPol
        description: Egress Data Plane Policing Policy Name

    infraRsQosIngressDppIfPol
        description: Ingress Data Plane Policing Policy Name

    infraRsMonIfInfraPol
        description: Monitoring Policy Name

    infraRsFcIfPol
        description: 
        Fibre Channel Interface Policy Name
        A Fibre Channel interface policy specifies whether the interface to which 
        this policy is applied is enabled to function as an FCoE F port or as an NP port.

    infraRsQosPfcIfPol
        description: 
        Fibre Channel Interface Priority Flow Control Policy name. 
        Specifies whether the state of priority flow control on an associated FCoE-enabled interface is 
        on, off, or determined by configuration of a DCBX and peer negotiation success.

    infraRsQosSdIfPol  
        description: 
        Fibre Channel Interface Slow Drain Policy Name. 
        The Policy is for handling FCoE packets that are causing traffic congestion on the ACI fabric

    infraRsAttEntP
        description: Name of the AEP (Attachable Entity Endpoint) Policy.

'''

EXAMPLES = r'''

'''

RETURN = r''' # '''

from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import AnsibleModule


class CiscoAPIC(object):

    def __init__(self, mod):
        self.mod = mod
        self.params = mod.params
        self.request = dict()
        self.result = dict()
        self.headers = None
        self.apicLogin()

    ###
    # 
    ###
    def apicLogin(self):

        # basic login body    
        bodyJson = {'aaaUser': {'attributes': {'name': self.params['username'], 'pwd': self.params['password']}}}
        
        url = ""
        if self.params.get('use_ssl', True):
            url = 'https://%(hostname)s/api/aaaLogin.json' % self.params
        else:
            url = 'http://%(hostname)s/api/aaaLogin.json' % self.params
        
        # login
        resp, info = fetch_url(self.mod, 
                            url,
                            data=json.dumps(bodyJson),
                            headers=None,
                            method='POST',
                            use_proxy=self.params['use_proxy'],
                            force=False, 
                            last_mod_time=None,
                            timeout=self.params['timeout'])        
       
        if info['status'] != 200:
                self.mod.fail_json(msg='Login failed for %(url)s. %(msg)s' % info)

        self.headers = dict(Cookie=resp.headers['Set-Cookie'])
        self.result['loginResult'] = json.loads(resp.read())

    ####
    # 
    ####
    def apicPost(self):
       
       # POST body to URL
        resp, info = fetch_url(self.mod, 
                            self.request['url'],
                            data=json.dumps(  self.request['jsonPayload'] ),
                            headers=self.headers,
                            method="POST",
                            use_proxy=self.params['use_proxy'],
                            force=False, 
                            last_mod_time=None,
                            timeout=self.params['timeout'])

        if info['status'] != 200:
                self.mod.fail_json(
                        msg='apicPost failed for %(url)s. %(msg)s %(body)s' % info, 
                        msgbody='Message Body: %(body)s' % info, 
                        #payload=self.request['jsonPayload']
                        )

        self.result['postResult'] = json.loads(resp.read())


    ###
    # Creates a Leaf Interface Profile [infraAccPortP] with selected ports
    # and binds to a Specific Interface Policy Group [infraAccBndlGrp]
    ###
    def createInterfaceProfile(self):

        # accportgrp-XXXXX (for Single Port)  accbundle-XXXXX (for PC/VPC)

        infraRsAccBaseGrp = { 
            "attributes"    :   {
                "tDn"   :   "uni/infra/funcprof/accbundle-"+self.params['access_policy_group_name'],
                "fexId" :   str(self.params['access_policy_group_fexid'])
            }
        }

        infraPortBlk =  { 
            "attributes"    :   { 
                "name"        : 'portBlock1', 
                "descr"       : "",
                "fromPort"    : str(self.params['port_block_from_port']),
                "fromCard"    : str(self.params['port_block_from_card']),
                "toPort"      : str(self.params['port_block_to_port']),
                "toCard"      : str(self.params['port_block_to_card'])  
            }
        }

        infraHPortS =  { 
            "attributes"    :   { 
                "name"  :   self.params['access_port_selector_name'], 
                "descr" :   self.params['access_port_selector_description']  ,
                "type"  :   self.params['access_port_selector_type']  
            },
            "children" : [
                {"infraRsAccBaseGrp" : infraRsAccBaseGrp},
                {"infraPortBlk"  :   infraPortBlk}
            ]
        }

        infraAccPortP =  { 
            "attributes"    :   { 
                "name"  :   self.params['interface_profile_name'],
                "descr" :   self.params['interface_profile_description']
            },
            "children" : [{
                "infraHPortS"   :   infraHPortS
            }]
        }

        infraInfra = {
            "attributes": {},
            "children" : [{
                "infraAccPortP" :   infraAccPortP
            }]
        }

        polUni = {
            "attributes": {},
            "children" : [{
                "infraInfra"    :   infraInfra
            }]
        }

        payload = {
                "polUni"    :   polUni
        }

        self.request['url'] = 'https://%(hostname)s/api/mo.json' % self.params
        self.request['jsonPayload'] = payload 

    ####
    # Creates a VPC Policy Group [infraAccBndlGrp] and 
    # binds to an AEP [infraAttEntityP]
    ####
    def createPolicyGroup(self):

        #-- Port Policy --
        infraRsLacpPol =            { "attributes" : { "tnLacpLagPolName"           : self.params['infraRsLacpPol'] }}
        infraRsHIfPol =             { "attributes" : { "tnFabricHIfPolName"         : self.params['infraRsHIfPol'] } }
        infraRsCdpIfPol =           { "attributes" : { "tnCdpIfPolName"             : self.params['infraRsCdpIfPol'] } }
        infraRsMcpIfPol =           { "attributes" : { "tnMcpIfPolName"             : self.params['infraRsMcpIfPol'] } }
        infraRsLldpIfPol =          { "attributes" : { "tnLldpIfPolName"            : self.params['infraRsLldpIfPol'] } }
        infraRsStpIfPol =           { "attributes" : { "tnStpIfPolName"             : self.params['infraRsStpIfPol'] } }
        infraRsStormctrlIfPol =     { "attributes" : { "tnStormctrlIfPolName"       : self.params['infraRsStormctrlIfPol'] } }
        infraRsL2IfPol =            { "attributes" : { "tnL2IfPolName"              : self.params['infraRsL2IfPol'] } }
        infraRsL2PortSecurityPol =  { "attributes" : { "tnL2PortSecurityPolName"    : self.params['infraRsL2PortSecurityPol'] } }        
        #-- Data Plane Policy --
        infraRsQosDppIfPol =        { "attributes" : { "tnQosDppPolName"            : self.params['infraRsQosDppIfPol'] } }
        infraRsQosEgressDppIfPol =  { "attributes" : { "tnQosDppPolName"            : self.params['infraRsQosEgressDppIfPol'] } }
        infraRsQosIngressDppIfPol = { "attributes" : { "tnQosDppPolName"            : self.params['infraRsQosIngressDppIfPol'] } }        
        #-- Monitoring Policy --
        infraRsMonIfInfraPol =      { "attributes" : { "tnMonInfraPolName"          : self.params['infraRsMonIfInfraPol'] } }        
        #-- Fibre Channel - FCOE --
        infraRsFcIfPol =            { "attributes" : { "tnFcIfPolName"              : self.params['infraRsFcIfPol'] } }
        infraRsQosPfcIfPol =        { "attributes" : { "tnQosPfcIfPolName"          : self.params['infraRsQosPfcIfPol'] } }
        infraRsQosSdIfPol =         { "attributes" : { "tnQosSdIfPolName"           : self.params['infraRsQosSdIfPol'] } }        
        #-- AEP --
        infraRsAttEntP =            { "attributes" : { "tDn"                        : self.params['infraRsAttEntP'] } }

        #build VPC/PC policy  - note using infraAccBndlGrp, NOT infraAccPortGrp for single port
        infraAccBndlGrp = {
                "attributes" : {
                    "name"  : self.params['access_policy_group_name'],
                    "descr" : "",
                    "lagT"  : "node"
                },
                "children" : [ 
                    {"infraRsLacpPol"           : infraRsLacpPol},
                    {"infraRsHIfPol"            : infraRsHIfPol},
                    {"infraRsCdpIfPol"          : infraRsCdpIfPol},
                    {"infraRsMcpIfPol"          : infraRsMcpIfPol},
                    {"infraRsLldpIfPol"         : infraRsLldpIfPol},
                    {"infraRsStpIfPol"          : infraRsStpIfPol},
                    {"infraRsStormctrlIfPol"    : infraRsStormctrlIfPol},
                    {"infraRsL2IfPol"           : infraRsL2IfPol},
                    {"infraRsL2PortSecurityPol" : infraRsL2PortSecurityPol},
                    {"infraRsQosDppIfPol"       : infraRsQosDppIfPol},
                    {"infraRsQosEgressDppIfPol" : infraRsQosEgressDppIfPol},
                    {"infraRsQosIngressDppIfPol": infraRsQosIngressDppIfPol},
                    {"infraRsMonIfInfraPol"     : infraRsMonIfInfraPol},
                    {"infraRsFcIfPol"           : infraRsFcIfPol},
                    {"infraRsQosPfcIfPol"       : infraRsQosPfcIfPol},
                    {"infraRsQosSdIfPol"        : infraRsQosSdIfPol},                    
                    {"infraRsAttEntP"           : infraRsAttEntP}         
                ]
                }

        infraFuncP = {
                "attributes": {},
                "children" : [{
                    "infraAccBndlGrp" : infraAccBndlGrp
                }]
            }

        infraInfra = {
            "attributes": {},
            "children" : [{
                "infraFuncP" :  infraFuncP
            }]
        }

        polUni = {
            "attributes": {},
            "children" : [{
                "infraInfra" :  infraInfra
            }]
        }

        payload = {
                "polUni" :  polUni
        }

        self.request['url'] = 'https://%(hostname)s/api/mo.json' % self.params
        self.request['jsonPayload'] = payload 

    ####
    # Creates a switch profile and binds switches (leaf selector)
    # infraNodeP =>> infraLeafS =>> infraNodeBlk
    ####
    def createSwitchProfile(self):
        
        infraNodeBlk = {
            "attributes": {
                "name"  : "SW-BLK-S" + self.params['switch_block_from'] + "-S" + self.params['switch_block_to'],
                "descr" : "",
                "from_" : self.params['switch_block_from'],
                "to_"   : self.params['switch_block_to']
            }
        }

        infraLeafS = {
            "attributes": {
                "name" : self.params['switch_selector_name'],
                "type" : self.params['switch_selector_type'],
                "descr" : ""
            },
            "children" : [{
                "infraNodeBlk"      :   infraNodeBlk
            }]
        }

        infraNodeP = {
            "attributes": {
                "name" : self.params['switch_profile_name'],
                "descr" : ""
            },
            "children" : [
                {"infraLeafS" : infraLeafS},
                {"infraRsAccPortP" : {"attributes": {  "tDn" : "uni/infra/accportprof-"+self.params['interface_profile_name']  } } }
            ]
        }

        infraInfra = {
            "attributes": {},
            "children" : [{
                "infraNodeP" : infraNodeP
            }]
        }

        polUni = {
            "attributes": {},
            "children" : [{
                "infraInfra" : infraInfra
            }]
        }

        payload = {
                "polUni" : polUni
        }

        self.request['url'] = 'https://%(hostname)s/api/mo.json' % self.params
        self.request['jsonPayload'] = payload 




###
#
###
def main():
    argument_spec = dict(
        # Login Params
        hostname=dict(type='str', required=True, aliases=['host']),
        username=dict(type='str', default='admin', aliases=['user']),
        password=dict(type='str', required=True, no_log=True),
        timeout=dict(type='int', default=30),
        use_proxy=dict(type='bool', default=True),
        use_ssl=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
        # Config Params
        interface_profile_name=dict(type='str', required=True),
        interface_profile_description=dict(type='str', required=False),
        access_port_selector_name=dict(type='str', required=True),
        access_port_selector_description=dict(type='str', required=False),
        access_port_selector_type=dict(choices=['ALL', 'range'], type='str', default='range'),
        access_policy_group_name=dict(type='str', required=True),
        access_policy_group_fexid=dict(type='int', default=101),
        # ports
        port_block_from_card=dict(type='int'),
        port_block_from_port=dict(type='int'),
        port_block_to_card=dict(type='int'),
        port_block_to_port=dict(type='int'),
        # switches / switch profile
        switch_profile_name=dict(type='str', required=True),
        switch_selector_name=dict(type='str', required=True),
        switch_selector_type=dict(choices=['ALL', 'range'], type='str', default='range'),
        switch_block_from=dict(type='str', required=True),
        switch_block_to=dict(type='str', required=True),
        # policy group
        infraRsLacpPol=dict(type='str', default='default'),
        infraRsHIfPol=dict(type='str', default='default'),
        infraRsCdpIfPol=dict(type='str', default='default'),
        infraRsMcpIfPol=dict(type='str', default='default'),
        infraRsLldpIfPol=dict(type='str', default='default'),
        infraRsStpIfPol=dict(type='str', default='default'),
        infraRsStormctrlIfPol=dict(type='str', default='default'),
        infraRsL2IfPol=dict(type='str', default='default'),
        infraRsL2PortSecurityPol=dict(type='str', default='default'),
        infraRsQosDppIfPol=dict(type='str', default='default'),
        infraRsQosEgressDppIfPol=dict(type='str', default='default'),
        infraRsQosIngressDppIfPol=dict(type='str', default='default'),
        infraRsMonIfInfraPol=dict(type='str', default='default'),
        infraRsFcIfPol=dict(type='str', default='default'),
        infraRsQosPfcIfPol=dict(type='str', default='default'),
        infraRsQosSdIfPol=dict(type='str', default='default'),              
        infraRsAttEntP=dict(type='str', default='default')
    )

    mod = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[ 
                        ['access_port_selector_type', 'range', 
                            ['port_block_from_card', 
                             'port_block_from_port',
                             'port_block_to_card', 
                             'port_block_to_port' ]],

                         ['switch_selector_type', 'range', 
                            ['switch_block_from', 
                             'switch_block_to']]
                    ]
    )

    # kick off and login to APIC
    apic = CiscoAPIC(mod)
    # create the Interface Policy Group and bind to AEP
    apic.createPolicyGroup()
    # commit
    apic.apicPost()
    # create the Interface Profile with selected ports
    apic.createInterfaceProfile()
    # commit
    apic.apicPost()
    # create the Switch Profile with selected switches and bind to Interface Profile
    apic.createSwitchProfile()
    # commit
    apic.apicPost()


    # Exit 
    mod.exit_json(changed = True, result = apic.result)


#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
if __name__ == "__main__":
    main()
