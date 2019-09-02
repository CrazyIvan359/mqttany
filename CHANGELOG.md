# Change Log

## 0.3.6

* __Added__: GPIO log entry if no pins match topic for SET.
* __Added__: Example module.
* __Added__: Logging automatically gets module name, call `logger.get_module_logger` with no args.
* __Fixed__: GPIO if `initial state` is not `payload on` or `payload off`, pin will be set to `payload off` and a warning displayed.
* __Added__: Config file verfication and path expansion.
* __Added__: Debug logging now shows process name.
* __Changed__: Subprocess loop moved to `modules.__init__.py`.
* __Fixed__: 2 things in GPIO??

## 0.3.5

* __Fixed__: Remove module validation check for `queue` that should have been removed.
* __Fixed__: GPIO interrupt log message print number instead of the word.

## 0.3.4

* __Changed__: GPIO message callbacks rewritten for effeciency gains and simplicity.
* __Added__: GPIO `initial state` option to specify the state of the pin when the module is loaded. Fixes #5
* __Fixed__: GPIO `set` payload as `bytes` not matching string `payload on`/`payload off`. Fixes #6
* __Fixed__: Queues not being accessible to all modules. Fixes #6

## 0.3.3

* __Fixed__: GPIO lock release causing process crashes
* __Fixed__: Fixed typo in configuration file `/set` should have been `/get`
* __Fixed__: Module name now display only the module name instead of `modules.[name]`
* __Added__: GPIO module `direction` default is now `input`
* __Fixed__: GPIO module `resistor` default is now `GPIO.PUD_OFF` instead of invalid `None`
* __Fixed__: Config `selection` type not adding value to config dict.
* __Fixed__: Modules loading in random order. MQTT module needs to be loaded first.
  Switched to `yamlloader` to load config sections in file order.
* __Fixed__: Added missing dependency `RPi.GPIO`

## 0.3.2

* __Fixed__: GPIO module was not updated when `resolve_topic` was changed in v0.3.1

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
