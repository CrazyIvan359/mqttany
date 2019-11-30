# Contributing to MQTTany

Thank you for taking the time to make a contribution!

<br><br>

## Branching

Active development happens on the `dev` branch, please make any Pull Requests
against that branch and not `master`.

## Submitting a PR

When submitting a new PR, please rebase to the tip of `dev` using the below
commands before submitting. Try to reduce the number of commits to close to 1,
use `f` at the start of the line to squash the commit while rebasing.

```text
git checkout dev
git pull dev
git checkout [YOUR-BRANCH]
git rebase -i dev
git push -f origin
```
