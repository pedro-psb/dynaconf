# Dynaconf 4 (development)

## Breaking Changes

* General Usage:
    * Main approach to defining settings is now based on a typed schema definition
    * Split Dynaconf class into 2: a data-like class (DataDict) and a manager class (DynaconfManager)
* Validation:
    * Default is no longer set in the validation process
    * More generally, the validation shouldn't modify the settings in any way
    * Validation is defined in the schema

## Highlights

* 
