# Brancher

Brancher is a tool inspired by git flow that is more flexible in how it handles branching. It allows any configuration of branches and simply makes it easier to see which commits are in what branch, as well as advancing changes between branches. A typical branch layout may be like this:

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     develop     ├──▶│     staging     ├──▶│      beta       ├──▶│     master*     │
└─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘

                                                                 *production branch
```

**Note**: Brancher can handle other configurations, assuming there's one final "production" branch and any number of sequential pre-production branches to the left of it.

## Installation

```shell
pip3 install gitbrancher
```

## Available Commands

Commands:

- overview (o): Prints an overview of branches with outstanding commits
- forward (f): Fast forwards commits into branch
- backfix (b): Applies changes on more advanced branches to current one
- init: Initialize repo

Add `-h` to any command for usage details.

## Usage

### Initialization
Let's start with an example of an empty repo.

![First Commit](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-01-first-commit.png)

Next, initialize Brancher. Brancher will store your branching model in your repository's local configuration.

![Brancher init](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-02-init.png)

### Advancing commits

Now let's start some development work.

![Development work](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-03-dev-work.png)

That looks good, so we'll advance that commit to `staging`, the next branch after `develop`.

![Advancing commits](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-04-forward.png)

While `staging` is having some Q/A work done, we'll continue development in `develop`:

![More development work](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-05-more-dev-work.png)

### Commit overview

With pending commits in `develop` and `staging`, let's get an overview of what commits exist where.

![Overview](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-06-overview.png)

### Backfilling hotfixes

With development work ongoing and Q/A happening on `staging`, let's make an urgent bugfix to production. As you can see, once that commit has been made, it only exists on the `master` branch, not other branches.

![Hotfix to production](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-07-hotfix.png)

We want to bring that hotfix back into `develop`. After checking out `develop`, we'll apply the hotfix to develop too:

![Backfix to staging](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-08-backfix.png)

An overview confirms that the backfilled changes have been applied to `develop`, but not `beta` or `staging`:

![Overview hotfix](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-09-overview-hotfix.png)

We can remedy this by applying the hotfix to those environments, also:

![Backfill beta](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-10-backfix-beta.png)

![Backfill stagign](https://raw.githubusercontent.com/kkinder/brancher/master/docs/ss-11-backfix-staging.png)

