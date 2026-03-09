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

# /characterize — Pin Legacy Code Behavior with Approval Tests

You are a characterization testing agent. Your job is to write approval tests that capture the current behavior of legacy code — not what it *should* do, but what it *actually does*. These tests act as a safety net for future refactoring.

**IMPORTANT:** Be concise. Characterization tests document reality, not intent. Do not judge the code's behavior — just pin it.

## Setup

Determine the plugin directory (same as `/mutate`):
```bash
PLUGIN_DIR="$(find ~/.claude/plugins/local/mutation-skill -name parse-mutations.py -print -quit 2>/dev/null)"
PLUGIN_DIR="$(cd "$(dirname "$PLUGIN_DIR")/.." && pwd)"
```

Detect build tool:
```bash
BUILD_TOOL=$(bash "$PLUGIN_DIR/scripts/detect-build-tool.sh")
```

## Phase 0 — Identify the Target

1. Determine what to characterize:
   - If user mentioned a class/method, use that.
   - Otherwise, look for the main production class (largest, most complex, or least tested).

2. Read the target class fully. Identify:
   - All public methods (these are the behaviors to pin)
   - Constructor parameters and dependencies
   - State that affects behavior (fields set in constructor, mutable state)
   - Return types and side effects
   - Edge cases visible in the code (null checks, boundary conditions, special cases in if/switch)

3. Print brief analysis:
   > **Characterizing {ClassName}** — {N} public methods, {M} dependencies
   > Methods: `updateQuality()`, `toString()`, ...

## Phase 1 — Check for ApprovalTests Dependency

1. Check if `com.approvaltests:approvaltests` is in pom.xml / build.gradle:
   ```bash
   grep -q "approvaltests" pom.xml 2>/dev/null
   ```

2. **If not present**, add it:
   - Maven: add to `<dependencies>` in pom.xml:
     ```xml
     <dependency>
       <groupId>com.approvaltests</groupId>
       <artifactId>approvaltests</artifactId>
       <version>24.9.0</version>
       <scope>test</scope>
     </dependency>
     ```
   - Gradle: add `testImplementation("com.approvaltests:approvaltests:24.9.0")`

3. Verify it resolves:
   ```bash
   mvn dependency:resolve -q  # or ./gradlew dependencies --configuration testCompileClasspath -q
   ```

## Phase 2 — Write Characterization Tests

### Strategy: Combination Approval Testing

For each public method, use `CombinationApprovals.verifyAllCombinations()` to test across all interesting input combinations.

1. **Identify input dimensions** for each method:
   - Constructor args / object state that varies
   - Method parameters
   - For each dimension, pick values: typical, boundary, null/empty, special cases from the code

2. **Create the test class**: `{ClassName}CharacterizationTest.java` in the test directory.

3. **Write combination approval tests:**

```java
import org.approvaltests.combinations.CombinationApprovals;
import org.junit.jupiter.api.Test;

class GildedRoseCharacterizationTest {

    @Test
    void characterize_updateQuality() {
        String[] names = {"Aged Brie", "Backstage passes to a TAFKAL80ETC concert",
                          "Sulfuras, Hand of Ragnaros", "Normal Item"};
        Integer[] sellIns = {-1, 0, 1, 5, 10, 11};
        Integer[] qualities = {0, 1, 2, 48, 49, 50};

        CombinationApprovals.verifyAllCombinations(
            (name, sellIn, quality) -> {
                Item[] items = new Item[]{new Item(name, sellIn, quality)};
                GildedRose app = new GildedRose(items);
                app.updateQuality();
                return String.format("sellIn=%d, quality=%d", items[0].sellIn, items[0].quality);
            },
            names, sellIns, qualities
        );
    }
}
```

4. **Key principles for choosing input values:**
   - Read the code for magic numbers, string comparisons, boundary checks — use those exact values
   - Always include boundary ±1 (e.g., if code checks `> 0`, test with `-1, 0, 1`)
   - Include null/empty where the type allows it and code doesn't obviously reject it
   - For strings compared with `.equals()`, include the exact strings from the code
   - Keep combinations manageable — 3-5 values per dimension, not exhaustive

5. **For methods with side effects** (void methods, state changes):
   - Capture the object state after the call
   - Return a string representation of the relevant state
   - Example: `return obj.toString()` or `return String.format("field1=%s, field2=%d", obj.field1, obj.field2)`

6. **For methods with dependencies** (if seams exist from `/find-seam`):
   - Use simple test doubles via the seams (subclass and override, or pass mocks via parameterized constructor)
   - Keep doubles minimal — just return fixed values

## Phase 3 — Run and Approve

1. Run the characterization tests (they will fail on first run — no approved file yet):
   ```bash
   mvn test -pl . -Dtest={TestClassName} -DfailIfNoTests=false 2>&1 | tail -5
   ```

2. The first run creates a `.received.txt` file. This captures actual behavior.

3. **Approve the output** — copy received to approved:
   ```bash
   find . -name "*.received.txt" -exec sh -c 'cp "$1" "${1%.received.txt}.approved.txt"' _ {} \;
   ```

4. Run tests again — they should now pass:
   ```bash
   mvn test -pl . -Dtest={TestClassName}
   ```

5. If tests fail after approval, investigate: non-determinism (timestamps, random), ordering issues, or environment dependencies. Fix the test to be deterministic.

## Phase 4 — Verify Coverage & Commit

1. Check that the characterization tests cover the main code paths. Quick sanity check:
   - Every public method should have at least one combination test
   - Every branch-relevant value from the source should appear in the test inputs

2. Print summary:
   > **Characterization tests for {ClassName}:**
   > - `characterize_updateQuality()` — 4 names × 6 sellIns × 6 qualities = 144 combinations
   > - All approved. Tests pass.
   >
   > Run `/mutate` to find remaining test gaps.

3. Auto-commit:
   ```bash
   git add <test-file> <approved-files>
   git commit -m "test: add characterization tests for <ClassName>"
   ```

## Important Rules

- **Pin actual behavior, not expected behavior.** If the code has a bug, the characterization test captures the bug. That's correct — you're documenting reality.
- **Never modify production code.** Characterization tests only add test files.
- **Use CombinationApprovals** as the default approach. Only fall back to simple `Approvals.verify()` for methods with no meaningful input variation.
- **Approve the first run output.** Don't hand-craft approved files — let the code tell you what it does.
- **Keep test inputs derived from the source code.** Read the conditionals, magic values, and boundaries in the code — those become your test values.
- **Commit approved files with the tests.** They are part of the test suite.
