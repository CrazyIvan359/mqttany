# MQTTany Change Log

## Development

### Major Core Rewrite

This release is a big one! The core functionality has been almost completely rewritten
in order to make things a lot simplier for modules. There is now a standardized message
bus that modules use, instead of calling functions directly in other modules. This
abstraction also paves the way for adding other communication modules. However, as with
anything, there was a price; a lot of things have changed and a few features were dropped.

One of the major goals of this rewrite is to bring [Homie](https://homieiot.github.io/specification/)
support to MQTTany. In order to do that it was necessary to abstract the way interface
modules connect to communication modules. This means that interface modules must now
provide more details on the data they export, but can no longer directly specify topics.

Internally the new message bus largely resembles the Homie convention in order to have all
details required for it. This means that topics must now have a minumum depth of 2 (ex.
`{node}/{property}`, `gpio/1`) and absolute topics are no longer supported.

Due to the number of changes, you will need to go over the documentation for each module
you are using and update your configuration file to work with the new options and changes.
If you were using default MQTT topics you will likely not have to change your home
automation setup much in order to interface with this version of MQTTany.

* ***BREAKING CHANGE***
  * Absolute and custom topic support removed. This means all `topic` options in config
    will now be ignored. **See the documentation for each module to see how paths work.**
  * **GPIO** Digital pins now report their state as `ON` or `OFF`.
  * **GPIO** Digital pins no longer support time only or comma separated messages for
    pulse commands, only JSON is supported now.
  * **I2C** MCP230xx pins now report their state as `ON` or `OFF`.
  * **I2C** MCP230xx pins no longer support time only or comma separated messages for
    pulse commands, only JSON is supported now.
  * **LED** Options specific to output methods are now in a nested section inside the
    array definition. See the documentation for details.
  * **LED** Animations can only be called with JSON on path `{array_id}/animation/set`.
  * **OneWire** Options specific to devices are now in nested sections inside the device
    definition. See the device documentation for details.
  * **GPIO** - Change language for `direction` to `pin mode` to be less specific and lay
    ground work for additional pin modes.

* **Added**
  * Colorized log output to terminal.
  * `.pylintrc` file.
  * GitHub Actions for pylint and black checks.
  * Python version check before importing anything with a minimum version requirement.
  * Import checking for the core requirements with log entries for missing packages.
  * Template modules and documentation to help with creating new modules.
  * Config file version key. This will prevent MQTTany from running with an outdated
    config file that may cause errors or strange behavior. Config version number will
    incriment when incompatible changes occur in the config format.
  * Config option flag `secret` to obfuscate values in the log for passwords, etc.
  * **I2C** If `bus` is a number, checks for path `/dev/i2c{bus}` as well as
    `/dev/i2c-{bus}` now.
  * `udev` rule files to help with hardware permissions.

* **Changed**
  * Convert all string formatting to use *f-strings*. This change means you must be using
    a minimum Python version of 3.6.
  * Convert all logging to use lazy formatting. This should save some time building log
    messages for disabled log levels.
  * Logger `get_module_logger` now uses entire module name after `modules` instead of
    only selecting the element after the last period.
  * Move `mprop` requirement up into core, now modules don't need to make sure it is
    installed.
  * **MQTT** - Messages arriving on ``{node}/{property}/+/#`` will match and the callback
    for the property will be called. The callback should further inspect the topic before
    taking action.
  * **LED** - Remove the modified version of `libsacn` that was bundled with the LED module.
    The needed modifications are now available upstream in version 1.4.5.
  * **LED** - Move the `fps` option from module config to array config allowing per-array
    FPS setting. This is now published when the array is setup also.
  * Updated Adafruit Platform Detect version from 1.x to 2.x.
  * Consolidate `get_module_logger` and `get_logger` into single function and remove
    leading `mqttany` from all logger names.
  * `log_traceback` now formats entire traceback into a single log entry with correct
    indentation to match other log messages.

* **Fixed**
  * Remove requirements file for old MCP230xx module that was removed in v0.10.0.
  * Fix logger checking if ``TRACE`` logging was enabled for ``WARN`` messages.
  * Core not exiting correctly if an exception occurred in the core.
  * Logging not truncating process name or logger name, this could have resulted in
    misaligned log entries.

## 0.11.0

* **Added**
  * XSET module to allow sending `xset` commands to control screensaver,
    screen power options, etc.

* **Changed**
  * Begin using Python Black code formatter. This has resulted in a massive commit as
    there are changes to most files. All changes made by Black have been reviewed and
    no errors were found.

* **Fixed**
  * MQTT not handling absolute topics correctly.
  * Incorrect reference to `rpiGPIO` in ODroid GPIO interface.

## 0.10.3

* **Fixed**
  * I2C device MCP230xx throwing `TypeError: can only concatenate list (not "int") to list`
    when initializing devices. [(#43)](https://github.com/CrazyIvan359/mqttany/issues/43)

## 0.10.2

* **Fixed**
  * Dependency issue with Adafruit Platform Detect reaching version 2.x. [(#41)](https://github.com/CrazyIvan359/mqttany/issues/41)
  * All requirements files updated to prevent similar issues.

## 0.10.1

* **Fixed**
  * I2C device MCP230xx highest pin index out of range error.
  * OneWire module error `object has no attribute 'CONF_KEY_TOPIC_SETTER'`
  * Module loader crashing when trying to delete module that failed to load.

## 0.10.0

* ***BREAKING CHANGE***
  * MCP230xx module has been removed as its functionality has been replaced
    by the MCP230xx device profiles in the new I2C module.
  * LED configuration refactored to better allow different outputs.
  * LED ``anim frame min`` setting replaced with ``anim fps`` which is used to
    calculate frame duration. This setting is more user friendly.

* **Added**
  * MQTT heartbeat messages, currently status and version only.
  * LED add white channel to `test.order` animation.
  * I2C module for I2C communication.
  * I2C support for MCP230xx devices including output pulsing.
  * LED interface for DMX output using the sACN protocol.

* **Changed**
  * Move active development to `dev` branch, master branch is stable release only.
  * Moved `Direction`, `Resistor`, and `Interrupt` enums to global common.

* **Fixed**
  * Incorrect naming of keyword `__all__`.
  * GPIO incorrect imports and exports in `common`.
  * LED array topic getting root and module topics added twice.
  * MQTT typo in assignment of `on_connect` callback causing it to never be called.

## 0.9.0

* **Added**
  * LED module for controlling WS281x and similar LED arrays.

* **Fixed**
  * Actually remove `.lower()` from key check in *selection* type config
    values. It was mistakenly not removed in [`08d66f4`](https://github.com/CrazyIvan359/mqttany/commit/08d66f46316755a361c1f6f817b22010a24470a8).
  * Config value not being set in *selection* type if options are a `list`.

## 0.8.2

* **Added**
  * Logging ``warn`` method as the built-in one is depreciated in Python 3.7.

* **Changed**
  * Signal handler now used in all subprocesses. This should help stop orphaned
    processes remaining after a crash. They will respond to `SIGTERM`.
  * MQTT moved log entry for unknown message to `TRACE`.

* **Fixed**
  * Removed `.lower()` from key check in *selection* type config value validation.
    This was leftover from an early draft and should have been removed.
  * GPIO now catches errors from system calls to _wiringpi_ command `gpio`.

## 0.8.1

* **Added**
  * GPIO module now supports Odroid boards C1, C1+, C2, XU3, XU4, and N2.

* **Changed**
  * GPIO now relies on `getGPIO()` to determine board compatibility. It returns `None`
    if no library is available to access GPIO on this board.
  * Clear configuration from memory once loaded, saves some overhead in subprocesses.

* **Fixed**
  * MCP230xx cleanup pin configured log entries.
  * OneWire cleanup logging on device configured and during bus scan.
  * GPIO must use `SOC` pin numbering when disabling pin interrupts using `gpio` command.

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
