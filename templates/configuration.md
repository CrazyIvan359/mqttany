# Configuration

MQTTany's configuration parser takes on the task of validating configuration formatting
and basic type checking.

## Basics

You must describe the options to the parser in a `collections.OrderedDict` like this:

```python
from collections import OrderedDict

CONF_KEY_ANY = "any"
CONF_KEY_SUBSECTION = "sub section"

CONF_OPTIONS = OrderedDict(
    [
        (  # an empty dict means any value is valid and the option is required
            CONF_KEY_ANY,
            {}
        ),
        (  # subsections are also possible and can be nested.
            CONF_KEY_SUBSECTION,
            {
                # they must have their type set to 'section'
                "type": "section",
                # if a subsection is optional you must specify this, if this
                # is omitted the subsection is assumed to be required.
                "required": False,
                # keys can be reused in subsections
                CONF_KEY_ANY: {},
            }
        ),
    ]
)
```

Given the above set of `CONF_OPTIONS`, the parser would take the below configuration
and return the `dict` below that to the caller, assuming the module name is `example`.

```yaml
example:
  any: this is a string

  sub section:
    any: string in subsection
    unknown key: 0

  unlisted subsection:
    any: this won't get you anything
```

```python
{
    "any": "this is a string",
    "sub section":
    {
        "any": "string in subsection"
    },
}
```

Note that anything not described in the `CONF_OPTIONS` passed to the parser will be
ignored.

## Typing

Basic typing can be done by specifying the type in the option:

```python
(
    CONF_KEY_TYPED, {"type": bool}
)
```

The parser uses a custom type resolver in order to match some special strings. This
function is available for use by modules if needed by importing `resolve_type` from the
`config` module.

* First it checks for case insensitive `true` or `false` strings and returns a boolean
  if a match is found.
* Next it checks for a case insensitive `none` string and returns `None` if found.
* If no string matches are found it will attempt to cast to an `int`.
* Failing that it will attempt to cast to a `float`.
* If none of the above have worked so far, it will attempt a call to `ast.literal_eval`
  and return the result. Only `ValueError` and `SyntaxError` will be ignored in this
  call, all others will be raised.
* If all attempts to cast the value to a type fail, the passed value is returned as is.

## Defaults

An option can have a default value to use in the event one is not given in the config
file. If a default value is provided then the option is assumed to be optional and the
config will be valid even if it is not present in the file. Default values are returned
as is and are not type checked.

```python
(CONF_KEY_OPTIONAL, {"type": bool, "default": False})
```

## Selection Options

Selection type options are like enumerations, you provide a `list` or `dict` of values
that are acceptable. If you provide a `list` then the value will be the matching
element. If a `dict` was provided then the valid options are the keys, but the value of
the matching key will be in the dictionary returned by the parser. This is useful to
match a string for user friendliness to an otherwise ambiguous value.

```python
(
    CONF_KEY_SELECTION_LIST,
    {
        "selection": {"option 1": 10, "option 2": 20},
        "default": None
    }
)
```

The example above would return the internally used value while allowing the user to
provide a plain text value in the config file. This also demonstrates how the skipping
of type checks on the default value can be used to return `None` if no value was given.
This can simplify module code in certain cases.

## Regex Options

It is possible to use regex patterns to match multiple subsections with unknown names.
This is used, for example, by the GPIO module to match any subsection which are then
handled as pin configurations.

The key should be in the form of `"regex:{pattern}"` where `{pattern}` is the expression
to match. If the pattern could match one of the fixed name options in the config it
**MUST** go after that option in the configuration description. Options are parsed in
the order they appear in `CONF_OPTIONS` and are removed from the config data as they are
matched. If the regex matches one of your fixed name options and the regex is parsed
first, it will consume the fixed name option.

This is the entire base configuration description of the GPIO module. This is not the
full description though, options from the different pin classes are collected and
combined with this base to form the full description. See the next section for more
details on that.

```python
CONF_KEY_MODE = "mode"
CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_PIN = "pin"
CONF_KEY_NAME = "name"
CONF_KEY_FIRST_INDEX = "first index"
CONF_KEY_DIRECTION = "direction"
CONF_KEY_INVERT = "invert"

CONF_OPTIONS = OrderedDict(
    [
        (
            CONF_KEY_MODE,
            {
                "default": Mode.SOC,
                "selection": {
                    "BOARD": Mode.BOARD,
                    "board": Mode.BOARD,
                    "SOC": Mode.SOC,
                    "soc": Mode.SOC,
                    "BCM": Mode.SOC,
                    "bcm": Mode.SOC,
                    "WIRINGPI": Mode.WIRINGPI,
                    "wiringpi": Mode.WIRINGPI,
                    "WiringPi": Mode.WIRINGPI,
                },
            },
        ),
        (CONF_KEY_POLL_INT, {"type": float, "default": 0.0}),
        (
            "regex:.+",
            {
                "type": "section",
                "required": False,
                CONF_KEY_PIN: {"type": (int, list)},
                CONF_KEY_NAME: {"type": (str, list), "default": "{pin}"},
                CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
                CONF_KEY_DIRECTION: {"default": Direction.INPUT, "selection": {}},
                CONF_KEY_INVERT: {"type": bool, "default": False},
            },
        ),
    ]
)
```

## Combining Options from Multiple Files

The GPIO module and others have a plugin like system for their components. In the case
of the GPIO module it has a base pin class that specific pin types inherit from. This
means that adding a new type of pin does not require any modification to the core of the
module, simply subclassing the base class is required. Each of these specific pin types
have configuration options unique to them that need to be collected. The module loader
collects these options and combines them with the base description like so:

In `gpio.pin__init__` there is a function that collects all the options:

```python
def updateConfOptions(conf_options):
    """
    Returns a copy of ``conf_options`` updated with options from each pin type.
    """
    conf_options = update_dict(conf_options, digital.CONF_OPTIONS)
    return conf_options
```

And in `gpio.core` these are added to the base description before calling the parser.
_ **NOTE** that the regex element is pushed to the end of the `dict` to make sure it
  doesn't gulp any of the options with fixed names.

```python
def load(config_raw: dict = {}):
    ...
    conf_options = updateConfOptions(CONF_OPTIONS)
    conf_options.move_to_end("regex:.+")
    config_data = parse_config(config_raw, conf_options, log)
    ...
```

If we combine the base description and that of `gpio.pin.digital` we end up with this
being passed to the parser:

```python
CONF_OPTIONS = OrderedDict(
    [
        (
            CONF_KEY_MODE,
            {
                "default": Mode.SOC,
                "selection": {
                    "BOARD": Mode.BOARD,
                    "board": Mode.BOARD,
                    "SOC": Mode.SOC,
                    "soc": Mode.SOC,
                    "BCM": Mode.SOC,
                    "bcm": Mode.SOC,
                    "WIRINGPI": Mode.WIRINGPI,
                    "wiringpi": Mode.WIRINGPI,
                    "WiringPi": Mode.WIRINGPI,
                },
            },
        ),
        (CONF_KEY_POLL_INT, {"type": float, "default": 0.0}),
        (CONF_KEY_DEBOUNCE, {"type": int, "default": 50}),
        (
            "regex:.+",
            {
                "type": "section",
                "required": False,
                CONF_KEY_PIN: {"type": (int, list)},
                CONF_KEY_NAME: {"type": (str, list), "default": "{pin}"},
                CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
                CONF_KEY_DIRECTION: {"default": Direction.INPUT, "selection": {}},
                CONF_KEY_INVERT: {"type": bool, "default": False},
                CONF_KEY_DIRECTION: {
                    "selection": {
                        "input": Direction.INPUT,
                        "in": Direction.INPUT,
                        "output": Direction.OUTPUT,
                        "out": Direction.OUTPUT,
                    }
                },
                CONF_KEY_INTERRUPT: {
                    "default": Interrupt.NONE,
                    "selection": {
                        "rising": Interrupt.RISING,
                        "falling": Interrupt.FALLING,
                        "both": Interrupt.BOTH,
                        "none": Interrupt.NONE,
                    },
                },
                CONF_KEY_RESISTOR: {
                    "default": Resistor.OFF,
                    "selection": {
                        "pullup": Resistor.PULL_UP,
                        "up": Resistor.PULL_UP,
                        "pulldown": Resistor.PULL_DOWN,
                        "down": Resistor.PULL_DOWN,
                        "off": Resistor.OFF,
                        "none": Resistor.OFF,
                    },
                },
                CONF_KEY_INITIAL: {"type": bool, "default": False},
            },
        ),
    ]
)
```
