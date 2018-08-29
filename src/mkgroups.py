#!/usr/bin/env python
#------------------------------------------------------------------------------

from __future__ import print_function
from collections import defaultdict
from sets import Set

import argparse
import glob
import os.path
import sys
import yaml

#------------------------------------------------------------------------------

DEBUG = False

#------------------------------------------------------------------------------

def eprint(*args, **kwargs):
    '''
    Print to stderr.
    '''
    print(*args, file=sys.stderr, **kwargs)
    
#------------------------------------------------------------------------------

def error(*args, **kwargs):
    '''
    Print an error message beginning with ERROR: to stderr.
    '''
    eprint(*(['ERROR:'] + list(args)), **kwargs)

#------------------------------------------------------------------------------

def warning(*args, **kwargs):
    '''
    Print a warning message beginning with WARNING: to stderr.
    '''
    eprint(*(['WARNING:'] + list(args)), **kwargs)

#------------------------------------------------------------------------------

class Server:
    '''
    Abstract base of classes that encapsulate the connection to a server 
    for the purposes of issuing permissions commands.
    '''
    def __init__(self, name, doChange):
        '''
        Base constructor. Do not instantiate Server directly.
        
        Args:
            name     - The server name in the mark2 tabs, or the empty string 
                       for the default.        
            doChange - If True, command is sent to mark2; otherwise the command
                       is simply logged to stdout.
            plugin   - The name of the permissions plugin.
        '''
        self.name = name
        self.doChange = doChange
        
    #--------------------------------------------------------------------------

    @staticmethod
    def withPermissionsPlugin(plugin, name, doChange):
        '''
        Construct a new Server with the specified permissions plugin.
        
        Args:
            plugin   - The name of the permissions plugin.
            name     - The server name in the mark2 tabs, or the empty string 
                       for the default.        
            doChange - If True, command is sent to mark2; otherwise the command
                       is simply logged to stdout.
        '''
        if plugin == 'bPermissions':
            return bPermissionsServer(name, doChange)
        elif plugin == 'LuckPerms':
            return LuckPermsServer(name, doChange)
        else:
            error('unsupported permissions plugin: ' + plugin)
            sys.exit(1)

    #--------------------------------------------------------------------------

    def send(self, *args):
        '''
        Do a configuration action on the server by running a command with 
        mark2 send.
        
        Args:
            *args - Array of strings containing the command. A single space is
                    interposed between consecutive arguments. 
        '''
        command = 'mark2 send '
        if self.name != '':
            command += '-n ' + self.name + ' '
        command += ' '.join(args)
    
        print(command)
        if self.doChange:
            errorCode = os.system(command) 
            if errorCode != 0:
                error('failed to send to mark2: ' + errorCode)
            
    #--------------------------------------------------------------------------
    
    def createGroup(self, groupName, weight = None, world = None):
        '''
        Create a new permissions group by sending commands to the server.
        
        Args:
            groupName - The name of the group.
            weight    - The weight of the group (LuckPerms concept), or None 
                        if not specified.
            world     - The name of the world that is the context of the
                        permission, or None to signify the default world.
        '''
        pass
    
    #--------------------------------------------------------------------------
    
    def deleteGroup(self, groupName, world = None):
        '''
        Delete a permissions group.
        Args:
            groupName - The name of the group.
            world     - The name of the world that is the context of the
                        permission, or None to signify the default world.
        '''
        pass
        
    #--------------------------------------------------------------------------

    def groupClearPerms(self, groupName, world = None):
        '''
        Add the specified permission to the specified group.
        
        Args:
            groupName - The name of the group.
            world     - The name of the world that is the context of the
                        permission, or None to signify the default world.
        '''
        pass

    #--------------------------------------------------------------------------
    
    def groupAddPerm(self, groupName, bpermission, world = None):
        '''
        Add the specified permission to the specified group.
        
        Args:
            groupName    - The name of the group.
            bpermissions - The permission name, using bPermissions-style syntax,
                           wherein a permission beginning with the caret '^' is
                           negated.
            world        - The name of the world that is the context of the
                           permission, or None to signify the default world.
        '''
        pass
        
    #--------------------------------------------------------------------------
    
    def groupAddParent(self, groupName, parentGroupName, world = None):
        '''
        Add the specified permission to the specified group.
        
        Args:
            groupName    - The name of the group.
            bpermissions - The permission name, using bPermissions-style syntax,
                           wherein a permission beginning with the caret '^' is
                           negated.
            world        - The name of the world that is the context of the
                           permission, or None to signify the default world.
        '''
        pass
        
    #--------------------------------------------------------------------------
    
    def savePerms(self):
        '''
        Save all permissions.
        '''
        pass

#------------------------------------------------------------------------------

class bPermissionsServer(Server):
    '''
    Implementation of Server for bPermissions.
    '''
    def __init__(self, name, doChange):
        Server.__init__(self, name, doChange)

    #--------------------------------------------------------------------------

    def createGroup(self, groupName, weight = None, world = None):
        self.send('group', groupName)
        # TOOD: world parameter

    #--------------------------------------------------------------------------
    
    def deleteGroup(self, groupName, world = None):
        warning("deleting groups is not supported by bPermissions commands; you must clear groups.yml yourself!")
        
    #--------------------------------------------------------------------------

    def groupClearPerms(self, groupName, world = None):
        warning("clearing default group permissions is not implemented; review the resulting permissions!")

    #--------------------------------------------------------------------------

    def groupAddPerm(self, groupName, bpermission, world = None):
        if not world:
            world = 'world'
        self.send('exec g:' + groupName, 'a:addperm', 'v:' + bpermission, 'w:' + world)

    #--------------------------------------------------------------------------
    
    def groupAddParent(self, groupName, parentGroupName, world = None):
        if not world:
            world = 'world'
        self.send('exec g:' + groupName, 'a:addgroup', 'v:' + parentGroupName, 'w:' + world)

    #--------------------------------------------------------------------------
    
    def savePerms(self):
        self.send('permissions save')
    
#------------------------------------------------------------------------------

class LuckPermsServer(Server):
    '''
    Implementation of Server for LuckPerms.
    '''
    def __init__(self, name, doChange):
        Server.__init__(self, name, doChange)
        
    #--------------------------------------------------------------------------

    def createGroup(self, groupName, weight = None, world = None):
        self.send('lp creategroup', groupName)
        if weight:
            self.send('lp group', groupName, 'setweight', str(weight))

    #--------------------------------------------------------------------------
    
    def deleteGroup(self, groupName, world = None):
        if world:
            self.send('lp deletegroup', groupName, 'world=' + world)
        else: 
            self.send('lp deletegroup', groupName)

    #--------------------------------------------------------------------------

    def groupClearPerms(self, groupName, world = None):
        self.send('send lp group', groupName, 'clear')

    #--------------------------------------------------------------------------

    def groupAddPerm(self, groupName, bpermission, world = None):
        if bpermission.startswith('^'):
            permission = bpermission[1:]
            state = 'false'
        else:
            permission = bpermission
            state = 'true'
            
        if world:
            self.send('lp group', groupName, 'permission set', permission, state, 'world=' + world)
        else:
            self.send('lp group', groupName, 'permission set', permission, state)

    #--------------------------------------------------------------------------
    
    def groupAddParent(self, groupName, parentGroupName, world = None):
        if world:
            self.send('lp group', groupName, 'parent add', parentGroupName, 'world=' + world)
        else:
            self.send('lp group', groupName, 'parent add', parentGroupName)

    #--------------------------------------------------------------------------
    
    def savePerms(self):
        self.send('lp sync')

#------------------------------------------------------------------------------

def lowerArray(a):
    '''
    Return a new array of all the elements of the input array converted to 
    lower case.
    '''
    return [x.lower() for x in a]

#------------------------------------------------------------------------------

def mergePermissions(a, b):
    '''
    Merge two arrays of permission nodes by converting them to lower case,
    computing the set union, and returning the result as a sorted list.

    Args:
        a, b - Arrays. None is treated as the empty array.
    '''
    aSet = Set(lowerArray(a or [])) 
    bSet = Set(lowerArray(b or []))
    return sorted(list(aSet | bSet))

#------------------------------------------------------------------------------

def mergeGroups(a, b):
    '''
    Merge two arrays of parent groups, removing duplicates, but preserving
    order and case.

    Args:
        a, b - Arrays of groups.
    '''
    result = list(a)
    aSet = Set(a)
    for group in b:
        if not group in aSet:
            result.append(group)
    return result

#------------------------------------------------------------------------------

def mergeDicts(a, b, mergeValues):
    '''
    Merges two dictionaries, non-destructively, combining
    values on duplicate keys as defined by the optional mergeValues ternary
    function.
    
    Args:
        a, b        - Dictionaries to merge.
        mergeValues - Ternary function of (key, a[key], b[key]) to merge the 
                      values at key when it appears in both a and b.
    '''
    result = dict(a)
    for k, v in b.iteritems():
        if k in result:
            result[k] = mergeValues(k, result[k], v) 
        else:
            result[k] = v
    return result

#------------------------------------------------------------------------------

def mergeWeights(group, a, b):
    '''
    Handle merging of weights in modules as an error: weights should be
    specified once only.
    
    Args:
        group - The group (dictionary key) for which the weights are specified.
    '''
    error('the weight of group', group, 'has been specified with two different values:', a, 'and', b)
    sys.exit(1)

#------------------------------------------------------------------------------

def loadModules(moduleDirectory):
    '''
    Load *.yml in the specified directory and return a dict describing the 
    permissions ascribed to the corresponding context (world).
    
    Args:
        moduleDirectory - the directory containing YAML permission modules.
    
    Returns:
        A dict describing a permission context with the following keys:
            * `groups` is a map from case sensitive group name to sorted array
              of parent (inherited) group names in original case. All groups 
              referenced in the context will have a key in the map, even 
              if they have no parents.
            * `weights` is a map from group name to weight (LuckPerms concept).
            * `permissions` is a map from case sensitive group name to sorted
              array of lower-cased permission nodes.
    '''
    if not os.path.isdir(moduleDirectory):
        error('the specified module directory does not exist: ' + moduleDirectory)
        sys.exit(1)

    modules = glob.glob(moduleDirectory + '/*.yml')
    if not modules:
        error('no .yml files in ' + moduleDirectory)
        sys.exit(1)

    # Merge all module files.        
    groups = {}
    weights = {}
    permissions = {}
    for fileName in modules:
        with open(fileName, 'r') as f:
            if DEBUG:
                print('Loading', fileName)
            module = yaml.load(f)
            if module:
                # Warn about unexpected keys - could be typos.
                unexpectedKeys = set(module.keys()) - set(['groups', 'weights', 'permissions'])
                if unexpectedKeys:
                    warning('unexpected YAML keys in ' + fileName + ':', ' '.join(unexpectedKeys))

                if 'groups' in module:
                    groups = mergeDicts(groups, module['groups'], lambda _, x, y: mergeGroups(x, y))
                if 'weights' in module:
                    weights = mergeDicts(weights, module['weights'], mergeWeights)
                if 'permissions' in module:
                    permissions = mergeDicts(permissions, module['permissions'], lambda _, x, y: mergePermissions(x, y))

    # Check that consistent case has been used for group names throughout.
    allGroups = set(groups.keys()) | set(permissions.keys()) | set(weights.keys())
    for parents in groups.values():
        allGroups |= set(parents)
    groupMentions = defaultdict(list)
    for group in allGroups:
        groupMentions[group.lower()].append(group)
    
    groupNameError = False
    for group, mentions in groupMentions.iteritems():
        if len(mentions) > 1:
            error('group', group, 'is mentioned variously as:', ' '.join(mentions))
            groupNameError = True
        
    if groupNameError:
        eprint('Ensure that group names always use consistent letter case.')
        sys.exit(1)

    # Ensure that all groups have an entry in the groups map.
    for group in allGroups:
        if not group in groups:
            groups[group] = []                    

    context = dict()
    context['groups'] = groups
    context['weights'] = weights
    context['permissions'] = permissions
    return context
    
#------------------------------------------------------------------------------

def updatePermissions(server, context, world):
    '''
    Update permissions.
    
    Args:
        server  - The server to update.
        context - A dict containing 'groups', 'weights' and 'permissions' keys
                  describing the permissions in specific world, or the default 
                  world/permission context.
        world   - The name of the context world, or None for the default 
                  context.
    '''
    groups = context['groups']
    weights = context['weights']
    permissions = context['permissions']
    sortedGroupNames = sorted(groups.keys(), key=lambda v: v.upper())
    
    # Note: default group is 'default' for bPermissions and LuckPerms.
    for group in sortedGroupNames:
        if group.lower() != 'default':
            weight = weights.get(group)
            server.createGroup(group, weight, world)
            
    for group in sortedGroupNames:
        for parent in groups.get(group):
            # TODO: worlds.
            server.groupAddParent(group, parent, world)    
    
    for group in sortedGroupNames:
        for perm in permissions.get(group, []):
            # TODO: worlds.
            server.groupAddPerm(group, perm, world)
    
#------------------------------------------------------------------------------
        
def deletePermissions(server, context, world):
    '''
    Delete all permissions.

    Args:
        server  - The server to update.
        context - A dict containing 'groups', 'weights' and 'permissions' keys
                  describing the permissions in specific world, or the default 
                  world/permission context.
        world   - The name of the context world, or None for the default 
                  context.
    '''
    groups = context['groups']
    sortedGroupNames = sorted(groups.keys(), key=lambda v: v.upper())
    for group in sortedGroupNames:
        if group.lower() == 'default':
            server.groupClearPerms(group, world)
        else:
            server.deleteGroup(group, world)

#------------------------------------------------------------------------------

def listPermissions(context):
    '''
    List the combined groups, weights and permissions in the context.
    '''
    groups = context['groups']
    weights = context['weights']
    permissions = context['permissions']
    if groups:
        print('Groups')
        print('~~~~~~')
        print(yaml.dump(groups, default_flow_style=False))
        print()
    if weights:
        print('Weights')
        print('~~~~~~~')
        print(yaml.dump(weights, default_flow_style=False))
        print()
    if permissions:
        print('Permissions')
        print('~~~~~~~~~~~')
        print(yaml.dump(permissions, default_flow_style=False))

#------------------------------------------------------------------------------

class readable_dir(argparse.Action):
    '''
    Extend argparse to support directory arguments, courtesy of StackOverflow.
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentError(self, "readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentError(self, "readable_dir:{0} is not a readable dir".format(prospective_dir))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Configure permissions for a specified server using mark2 send commands.',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog='''
Examples:
    {0} --server pve-dev --world all --plugin bPermissions --delete --add
        Delete, then add permissions to bPermissions in all worlds on pve-dev.
        Commands to perform the actions are output but not sent to the server.                                         
                                     
    {0} --server pve23 --add --update --modules ~/permissions/pve
        Add permissions for the default world of server pve23, using YAML
        module files from the specified directory as input.
        Commands for the default plugin (LuckPerms) are output to console 
        and sent to the server.
                                     '''.format(sys.argv[0]))
    parser.add_argument('-s', '--server', required=True, 
                        help='The name of the server in the mark2 tabs.')
    parser.add_argument('-m', '--modules', action=readable_dir, 
                        help='The path to the directory containing YAML permission modules. If unspecified, a subdirectory of the CWD named after the server is tried.')
    parser.add_argument('-w', '--world', 
                        help='The name of a specific world to configure; treated as the name of a subdirectory of the modules directory. Leave unset/empty string for the default worlds. Use "all" to signify all worlds.')
    parser.add_argument('-p', '--plugin', default='LuckPerms',
                        help='The name of the permissions plugin.')
    parser.add_argument('-d', '--delete', action='store_true',
                        help='Delete all permissions on the specified server (and world if specified).')
    parser.add_argument('-a', '--add', action='store_true',
                        help='Add all permissions on the specified server (and world if specified).')
    parser.add_argument('-u', '--update', action='store_true',
                        help='Update permissions; without this flag, commands are logged but permissions not changed.')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List combined groups, weights and permissions to stdout.')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging.')
    
    args = parser.parse_args()
    if not args.modules:
        args.modules = args.server
        if not os.path.isdir(args.modules):
            error('the default modules path cannot be read:', args.modules)
            sys.exit(1)
    
    DEBUG = args.debug
    if DEBUG:
        print('# server:', args.server)
        print('# plugin:', args.plugin)
        print('# modules:', args.modules)
        print('# world:', (args.world or '<default world>'))
        print()
    
    server = Server.withPermissionsPlugin(args.plugin, args.server, args.update)
    context = loadModules(args.modules)
    
    if args.list:
        listPermissions(context)

    if args.delete:
        if args.world == 'all':
            for world in context.keys():
                deletePermissions(server, context, world)
        else:
            deletePermissions(server, context, args.world)

    if args.add:
        if args.world == 'all':
            for world in context.keys():
                updatePermissions(server, context, world)
        else:
            updatePermissions(server, context, args.world)
