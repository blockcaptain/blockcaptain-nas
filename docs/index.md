# paranoidNAS

paranoidNAS is not a Linux distribution. After installation you will have a near-stock 
Ubuntu Server 20.04 installation.

## Principles

We are absolutely paranoid about data loss. The chance of data loss should be virtually 0%. Everything threat that can be mitigated should be: e.g. silent data corruption ([bitrot](https://en.wikipedia.org/wiki/Data_degradation)), malicious data corruption, complete failure of 1, 2 or all physical disks, an unrecoverable data bug in the cloud backup tool, or forgetting to pay the bill on your cloud storage!

paranoidNAS does not strive to be an appliance. Some things are automated, but very little effort
is made to hide or "abstract away" the system. There will never be web interface. The interface is the CLI via SSH. 

The data integrity components of the system (disk layout, filesystems, backup tools) are highly opinionated. Outside of that,
you can do whatever you want, because it's just a Linux server.

The system must be low maintenance and run securely for many years. [Ubuntu 20.04](https://ubuntu.com/about/release-cycle) will receive security updates
via [ESM](https://ubuntu.com/esm) until April 2030. ESM is available [free for personal use](https://ubuntu.com/advantage) or for a nominal fee for commerical use. 
Ubuntu also has kernel [Livepatch Service](https://ubuntu.com/livepatch) to address security issues without reboots, also free for personal use.

### Why use paranoidNAS?

You agree with the principles above. You enjoy learning and using Linux. You want a general purpose server to easily run VMs and/or containers. 
You want to have a deep understanding and closeness to the software that is protecting your precious data.

### Why not use paranoidNAS?

You don't want to use Ubuntu[^1]. You want to use ZFS. You want a simple appliance with a web interface and you don't care how it works underneath.

## Alternatives

Rockstor
Freenas
OpenMediaVault

[^1]: Changes to support Debian are welcome. See [Contributing](contributing.md).