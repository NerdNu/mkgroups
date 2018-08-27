mkgroups
========

Make Bukkit server permission groups by sending commands to the mark2 server wrapper.

This project provides a `mkgroups` command that issues commands to a permissions
plugin selected by a command line argument. Supported plugins currently include
`LuckPerms` (the default) and `bPermissions` (not recommended and has limitations
due to bugs and missing commands).


Concept of Operation
--------------------

`mkgroups` takes as input the `mark2` _name_ of a server to send commands to,
and a directory path containing a set of "module" files, written in YAML.
The script can also take command line arguments to specify the permissions
plugin to talk to, and the name of a world to configure. By default, the script
configures the default world, only.

Given these inputs, `mkgroups` can issue plugin commands to configure groups:
their inheritances, relative priorities and permissions. The script can send
these commands to the server with `mark2 send`, or simply log the commands that
would be issued to the terminal (stdout).

Note that `mkgroups` does NOT configure group membership or permissions of 
individual players.


Benefits
--------

 * _Supports Separation of Concerns_: Bukkit allows server functions to be
   separated into different concerns in the form of plugins. `mkgroups` allows
   an analogous expression of permission groups. You can have one YAML file per
   plugin, or you can have a more coarse-grained division, e.g. by functional
   area (chat, build protections, moderation, etc.). However, you slice the
   permissions into files, `mkgroups` combines them into a single tree before
   configuring the server.
 
 * _It's Always All YAML_: Regardless of how the permissions plugin stores
   permission groups and nodes, whether YAML files or a relational database, you
   edit permissions in YAML syntax. You get clarity, succinctness and you can
   even include comments in your YAML, if you desire.
 
 * _Rebuild Easily_: `mkgroups` makes it trivial to clear out all permissions 
   and rebuild them from scratch. Thus obsolete or mistakenly added permission
   nodes can easily be expunged.


Module Files
------------

`mkgroups` takes as input one or more YAML files (with the suffix `.yml`) called
_modules_ in the same directory, that together define groups and permissions
for a single world.

Modules can contain one or more top level maps with the name `groups`, `weights`
and `permissions`. `mkgroups` will show a warning message if there are other,
unexpected keys in the YAML.


### Groups Map

The `groups` map has the names of groups as its keys, and an array of strings
containing the parent (inherited) groups as the corresponding values. For example:

```
groups:
  Moderators:
  - default
  
  Admins:
  - Moderators
```

The above configuration mentions three groups (`default`, `Admins` and `Moderators`);
`Moderators` inherits from the `default` group and `Admins` inherits from `Moderators`.
`mkgroups` enforces consistent usage of letter case for group names; it is an
error to mention a group with different variations of letter case. (This may
not be enforced in a future version, since it turns out LuckPerms converts all
the group names to lower case anyway.)


### Weights Map

The `weights` map has group names as its keys and integer group weights as its
values, for example:
```
weights:
  Moderators: 10
  Admins: 20
```

Group weights are a LuckPerms concept required to disambiguate the "primary"
group in situations of multiple group inheritance. You may not need to configure
them. You may want to (and can) put the `groups` and `weights` maps in the same
YAML file (e.g. `groups.yml`), since they both relate to the group inheritance
hierarchy.


### Permissions Map

The `weights` map has group names as its keys and arrays of case-insensitive,
permissions node strings as its values. When `mkgroups` loads multiple modules,
it concatenates and sorts the permission nodes for each group.

For example, given modules for plugins `APlugin` and `BPlugin`:

```
# aplugin.yml
permissions:
  default:
  - aplugin.player
  
  Moderators:
  - aplugin.staff
```

```
# bplugin.yml
permissions:
  default:
  - bplugin.player
  
  Admins:
  - bplugin.*
```

`mkgroups` would compute an effective, combined set of permissions:
```
permissions:
  default:
  - aplugin.player
  - bplugin.player
  
  Moderators:
  - aplugin.staff
  
  Admins
  - bplugin.*
```

`mkgroups` supports the bPermissions syntax for negated permission nodes - they
begin with the caret (`^`), e.g. `^pluginname.permission`. It does _not_ do any
special interpretation of wildcard permissions, e.g. `pluginname.*`.


Modules Directory
-----------------
One of the command line options to `mkgroups` is the modules directory: a 
directory that contains YAML modules. `mkgroups` only consults files in this
directory that end in the suffix `.yml`, so modules can be disabled by changing
the file suffix.

Subdirectories of the modules directory configure worlds with the same name as
the subdirectory. When `mkgroups` is told to configure all worlds (`--world all`),
only subdirectories that do not contain the period (`.`) in their name will be
configured, so similarly, world configurations can be disabled by renaming the
subdirectory to add a suffix.

NOTE: currently, world-specific permissions are not implemented, but they will
be very soon!


Command Line Arguments
----------------------

```
$ ./mkgroups --help
usage: mkgroups.py [-h] -s SERVER [-m MODULES] [-w WORLD] [-p PLUGIN] [-d]
                   [-a] [-u] [-l] [--debug]

Configure permissions for a specified server using mark2 send commands.

optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        The name of the server in the mark2 tabs.
  -m MODULES, --modules MODULES
                        The path to the directory containing YAML permission
                        modules. If unspecified, a subdirectory of the CWD
                        named after the server is tried.
  -w WORLD, --world WORLD
                        The name of a specific world to configure; treated as
                        the name of a subdirectory of the modules directory.
                        Leave unset/empty string for the default worlds. Use
                        "all" to signify all worlds.
  -p PLUGIN, --plugin PLUGIN
                        The name of the permissions plugin.
  -d, --delete          Delete all permissions on the specified server (and
                        world if specified).
  -a, --add             Add all permissions on the specified server (and world
                        if specified).
  -u, --update          Update permissions; without this flag, commands are
                        logged but permissions not changed.
  -l, --list            List combined groups, weights and permissions to
                        stdout.
  --debug               Enable debug logging.

Examples:
    /home/david/projects/python/mkgroups/src/mkgroups.py --server pve-dev --world all --plugin bPermissions --delete --add
        Delete, then add permissions to bPermissions in all worlds on pve-dev.
        Commands to perform the actions are output but not sent to the server.                                         
                                     
    /home/david/projects/python/mkgroups/src/mkgroups.py --server pve23 --add --update --modules ~/permissions/pve
        Add permissions for the default world of server pve23, using YAML
        module files from the specified directory as input.
        Commands for the default plugin (LuckPerms) are output to console 
        and sent to the server.
```

