---
triggers:
  - characterization test
  - approval test
  - approval testing
  - pin behavior
  - combination testing
  - golden master
  - snapshot test
  - characterize
  - CombinationApprovals
  - approvaltests
---

# Characterization Testing with ApprovalTests

## What is a Characterization Test?

A characterization test captures what code *actually does*, not what it *should do*. You run the code, record the output, and approve it as the baseline. Any future change that alters behavior breaks the test — giving you a safety net for refactoring.

The term comes from Michael Feathers: "A characterization test is a test that characterizes the actual behavior of a piece of code."

## ApprovalTests.Java

[ApprovalTests](https://github.com/approvals/ApprovalTests.Java) is the standard library for approval testing in Java. It captures output as text, compares against an approved file, and fails on any difference.

### Setup

Maven:
```xml
<dependency>
  <groupId>com.approvaltests</groupId>
  <artifactId>approvaltests</artifactId>
  <version>24.9.0</version>
  <scope>test</scope>
</dependency>
```

Gradle:
```kotlin
testImplementation("com.approvaltests:approvaltests:24.9.0")
```

### Key Classes

- `Approvals.verify(object)` — capture a single output
- `CombinationApprovals.verifyAllCombinations(function, inputs...)` — test all input combinations
- Approved files: `*.approved.txt` (committed to repo)
- Received files: `*.received.txt` (generated on test run, gitignored)

## Combination Approval Testing

The most powerful technique for legacy code. Instead of writing individual test cases, you define input dimensions and test every combination automatically.

```java
@Test
void characterize_calculatePrice() {
    String[] customerTypes = {"regular", "premium", "employee"};
    Integer[] quantities = {0, 1, 5, 100};
    Double[] unitPrices = {0.0, 9.99, 99.99};

    CombinationApprovals.verifyAllCombinations(
        (type, qty, price) -> {
            PriceCalculator calc = new PriceCalculator();
            return String.valueOf(calc.calculate(type, qty, price));
        },
        customerTypes, quantities, unitPrices
    );
}
```

This generates 3 × 4 × 3 = 36 test cases in one method. The approved file shows every combination and its result.

### Choosing Input Values

Read the source code to find interesting values:

1. **Boundary values**: If code checks `quantity > 10`, test 9, 10, 11
2. **Magic strings**: If code compares `name.equals("Aged Brie")`, include that exact string
3. **Zero/null/empty**: The universal edge cases
4. **Domain extremes**: Min/max values the code handles (e.g., quality 0 and 50 in Gilded Rose)
5. **Special cases**: Values that trigger different branches

### Handling State Changes

For void methods or methods with side effects, capture the state after:

```java
CombinationApprovals.verifyAllCombinations(
    (name, sellIn, quality) -> {
        Item item = new Item(name, sellIn, quality);
        GildedRose app = new GildedRose(new Item[]{item});
        app.updateQuality();
        return String.format("sellIn=%d, quality=%d", item.sellIn, item.quality);
    },
    names, sellIns, qualities
);
```

### Handling Non-Determinism

If code uses timestamps, random numbers, or system state:
1. Use seams (from `/find-seam`) to control the non-deterministic input
2. Or scrub the output: replace timestamps with `[TIMESTAMP]` before verification

## Workflow

1. `/find-seam` — make the code testable (if needed)
2. `/characterize` — pin current behavior with combination approval tests
3. Refactor with confidence — any behavior change breaks a test
4. `/mutate` — strengthen the test suite by killing surviving mutations

## Tips

- **Approve immediately.** The first run output IS the approved output — you're documenting reality.
- **Commit approved files.** They're part of your test suite.
- **Add `*.received.txt` to `.gitignore`.** These are transient.
- **One test per public method.** Use combinations to cover breadth.
- **Don't judge the output.** If the code returns wrong results for edge cases, that's what the characterization test captures. Fix bugs later, after you have the safety net.
