# MQTTany Documentation Source

This branch contains the source files for the documentation of MQTTany.

If you have a contribution to the docs, please make a PR against this branch
not the `gh-pages` branch.

## Build Process

1. Run `make gh` in repo root to generate html files.
2. Switch to `ghpages` branch.
3. Run `copydocs` to copy the html out of the build folder.
4. Commit and push to `ghpages` branch.
