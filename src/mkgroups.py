#!/usr/bin/env python
#------------------------------------------------------------------------------

from __future__ import print_function
from collections import defaultdict
from collections import OrderedDict
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

def lowerArray(a):
    '''
    Return a new array of all the elements of the input array converted to
    lower case.
    '''
    return [x.lower() for x in a]

#------------------------------------------------------------------------------

def permissionsAsBooleanMap(perms, group):
    '''
    Convert a list of permissions in bPermissions syntax (caret '^' for
    negation) to a map from permission node to True or False state.

    Args:
        perms - List of permissions in bPermissions syntax.
        group  - The name of the group where the permissions are specified.
                 This is only used to provide a more detailed error message in
                 the situation where the group includes both a node and its
                 negation.

    Returns:
        A map from lowercased node to True/False representing the permissions.
    '''
    result = {}
    for bPermission in lowerArray(perms):
        if bPermission.startswith('^'):
            permission = bPermission[1:]
            state = False
        else:
            permission = bPermission
            state = True
        if result.get(permission) == (not state):
            error('group "' + group + '" includes both ' + permission + ' and ^' + permission)
            sys.exit(1)
        else:
            result[permission] = state
    return result

#------------------------------------------------------------------------------

def differencePermissions(before, after, group):
    '''
    Given two lists of permission nodes in bPermissions syntax, return a
    minimal list of changes that must be made to turn the before permissions
    into the after permissions.

    Args:
        before - The permissions before the changes.
        after  - The permissions after the changes.
        group  - The name of the group where the permissions are specified.
                 This is only used to provide a more detailed error message in
                 the situation where the group includes both a node and its
                 negation.

    Returns:
        A sorted, list of lower cased changed permissions in bPermissions
        format (using ^ to indicate a negated node).
    '''
    changes = []
    beforeMap = permissionsAsBooleanMap(before, group)
    afterMap = permissionsAsBooleanMap(after, group)
    for node in set(beforeMap.keys()) | set(afterMap.keys()):
        afterValue = afterMap.get(node)
        # Treat absence of a value in afterMap as keeping the beforeMap value.
        if afterValue is not None and afterValue != beforeMap.get(node):
            changes.append(node if afterValue else '^' + node)
    return sorted(changes)

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
        if self.name:
            command += '-n ' + self.name + ' '
        command += ' '.join(args)

        print(command)
        if self.doChange:
            errorCode = os.system(command)
            if errorCode != 0:
                error('failed to send to mark2: ' + str(errorCode))

    #--------------------------------------------------------------------------

    def createGroup(self, groupName, world='default'):
        '''
        Create a new permissions group by sending commands to the server.

        Args:
            groupName - The name of the group.
            world     - The name of the world that is the context of the
                        permission, or 'default' to signify the default world.
        '''
        pass

    #--------------------------------------------------------------------------

    def setGroupWeight(self, groupName, weight, world='default'):
        '''
        Specify the weight of the group.

        Args:
            groupName - The name of the group.
            weight    - The weight of the group (LuckPerms concept), or None
                        if not specified.
            world     - The name of the world that is the context of the
                        permission, or 'default' to signify the default world.
        '''
        pass

    #--------------------------------------------------------------------------

    def deleteGroup(self, groupName, world='default'):
        '''
        Delete a permissions group.
        Args:
            groupName - The name of the group.
            world     - The name of the world that is the context of the
                        permission, or 'default' to signify the default world.
        '''
        pass

    #--------------------------------------------------------------------------

    def groupClearPerms(self, groupName, world='default'):
        '''
        Add the specified permission to the specified group.

        Args:
            groupName - The name of the group.
            world     - The name of the world that is the context of the
                        permission, or 'default' to signify the default world.
        '''
        pass

    #--------------------------------------------------------------------------

    def groupAddPerm(self, groupName, bpermission, world='default'):
        '''
        Add the specified permission to the specified group.

        Args:
            groupName    - The name of the group.
            bpermissions - The permission name, using bPermissions-style syntax,
                           wherein a permission beginning with the caret '^' is
                           negated.
            world        - The name of the world that is the context of the
                           permission, or 'default' to signify the default world.
        '''
        pass

    #--------------------------------------------------------------------------

    def groupAddParent(self, groupName, parentGroupName, world='default'):
        '''
        Add the specified permission to the specified group.

        Args:
            groupName    - The name of the group.
            bpermissions - The permission name, using bPermissions-style syntax,
                           wherein a permission beginning with the caret '^' is
                           negated.
            world        - The name of the world that is the context of the
                           permission, or 'default' to signify the default world.
        '''
        pass

    #--------------------------------------------------------------------------

    def savePerms(self):
        '''
        Save all permissions.
        '''
        pass

    #--------------------------------------------------------------------------

    def updatePermissions(self, contextMap, world):
        '''
        Update permissions.

        Args:
            contextMap - A map from context name to context, where a context is
                         a dict containing 'groups', 'weights' and 'permissions'
                         keys describing the permissions in specific world, or
                         the default world/permission context.
            world      - The name of the context world, or 'default' for the
                         default context.
        '''
        context = contextMap[world]
        groups = context['groups']
        weights = context['weights']
        permissions = context['permissions']
        sortedGroupNames = sorted(groups.keys(), key=lambda v: v.upper())

        # Note: default group is 'default' for bPermissions and LuckPerms.
        for group in sortedGroupNames:
            if group.lower() != 'default':
                self.createGroup(group, world)
            weight = weights.get(group)
            self.setGroupWeight(group, weight, world)

        for group in sortedGroupNames:
            for parent in groups.get(group):
                self.groupAddParent(group, parent, world)

        for group in sortedGroupNames:
            for perm in permissions.get(group, []):
                self.groupAddPerm(group, perm, world)

    #--------------------------------------------------------------------------

    def deletePermissions(self, contextMap, world):
        '''
        Delete all permissions.

        Args:
            contextMap - A map from context name to context, where a context is
                         a dict containing 'groups', 'weights' and 'permissions'
                         keys describing the permissions in specific world, or
                         the default world/permission context.
            world      - The name of the context world, or 'default' for the
                         default context.
        '''
        context = contextMap[world]
        groups = context['groups']
        sortedGroupNames = sorted(groups.keys(), key=lambda v: v.upper())
        for group in sortedGroupNames:
            if group.lower() == 'default':
                self.groupClearPerms(group, world)
            else:
                self.deleteGroup(group, world)

#------------------------------------------------------------------------------

class bPermissionsServer(Server):
    '''
    Implementation of Server for bPermissions.
    '''

    def __init__(self, name, doChange):
        Server.__init__(self, name, doChange)

    #--------------------------------------------------------------------------

    def createGroup(self, groupName, world):
        if world == 'default':
            self.send('group', groupName)
        else:
            # TODO: verify world parameter actually works.
            self.send('group', groupName, 'w:' + world)

    #--------------------------------------------------------------------------

    def setGroupWeight(self, groupName, weight, world):
        # Weight is a LuckPerms concept.
        pass

    #--------------------------------------------------------------------------

    def deleteGroup(self, groupName, world):
        warning("deleting groups is not supported by bPermissions commands; you must clear groups.yml yourself!")

    #--------------------------------------------------------------------------

    def groupClearPerms(self, groupName, world):
        warning("clearing default group permissions is not implemented; review the resulting permissions!")

    #--------------------------------------------------------------------------

    def groupAddPerm(self, groupName, bpermission, world):
        if world == 'default':
            world = 'world'
        self.send('exec g:' + groupName, 'a:addperm', 'v:' + bpermission, 'w:' + world)

    #--------------------------------------------------------------------------

    def groupAddParent(self, groupName, parentGroupName, world):
        if world == 'default':
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

    def createGroup(self, groupName, world):
        # LuckPerms considers that groups exist in all worlds. Ignore world.
        self.send('lp creategroup', groupName)

    #--------------------------------------------------------------------------

    def setGroupWeight(self, groupName, weight, world):
        if weight:
            worldClause = '' if world == 'default' else ' world=' + world
            self.send('lp group ' + groupName + ' setweight ' + str(weight) + worldClause)

    #--------------------------------------------------------------------------

    def deleteGroup(self, groupName, world):
        # Group deletion ignores the world.
        self.send('lp deletegroup', groupName)

    #--------------------------------------------------------------------------

    def groupClearPerms(self, groupName, world):
        worldClause = '' if world == 'default' else ' world=' + world
        self.send('lp group ' + groupName + ' clear' + worldClause)

    #--------------------------------------------------------------------------

    def groupAddPerm(self, groupName, bpermission, world):
        if bpermission.startswith('^'):
            permission = bpermission[1:]
            state = 'false'
        else:
            permission = bpermission
            state = 'true'

        worldClause = '' if world == 'default' else ' world=' + world
        self.send('lp group ' + groupName + ' permission set ' + permission + ' ' + state + worldClause)

    #--------------------------------------------------------------------------

    def groupAddParent(self, groupName, parentGroupName, world):
        worldClause = '' if world == 'default' else ' world=' + world
        self.send('lp group ' + groupName + ' parent add ' + parentGroupName + worldClause)

    #--------------------------------------------------------------------------

    def savePerms(self):
        self.send('lp sync')

    #--------------------------------------------------------------------------

    def updatePermissions(self, contextMap, world):
        '''
        Override Server.updatePermissions() to minimise the resulting YAML file
        when LuckPerms is configured for a YAML storage backend.

        In LuckPerms, groups exist in all worlds, but have entries in the YAML
        to override their properties (parents, weight, permission nodes) when
        their properties are configured for a specific world. The format of the
        YAML storage is much more compact and readable for the default context
        than for the world-specific properties, and the world-specific entries
        are added to the YAML when commands are issued to set properties for
        a specific world, regardless of whether they differ from the default
        context.

        So, to minimise the size of the YAML file, we need to compare the
        specific world to the default context and only set those properties
        that are different.

        '''
        # The default context requires no minimisation.
        if world == 'default':
            Server.updatePermissions(self, contextMap, world)
            return

        # In a non-default context, apply the minimum set of differences
        # between the world and the default context.
        defaultContext = contextMap['default']
        context = contextMap[world]
        groups = context['groups']
        weights = context['weights']
        permissions = context['permissions']
        sortedGroupNames = sorted(groups.keys(), key=lambda v: v.upper())

        # Compute list of groups in world in excess of those in default context.
        extraGroups = set(groups.keys()) - set(defaultContext['groups'].keys())
        for group in sorted(extraGroups, key=lambda v: v.upper()):
            if group.lower() != 'default':
                self.createGroup(group, world)

        # Where there are world-specific weight overrides, do those.
        for group in sortedGroupNames:
            weight = weights.get(group)
            defaultWeight = defaultContext['weights'].get(group)
            if weight is not None and weight != defaultWeight:
                self.setGroupWeight(group, weight, world)

        # Only issue parent commands if the parents differ in this world.
        for group in sortedGroupNames:
            defaultParents = defaultContext['groups'].get(group)
            groupParents = groups.get(group)
            if groupParents != defaultParents:
                for parent in groupParents:
                    self.groupAddParent(group, parent, world)

        # For each group, compare the permissions in this world to the same
        # group in the default world, and issue commands for just the changes.
        for group in sortedGroupNames:
            defaultPerms = defaultContext['permissions'].get(group, [])
            groupPerms = permissions.get(group, [])
            changedPerms = differencePermissions(defaultPerms, groupPerms, group)
            for perm in changedPerms:
                self.groupAddPerm(group, perm, world)

    #--------------------------------------------------------------------------

    def deletePermissions(self, contextMap, world):
        '''
        Delete all permissions in the specified world.

        Args:
            contextMap - A map from context name to context, where a context is
                         a dict containing 'groups', 'weights' and 'permissions'
                         keys describing the permissions in specific world, or
                         the default world/permission context.
            world      - The name of the context world, or 'default' for the
                         default context.
        '''
        if world == 'default':
            Server.deletePermissions(self, contextMap, world)
            return

        # For the non-default context, delete groups that are unique to the
        # specified world and clear the ones shared with the default context.
        defaultContext = contextMap['default']
        context = contextMap[world]
        defaultGroups = defaultContext['groups'].keys()
        for group in sorted(defaultGroups, key=lambda v: v.upper()):
            self.groupClearPerms(group, world)

        worldSpecificGroups = set(context['groups'].keys()) - set(defaultGroups)
        for group in sorted(worldSpecificGroups, key=lambda v: v.upper()):
            self.deleteGroup(group, world)

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

def makeContext(groups, weights, permissions):
    '''
    Make a context dict as defined in loadModules(). Specifically:
    ensure that all groups mentioned in all input arguments use consistent
    letter case across all mentions, and have a key in the groups dict of the
    return context. Also, ensure that all groups have an entry in the
    permissions map.

    Args:
        groups      - A dict mapping group name to list of case-sensitive parent
                      group names.
        weights     - The weight of each group where that is specified; key
                      missing to signify unspecified.
        permissions - Map from group name to sorted list of lower-cased
                      permissions.
    '''
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

    # Ensure that all groups have an entry in the groups and permissions maps.
    for group in allGroups:
        groups.setdefault(group, [])
        permissions.setdefault(group, [])

    return {'groups': groups, 'weights': weights, 'permissions': permissions}

#------------------------------------------------------------------------------

def loadModules(moduleDirectory, moduleNames):
    '''
    Load *.yml in the specified directory and return a dict describing the
    permissions ascribed to the corresponding context (world).

    Args:
        moduleDirectory - The directory containing YAML permission modules.
        moduleNames     - A list of names of module files to load in that
                          directory, possibly with file extensions omitted.
                          If None or the empty list, ALL modules in the
                          directory should be loaded.

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

    # Pre-process moduleNames into full filenames.
    if not moduleNames:
        moduleFileNames = modules
    else:
        moduleFileNames = []
        for name in moduleNames:
            baseName = name if name.endswith('.yml') else name + '.yml'
            moduleFileNames.append(os.path.join(moduleDirectory, baseName))

    # Merge all module files.
    groups = {}
    weights = {}
    permissions = {}
    for fileName in moduleFileNames:
        try:
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
        except IOError as e:
            error('cannot open module file "' + fileName + '" to read.')
            sys.exit(1)

    return makeContext(groups, weights, permissions)

#------------------------------------------------------------------------------

def loadContextMap(contextName, moduleDirectory, moduleNames):
    '''
    Build a map from context name to context.

    Per the loadModules() docs, a context is a dict containing groups, weights
    and permissions keys. The context name either signifies a single world
    ('default' for the default world at the top level of the moduleDirectory)
    or a specific world whose permission modules are stored in a sub-directory
    of the moduleDirectory. The context name 'all' signifies that all contexts
    should be loaded ('default' and all world sub-directories).

    To support minimisation of LuckPerms YAML storage, the default context is
    always loaded in addition to any specific world that might be requested.

    Args:
        contextName     - The name of the context to load: either 'default',
                          'all', or a specific sub-directory of moduleDirectory
                          corresponding to a specific world.
        moduleDirectory - The directory containing YAML permission modules and
                          world sub-directories.
        moduleNames     - A list of names of module files to load in that
                          directory, possibly with file extensions omitted,
                          and possibly the empty list. The empty list signifies
                          that ALL modules in the directory should be loaded.

    Returns:
        A dict mapping contextName(s) to contexts. It will always contain at
        least the default context.
    '''
    contextMap = {}
    contextMap['default'] = loadModules(moduleDirectory, moduleNames)
    if contextName == 'all':
        for path in os.listdir(moduleDirectory):
            fullPath = os.path.join(moduleDirectory, path)
            if os.path.isdir(fullPath):
                if DEBUG:
                    print('Loading world ' + fullPath)
                contextMap[path] = loadModules(fullPath, moduleNames)
    elif contextName != 'default':
        contextDir = os.path.join(moduleDirectory, contextName)
        if os.path.isdir(contextDir):
            contextMap[contextName] = loadModules(contextDir, moduleNames)
        else:
            error('context "' + contextName + '" is not a sub-directory of module directory "' + moduleDirectory + '".')
    return contextMap

#------------------------------------------------------------------------------

def loadBPermissions(groupsFile):
    '''
    Load a bPermissions groups file and return it as a context dict, as per
    loadModules().

    Args:
        groupsFile - The open file containing bPermissions groups.

    Returns:
        A context dict.
    '''
    groups = {}
    permissions = {}

    bPermissions = yaml.load(groupsFile)
    if bPermissions and 'groups' in bPermissions:
        bPermsGroups = bPermissions['groups']
        for name, group in bPermsGroups.iteritems():
            permissions[name] = sorted(lowerArray(group.get('permissions', [])))
            groups[name] = group.get('groups', [])

    return makeContext(groups, {}, permissions)

#------------------------------------------------------------------------------

def depthFirstPostOrderTraversal(node, edges, seenNodes, visit):
    '''
    Given a DAG, do a depth-first, postorder traversal of the subgraph
    rooted at the specified node, calling a specified visit() function as each
    node is visited.

    Args:
        node      - The root of the subtree to traverse.
        edges     - Directed edges, expressed as a map from the source node to
                    a list of the corresponding edge destination nodes.
        seenNodes - The set of nodes that have been visited so far. Should be
                    initialised to set() (the empty set).
        visit     - A unary function that takes a node and performs some
                    processing when it is visited.
    '''
    for dependency in edges[node]:
        if not dependency in seenNodes:
            seenNodes.add(dependency)
            depthFirstPostOrderTraversal(dependency, edges, seenNodes, visit)
            visit(dependency)

    if not node in seenNodes:
        visit(node)
        seenNodes.add(node)

#------------------------------------------------------------------------------

def naturallyOrderedGroups(groups):
    '''
    Given a dict mapping group name to list of parent groups, return a list of
    the groups, ordered from most general to most specific, according to the
    group inheritance relation.

    Where two groups are equally specific, their relative ordering is determined
    lexicographically, case-insensitively.

    Args:
        groups - A map from group name to list of parent groups. This map has a
                 key for all groups, whether they have parents or not.

    Returns:
        A list of all groups, ordered from furthest ancestor to deepest
        descendant.
    '''
    result = []
    visitedGroups = set()

    # Enforce preferred lexicographic ordering by pre-sorting groups.
    for group in sorted(groups.keys(), key=lambda v: v.upper()):
        depthFirstPostOrderTraversal(group, groups, visitedGroups, lambda node: result.append(node))
    return result

#------------------------------------------------------------------------------

def allAncestors(group, groups):
    '''
    Return all ancestors of a group, listed from immediate ancestor to furthest
    ancestor.

    Args:
        group  - The group whose ancestors are returned.
        groups - Map from group name to list of ancestors. It's possible for
                 this list to contain redundant ancestors. The function will
                 compensate for that.
    '''
    result = []
    depthFirstPostOrderTraversal(group, groups, set(), lambda node: result.append(node))
    result.reverse()
    # Skip the first node, which is always group itself.
    return result[1:]

#------------------------------------------------------------------------------

def writeModuleFiles(context, outputDirectory):
    '''
    Write YAML module files representing the specified context to the specified
    directory.

    Args:
        context         - A dict containing 'groups', 'weights' and 'permissions'
                          keys describing the permissions in specific world, or
                          the default world/permission context.
        outputDirectory - The directory where module files will be written.
    '''
    # Map from permission stem (prefix before '.') to OrderedDict from group
    # name to sorted list of permissions.
    modules = {}

    groups = context['groups']
    weights = context['weights']
    permissions = context['permissions']
    orderedGroups = naturallyOrderedGroups(groups)

    # Write a module representing groups and weights.
    groupsModuleGroups = UnsortableOrderedDict()
    groupsModuleWeights = UnsortableOrderedDict()
    for groupName in orderedGroups:
        groupsModuleGroups.setdefault(groupName, []).extend(groups[groupName])
        if groupName in weights.keys():
            groupsModuleWeights[groupName] = weights[groupName]

    groupsModule = UnsortableOrderedDict()
    groupsModule['groups'] = groupsModuleGroups
    groupsModule['weights'] = groupsModuleWeights
    with open(outputDirectory + '/GROUPS.yml', 'w') as f:
        yaml.dump(groupsModule, f, default_flow_style=False)

    # Group all permissions into modules based on the permission stem.
    for groupName in orderedGroups:
        for perm in permissions[groupName]:
            prefix, _, _ = perm.partition('.')
            if prefix.startswith('^'):
                stem = prefix[1:]
                inversePerm = perm[1:]
            else:
                stem = prefix
                inversePerm = '^' + perm

            module = modules.setdefault(stem, UnsortableOrderedDict())

            # Check if an ancestor group contains a permission before adding.
            inheritedPerm = False
            for ancestor in allAncestors(groupName, groups):
                # If an ancestor contains the inverse perm, then the module MUST
                # override that.
                if inversePerm in permissions[ancestor]:
                    break
                if perm in permissions[ancestor]:
                    inheritedPerm = True
                    print('NOTE: removing redundant permission', perm, 'from', groupName, 'because it is inherited from', ancestor)
                    break
            if not inheritedPerm:
                module.setdefault(groupName, []).append(perm)

    # Write all module files.
    for moduleName, modulePermissions in modules.iteritems():
        with open(outputDirectory + '/' + moduleName + '.yml', 'w') as f:
            module = {'permissions': modulePermissions}
            yaml.dump(module, f, default_flow_style=False)

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
    Extend argparse to check for readable directory arguments, courtesy of
    StackOverflow.
    '''

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentError(self, "readable_dir: {0} does not exist".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentError(self, "readable_dir: {0} is not a readable dir".format(prospective_dir))

#------------------------------------------------------------------------------

class writable_dir(argparse.Action):
    '''
    Extend argparse to check for writable directory arguments, courtesy of
    StackOverflow.
    '''

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentError(self, "writable_dir: {0} does not exist".format(prospective_dir))
        if os.access(prospective_dir, os.W_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentError(self, "writable_dir: {0} is not a writable dir".format(prospective_dir))

#------------------------------------------------------------------------------
# Set up PyYAML to write YAML keys in the order we add them.

class UnsortableList(list):

    def sort(self, *args, **kwargs):
        pass

class UnsortableOrderedDict(OrderedDict):

    def items(self, *args, **kwargs):
        return UnsortableList(OrderedDict.items(self, *args, **kwargs))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    yaml.add_representer(UnsortableOrderedDict, yaml.representer.SafeRepresenter.represent_dict)

    parser = argparse.ArgumentParser(description='''
Configure permissions for a specified server using mark2 send commands.

The command can also convert bPermissions groups.yml files to the new
Module File format. See https://github.com/NerdNu/mkgroups for full
documentation.''',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog='''
Examples:
    {0} --world all --input-modules pve --plugin bPermissions --delete --add
        Generate bPermissions commands to delete and add all groups and their
        permissions, in all worlds, according to the YAML modules in the
        directory./pveall worlds specified in the directory pve/. The commands
        are NOT sent to a server.

    {0} --server pve23 -au --input-modules ~/permissions/pve
        Add permissions for the default world of server pve23, using YAML
        module files from the specified directory as input.
        Commands for the default plugin (LuckPerms) are output to console
        and sent to the server.

    {0} -b /ssd/creative/plugins/bPermissions/groups.yml -o creative/
        Load a bPermissions groups.yml file and write out the corresponding
        module files.
                                     '''.format(sys.argv[0]))
    parser.add_argument('-s', '--server',
                        help='The name of the server in the mark2 tabs.')
    parser.add_argument('-i', '--input-modules', action=readable_dir,
                        help='''The path to the directory containing YAML
                                permission modules. If unspecified, a subdirectory
                                of the CWD named after the server is tried.''')
    parser.add_argument('-w', '--world', default='default',
                        help='''The name of a specific world to configure; treated
                                as the name of a subdirectory of the modules directory.
                                Leave unset/empty string for the default worlds.
                                Use "all" to signify all worlds.''')
    parser.add_argument('-m', '--modules', nargs='+', action='append',
                        help='''One or more module file names to load from the
                                --input-modules directory. This option can be
                                specified multiple times, and can be followed by
                                multiple file names each time. The '.yml' extension
                                can be omitted from file names. The purpose of this
                                option is to allow permissions to be added to a
                                module without having to load modules that have
                                not changed. The result will be that only the
                                commands to add permissions relating to the specified
                                modules will be issued. CAUTION: There is no analogously
                                minimal way to remove permissions. You need to remove
                                all permissions and re-add them all from scratch.
                                Caution is also advised when not working with the
                                default context (e.g. world 'all').''')
    parser.add_argument('-b', '--bperms-groups', type=argparse.FileType('r'),
                        help='''The path of a bPermissions groups.yml file to
                                read instead of module files. Overrides --input-modules.
                                Use this argument with -o to convert a bPermissions
                                groups.yml file into Module Files.''')
    parser.add_argument('-o', '--output-modules', action=writable_dir,
                        help='''The path to a directory where YAML module files
                                will be output. The directory must exist. A
                                module file will be generated for each permission
                                "stem": that part of the permission name that
                                precedes the first period, e.g. "bukkit" for
                                "bukkit.command.help".''')
    parser.add_argument('-p', '--plugin', default='LuckPerms',
                        help='The name of the permissions plugin.')
    parser.add_argument('-d', '--delete', action='store_true',
                        help='''Delete all permissions on the specified server
                                (and world if specified).''')
    parser.add_argument('-a', '--add', action='store_true',
                        help='''Add all permissions on the specified server
                        (and world if specified).''')
    parser.add_argument('-u', '--update', action='store_true',
                        help='''Update permissions; without this flag, commands
                                are logged but permissions not changed.''')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List combined groups, weights and permissions to stdout.')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging.')

    args = parser.parse_args()
    DEBUG = args.debug

    # If --modules is specified, it will be a list of lists. Flatten.
    if args.modules:
        args.modules = [item for sublist in args.modules for item in sublist]

    if DEBUG:
        print('# server:', args.server)
        print('# plugin:', args.plugin)
        print('# input_modules:', args.input_modules)
        print('# output_modules:', args.output_modules)
        print('# modules:', args.modules)
        print('# bPermissions:', args.bperms_groups.name if args.bperms_groups else None)
        print('# world:', args.world)
        print()

    # If no args are given, show short usage.
    if len(sys.argv) == 1:
        parser.print_usage()
        sys.exit(0)

    # Require a server name if commands will actually be sent.
    if args.update and args.server is None:
        error('you must specify the server name to send commands (-u/--update)')
        sys.exit(1)

    server = Server.withPermissionsPlugin(args.plugin, args.server, args.update)

    if args.bperms_groups:
        contextMap = {}
        contextMap[args.world] = loadBPermissions(args.bperms_groups)
    else:
        if not args.input_modules:
            args.input_modules = args.server
            if not args.input_modules:
                error('you need to specify a modules path or import from bPermissions')
                sys.exit(1)
            if not os.path.isdir(args.input_modules):
                error('the default modules path cannot be read:', args.input_modules)
                sys.exit(1)
        contextMap = loadContextMap(args.world, args.input_modules, args.modules)

    if args.list:
        listPermissions(contextMap[args.world])

    if args.output_modules:
        writeModuleFiles(contextMap[args.world], args.output_modules)

    if args.delete:
        if args.world == 'all':
            # Do 'default' context first.
            server.deletePermissions(contextMap, 'default')
            for world in sorted(set(contextMap.keys()) - set(['default'])):
                server.deletePermissions(contextMap, world)
        else:
            server.deletePermissions(contextMap, args.world)

    if args.add:
        if args.world == 'all':
            # Do 'default' context first.
            server.updatePermissions(contextMap, 'default')
            for world in sorted(set(contextMap.keys()) - set(['default'])):
                server.updatePermissions(contextMap, world)
        else:
            server.updatePermissions(contextMap, args.world)
