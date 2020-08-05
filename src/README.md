# Overview

[Keystone][keystone-upstream] is the identity service used by OpenStack for
authentication and high-level authorisation.

The keystone-kerberos subordinate charm allows for per-domain authentication
via a Kerberos ticket, thereby providing an additional layer of security. It is
used in conjunction with the [keystone][keystone-charm] charm.

An external Kerberos server is a prerequisite.

> **Note**: The keystone-kerberos charm is supported starting with OpenStack
  Queens.

> **Warning**: This charm is in a preview state and should not be used in
  production. See the [OpenStack Charm Guide][cg-preview-charms] for more
  information on preview charms.

# Usage

# Configuration

This section covers common and/or important configuration options. See file
`config.yaml` for the full list of options, along with their descriptions and
default values. See the [Juju documentation][juju-docs-config-apps] for details
on configuring applications.

#### `kerberos-realm`

The `kerberos-realm` option is used to supply the external Kerberos realm name.

#### `kerberos-server`

The `kerberos-server` option is used to supply the external Kerberos server
hostname.

#### `kerberos-domain`

The `kerberos-domain` option is the OpenStack domain against which Kerberos
authentication should be used.

## Deployment

Let file ``kerberos.yaml`` contain the deployment configuration:

```yaml
    keystone-kerberos:
        kerberos-realm: "PROJECT.SERVERSTACK"
        kerberos-server: "freeipa.project.serverstack"
        kerberos-domain: "k8s"
```

Deploy keystone-kerberos with other essential applications:

    juju deploy keystone
    juju deploy openstack-dashboard
    juju deploy --config kerberos.yaml --resource=/home/ubuntu/keystone.keytab keystone-kerberos
    juju add-relation keystone openstack-dashboard
    juju add-relation keystone keystone-kerberos

See the next section for retrieving the keytab file. It can also be added to
the application post-deploy:

    juju attach-resource keystone-kerberos keystone_keytab=keystone.keytab

## Kerberos pre-requisites - the Keystone service keytab

In an external Kerberos server, a service must be created for the Keystone
Principal.

1. First determine the FQDN of the Keystone server. For example:

       keystone-server.project.serverstack

   Ensure that the Keystone server can resolve the Kerberos server hostname. If
   it can't, consider adding an entry to `/etc/hosts`.

1. In the Kerberos server, create the host and service. This example is based
   on a FreeIPA Kerberos server:

       ipa host-add keystone-server.project.serverstack --ip-adress=10.0.0.2
       ipa service-add HTTP/keystone-server.project.serverstack
       ipa service-add-host HTTP/keystone-server.project.serverstack --hosts=keystone-server.project.serverstack

   If you have multiple Keystone servers, you should add each host to the
   principal:

       ipa host-add-principal keystone-server HTTP/<keystone-other-hostname>@PROJECT.SERVERSTACK

1. Retrieve the keytab associated with this service:

       ipa-getkeytab -p HTTP/keystone-server.project.serverstack -k keystone.keytab

## Authenticate from a host

The below steps show how to authenticate from a host using the `openstack` CLI
client.

1. Ensure that the following software is installed on the host:

       sudo apt install krb5-user python3-openstackclient python3-requests-kerberos

1. Retrieve a token for an existing user in the Kerberos/LDAP directory.

       kinit <username>

1. Source the OpenStack rc file.

       source k8s-user.rc

   Where the contents of `k8s-user.rc` is:

       export OS_AUTH_URL=http://kerberos-server.project.serverstack:5000/krb/v3
       export OS_PROJECT_ID=<projectID>
       export OS_PROJECT_NAME=<kerberos_domain> # i.e k8s
       export OS_PROJECT_DOMAIN_ID=<domainID>
       export OS_REGION_NAME="RegionOne"
       export OS_INTERFACE=public
       export OS_IDENTITY_API_VERSION=3
       export OS_AUTH_TYPE=v3kerberos

1. Test the client

       openstack token issue

# Bugs

Please report bugs on [Launchpad][lp-bugs-charm-keystone-kerberos].

For general charm questions refer to the [OpenStack Charm Guide][cg].

<!-- LINKS -->

[cg]: https://docs.openstack.org/charm-guide
[keystone-charm]: https://jaas.ai/keystone
[keystone-upstream]: https://docs.openstack.org/keystone/latest/
[cg-preview-charms]: https://docs.openstack.org/charm-guide/latest/openstack-charms.html#tech-preview-charms-beta
[lp-bugs-charm-keystone-kerberos]: https://bugs.launchpad.net/charm-keystone-kerberos/+filebug
[juju-docs-config-apps]: https://juju.is/docs/configuring-applications
