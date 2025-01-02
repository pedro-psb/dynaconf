# Core

## Overview Workflow

This is an overview of the main data organization.
(The names are not supposed to match the implementation)

```
* Core:
    * LoadRequestQ
    * Namespaces:
        * Namespace-0:
            * LoadedQ
            * PatchQ
            * LazyPatchQ
        * (...)
        * Namespace-k:
            * LoadedQ
            * PatchQ
            * LazyPatchQ
```

## Load Workflow

The core holds the LoadRequest Queue and is responsible for calling the
correct loader and distributing the data into the correct namespaces (ns).
It also holds several Registries for loaders, patch_operations, etc.

```
                                         ----> (ns-0) LoadedQ
                                        |         .
(core) LoadRequestQ -- load_pending() --|         .
                                        |         .
                                         ----> (ns-n) LoadedQ
```

## Merge Workflow

Each namespace is represented by a NamespaceState, which holds queues
for pending intermediary datastructures, like loaded data (but not merged),
patches ready to be applied and lazy patches, that should be applied later.

In this step, tokens, converteres and dynamic values are evaluated when
possible or moved to the lazyQ.

```
     namespace-k
    +------------------------------------------------+
    | base: DataDict                                 |
    |                                                |
    |    pending_loaded Q                            |
    |          |                                     |
    |          | create_patch(loaded) -> Patch       |
    |          |                                     |
    |    pending_patch Q                             |
    |          |                                     |
    |          | apply_patch(base, Patch) -> Patch   |
    |          |                                     |
    |  pending_patch_lazy Q                          |
    |          |                                     |
    |          | apply_lazy_patch(base, Patch)       |
    |          x                                     |
    +------------------------------------------------+
```

## Default System

The 'default' namespace (ns-default) always exist and it's content is the access-time
fallback for when the activate namespace doesnt contain the requested key. The system
is a simple implementation of a ChainMap using dynaconf internals.

The ns-default content comes first from the schema declaration, then from loaded data.

For example, given the namespace content:

* ns-default = {'a': 0, 'b': 0}
* ns-dev = {'a': 1}

Then:

```python
>>> settings['a']  # active env has the key, use its value
1
>>> settings['b']  # activate env dont have the key, try ns-default
0
>>> settings['c']  # ns-default doesnt have it either
KeyError: ...
```
