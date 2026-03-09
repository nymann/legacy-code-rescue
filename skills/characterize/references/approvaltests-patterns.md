# ApprovalTests Patterns & Recipes

## Common Patterns

### Basic Approval
```java
Approvals.verify(object);  // calls toString()
Approvals.verify(formattedString);
```

### Combination Approval (Most Used)
```java
CombinationApprovals.verifyAllCombinations(
    (a, b, c) -> function(a, b, c),
    arrayOfA, arrayOfB, arrayOfC
);
```

### Verify Array/Collection
```java
Approvals.verifyAll("header", items, item -> item.toString());
```

### Verify Exception
```java
Approvals.verify(ExceptionUtils.getStackTrace(
    assertThrows(Exception.class, () -> riskyMethod())
));
```

## Input Selection Recipes

### Numeric Boundaries
For code with `if (x > threshold)`:
```java
Integer[] values = {threshold - 1, threshold, threshold + 1};
```

### String Matching
For code with `if (name.equals("Special"))`:
```java
String[] names = {"Special", "Normal", "", null};
```

### Enum-like Inputs
For code branching on a type:
```java
String[] types = {"typeA", "typeB", "typeC", "unknown"};
```

### State Combinations
For objects with mutable state:
```java
// Test all meaningful state combinations
Boolean[] flags = {true, false};
Integer[] counts = {0, 1, Integer.MAX_VALUE};
```

## Approved File Management

### File Location
Approved files are created next to the test class:
```
src/test/java/com/example/
├── MyClassTest.java
├── MyClassTest.characterize_method.approved.txt
```

### Gitignore Pattern
Add to `.gitignore`:
```
*.received.txt
```

### Approving Output
```bash
# Copy all received files to approved
find . -name "*.received.txt" -exec sh -c \
  'cp "$1" "${1%.received.txt}.approved.txt"' _ {} \;
```

## Handling Tricky Cases

### Non-Deterministic Output
Scrub before verifying:
```java
String output = getOutput();
output = output.replaceAll("\\d{4}-\\d{2}-\\d{2}", "[DATE]");
output = output.replaceAll("[0-9a-f-]{36}", "[UUID]");
Approvals.verify(output);
```

### Large Objects
Use a custom toString or formatter:
```java
CombinationApprovals.verifyAllCombinations(
    (input) -> {
        Result r = process(input);
        return String.format("status=%s, count=%d", r.getStatus(), r.getCount());
    },
    inputs
);
```

### Multiple Side Effects
Capture all relevant state:
```java
(input) -> {
    obj.process(input);
    return String.format("field1=%s\nfield2=%s\nlistSize=%d",
        obj.getField1(), obj.getField2(), obj.getList().size());
}
```

### Void Methods
Capture state before and after:
```java
(input) -> {
    MyClass obj = new MyClass(input);
    String before = obj.toString();
    obj.voidMethod();
    String after = obj.toString();
    return String.format("before: %s\nafter:  %s", before, after);
}
```
