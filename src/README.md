# keystone-kerberos

This subordinate charm provides a way to authenticate in Openstack for 
a specific domain with a Kerberos ticket. This provides an additional 
security layer. An external Kerberos server is necessary.

The following documentation is useful to understand better the charm 
implementation:

* https://www.objectif-libre.com/fr/blog/2018/02/26/kerberos-authentication-for-keystone/ 
* https://jaosorior.dev/2018/keberos-for-keystone-with-mod_auth_gssapi/


# Usage

Use this charm with the Keystone and Keystone-LDAP charms:
    
    juju deploy keystone
    juju deploy keystone-ldap
    juju deploy openstack-dashboard
    juju deploy keystone-kerberos
    juju add-relation keystone keystone-ldap
    juju add-relation keystone openstack-dashboard
    juju add-relation keystone keystone-kerberos
    
In a bundle:

```
    applications
    # ...
      keystone-kerberos:
        charm: ../../../keystone-kerberos
        num_units: 0
        options:
          kerberos-realm: "PROJECT.SERVERSTACK"
          kerberos-server: "freeipa.project.serverstack"
          kerberos-domain: "k8s"
        resources:
          keystone_keytab: "/home/ubuntu/keystone.keytab"
      relations:
      # ...
      - - keystone
        - keystone-kerberos
```

# Prerequisites

To authenticate against Keystone and Kerberos from a host, the following 
librairies need to be installed :
- sudo apt install krb5-user gcc python-dev libkrb5-dev python-pip
- pip install keystoneauth1[kerberos]

# Configuration

In the Kerberos server, a service must be created for the Keystone Principal. 
For example, first find the hostname of the keystone server :

    ubuntu@keystone-server$ hostname -f
    keystone-server.project.serverstack

Note 1 : make sure that your keystone server can resolve the Kerberos server 
hostname. If if can't, consider adding an entry to /etc/hosts. 

Then, in the Kerberos server, create the host and service (this example is 
based on a FreeIPA Kerberos Server):

    ipa host-add keystone-server.project.serverstack --ip-adress=10.0.0.2
    ipa service-add HTTP/keystone-server.project.serverstack
    ipa service-add-host HTTP/keystone-server.project.serverstack --hosts=keystone-server.project.serverstack

Note 2 : If you have multiple keystone servers, you should add each host to 
the principal with the command 

    ipa host-add-principal keystone-server HTTP/<keystone-other-hostname>@PROJECT.SERVERSTACK

Retrieve the keytab associated with this service:
    
    ipa-getkeytab -p HTTP/keystone-server.project.serverstack -k keystone.keytab
    
This is the keytab needed in the resources of the keystone-kerberos charm. If 
you retrieved it post-deploy, you can attach it with a command to keystone:

    juju attach-resource keystone-kerberos/0 keystone_keytab=new_keytab.keytab

# Authentication from a host

To use the Openstack cli, two steps are required. 
1) Retrieve a token for an existing user in the Kerberos/LDAP directory:
```
    kinit <username>
```
2) Source the openstack rc file with the correct information:
```
    cat k8s-user.rc
    export OS_AUTH_URL=http://kerberos-server.project.serverstack:5000/krb/v3
    export OS_PROJECT_ID=<projectID>
    export OS_PROJECT_NAME=<kerberos_domain> # i.e k8s
    export OS_PROJECT_DOMAIN_ID=<domainID>
    export OS_REGION_NAME="RegionOne"
    export OS_INTERFACE=public
    export OS_IDENTITY_API_VERSION=3
    export OS_AUTH_TYPE=v3kerberos

    source k8s-user.rc
    openstack token issue
```

# Bugs
Please report bugs on [Launchpad](link missing).

For general questions please refer to the OpenStack [Charm Guide](https://docs.openstack.org/charm-guide/latest/).