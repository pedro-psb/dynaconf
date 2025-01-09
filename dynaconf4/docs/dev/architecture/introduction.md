
## Design Principles

There are some core ideas that drove development of the current design.
They are:

1. **Privacy layers:** Defined layers and API between public and internal objects.
2. **Data Pipieline:** Unique data flow and control API for data ingest/transformation (load, merge, evalute, ...)
3. **Compatibility**: Most important legacy features should be supported.

### Privacy Layers

There are two main layers, the user and the core.

The user layer includes (among other utilities):

* `dynaconf.Dynaconf`: The initialization object or function, which bootstraps dynaconf.
* `dynaconflib.datastructures.DataDict`: A setting object (of type `DataDict`) which should be very close to a dictionary and with the minimum
  amount of modifications possible (soon I'll break that rule).
* `dynaconf.DynaconfApi(?)`(Optional) An public API object that provide extra dynaconf facilities, such as fine controling load
  order and options, merge rules, validation and extension. E.g, aceesible by `settings.DYNACONF`.

The core layer includes:

* `dynaconflib.core.DynaconfCore`: A single manager object that holds everything togheter.
* `dynaconflib.datastructures`: Several datastructures and algorithms for storing and processing data.
* `dynaconflib.core.DyaconfCore.process_api`: A single process api which provides a simple control command for the data processing.

The goal is to have a clear separation of context and predictable coupling.
E.g, core components never rely on user components.

### Data Pipeline

...
