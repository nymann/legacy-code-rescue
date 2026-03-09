# Pitest Mutator Descriptions

Quick reference: mutator short name → what it does → how to kill it.

## DEFAULT_GROUP Mutators

### CONDITIONALS_BOUNDARY
**What it does:** Changes boundary conditions: `<` → `<=`, `<=` → `<`, `>` → `>=`, `>=` → `>`.
**How to kill:** Write a test with input exactly at the boundary value. If code says `x < 10`, test with `x = 10`.

### INCREMENTS
**What it does:** Replaces `++` with `--` and vice versa (both pre and post variants).
**How to kill:** Assert the incremented/decremented value after the operation. Loop counters and index updates are common targets.

### INVERT_NEGS
**What it does:** Removes unary negation: `-x` becomes `x`.
**How to kill:** Provide input where the sign matters and assert the result's sign or exact value.

### MATH
**What it does:** Replaces binary arithmetic operators: `+` → `-`, `-` → `+`, `*` → `/`, `/` → `*`, `%` → `*`, `&` → `|`, `|` → `&`, `^` → `&`, `<<` → `>>`, `>>` → `<<`, `>>>` → `<<`.
**How to kill:** Assert exact computed values. Use inputs where swapping the operator produces a different result (avoid identities like `x + 0` or `x * 1`).

### NEGATE_CONDITIONALS
**What it does:** Negates conditional checks: `==` → `!=`, `!=` → `==`, `<` → `>=`, `>=` → `<`, `>` → `<=`, `<=` → `>`.
**How to kill:** Test both the true and false branches of the conditional. Ensure both paths produce observably different results.

### VOID_METHOD_CALLS
**What it does:** Removes calls to void methods entirely.
**How to kill:** Assert the side effect of the void method call — state change, collection modification, output written, etc.

### EMPTY_RETURNS
**What it does:** Replaces return values with "empty" equivalents: `""` for String, `0` for int, `Collections.emptyList()` for lists, `Optional.empty()`, etc.
**How to kill:** Assert that the return value is non-empty / non-zero / non-default when it should be.

### FALSE_RETURNS
**What it does:** Replaces `return true` with `return false`.
**How to kill:** Test a scenario where the method must return `true` and assert the result.

### TRUE_RETURNS
**What it does:** Replaces `return false` with `return true`.
**How to kill:** Test a scenario where the method must return `false` and assert the result.

### NULL_RETURNS
**What it does:** Replaces return values with `null`.
**How to kill:** Assert the returned object is not null, or assert on a property of the returned object (which would NPE on null).

### PRIMITIVE_RETURNS
**What it does:** Replaces `int`/`long`/`float`/`double` returns with `0`, replaces `boolean` returns where the value is a non-zero literal.
**How to kill:** Assert the exact return value for non-zero cases.

## STRONGER Group (additional mutators)

### REMOVE_CONDITIONALS
**What it does:** Removes conditional statements entirely, forcing either the if-branch or else-branch unconditionally.
**How to kill:** Ensure both branches are reachable and produce different, asserted outcomes.

### NON_VOID_METHOD_CALLS
**What it does:** Replaces return values of non-void method calls with their type's default value (0, null, false).
**How to kill:** Assert the result of chained or intermediate method calls.

### CONSTRUCTOR_CALLS
**What it does:** Replaces `new Foo()` with `null`.
**How to kill:** Assert that constructed objects are not null, or that their methods work (any method call on null throws NPE).

### REMOVE_INCREMENTS
**What it does:** Removes increment/decrement operations entirely (the `i++` or `i--` is deleted, not the variable).
**How to kill:** Assert the state after the increment/decrement should have taken effect.

### EXPERIMENTAL_SWITCH
**What it does:** Changes switch statement default labels; replaces the first case with the default and vice versa.
**How to kill:** Test the default case and at least the first case of switch statements, asserting different outcomes.
