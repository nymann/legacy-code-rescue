---
triggers:
  - mutation testing
  - pitest
  - surviving mutations
  - mutation score
  - kill mutations
  - mutation coverage
---

# Mutation Testing with Pitest

## What is Mutation Testing?

Mutation testing measures test suite effectiveness by introducing small faults (mutations) into source code and checking whether tests detect them. A mutation is "killed" if at least one test fails; it "survives" if all tests pass despite the change. The mutation score (killed / total) is a stronger quality metric than line or branch coverage.

**Pitest** is the standard mutation testing tool for Java/JVM. It modifies bytecode at the class level, runs only relevant tests per mutation, and is significantly faster than source-level mutation tools.

## Key Concepts

- **Mutant**: A single change to the program (e.g., `<` → `<=`).
- **Killed**: A test failed when the mutant was applied — the test detects the fault.
- **Survived**: All tests passed with the mutant — a gap in the test suite.
- **No Coverage**: No test executes the mutated line at all.
- **Equivalent mutant**: A mutation that produces identical behavior to the original — cannot be killed. These are rare but exist.
- **Mutation score**: `killed / (total - equivalent)` — aim for > 80%.

## Pitest Configuration Essentials

### Maven
```xml
<plugin>
  <groupId>org.pitest</groupId>
  <artifactId>pitest-maven</artifactId>
  <version>1.17.4</version>
  <configuration>
    <targetClasses>
      <param>com.example.*</param>
    </targetClasses>
    <targetTests>
      <param>com.example.*Test</param>
    </targetTests>
    <mutators>
      <mutator>DEFAULTS</mutator>
    </mutators>
    <outputFormats>
      <param>XML</param>
      <param>HTML</param>
    </outputFormats>
    <timestampedReports>false</timestampedReports>
  </configuration>
</plugin>
```

Run: `mvn test pitest:mutationCoverage`

### Gradle
```kotlin
plugins {
    id("info.solidsoft.pitest") version "1.15.0"
}

pitest {
    targetClasses.set(listOf("com.example.*"))
    targetTests.set(listOf("com.example.*Test"))
    mutators.set(listOf("DEFAULTS"))
    outputFormats.set(listOf("XML", "HTML"))
    timestampedReports.set(false)
}
```

Run: `./gradlew pitest`

## Test-Writing Strategies for Killing Mutations

### 1. Assert exact values, not just non-null
```java
// Weak — survives MATH, PRIMITIVE_RETURNS
assertNotNull(calculator.add(2, 3));

// Strong — kills MATH, PRIMITIVE_RETURNS
assertEquals(5, calculator.add(2, 3));
```

### 2. Test boundary values for CONDITIONALS_BOUNDARY
```java
// If code has: if (age >= 18)
// Test exactly at the boundary:
assertTrue(service.isAdult(18));   // kills >= → >
assertFalse(service.isAdult(17));  // kills >= → <
```

### 3. Test both branches for NEGATE_CONDITIONALS
```java
// Always test true AND false paths
assertTrue(validator.isValid(goodInput));
assertFalse(validator.isValid(badInput));
```

### 4. Verify side effects for VOID_METHOD_CALLS
```java
// If code calls list.add(item) — a void method
service.process(item);
assertEquals(1, repository.count());  // verify the side effect happened
```

### 5. Avoid test values that are identity elements
```java
// BAD: x + 0 == x - 0, so MATH mutant survives
assertEquals(5, calculator.add(5, 0));

// GOOD: different result if + becomes -
assertEquals(8, calculator.add(5, 3));
```

### 6. Test return value content, not just type
```java
// Weak — survives EMPTY_RETURNS
assertNotNull(service.findUsers());

// Strong — kills EMPTY_RETURNS and NULL_RETURNS
assertEquals(3, service.findUsers().size());
assertEquals("Alice", service.findUsers().get(0).getName());
```

## Running the Mutation Skill

Use `/mutate` to start an autonomous loop that:
1. Runs a pitest baseline (or uses existing one)
2. Picks surviving mutations one at a time (NO_COVERAGE first)
3. Writes a targeted test to kill each mutation
4. Verifies the kill with a scoped pitest run
5. Auto-commits on success, retries or skips on failure

See `references/mutator-descriptions.md` for a full lookup table of what each mutator does and how to kill it.
