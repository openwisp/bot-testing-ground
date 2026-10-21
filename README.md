# Bot Testing Ground

This repository contains focused fixtures for testing OpenWISP automation.

The version fixtures represent the two Python version layouts used by OpenWISP
packages:

- `version_fixture_package` defines `VERSION` at the package root.
- `version_fixture_submodule.version` defines `VERSION` in a version submodule,
  which `version_fixture_submodule` re-exports.

Both fixtures expose `VERSION` and `__version__` as version tuples while
remaining free of runtime dependencies.
