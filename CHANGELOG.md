# MQTTany Change Log

## 0.8.0

* **Added**
  * OneWire module, currently supports wire-1 and DS18x20.
  * GPIO module now supports pulsing a digital pin for a period of time.

* **Changed**
  * Non-standard imports now show custom ImportError messages if they are not installed.

* **Fixed**
  * GPIO add missing `initial state` info to example config.
  * GPIO fix signature of `gpio.pin.base` init to remove unused `pin_config`. Fixes #29
  * OneWire fix missing CRC8 bytes to hex in `validate_address` causing error when address
    provided in config is not 8 bytes.

## 0.7.3

* **Added**
  * GPIO `mode` setting to allow specifying pin numbering mode `BOARD`, `SOC`, or `WIRINGPI`.

* **Changed**
  * GPIO underlying library moved from `RPi.GPIO` to `wiringpi` to allow selecting pin number mode.
  * GPIO locks now handle pin numbering mode, locks always use `SOC` numbers.
  * GPIO default debounce time is now 50ms.

## 0.7.2

* **Added**
  * Log level `trace`, available by passing `-vv` when launching MQTTany.

* **Fixed**
  * I2C lock acquisition waiting full timeout before returning on successful bus lock ([#22](https://github.com/CrazyIvan359/mqttany/issues/22)).
  * MCP230xx log and publish wrong pin states if new state != old state ([#22](https://github.com/CrazyIvan359/mqttany/issues/22)).

## 0.7.1

* **Added**
  * Catch configuration file syntax errors and exit cleanly.

* **Changed**
  * GPIO remove dependence on `Adafruit-Blinka` and use `Adafruit-PlatformDetect`
    since that is the only component being used.

* **Fixed**
  * MCP230xx outdated key `device` in example configuration, should be `chip` ([#21](https://github.com/CrazyIvan359/mqttany/issues/21)).
  * MCP230xx fix missing log format key ([#21](https://github.com/CrazyIvan359/mqttany/issues/21)).

## 0.7.0

* **Added**
  * Log traceback on module import errors.

* **Changed**
  * Moved requirements to a folder.
  * GPIO module rewrite. Now uses pin classes and custom GPIO library wrappers
    to allow support of libraries for other boards.
  * `resolve_type` now tries to cast to `int` and `float` first.
  * Requirements now use `>=` and split board specific requirements.
  * MCP230xx logging cleaned up and made more uniform.

## 0.6.1

* **Fixed**
  * Import name errors in cleanup done for `v0.6.0`.

## 0.6.0

* ***BREAKING CHANGE***
  * GPIO and MCP230xx `topic poll` settings have been removed and now
    use the value of `topic get` for the same functions.

* **Changed**
  * MQTT `topic_matches_sub` now strips `/` to ensure absolute topics are matched.

* **Fixed**
  * GPIO not matching messages for pins with absolute topics because of leading `/`.

## 0.5.3

* **Fixed**
  * MCP230xx wrong pin state being published after setting pin.
    State was being read back from device too fast, now we cache the new state.
  * MCP230xx not matching messages for pins with absolute topics because of leading `/`.
  * MCP230xx incorrect types `(int, list)` for pin topics, should be `(str, list)`.
  * MCP230xx missing key `pin_name` in topic substitutions for pin topics.

## 0.5.2

* **Fixed**
  * Crash when parsing single relative topics.
    `literal_eval` throws a syntax error when passed a string starting with `/`.

## 0.5.1

* **Changed**
  * Improvements to service file.
  * Requirements separated based on modules.

* **Fixed**
  * MQTT prevent ability to provide reserved substitutions to `resolve_topic`.
  * MQTT absolute topics not being resolved correctly.
  * MQTT LWT messages are now retained.

## 0.5.0

* **Added**
  * MCP230xx module to support MCP23017 and MCP23008 I/O Expanders over I2C.

## 0.4.1

* **Added**
  * GPIO pin topics can now use `pin_name` substitution.

* **Fixed**
  * GPIO logging of logic state wrong if using `invert: true` for pin.
  * MQTT `resolve_topic` now replaces whitespace with `_`.
  * Argparse error where no verbosity would result in an invalid `NoneType` comparison.

## 0.4.0

* ***BREAKING CHANGE***
  * GPIO module configuration changed to friendly names for pin sections.
    Also supports configuring multiple pins in a single section, refer to example configuration file for details.

## 0.3.8

* **Added**
  * Provide MQTT client function `topic_matches_sub` directly from MQTT module.
  * `log_traceback` function to support printing stack traces when errors occur without processes crashing.

* **Changed**
  * Verify subprocess queue message `func` is callable before attempting to do so.

## 0.3.7

* **Added**
  * Command line argument parsing.
  * Configuration file can now be specified as a command line argument.

## 0.3.6

* **Added**
  * GPIO log entry if no pins match topic for SET.
  * Example module.
  * Logging automatically gets module name, call `logger.get_module_logger` with no args.
  * Config file verfication and path expansion.
  * Debug logging now shows process name.

* **Changed**
  * Subprocess loop moved to `modules.__init__.py`.

* **Fixed**
  * GPIO if `initial state` is not `payload on` or `payload off`, pin will be set to `payload off` and a warning displayed.
  * GPIO will write to log if it cannot match a message topic to a configured pin.

## 0.3.5

* **Fixed**
  * Remove module validation check for `queue` that should have been removed.
  * GPIO interrupt log message print number instead of the word.

## 0.3.4

* **Added**
  * GPIO `initial state` option to specify the state of the pin when the module is loaded. Fixes #5

* **Changed**
  * GPIO message callbacks rewritten for effeciency gains and simplicity.

* **Fixed**
  * GPIO `set` payload as `bytes` not matching string `payload on`/`payload off`. Fixes #6
  * Queues not being accessible to all modules. Fixes #6

## 0.3.3

* **Changed**
  * GPIO module `direction` default is now `input`

* **Fixed**
  * GPIO lock release causing process crashes
  * Fixed typo in configuration file `/set` should have been `/get`
  * Module name now display only the module name instead of `modules.[name]`
  * GPIO module `resistor` default is now `Resistor.OFF` instead of invalid `None`
  * Config `selection` type not adding value to config dict.
  * Modules loading in random order. MQTT module needs to be loaded first.
    Switched to `yamlloader` to load config sections in file order.
  * Added missing dependency `RPi.GPIO`

## 0.3.2

* **Fixed**
  * GPIO module was not updated when `resolve_topic` was changed in v0.3.1

## 0.3.1

* **Added**
  * `selection` type to configuration options. Allows limiting option to a list or mapping of choices.

* **Changed**
  * Improvements to `resolve_topic`. Can apply nested subtopics now.
    More substitutions available `module_topic`, `module_name`.
  * Improvements to GPIO locking. Now registers the module doing the locking and only that module can unlock.

## 0.3.0

* ***BREAKING CHANGE***
  * Move to single YAML configuration file instead of per module CONF files.

* **Fixed**
  * GPIO pin locks now work correctly, using `multiprocessing.Lock`s

## 0.2.0

* **Added**
  * GPIO Module. Currently supports RPi3
  * GPIO pin lock acquire/release. Does not work inter-process yet.

* **Changed**
  * Allow optional sections in configuration

* **Fixed**
  * Wrap `modules.load()` call in try/except to avoid issues where the main process crashes but children survive.
  * MQTT public functions now add messages to queue.
    Previously they would run in the calling process and fail because the MQTT client is running in another process.

## 0.1.0

Initial development release
