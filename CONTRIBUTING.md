# Contributing to MQTTany

Thank you for taking the time to make a contribution!

## Adding Device Support

If you are looking to add support for a device that uses a protocol that already has a
module, like I2C or OneWire, it should be added to that module. The devices are
subclassed from a base class within the module, this simplifies adding support for new
devices because the module looks after all the bus communication. The GPIO module also
handles pin types this way (Digital, etc). Take a look in the module you are looking
to add a device to for the base class, it will contain documentation on how to subclass
it. You can also look at the existing devices to see what is possible.

## Writing a Module

MQTTany makes writing modules pretty simple, have a look in the `templates` directory
for documentation and template modules to help you get started.

## Submitting a PR

When submitting a new PR, please rebase to the tip of `master` using the below
commands before submitting. Try to reduce the number of commits to close to 1,
use `f` at the start of the line to squash the commit while rebasing.

```text
git checkout master
git pull master
git checkout [YOUR-BRANCH]
git rebase -i master
git push -f origin
```
