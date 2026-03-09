---
triggers:
  - find seam
  - make testable
  - legacy code
  - extract and override
  - parameterize constructor
  - working effectively with legacy code
  - michael feathers
  - untestable
  - hard-coded dependency
---

# Finding Seams in Legacy Code

A **seam** is a place where you can alter behavior without editing the code at that point. The concept comes from Michael Feathers' "Working Effectively with Legacy Code." Seams make untestable code testable by creating substitution points for dependencies.

## Why Seams Matter

Legacy code typically can't be tested because:
- Dependencies are created internally (`new Service()` inside methods)
- Static calls can't be substituted
- Constructors do real work, preventing subclassing
- Hidden globals/singletons couple everything

A seam breaks these couplings with minimal, behavior-preserving changes.

## Core Patterns

### Extract & Override (The Workhorse)

The most commonly used pattern. Works when a method calls something you can't control.

```java
// Before — untestable (can't substitute the service call)
public void process(Order order) {
    boolean valid = PaymentService.validate(order.getPayment());
    if (valid) { /* ... */ }
}

// After — seam created
protected boolean validatePayment(Payment payment) {
    return PaymentService.validate(payment);
}
public void process(Order order) {
    boolean valid = validatePayment(order.getPayment());
    if (valid) { /* ... */ }
}

// In test — override the seam
OrderProcessor testProcessor = new OrderProcessor() {
    @Override protected boolean validatePayment(Payment p) {
        return true; // controlled by test
    }
};
```

**When to use:** Method-level dependencies, static calls, complex object creation.

### Parameterize Constructor

```java
// Before
public class ReportGenerator {
    private final DataSource ds;
    public ReportGenerator() {
        this.ds = new ProductionDataSource();
    }
}

// After — both constructors exist
public class ReportGenerator {
    private final DataSource ds;
    public ReportGenerator() { this(new ProductionDataSource()); }
    public ReportGenerator(DataSource ds) { this.ds = ds; }
}
```

**When to use:** Constructor creates its own dependencies.

### Wrap Method

```java
// Before — need to add logging but can't modify process()
public void process(Order order) { /* complex logic */ }

// After
private void processOriginal(Order order) { /* same logic, renamed */ }
public void process(Order order) {
    log(order);
    processOriginal(order);
}
```

**When to use:** Adding cross-cutting behavior without touching existing logic.

### Introduce Instance Delegator

```java
// Before — static utility calls everywhere
total = MathUtils.calculateTax(subtotal, rate);

// After — injectable delegator
public class TaxCalculator {
    public double calculateTax(double subtotal, double rate) {
        return MathUtils.calculateTax(subtotal, rate);
    }
}
```

**When to use:** Pervasive static utility usage that needs substitution.

## Decision Guide

| Problem | Pattern | Risk |
|---------|---------|------|
| `new` in constructor | Parameterize Constructor | Very low |
| Static call in method | Extract & Override | Low |
| Need to add behavior | Wrap Method | Low |
| Static utility everywhere | Introduce Instance Delegator | Medium |
| Concrete class dependency | Extract Interface | Medium |

## Safety Rules

1. **Never change behavior.** The refactoring must be purely structural.
2. **Keep existing API.** Add new constructors/methods alongside originals.
3. **Compile after every change.** Small steps, verified continuously.
4. **One seam at a time.** Don't batch refactorings.
5. **Run existing tests after each change.** If any test breaks, the refactoring changed behavior — undo it.

## Workflow

Use `/find-seam` to automatically identify testability issues and apply these patterns. Then use `/characterize` to write approval tests that pin the behavior through the new seams.
