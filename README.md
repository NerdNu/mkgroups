mkgroups
========

Make Bukkit server permission groups by sending commands to the mark2 server wrapper.

This project provides a `mkgroups` command that issues commands to a permissions
plugin selected by a command line argument. Supported plugins currently include
`LuckPerms` (the default) and `bPermissions` (not recommended and has limitations
due to bugs and missing commands).

`mkgroups` can also convert a bPermissions `groups.yml` file to the new input
format.


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
   and rebuild them from scratch. Thus, obsolete or mistakenly added permission
   nodes can easily be expunged.


Module Files
------------

`mkgroups` takes as input one or more YAML files (with the suffix `.yml`) called
_modules_, in the same directory, that together define groups and permissions
for a single world.

Modules can contain one or more top level maps with the name `groups`, `weights`
and `permissions`. `mkgroups` will show a warning message if there are other,
unexpected keys in the YAML.

There are no distinguished file names; any module file can contain any
combination of `groups`, `weights` and `permissions` maps that you desire.


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

The `permissions` map has group names as its keys and arrays of case-insensitive,
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

`mkgroups` supports the bPermissions syntax for negated permission nodes: they
begin with the caret (`^`), e.g. `^pluginname.permission`. It does _not_ do any
special interpretation of wildcard permissions, e.g. `pluginname.*`.


Modules Directory
-----------------
One of the command line options to `mkgroups` is the modules directory: a 
directory that contains YAML modules. `mkgroups` only consults files in this
directory that end in the suffix `.yml`, so modules can be disabled by changing
the file suffix.


World Specific Modules
----------------------
Subdirectories of the modules directory configure worlds with the same name as
the subdirectory. When `mkgroups` is told to configure all worlds (`--world all`),
only subdirectories that do not contain the period (`.`) in their name will be
configured, so similarly, world configurations can be disabled by renaming the
subdirectory to add a suffix.

The permissions in module files for a specific world override or add to the
permissions defined by the module files in the modules directory. That is to
say, for a specific world, the module files only need to define the specific
permissions that are *different* from those that apply to the default, global
context.

In the LuckPerms permission model, groups exist in all contexts (the "default"
or "global" context as well as each world) but can have different permissions,
weight and parent groups on a per-context (per-world) basis. `mkgroups` blesses
this interpretation of groups as applying to all supported backends.

The format of YAML storage of group permissions in LuckPerms is not compact or
readable in the case of world-specific permissions, so `mkgroups` minimises the
number of world-specific permission values stored by the LuckPerms YAML storage
backend by taking into account the default values of all permissions in the
default (global) context.


bPermissions Import
-------------------
The `--bperms-groups` (`-b`) command line option can be used to import groups
and permissions from an existing bPermissions `groups.yml` file. Those
settings can then be written back out to disk using the `--output-modules`
(`-o`) option. The use of these two options together constitutes a
bPermissions import/conversion facility.


Command Line Arguments
----------------------

```
$ bin/mkgroups --help
usage: mkgroups.py [-h] [-s SERVER] [-i INPUT_MODULES] [-w WORLD]
                   [-m MODULES [MODULES ...]] [-b BPERMS_GROUPS]
                   [-o OUTPUT_MODULES] [-p PLUGIN] [-d] [-a] [-u] [-l]
                   [--debug]

Configure permissions for a specified server using mark2 send commands.

The command can also convert bPermissions groups.yml files to the new
Module File format. See https://github.com/NerdNu/mkgroups for full
documentation.

optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        The name of the server in the mark2 tabs.
  -i INPUT_MODULES, --input-modules INPUT_MODULES
                        The path to the directory containing YAML permission
                        modules. If unspecified, a subdirectory of the CWD
                        named after the server is tried.
  -w WORLD, --world WORLD
                        The name of a specific world to configure; treated as
                        the name of a subdirectory of the modules directory.
                        Leave unset/empty string for the default worlds. Use
                        "all" to signify all worlds.
  -m MODULES [MODULES ...], --modules MODULES [MODULES ...]
                        One or more module file names to load from the
                        --input-modules directory. This option can be
                        specified multiple times, and can be followed by
                        multiple file names each time. The '.yml' extension
                        can be omitted from file names. The purpose of this
                        option is to allow permissions to be added to a module
                        without having to load modules that have not changed.
                        The result will be that only the commands to add
                        permissions relating to the specified modules will be
                        issued. CAUTION: There is no analogously minimal way
                        to remove permissions. You need to remove all
                        permissions and re-add them all from scratch. Caution
                        is also advised when not working with the default
                        context (e.g. world 'all').
  -b BPERMS_GROUPS, --bperms-groups BPERMS_GROUPS
                        The path of a bPermissions groups.yml file to read
                        instead of module files. Overrides --input-modules.
                        Use this argument with -o to convert a bPermissions
                        groups.yml file into Module Files.
  -o OUTPUT_MODULES, --output-modules OUTPUT_MODULES
                        The path to a directory where YAML module files will
                        be output. The directory must exist. A module file
                        will be generated for each permission "stem": that
                        part of the permission name that precedes the first
                        period, e.g. "bukkit" for "bukkit.command.help".
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
    /home/david/projects/python/mkgroups/src/mkgroups.py --world all --input-modules pve --plugin bPermissions --delete --add
        Generate bPermissions commands to delete and add all groups and their
        permissions, in all worlds, according to the YAML modules in the
        directory./pveall worlds specified in the directory pve/. The commands
        are NOT sent to a server.

    /home/david/projects/python/mkgroups/src/mkgroups.py --server pve23 -au --input-modules ~/permissions/pve
        Add permissions for the default world of server pve23, using YAML
        module files from the specified directory as input.
        Commands for the default plugin (LuckPerms) are output to console
        and sent to the server.

    /home/david/projects/python/mkgroups/src/mkgroups.py -b /ssd/creative/plugins/bPermissions/groups.yml -o creative/
        Load a bPermissions groups.yml file and write out the corresponding
        module files.
```

