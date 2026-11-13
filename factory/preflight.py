#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight sanity checks for generated Shadowrocket configs.

This is a build guard, not the full routing test suite.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = ("sr_cn.conf", "sr_hk.conf", "sr_sg.conf")
STATUS_PATH = os.path.join(ROOT, "factory", "cache", "build_status.json")
REQUIRED_GROUPS = {"PCDN", "Ads", "AI", "SiriAI", "Streaming", "Apple", "BackCN"}
MIN_RULES = 10000
MIN_BLOCK_RULES = 5000
MIN_ADS_RULES = 5000
MIN_PCDN_RULES = 10
MIN_AI_RULES = 20
MIN_SIRI_RULES = 5
MIN_APPLE_RULES = 10
MIN_STREAMING_RULES = 100
MIN_BACKCN_RULES = 100


def load_groups(lines):
    groups = set()
    in_groups = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[Proxy Group]":
            in_groups = True
            continue
        if stripped.startswith("[") and stripped != "[Proxy Group]":
            in_groups = False
            continue
        if in_groups and "=" in stripped:
            groups.add(stripped.split("=", 1)[0].strip())
    return groups


def validate(path):
    errors = []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    groups = load_groups(lines)
    allowed = groups | {"DIRECT", "REJECT", "PROXY"}

    rules = []
    skip_proxy = ""
    in_rules = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("skip-proxy"):
            skip_proxy = stripped
        if stripped == "[Rule]":
            in_rules = True
            continue
        if in_rules and stripped and not stripped.startswith("#"):
            rules.append(stripped)

    if REQUIRED_GROUPS - groups:
        errors.append("missing proxy groups: %s" % sorted(REQUIRED_GROUPS - groups))
    if "{{" in text:
        errors.append("unresolved placeholder found")
    if "*.ls.apple.com" in skip_proxy:
        errors.append("skip-proxy still contains *.ls.apple.com")
    if len(rules) < MIN_RULES:
        errors.append("too few rules: %d < %d" % (len(rules), MIN_RULES))

    final_positions = []
    block_rules = 0
    policy_counts = {
        "Ads": 0,
        "PCDN": 0,
        "AI": 0,
        "SiriAI": 0,
        "Streaming": 0,
        "Apple": 0,
        "BackCN": 0,
    }
    for index, rule in enumerate(rules):
        parts = [part.strip() for part in rule.split(",")]
        if parts[0] == "FINAL":
            final_positions.append(index)
            if len(parts) < 2:
                errors.append("bad FINAL rule: %s" % rule)
                continue
            target = parts[1]
        else:
            if len(parts) < 3:
                errors.append("bad rule: %s" % rule)
                continue
            target = parts[2]
            if target in ("Ads", "PCDN"):
                block_rules += 1
        if target not in allowed:
            errors.append("unknown policy %r in %s" % (target, rule))
        if target in policy_counts:
            policy_counts[target] += 1

    if policy_counts["Ads"] < MIN_ADS_RULES:
        errors.append(
            "too few Ads rules: %d < %d"
            % (policy_counts["Ads"], MIN_ADS_RULES)
        )
    if policy_counts["PCDN"] < MIN_PCDN_RULES:
        errors.append(
            "too few PCDN rules: %d < %d"
            % (policy_counts["PCDN"], MIN_PCDN_RULES)
        )
    if policy_counts["AI"] < MIN_AI_RULES:
        errors.append("too few AI rules: %d" % policy_counts["AI"])
    if policy_counts["SiriAI"] < MIN_SIRI_RULES:
        errors.append("too few SiriAI rules: %d" % policy_counts["SiriAI"])
    if policy_counts["Apple"] < MIN_APPLE_RULES:
        errors.append("too few Apple rules: %d" % policy_counts["Apple"])
    if policy_counts["Streaming"] < MIN_STREAMING_RULES:
        errors.append(
            "too few Streaming rules: %d < %d"
            % (policy_counts["Streaming"], MIN_STREAMING_RULES)
        )
    if policy_counts["BackCN"] < MIN_BACKCN_RULES:
        errors.append(
            "too few BackCN rules: %d < %d"
            % (policy_counts["BackCN"], MIN_BACKCN_RULES)
        )

    if len(final_positions) != 1:
        errors.append("expected exactly one FINAL, got %d" % len(final_positions))
    elif final_positions[0] != len(rules) - 1:
        errors.append("FINAL is not the last rule")
    if block_rules < MIN_BLOCK_RULES:
        errors.append(
            "too few ad/PCDN rules: %d < %d" % (block_rules, MIN_BLOCK_RULES)
        )
    if os.path.getsize(path) < 100 * 1024:
        errors.append("file too small")

    return errors, len(rules), block_rules, groups


def main():
    failed = False

    if not os.path.exists(STATUS_PATH):
        print("FAIL build status: missing (run factory/build.py first)")
        failed = True
    else:
        try:
            with open(STATUS_PATH, encoding="utf-8") as f:
                status = json.load(f)
        except (OSError, ValueError) as exc:
            print("FAIL build status: %s" % exc)
            failed = True
        else:
            skipped = [
                name for name, info in status.items() if info.get("skipped")
            ]
            cached = [
                name for name, info in status.items() if info.get("from_cache")
            ]
            if skipped:
                print("FAIL skipped sources: %s" % ", ".join(sorted(skipped)))
                failed = True
            if cached:
                print("WARN cached sources: %s" % ", ".join(sorted(cached)))

    for name in CONFIGS:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            print("FAIL %s: missing" % name)
            failed = True
            continue
        errors, rule_count, block_rules, groups = validate(path)
        if errors:
            failed = True
            print("FAIL %s" % name)
            for error in errors:
                print("  - %s" % error)
        else:
            print(
                "OK   %s: %d rules, %d ad/PCDN rules, groups=%s"
                % (name, rule_count, block_rules, ",".join(sorted(groups)))
            )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
