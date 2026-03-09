---
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Edit
  - Write
  - Agent
triggers:
  - find seam
  - make testable
  - legacy code
  - change legacy
  - working effectively with legacy code
  - michael feathers
  - untestable
  - hard-coded dependency
  - where does this happen
  - trace dependency
---

# /find-seam — Explore Legacy Code and Prepare It for Change

You are a legacy code exploration partner. The user has a change they want to make — maybe specific ("add a retry to the MQ call"), maybe vague ("somewhere we send to IBM MQ and wait for a reply, I want to replace that"). Your job is to **find where the behavior lives**, **map the change surface**, and **create seams** so the code can be safely tested and modified.

This is collaborative. Ask questions. Share what you find. Think out loud.

## Phase 0 — Understand the Goal

1. **Listen to what the user wants to change.** It might be:
   - A behavior: "we send a message to a queue and wait for a reply"
   - A dependency: "we talk to IBM MQ somewhere, I want to migrate to REST"
   - A feature: "I need to add retry logic to the payment processing"
   - A bug: "something goes wrong when the order has more than 100 items"

2. **Extract search terms** from the description. Think about:
   - Class/package names (the user might know some)
   - Library imports (`com.ibm.mq`, `javax.jms`, `software.amazon.awssdk`, etc.)
   - String literals, queue names, URL patterns, config keys
   - Interface or method names that hint at the behavior

3. **Don't assume you know the codebase.** Start by exploring.

## Phase 1 — Find Where the Behavior Lives

Use multiple search strategies in parallel to locate the relevant code:

1. **Search for imports/dependencies** — library-specific imports are the fastest signal:
   ```
   Grep for "import com.ibm.mq" or "import javax.jms" etc.
   ```

2. **Search for domain terms** — string literals, config keys, method names:
   ```
   Grep for queue names, URLs, feature flags, domain-specific terms the user mentioned
   ```

3. **Search for structural patterns** — interfaces, base classes, annotations:
   ```
   Grep for @JmsListener, @RabbitListener, @KafkaListener, etc.
   ```

4. **Follow the call chain** — once you find a hit, trace callers:
   - Who calls this method? Who constructs this class?
   - Where is this interface implemented? Where is it injected?
   - Use Grep for the class/method name to find call sites.

5. **Report what you find** as you go — don't wait until you've mapped everything:
   > Found `OrderMessageSender` (src/main/java/.../OrderMessageSender.java) — sends to `ORDER.REQUEST` queue via JMS template.
   > Called from `OrderService.submitOrder()` at line 47.
   > Reply received in `OrderReplyListener` — listens on `ORDER.REPLY` queue.

## Phase 2 — Map the Change Surface

Once you've found the relevant code, summarize the **change surface** — everything the user needs to understand before making their change:

1. **The behavior chain**: entry point → processing → external interaction → result handling
2. **The dependencies**: what external systems, libraries, or infrastructure is involved?
3. **The blast radius**: what other code depends on this? What breaks if it changes?
4. **The test situation**: are there existing tests? What's covered, what's not?

Present this as a brief map:
> **Change surface for MQ migration:**
> - `OrderService.submitOrder()` → `OrderMessageSender.send()` → JMS → `ORDER.REQUEST` queue
> - Reply: `OrderReplyListener.onMessage()` ← JMS ← `ORDER.REPLY` queue
> - `OrderService` blocks on a `CountDownLatch` waiting for the reply
> - No tests for `OrderMessageSender` or `OrderReplyListener`
> - `OrderService` has 3 callers: `OrderController`, `BatchProcessor`, `RetryScheduler`

## Phase 3 — Create Seams

Now that the change surface is mapped, create the minimum seams needed to get this code under test. This is where Feathers patterns apply — but targeted at the specific change, not a generic cleanup.

**Ask the user before applying seams:** "I'd suggest extracting the MQ interaction behind an interface so we can test OrderService without a real queue. Want me to proceed?"

### Patterns (apply the least invasive one that works):

**Parameterize Constructor** — when the class creates its own dependency:
```java
// Add a constructor that accepts the dependency; keep the original
public OrderService() { this(new OrderMessageSender()); }
public OrderService(OrderMessageSender sender) { this.sender = sender; }
```

**Extract Interface** — when you need to substitute the whole interaction:
```java
// Extract interface from the concrete class
public interface OrderGateway {
    OrderReply submitOrder(Order order);
}
// Existing class implements it; new implementation can use REST instead of MQ
```

**Extract & Override** — when a method calls something you can't control:
```java
// Move the external call into a protected method
protected OrderReply sendToQueue(Order order) { /* MQ logic */ }
// Override in tests to return canned responses
```

### After each seam:
1. Verify it compiles:
   ```bash
   ./mvnw compile -q  # or ./gradlew compileJava -q (use ./mvnw if present, else mvn)
   ```
2. Run existing tests to confirm no behavioral change:
   ```bash
   ./mvnw test -q  # or ./gradlew test -q
   ```

## Phase 4 — Summarize and Hand Off

Print a summary of what was found and what was done:
> **Exploration complete:**
> - Found MQ interaction in `OrderMessageSender` and `OrderReplyListener`
> - Change surface: 3 classes, 2 queues, 3 callers
> - Created seam: extracted `OrderGateway` interface from `OrderMessageSender`
> - `OrderService` now depends on `OrderGateway` (injectable)
>
> **Next steps:**
> - Run `/characterize` to pin current behavior of `OrderService`
> - Implement `RestOrderGateway` as a new `OrderGateway` implementation
> - Run `/mutate` to verify test strength

Auto-commit the seam changes:
```bash
git add <modified-files>
git commit -m "refactor: extract <InterfaceName> to decouple <ClassName> from <Dependency>"
```

## Important Rules

- **This is collaborative.** Ask the user questions when the codebase is ambiguous. Share findings as you go. Don't disappear into a 20-file exploration and come back with a monologue.
- **Explore before you act.** Don't start creating seams until you and the user agree on what the change surface looks like.
- **Never change behavior.** Seams are structural only. The code must do exactly what it did before.
- **Prefer adding code over modifying code.** New constructors, interfaces, wrapper methods — not changes to existing signatures.
- **Minimum viable seams.** Only create what's needed for the immediate change. Don't refactor the whole class.
- **Compile after every change.** Small steps, verified continuously.

## Reference: Feathers Patterns

See `references/feathers-patterns.md` for the complete pattern catalog with decision guide.
