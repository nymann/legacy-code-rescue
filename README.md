# Legacy Code Rescue

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills toolkit for rescuing legacy Java code. Three skills that follow the workflow from Michael Feathers' *Working Effectively with Legacy Code*:

```
/find-seam  →  /characterize  →  /mutate
```

1. **`/find-seam`** — Identify untestable code and apply minimal, behavior-preserving refactoring patterns (Extract & Override, Parameterize Constructor, etc.) to create test seams.

2. **`/characterize`** — Pin current behavior with combination approval tests using [ApprovalTests.Java](https://github.com/approvals/ApprovalTests.Java). Documents what the code *actually does*, not what it *should do*.

3. **`/mutate`** — Autonomous loop that runs [pitest](https://pitest.org/) mutation testing, writes targeted tests to kill surviving mutations, verifies each kill, and auto-commits. Uses the STRONGER mutator group by default.

## Install

```bash
git clone https://github.com/nymann/legacy-code-rescue.git
cd legacy-code-rescue
./install.sh
```

This symlinks the skills into `~/.claude/skills/`. Restart Claude Code to activate.

## Usage

Open a Java project (Maven or Gradle) in Claude Code and run the skills in order:

```
/find-seam          # make legacy code testable (skip if no external deps)
/characterize       # pin behavior with approval tests
/mutate             # kill surviving mutations
```

Each skill is autonomous — it analyzes the code, makes changes, verifies them, and commits. `/mutate` loops until all mutations are killed or you stop it.

### What `/mutate` does on each iteration

1. Picks the next surviving mutation (NO_COVERAGE first, then SURVIVED)
2. Reads ~11 lines around the mutation, looks up the mutator type
3. Writes a targeted test to kill it
4. Runs a scoped pitest (only the target class + surviving mutators)
5. If killed: updates baseline, commits. If not: rolls back, retries up to 2x, then skips.

### Auto-configuration

If pitest isn't configured in your `pom.xml`, `/mutate` adds it automatically with the correct version for your Java source level:

| Java version | pitest-maven version |
|---|---|
| 8 - 10 | 1.17.4 |
| 11+ | 1.18.1 |

JUnit 5 plugin is added automatically if Jupiter is detected.

## Project structure

```
legacy-code-rescue/
├── install.sh                              # Symlink skills into ~/.claude/skills/
├── skills/
│   ├── find-seam/
│   │   ├── SKILL.md                        # /find-seam skill
│   │   └── references/
│   │       └── feathers-patterns.md        # Feathers pattern catalog
│   ├── characterize/
│   │   ├── SKILL.md                        # /characterize skill
│   │   └── references/
│   │       └── approvaltests-patterns.md   # ApprovalTests recipes
│   └── mutate/
│       ├── SKILL.md                        # /mutate skill
│       └── references/
│           └── mutator-descriptions.md     # Pitest mutator lookup table
├── scripts/
│   ├── add-pitest-config.py                # Add pitest to pom.xml
│   ├── detect-build-tool.sh                # Detect Maven vs Gradle
│   ├── parse-mutations.py                  # Parse mutations.xml → JSON lines
│   └── run-pitest.sh                       # Run scoped pitest
└── test-fixtures/
    └── gilded-rose/                        # Gilded Rose kata (git submodule)
```

## Test fixture

The [Gilded Rose Refactoring Kata](https://github.com/emilybache/GildedRose-Refactoring-Kata) is included as a submodule for testing the full workflow:

```bash
cd test-fixtures/gilded-rose/Java
# then run /characterize → /mutate
```
