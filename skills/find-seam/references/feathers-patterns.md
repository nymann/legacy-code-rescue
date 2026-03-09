# Feathers Patterns Quick Reference

Patterns from "Working Effectively with Legacy Code" by Michael Feathers, organized by the problem they solve.

## I can't get this class into a test harness

| Problem | Pattern | Description |
|---------|---------|-------------|
| Constructor creates dependencies | **Parameterize Constructor** | Add constructor that accepts dependencies; original delegates to it |
| Constructor does too much work | **Extract & Override Factory Method** | Move creation logic to a protected method; override in test subclass |
| Hidden dependency in constructor | **Supersede Instance Variable** | Add a setter or second constructor to replace the hidden dep after construction |
| Too many constructor parameters | **Extract Interface** on groups of params | Group related params into an interface/object |

## I can't run this method in a test

| Problem | Pattern | Description |
|---------|---------|-------------|
| Method calls static/global | **Extract & Override** | Extract the call to a protected method; override in test |
| Method has a side effect I can't see | **Extract & Override** the side effect | Move the effect into an overridable method |
| Method uses `new` internally | **Extract & Override Factory Method** | Move the `new` call to a protected method |
| Method is private | Test through the public method that calls it | Don't make private methods public for testing |

## I need to change this code but have no tests

| Situation | Approach |
|-----------|----------|
| Small change, clear behavior | Write characterization tests first, then change |
| Large change, tangled code | Sprout Method/Class — write new code in a new testable method/class, call from old code |
| Need to add feature | **Wrap Method** — rename original, create wrapper with old name |
| Code is too big to understand | **Scratch refactoring** — refactor freely to understand, then revert and do it properly with tests |

## Key Concepts

### Object Seam
Override a method in a subclass to change behavior at the seam.
- **Enabling point:** The place where you decide which class to instantiate (constructor, factory).

### Link Seam
Substitute a dependency at link time (classpath manipulation, dependency injection).
- **Enabling point:** The configuration file, DI container, or classpath setup.

### Preprocessing Seam
Substitute behavior via preprocessing (rare in Java — more relevant in C/C++).

## The Legacy Code Change Algorithm

1. **Identify change points** — what code needs to change?
2. **Find test points** — where can you observe the behavior?
3. **Break dependencies** — create seams to make it testable
4. **Write tests** — characterization tests to pin current behavior
5. **Make changes and refactor** — with the safety net of tests
