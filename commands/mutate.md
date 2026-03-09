---
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Edit
  - Write
  - Agent
---

# /mutate — Autonomous Mutation Testing Loop

You are an autonomous mutation-killing agent. Run a pitest baseline, then iteratively write tests to kill surviving mutations. Auto-commit each kill. Continue until all mutations are dead or the user stops you.

**IMPORTANT:** Be concise in your output. Minimize token usage. Do not explain mutation testing concepts — just do the work.

## Setup

Determine the plugin directory by finding `parse-mutations.py`:
```bash
PLUGIN_DIR="$(dirname "$(which parse-mutations.py 2>/dev/null || find ~/.claude/plugins/local/mutation-skill -name parse-mutations.py -print -quit 2>/dev/null)")"
PLUGIN_DIR="$(cd "$PLUGIN_DIR/.." && pwd)"
```
If that fails, search for the plugin at `~/.claude/plugins/local/mutation-skill`. Store this path — all script references use it.

## Phase 0 — Setup & Baseline

1. Detect the build tool:
   ```bash
   BUILD_TOOL=$(bash "$PLUGIN_DIR/scripts/detect-build-tool.sh")
   ```

2. **Check if pitest is configured** in the project:
   - Maven: check if `pom.xml` contains `pitest-maven` (use Grep)
   - If pitest is **not configured**, add it automatically:
     ```bash
     python3 "$PLUGIN_DIR/scripts/add-pitest-config.py" pom.xml
     ```
     This detects the Java version, picks the right pitest version, adds JUnit 5 plugin if needed, and sets targetClasses from the groupId.
   - Print what was added (the script outputs a summary).
   - Note: for Gradle, tell the user to add the plugin manually (print the snippet from SKILL.md) and stop.

3. Check if `.pitest-baseline/mutations.xml` exists in the project root.

4. **If no baseline exists:**
   - Run full pitest:
     - Maven: `mvn test pitest:mutationCoverage -DoutputFormats=XML -DtimestampedReports=false`
     - Gradle: `./gradlew pitest`
   - Create `.pitest-baseline/` directory (add it to `.gitignore` if not already there)
   - Copy the mutations.xml to `.pitest-baseline/mutations.xml`
     - Maven: from `target/pit-reports/mutations.xml`
     - Gradle: find it under `build/reports/pitest/`
   - Run summary: `python3 "$PLUGIN_DIR/scripts/parse-mutations.py" .pitest-baseline/mutations.xml --summary`
   - Print the summary counts and proceed

5. **If baseline exists:** Skip to Phase 1.

## Phase 1 — Pick a Mutation

Run:
```bash
python3 "$PLUGIN_DIR/scripts/parse-mutations.py" .pitest-baseline/mutations.xml
```

This outputs JSON lines to stdout (one per surviving mutation, sorted: NO_COVERAGE first, then SURVIVED, grouped by class, by line). Summary stats go to stderr.

- Read the **first line** of stdout — this is the next mutation to kill.
- Parse the JSON: `mutatedClass`, `mutatedMethod`, `sourceFile`, `lineNumber`, `mutator`, `mutatorShortName`, `status`.
- If there are **no surviving mutations**, report success: "All mutations killed!" and **stop**.

## Phase 2 — Show Minimal Context

1. Find the source file using Glob: `**/<sourceFile>` (from the mutation JSON).
2. Read ~11 lines around the mutation: use Read with `offset: lineNumber - 5` and `limit: 11`.
3. Read the mutator description from `$PLUGIN_DIR/skills/mutation-testing/references/mutator-descriptions.md` to understand what the mutator does.
4. Print a **one-line summary**:
   > Line {N} of {SourceFile}: pitest {mutator description}. Status: {status}.

## Phase 3 — Write a Test

1. Determine the test directory structure:
   - Find existing tests: `Glob("**/src/test/**/*Test.java")` or `*Test.java` / `*Tests.java`
   - Look for an existing test class for the mutated class: `{ClassName}Test.java`
   - If none exists, create one in the matching test package directory

2. Read the existing test class (if any) to understand imports, patterns, and style.

3. Read the source class fully (the mutated method at minimum) to understand what to test.

4. Write a focused test method:
   - Name: `test{MethodName}_detectsMutationAtLine{N}` (camelCase the method name)
   - Target the specific mutation: use boundary values, assert exact results, test both branches — whatever is needed for this mutator type
   - Follow the existing test style (JUnit 4 vs 5, assertion library, setup patterns)
   - Add any missing imports

5. If adding to an existing test class, use Edit to insert the method. If creating a new file, use Write.

## Phase 4 — Verify the Kill

1. Get the surviving mutators for the target class:
   ```bash
   MUTATORS=$(python3 "$PLUGIN_DIR/scripts/parse-mutations.py" .pitest-baseline/mutations.xml --surviving-mutators <mutatedClass>)
   ```

2. Run targeted pitest:
   ```bash
   REPORT=$(bash "$PLUGIN_DIR/scripts/run-pitest.sh" "$BUILD_TOOL" "<mutatedClass>" "<testClass>" "$MUTATORS")
   ```
   Where `<testClass>` is the fully qualified test class name.

3. Parse the new report:
   ```bash
   python3 "$PLUGIN_DIR/scripts/parse-mutations.py" "$REPORT"
   ```

4. Check: is the specific mutation (matching class + method + lineNumber + mutator) now KILLED in the new report?

## Phase 5 — Handle Result

### If KILLED:
1. **Update baseline**: Copy the new mutations.xml over the relevant entries in `.pitest-baseline/mutations.xml`. The simplest approach: for each mutation in the new report that is KILLED, update its status in the baseline file. Use `python3` or direct XML manipulation.

   Practical approach: replace the entire baseline with a merged view. Read both XMLs. For any mutation in the new report that is KILLED, update the matching mutation in the baseline (match on mutatedClass + mutatedMethod + lineNumber + mutator). Write the updated baseline back.

2. **Auto-commit**:
   ```bash
   git add <test-file>
   git commit -m "test: kill <mutatorShortName> mutation in <ClassName>:<lineNumber>"
   ```

3. Print: `Killed {mutatorShortName} in {ClassName}:{lineNumber}. Committed.`

4. **Loop back to Phase 1** immediately.

### If NOT KILLED:
1. **Rollback** the test file:
   ```bash
   git checkout -- <test-file>
   ```
   If the file is new (not tracked), use `rm <test-file>` instead.

2. Print: `Failed to kill {mutatorShortName} in {ClassName}:{lineNumber}. Retrying...`

3. **Retry** with a different test approach (up to 2 retries total):
   - On retry 1: Try a different assertion strategy or test input values
   - On retry 2: Try testing from a different angle (e.g., integration-style test, or test a calling method)

4. After 2 failed retries, **skip** this mutation:
   - Print: `Skipping {mutatorShortName} in {ClassName}:{lineNumber} after 2 retries.`
   - Mark it internally so you don't pick it again (add the mutation signature to a skip list)
   - **Loop back to Phase 1** to pick the next mutation.

## Important Rules

- **Never ask the user for input.** This is fully autonomous.
- **Minimize output.** One-line status per mutation. No explanations unless something goes wrong.
- **Keep running** until all mutations are killed, all remaining are skipped, or the user interrupts.
- **Only commit test files.** Never commit source changes.
- **Use targeted pitest runs** (Phase 4) — never re-run full pitest after the baseline.
- **Preserve existing tests.** When editing test files, only add new methods — never modify or delete existing test methods.
