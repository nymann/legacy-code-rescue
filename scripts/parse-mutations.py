#!/usr/bin/env python3
"""Parse pitest mutations.xml → JSON lines (surviving mutations) or summary."""

import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter

# Full class name → short CLI name mapping
MUTATOR_SHORT_NAMES = {
    "org.pitest.mutationtest.engine.gregor.mutators.ConditionalsBoundaryMutator": "CONDITIONALS_BOUNDARY",
    "org.pitest.mutationtest.engine.gregor.mutators.IncrementsMutator": "INCREMENTS",
    "org.pitest.mutationtest.engine.gregor.mutators.InvertNegsMutator": "INVERT_NEGS",
    "org.pitest.mutationtest.engine.gregor.mutators.MathMutator": "MATH",
    "org.pitest.mutationtest.engine.gregor.mutators.NegateConditionalsMutator": "NEGATE_CONDITIONALS",
    "org.pitest.mutationtest.engine.gregor.mutators.VoidMethodCallMutator": "VOID_METHOD_CALLS",
    "org.pitest.mutationtest.engine.gregor.mutators.EmptyObjectReturnValsMutator": "EMPTY_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.FalseReturnValsMutator": "FALSE_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.TrueReturnValsMutator": "TRUE_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.NullReturnValsMutator": "NULL_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.PrimitiveReturnsMutator": "PRIMITIVE_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.returns.EmptyObjectReturnValsMutator": "EMPTY_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.returns.FalseReturnValsMutator": "FALSE_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.returns.TrueReturnValsMutator": "TRUE_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.returns.NullReturnValsMutator": "NULL_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.returns.PrimitiveReturnsMutator": "PRIMITIVE_RETURNS",
    "org.pitest.mutationtest.engine.gregor.mutators.RemoveConditionalMutator_EQUAL_IF": "REMOVE_CONDITIONALS_EQUAL_IF",
    "org.pitest.mutationtest.engine.gregor.mutators.RemoveConditionalMutator_EQUAL_ELSE": "REMOVE_CONDITIONALS_EQUAL_ELSE",
    "org.pitest.mutationtest.engine.gregor.mutators.RemoveConditionalMutator_ORDER_IF": "REMOVE_CONDITIONALS_ORDER_IF",
    "org.pitest.mutationtest.engine.gregor.mutators.RemoveConditionalMutator_ORDER_ELSE": "REMOVE_CONDITIONALS_ORDER_ELSE",
    "org.pitest.mutationtest.engine.gregor.mutators.experimental.NakedReceiverMutator": "EXPERIMENTAL_NAKED_RECEIVER",
    "org.pitest.mutationtest.engine.gregor.mutators.experimental.MemberVariableMutator": "EXPERIMENTAL_MEMBER_VARIABLE",
    "org.pitest.mutationtest.engine.gregor.mutators.experimental.SwitchMutator": "EXPERIMENTAL_SWITCH",
    "org.pitest.mutationtest.engine.gregor.mutators.experimental.ArgumentPropagationMutator": "EXPERIMENTAL_ARGUMENT_PROPAGATION",
    "org.pitest.mutationtest.engine.gregor.mutators.experimental.BigIntegerMutator": "EXPERIMENTAL_BIG_INTEGER",
    "org.pitest.mutationtest.engine.gregor.mutators.NonVoidMethodCallMutator": "NON_VOID_METHOD_CALLS",
    "org.pitest.mutationtest.engine.gregor.mutators.ConstructorCallMutator": "CONSTRUCTOR_CALLS",
    "org.pitest.mutationtest.engine.gregor.mutators.RemoveIncrementsMutator": "REMOVE_INCREMENTS",
}


def short_name(full_mutator: str) -> str:
    if full_mutator in MUTATOR_SHORT_NAMES:
        return MUTATOR_SHORT_NAMES[full_mutator]
    # Fallback: extract class name and upper-snake-case it
    cls = full_mutator.rsplit(".", 1)[-1]
    name = cls.replace("Mutator", "")
    result = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            result.append("_")
        result.append(ch.upper())
    return "".join(result)


def parse(path: str):
    tree = ET.parse(path)
    root = tree.getroot()
    mutations = []
    for m in root.findall("mutation"):
        status = m.get("status", "UNKNOWN")
        detected = m.get("detected", "false")
        entry = {
            "mutatedClass": m.findtext("mutatedClass", ""),
            "mutatedMethod": m.findtext("mutatedMethod", ""),
            "sourceFile": m.findtext("sourceFile", ""),
            "lineNumber": int(m.findtext("lineNumber", "0")),
            "mutator": m.findtext("mutator", ""),
            "description": m.findtext("description", ""),
            "status": status,
            "detected": detected == "true",
        }
        entry["mutatorShortName"] = short_name(entry["mutator"])
        mutations.append(entry)
    return mutations


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: parse-mutations.py <mutations.xml> [--summary] [--surviving-mutators <className>]", file=sys.stderr)
        sys.exit(1)

    path = args[0]
    flags = args[1:]
    mutations = parse(path)

    if "--summary" in flags:
        counts = Counter(m["status"] for m in mutations)
        total = len(mutations)
        print(json.dumps({
            "total": total,
            "killed": counts.get("KILLED", 0),
            "survived": counts.get("SURVIVED", 0),
            "no_coverage": counts.get("NO_COVERAGE", 0),
            "timed_out": counts.get("TIMED_OUT", 0),
            "other": total - counts.get("KILLED", 0) - counts.get("SURVIVED", 0) - counts.get("NO_COVERAGE", 0) - counts.get("TIMED_OUT", 0),
        }))
        return

    if "--surviving-mutators" in flags:
        idx = flags.index("--surviving-mutators")
        if idx + 1 >= len(flags):
            print("Error: --surviving-mutators requires a class name", file=sys.stderr)
            sys.exit(1)
        class_name = flags[idx + 1]
        short_names = sorted(set(
            m["mutatorShortName"]
            for m in mutations
            if m["mutatedClass"] == class_name and m["status"] in ("SURVIVED", "NO_COVERAGE")
        ))
        print(",".join(short_names))
        return

    # Default: output surviving mutations as JSON lines
    surviving = [m for m in mutations if m["status"] in ("SURVIVED", "NO_COVERAGE")]

    # Sort: NO_COVERAGE first, then SURVIVED, then by class, then by line
    def sort_key(m):
        status_order = 0 if m["status"] == "NO_COVERAGE" else 1
        return (status_order, m["mutatedClass"], m["lineNumber"])

    surviving.sort(key=sort_key)

    counts = Counter(m["status"] for m in mutations)
    total = len(mutations)
    print(
        f"Total: {total} | Killed: {counts.get('KILLED', 0)} | Survived: {counts.get('SURVIVED', 0)} | No Coverage: {counts.get('NO_COVERAGE', 0)}",
        file=sys.stderr,
    )

    for m in surviving:
        print(json.dumps(m))


if __name__ == "__main__":
    main()
