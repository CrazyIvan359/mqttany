# Contributing to MQTTany

Thank you for taking the time to make a contribution!

<br><br>

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
