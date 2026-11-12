# Git Branching

A branch is a movable pointer to a commit. Create one with `git switch -c feature-name`.

A common workflow is to create a branch for each feature, commit small changes with clear messages, open a pull request, and merge after review.

Use `git rebase` to keep history linear, but never rebase commits that other people have already pulled.
