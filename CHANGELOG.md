# Change Log

## 0.3.1

* __Added__: `selection` type to configuration options. Allows limiting option to a list or mapping of choices.
* __Changed__: Improvements to `resolve_topic`. Can apply nested subtopics now.
  More substitutions available `module_topic`, `module_name`.
* __Changed__: Improvements to GPIO locking. Now registers the module doing the locking and only that module can unlock.

## 0.3.0

* __BREAKING CHANGE__: Move to single YAML configuration file instead of per module CONF files.
* __Fixed__: GPIO pin locks now work correctly, using `multiprocessing.Lock`s

## 0.2.0

* __Fixed__: Wrap `modules.load()` call in try/except to avoid issues where the main process crashes but children survive.
* __Added__: GPIO Module. Currently supports RPi3
* __Added__: GPIO pin lock acquire/release. Does not work inter-process yet.
* __Changed__: Allow optional sections in configuration
* __Fixed__: MQTT public functions now add messages to queue.
  Previously they would run in the calling process and fail because the MQTT client is running in another process.

## 0.1.0

* Initial Beta release
