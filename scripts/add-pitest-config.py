#!/usr/bin/env python3
"""Add pitest-maven plugin to pom.xml, picking the right version based on Java source level."""

import re
import sys
import xml.etree.ElementTree as ET

# pitest-maven versions by minimum Java version
# Java 8+  → pitest 1.17.4 (last to support Java 8)
# Java 11+ → pitest 1.18.1 (requires Java 11)
PITEST_VERSION_MAP = {
    8: "1.17.4",
    11: "1.18.1",
}

# pitest-junit5-plugin versions aligned with pitest versions
JUNIT5_PLUGIN_MAP = {
    "1.17.4": "1.2.1",
    "1.18.1": "1.2.1",
}

PITEST_GROUP_ID = "org.pitest"
PITEST_ARTIFACT_ID = "pitest-maven"
JUNIT5_ARTIFACT_ID = "pitest-junit5-plugin"

NS = ""


def detect_java_version(root: ET.Element, ns: str) -> int:
    """Detect Java source version from pom.xml properties or compiler plugin config."""
    props = root.find(f"{ns}properties")
    if props is not None:
        # Check common property names in priority order
        for prop_name in ["maven.compiler.release", "maven.compiler.source", "java.version"]:
            el = props.find(f"{ns}{prop_name}")
            if el is not None and el.text:
                return _parse_version(el.text.strip())

    # Check maven-compiler-plugin configuration
    build = root.find(f"{ns}build")
    if build is not None:
        plugins = build.find(f"{ns}plugins")
        if plugins is None:
            pm = build.find(f"{ns}pluginManagement")
            if pm is not None:
                plugins = pm.find(f"{ns}plugins")
        if plugins is not None:
            for plugin in plugins.findall(f"{ns}plugin"):
                aid = plugin.find(f"{ns}artifactId")
                if aid is not None and aid.text == "maven-compiler-plugin":
                    config = plugin.find(f"{ns}configuration")
                    if config is not None:
                        for tag in ["release", "source"]:
                            el = config.find(f"{ns}{tag}")
                            if el is not None and el.text:
                                return _parse_version(el.text.strip())

    return 0  # unknown


def _parse_version(text: str) -> int:
    """Parse '1.8' → 8, '11' → 11, '17' → 17, etc."""
    # Handle property references like ${java.version}
    if text.startswith("${"):
        return 0
    text = text.strip()
    if text.startswith("1."):
        text = text[2:]
    try:
        return int(text)
    except ValueError:
        return 0


def pick_pitest_version(java_version: int) -> str:
    """Pick the best pitest version for the given Java version."""
    if java_version <= 0:
        # Unknown — default to latest
        return "1.18.1"
    if java_version < 11:
        return PITEST_VERSION_MAP[8]   # 1.17.4 — last to support Java 8
    return PITEST_VERSION_MAP[11]      # 1.18.1 — requires Java 11+


def has_junit5(root: ET.Element, ns: str) -> bool:
    """Check if pom.xml has JUnit 5 (Jupiter) dependency."""
    for dep in root.iter(f"{ns}dependency"):
        aid = dep.find(f"{ns}artifactId")
        gid = dep.find(f"{ns}groupId")
        if aid is not None and "junit-jupiter" in (aid.text or ""):
            return True
        if gid is not None and "junit-jupiter" in (gid.text or ""):
            return True
        if aid is not None and "junit-bom" in (aid.text or ""):
            return True
    return False


def has_pitest(root: ET.Element, ns: str) -> bool:
    """Check if pitest-maven plugin is already configured."""
    for plugin in root.iter(f"{ns}plugin"):
        aid = plugin.find(f"{ns}artifactId")
        if aid is not None and aid.text == PITEST_ARTIFACT_ID:
            return True
    return False


def detect_target_classes(root: ET.Element, ns: str) -> str:
    """Detect base package from groupId + artifactId."""
    gid = root.find(f"{ns}groupId")
    if gid is not None and gid.text:
        return gid.text.strip() + ".*"
    # Try parent groupId
    parent = root.find(f"{ns}parent")
    if parent is not None:
        gid = parent.find(f"{ns}groupId")
        if gid is not None and gid.text:
            return gid.text.strip() + ".*"
    return "com.example.*"


def build_plugin_xml(pitest_version: str, junit5_version: str | None, target_classes: str) -> str:
    """Build the pitest plugin XML block."""
    deps = ""
    if junit5_version:
        deps = f"""
        <dependencies>
          <dependency>
            <groupId>{PITEST_GROUP_ID}</groupId>
            <artifactId>{JUNIT5_ARTIFACT_ID}</artifactId>
            <version>{junit5_version}</version>
          </dependency>
        </dependencies>"""

    return f"""      <plugin>
        <groupId>{PITEST_GROUP_ID}</groupId>
        <artifactId>{PITEST_ARTIFACT_ID}</artifactId>
        <version>{pitest_version}</version>
        <configuration>
          <targetClasses>
            <param>{target_classes}</param>
          </targetClasses>
          <mutators>
            <mutator>STRONGER</mutator>
          </mutators>
          <outputFormats>
            <param>XML</param>
            <param>HTML</param>
          </outputFormats>
          <timestampedReports>false</timestampedReports>
        </configuration>{deps}
      </plugin>"""


def main():
    pom_path = sys.argv[1] if len(sys.argv) > 1 else "pom.xml"

    # Read raw content for text-based insertion (preserves formatting)
    with open(pom_path, "r") as f:
        content = f.read()

    # Parse for analysis
    # Handle default namespace
    ns_match = re.search(r'xmlns="([^"]+)"', content)
    ns = f"{{{ns_match.group(1)}}}" if ns_match else ""

    tree = ET.parse(pom_path)
    root = tree.getroot()

    if has_pitest(root, ns):
        print("pitest-maven plugin already configured in pom.xml")
        sys.exit(0)

    java_version = detect_java_version(root, ns)
    pitest_version = pick_pitest_version(java_version)
    junit5 = has_junit5(root, ns)
    junit5_version = JUNIT5_PLUGIN_MAP.get(pitest_version) if junit5 else None
    target_classes = detect_target_classes(root, ns)

    plugin_xml = build_plugin_xml(pitest_version, junit5_version, target_classes)

    # Insert into pom.xml using text manipulation to preserve formatting
    # Strategy: find </plugins> or </build>, insert before it
    if "</plugins>" in content:
        # Insert before the last </plugins> inside <build>
        # Find the </plugins> that's inside <build> (not pluginManagement)
        content = content.replace("</plugins>", plugin_xml + "\n    </plugins>", 1)
    elif "<plugins>" in content:
        # Shouldn't happen (has <plugins> but no </plugins>), but handle it
        content = content.replace("<plugins>", "<plugins>\n" + plugin_xml, 1)
    elif "</build>" in content:
        # No <plugins> section yet
        content = content.replace("</build>", "  <plugins>\n" + plugin_xml + "\n    </plugins>\n  </build>", 1)
    elif "</project>" in content:
        # No <build> section at all
        build_block = f"""  <build>
    <plugins>
{plugin_xml}
    </plugins>
  </build>
"""
        content = content.replace("</project>", build_block + "</project>")
    else:
        print("Error: Cannot find insertion point in pom.xml", file=sys.stderr)
        sys.exit(1)

    with open(pom_path, "w") as f:
        f.write(content)

    version_info = f"Java {java_version}" if java_version > 0 else "unknown Java version (defaulting to latest)"
    junit_info = f" + pitest-junit5-plugin {junit5_version}" if junit5_version else ""
    print(f"Added pitest-maven {pitest_version}{junit_info} to {pom_path} (detected {version_info}, target: {target_classes})")


if __name__ == "__main__":
    main()
