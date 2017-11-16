<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Contributing to Plover](#contributing-to-plover)
  - [Reporting Issues](#reporting-issues)
    - [Ask for Help](#ask-for-help)
    - [Search Open Issues](#search-open-issues)
    - [Create a New Issue](#create-a-new-issue)
      - [New Issue Template](#new-issue-template)
  - [Contributing Code](#contributing-code)
    - [Pull Request Template](#pull-request-template)
    - [Picking an Issue](#picking-an-issue)
    - [Code Style](#code-style)
    - [Commit Style](#commit-style)
    - [Review Workflow](#review-workflow)
    - [Labels](#labels)
      - [Pull Request Review Flow](#pull-request-review-flow)
      - [Issue Priority](#issue-priority)
      - [Issue Category](#issue-category)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Contributing to Plover

## Reporting Issues
Run into a problem?

### Ask for Help
If you're having trouble using or configuring Plover,
you might get more eyes on your problem
and more immediate help
by reaching out to the whole community:

- [The Plover Google Group](https://groups.google.com/forum/#!forum/ploversteno)
- [The Plover Discord Chat Server](https://discord.gg/0lQde43a6dGmAMp2)


### Search Open Issues
Start by searching the
[list of open issues](https://github.com/openstenoproject/plover/issues).

If you can find an issue that's the same as yours:

- You might learn of a workaround from the discussion thread.
- You might be able to provide the crucial detail needed to reproduce
  and resolve the issue by adding a new comment with your details.

### Create a New Issue

You can
[create a new issue](https://github.com/openstenoproject/plover/issues/new).

## Contributing Code
We welcome pull requests, and the response time is usually less than a week.

If you need to ping the devteam for feedback on a discussion,
you can mention @openstenoproject/developers to ping the whole team.

### Picking an Issue
Issues that have been added to the milestone
[plover-next](https://github.com/openstenoproject/plover/milestones/plover-next)
are already on the dev team's "hitlist", and they're probably already working
on them.

Anything else is up for grabs! Please drop a comment on an issue you're
starting work on, and push your work to your fork regularly,
so that we don't duplicate effort.

If you want feedback on your work before it's complete,
open a pull request and include `[WIP]` at the start of your PR title.


### Code Style
Plover is not yet PEP8 compliant, but please use PEP8 in what you add and
modify.

Prefer use of classes where possible, decoupling of UI and logic is very
important.


### Commit Style
Try to keep whitespace changes in a different commit.

Similarly, if you need to update the style of a file, do that independently
of substantive changes to the code.

Please try to keep the number of commits as low as
needed, where each commit represents a logical separation. If you write
something and then rewrite it in a later commit and submit a PR, it creates
history that the repository doesn't need. It's best to squash commits that
don't contribute to understanding your code.

In terms of overall development approach,
the [contribution guidelines of the Swift project](https://swift.org/contributing/#contributing-code)
with regard to incremental development
and commit messages
are sound advice for your work on Plover, as well.

For concrete details of the recommended commit message text formatting,
see [A Note About Git Commit Messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).


### Review Workflow
New features must be tested, the test suite must pass and the code must be
buildable for a PR to be considered. In the pull request message, try to
declare why you made your change. If it fixes any issues, then use GitHub's
"[fix #123]" magic phrase. Mention what platforms you've tested the code on.

If more testing is needed, the devteam will apply the
[needs-testing](https://github.com/openstenoproject/plover/labels/needs-testing)
label.

Read on for more about labels and the review workflow.


### Labels
The devteam use labels to coordinate work on Plover.
GitHub permissions limit the ability to add permissions to
[members of the Open Steno Project organization;](https://github.com/orgs/openstenoproject/people)
if you're not yet a member, you won't be able to apply or remove labels
yourself.

#### Pull Request Review Flow
PRs use very few labels.
They are not tagged as to whether they are
a bug fix or a new feature because usually the scope is pretty small and easy
to understand.

- **needs-testing:**
  The PR exists but still needs to be tested and reviewed.
  This is basically a flag for developers that this is in the queue to be
  looked at.
- **in-progress:**
  A devteam member is either testing or reviewing the PR.
  This serves as a way to remove the "needs-testing" flag so that we don't
  duplicate effort by having multiple persons reviewing the same PR.
- **ready-to-submit:**
  The review is finished, and all's well, but we're holding off on merging for
  some reason.
    - Please leave a comment stating why you're holding off merging and
      when you expect to merge if you apply this label to an issue.
- **waiting-on-author:**
  The review is done for now, and some changes are needed before the PR can be
  merged.
    - Feedback comments will have been left on the PR and/or patches
      explaining the changes needed.
- **blocked-awaiting-external:**
  This work cannot be merged until another event has occurred.
  That event might be another issue getting resolved or another PR
  getting merged first.
  Either way, the labeled issue cannot continue being worked on until something
  else happens first.
    - Please leave a comment stating why you're holding off merging and
      when you expect to merge if you apply this label to an issue.


#### Issue Priority
Issues are classified by priority: low, medium, high, or critical.

- **Critical** means that the current version of Plover is unusable and needs
  a rerelease.
- **High** means short term.
- **Medium** means that it's desirable for a decent amount of people, or that
  it's a trivial task so getting it done won't take too much effort so why not
  do it.
- **Low** priority is either for things that we don't plan to work on but want
  to keep around, or for things that are very big in scope.


#### Issue Category
Unlike PRs, issues are categorized as one of:
Bug, feature-request, question, task, wishlist.

- **Bug** is something wrong in the code.
  This label will be accompanied by another label to give its state:
  - **needs-discussion** for clarification
  - **needs-testing** to reproduce the bug (especially true of machine-specific
    problems that require special hardware)
  - **confirmed** for bugs that have successfully been reproduced

- A **feature-request** represents a request for new functionality
  to be added to Plover.
  These will be prioritized as described in the previous section.
  - A [**wishlist** issue](https://github.com/openstenoproject/plover/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Awishlist)
    is an accepted feature request
    that the Plover developers would like to implement.
    This is an excellent label for would-be contributors to review.

- **Task** is something that needs to get done, like documentation, creating
  a testing environment, writing a contributing.md, making a release. Basically
  meta stuff around the Open Steno Project.

- The **duplicate** tag is added to issues when closing them as duplicates.

- The **invalid** tag is used when there's an issue that's not actually
  a problem, but maybe we want to keep it around as a note to clarify docs or
  something.
