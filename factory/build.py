#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Shadowrocket configs for mainland China, Hong Kong and Singapore.

All sources and profile settings live in sources.yaml.
No manual rule files are used.
"""

import argparse
import datetime
import hashlib
import ipaddress
import json
import os
import re
import ssl
import time
import urllib.request

try:
    import yaml
except ImportError:
    yaml = None

try:
    from factory.yaml_lite import parse as parse_yaml
except ImportError:
    from yaml_lite import parse as parse_yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "factory", "cache")
CONFIG = os.path.join(ROOT, "sources.yaml")
STATE = os.path.join(ROOT, "state", "sources.json")
MAX_STALE_DAYS = 730
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

DOM_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{1,62}$"
)


def fetch(name, url):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + ".txt")
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as resp:
                text = resp.read().decode("utf-8", errors="ignore").lstrip("﻿")
            if not text.strip():
                raise ValueError("empty response")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            print("  fetched %-24s %8d bytes" % (name, len(text)))
            return text
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    if os.path.exists(path):
        print("  WARN  %-24s fetch failed (%s), using cache" % (name, last_error))
        with open(path, encoding="utf-8") as f:
            return f.read()
    print("  WARN  %-24s fetch failed (%s), skipped" % (name, last_error))
    return ""


def norm_domain(value):
    value = value.strip().lower().strip(".")
    for prefix in ("+.", "*.", "||"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    value = value.strip("'\" ")
    value = re.sub(r":\d+$", "", value)
    value = value.split("/", 1)[0].split("^", 1)[0].split("|", 1)[0]
    return value.strip(".")


def add_domain(out, value):
    domain = norm_domain(value)
    if domain and DOM_RE.match(domain):
        out.add(domain)
        return True
    return False


def add_ip(out, value):
    value = value.strip()
    if not value:
        return False
    try:
        net = ipaddress.ip_network(value, strict=False)
    except ValueError:
        return False
    out.add(str(net))
    return True


def extract_abp_value(raw):
    value = raw.strip()
    if not value or value.startswith(("!", "[", "#")):
        return None
    if value.startswith("@@") or (value.startswith("/") and value.endswith("/")):
        return None
    if "##" in value or "#@#" in value or "#?#" in value:
        return None
    if value.startswith("||"):
        value = value[2:]
        host = value.split("^", 1)[0]
        rest = value[len(host):]
        if "/" in host or "*" in host or "?" in host or "*" in rest or "?" in rest:
            return None
    elif value.startswith("|http://") or value.startswith("|https://"):
        match = re.match(r"https?://([^/^|$]+)", value.lstrip("|"))
        value = match.group(1) if match else ""
    else:
        host = value.split("^", 1)[0].split("|", 1)[0]
        rest = value[len(host):]
        if "/" in host or "*" in host or "?" in host or "*" in rest or "?" in rest:
            return None
        value = host
    value = value.strip()
    if not value:
        return None
    candidate = value.split("^", 1)[0]
    try:
        net = ipaddress.ip_network(candidate, strict=False)
        return ("ip", str(net))
    except ValueError:
        pass
    value = value.split("^", 1)[0].split("/", 1)[0].strip()
    domain = norm_domain(value)
    if domain and DOM_RE.match(domain):
        return ("domain", domain)
    return None


def parse_abp(text):
    domains, ips, exceptions = set(), set(), set()
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith(("!", "[")):
            continue
        if raw.startswith("@@"):
            if "$" in raw:
                continue
            parsed = extract_abp_value(raw[2:])
            if parsed and parsed[0] == "domain":
                exceptions.add(parsed[1])
            continue
        if raw.startswith("#"):
            continue
        # ABP options such as $domain= or $third-party scope the rule to a path
        # or context; converting them to a full-domain block would over-block.
        if "$" in raw:
            continue
        match = re.match(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1)\s+(\S+)", raw)
        if match:
            add_domain(domains, match.group(1))
            continue
        parsed = extract_abp_value(raw)
        if not parsed:
            continue
        kind, value = parsed
        if kind == "ip":
            add_ip(ips, value)
        else:
            add_domain(domains, value)
    return domains, ips, exceptions


def parse_clash(text):
    domains, ips = set(), set()
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split(",")
        if len(parts) < 2:
            continue
        kind, value = parts[0].strip(), parts[1].strip()
        if kind in ("DOMAIN-SUFFIX", "DOMAIN"):
            add_domain(domains, value)
        elif kind in ("IP-CIDR", "IP-CIDR6"):
            add_ip(ips, value)
    return domains, ips


def parse_sr(text):
    rules = []
    seen = set()
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) < 2:
            continue
        kind, payload = parts[0], parts[1]
        options = [p for p in parts[2:] if p]
        if kind not in (
            "DOMAIN",
            "DOMAIN-SUFFIX",
            "DOMAIN-KEYWORD",
            "IP-CIDR",
            "IP-CIDR6",
            "IP-ASN",
            "USER-AGENT",
        ):
            continue
        if kind in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
            payload = payload.lower().strip(".")
        key = (kind, payload)
        if key in seen:
            continue
        seen.add(key)
        rules.append((kind, payload, options))
    return rules


def parse_ad_source(text):
    domains, ips = parse_clash(text)
    if domains or ips:
        return domains, ips, set()
    return parse_abp(text)


def parse_rule_source(text):
    rules = parse_sr(text)
    if rules:
        return rules
    domains, ips, _ = parse_abp(text)
    rules = [("DOMAIN-SUFFIX", domain, []) for domain in sorted(domains)]
    rules += [
        ("IP-CIDR6" if ":" in ip else "IP-CIDR", ip, ["no-resolve"])
        for ip in sorted(ips)
    ]
    return rules


def covered_by(domain, parents):
    parts = domain.split(".")
    for index in range(len(parts) - 1):
        if ".".join(parts[index:]) in parents:
            return True
    return False


def load_config(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if yaml is not None:
        return yaml.safe_load(text)
    return parse_yaml(text)


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def record_source(state, name, items):
    canonical = "\n".join(sorted(items))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    today = datetime.date.today()
    entry = state.get(name, {})
    if entry.get("hash") != digest:
        if entry:
            print("  changed %-24s %d rules" % (name, len(items)))
        else:
            print("  new     %-24s %d rules" % (name, len(items)))
        entry = {
            "hash": digest,
            "rule_count": len(items),
            "last_changed": today.isoformat(),
            "last_checked": today.isoformat(),
        }
    else:
        entry["last_checked"] = today.isoformat()
        entry["rule_count"] = len(items)
        last_changed = entry.get("last_changed")
        if last_changed:
            try:
                days = (today - datetime.date.fromisoformat(last_changed)).days
            except ValueError:
                days = 0
            if days > MAX_STALE_DAYS:
                print("  STALE   %-24s unchanged %d days" % (name, days))
                entry["stale_days"] = days
            else:
                entry.pop("stale_days", None)
    state[name] = entry


def load_ads(cfg, mode, state):
    ads_cfg = cfg["ads"]
    sources = list(ads_cfg.get("lite", []))
    if mode == "full":
        sources += list(ads_cfg.get("full_extra", []))
    sources += list(cfg.get("pcdn", []))

    domains, ips, exceptions = set(), set(), set()
    for source in sources:
        text = fetch(source["name"], source["url"])
        if not text:
            continue
        new_domains, new_ips, new_exceptions = parse_ad_source(text)
        record_source(
            state,
            source["name"],
            ["D:%s" % d for d in new_domains]
            + ["I:%s" % ip for ip in new_ips]
            + ["E:%s" % e for e in new_exceptions],
        )
        domains |= new_domains
        ips |= new_ips
        exceptions |= new_exceptions

    unban_domains, unban_ips = set(), set()
    for source in cfg.get("unban", []):
        text = fetch(source["name"], source["url"])
        if not text:
            continue
        new_domains, new_ips = parse_clash(text)
        if not new_domains and not new_ips:
            new_domains, new_ips, _ = parse_abp(text)
        record_source(
            state,
            source["name"],
            ["D:%s" % d for d in new_domains] + ["I:%s" % ip for ip in new_ips],
        )
        unban_domains |= new_domains
        unban_ips |= new_ips

    whitelist = exceptions | unban_domains
    if whitelist:
        domains = {d for d in domains if not covered_by(d, whitelist)}
    if unban_ips:
        ips -= unban_ips
    return domains, ips


def load_rules(cfg, key, state, blocklist=None, keyword_blocklist=None, siri=False):
    blocklist = set(blocklist or [])
    keyword_blocklist = set(keyword_blocklist or [])
    rules = []
    seen = set()
    for source in cfg.get(key, []):
        text = fetch(source["name"], source["url"])
        if not text:
            continue
        source_rules = parse_rule_source(text)
        record_source(
            state,
            source["name"],
            ["%s,%s,%s" % (kind, payload, ";".join(options)) for kind, payload, options in source_rules],
        )
        for kind, payload, options in source_rules:
            if siri:
                if kind not in ("DOMAIN", "DOMAIN-SUFFIX"):
                    continue
            if payload in blocklist:
                continue
            if kind == "DOMAIN-KEYWORD" and payload in keyword_blocklist:
                continue
            rule_key = (kind, payload)
            if rule_key in seen:
                continue
            seen.add(rule_key)
            rules.append((kind, payload, options))
    return rules


def render_rule(kind, payload, policy, options=None):
    parts = [kind, payload, policy]
    if options:
        parts.extend(options)
    return ",".join(parts)


def build_profile(cfg, key, profile, ads, rules):
    lines = []
    lines.append("# Shadowrocket %s profile" % profile["title"])
    lines.append("# Generated: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("# For %s network. See README.md for details." % profile["title"])
    lines.append("")
    lines.append("[General]")
    lines.append("ipv6 = false")
    lines.append(
        "bypass-system = %s"
        % ("true" if cfg["general"].get("bypass_system", True) else "false")
    )
    lines.append("skip-proxy = %s" % cfg["general"]["skip_proxy"])
    lines.append("bypass-tun = %s" % cfg["general"]["bypass_tun"])
    lines.append("dns-server = %s" % profile["dns"])
    lines.append("fallback-dns-server = system")
    lines.append("")
    lines.append("[Proxy Group]")
    for name in ("AI", "SiriAI", "Streaming", "Apple", "BackCN"):
        lines.append("%s = %s" % (name, profile["groups"][name]))
    lines.append("")
    lines.append("[Rule]")

    lines.append("# --- LAN ---")
    for kind, payload, options in rules["lan"]:
        lines.append(render_rule(kind, payload, "DIRECT", options))

    lines.append("# --- Ads ---")
    ad_domains, ad_ips = ads
    for domain in sorted(ad_domains):
        lines.append("DOMAIN-SUFFIX,%s,REJECT" % domain)
    for ip in sorted(ad_ips):
        kind = "IP-CIDR6" if ":" in ip else "IP-CIDR"
        lines.append(render_rule(kind, ip, "REJECT", ["no-resolve"]))

    lines.append("# --- Siri AI ---")
    for kind, payload, options in rules["siri"]:
        lines.append(render_rule(kind, payload, "SiriAI", options))

    lines.append("# --- AI ---")
    for kind, payload, options in rules["ai"]:
        lines.append(render_rule(kind, payload, "AI", options))

    lines.append("# --- Streaming ---")
    for kind, payload, options in rules["streaming"]:
        lines.append(render_rule(kind, payload, "Streaming", options))

    lines.append("# --- Apple ---")
    for suffix in cfg.get("apple_suffixes", []):
        lines.append("DOMAIN-SUFFIX,%s,Apple" % suffix)

    if profile.get("google_policy"):
        lines.append("# --- Google ---")
        for suffix in cfg.get("google_suffixes", []):
            lines.append("DOMAIN-SUFFIX,%s,%s" % (suffix, profile["google_policy"]))

    if profile.get("github_policy"):
        lines.append("# --- GitHub ---")
        for suffix in cfg.get("github_suffixes", []):
            lines.append("DOMAIN-SUFFIX,%s,%s" % (suffix, profile["github_policy"]))

    lines.append("# --- China ---")
    for kind, payload, options in rules["china"]:
        lines.append(render_rule(kind, payload, "BackCN", options))
    lines.append("DOMAIN-SUFFIX,cn,BackCN")
    lines.append("GEOIP,CN,BackCN")
    lines.append("FINAL,%s" % profile["final"])

    unique = []
    seen = set()
    for line in lines:
        if line.startswith("#") or line.startswith("["):
            unique.append(line)
            continue
        if line in seen:
            continue
        seen.add(line)
        unique.append(line)

    path = os.path.join(ROOT, profile["output"])
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(unique) + "\n")
    return path, len(unique)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ad-mode", choices=("lite", "full"), default="lite")
    parser.add_argument("--config", default=CONFIG)
    args = parser.parse_args()

    started = time.time()
    cfg = load_config(args.config)
    state = load_state()

    print("Fetching ad sources (%s mode)..." % args.ad_mode)
    ads = load_ads(cfg, args.ad_mode, state)
    print("  ads: %d domains, %d IPs" % (len(ads[0]), len(ads[1])))

    print("Fetching AI sources...")
    rules = {}
    rules["ai"] = load_rules(
        cfg, "ai", state, blocklist=cfg.get("ai_blocklist", [])
    )

    print("Fetching Siri AI sources...")
    rules["siri"] = load_rules(
        cfg,
        "siri_ai",
        state,
        blocklist=cfg.get("siri_blocklist", []),
        siri=True,
    )
    rules["siri"].sort(key=lambda item: (item[0], item[1]))

    print("Fetching streaming sources...")
    rules["streaming"] = load_rules(
        cfg,
        "streaming",
        state,
        keyword_blocklist=cfg.get("streaming_keyword_blocklist", []),
    )

    print("Fetching China sources...")
    rules["china"] = load_rules(cfg, "china", state)

    print("Fetching LAN sources...")
    rules["lan"] = load_rules(cfg, "lan", state)

    print("Building configs...")
    for key, profile in cfg["profiles"].items():
        path, count = build_profile(cfg, key, profile, ads, rules)
        size = os.path.getsize(path)
        print("  %-12s %7d lines  %8d bytes  %s" % (profile["title"], count, size, path))

    save_state(state)
    print("Done in %.1fs" % (time.time() - started))


if __name__ == "__main__":
    main()
