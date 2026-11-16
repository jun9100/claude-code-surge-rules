#!/usr/bin/env python3
"""校验 ClaudeCode.list 是否符合 Surge RULE-SET 文件格式。

RULE-SET 文件里不允许出现 FINAL、不允许写策略名，每行只能有一条规则，
可选参数只接受 no-resolve / extended-matching。
"""

import re
import sys
from collections import Counter
from pathlib import Path

RULESET = Path(__file__).resolve().parent.parent / "ClaudeCode.list"

ALLOWED_PREFIXES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "DOMAIN-SET",
    "RULE-SET",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
}

ALLOWED_FLAGS = {"no-resolve", "extended-matching"}

LOGICAL_PREFIXES = {"AND", "OR", "NOT"}

DOMAIN_RE = re.compile(r"^[A-Za-z0-9*?._-]+$")
IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}(/\d{1,2})?$")
IPV6_RE = re.compile(r"^[0-9A-Fa-f:]+(/\d{1,3})?$")


def fail(errors, lineno, line, msg):
    errors.append(f"line {lineno}: {msg}  ->  {line}")


def check_simple(errors, lineno, line, prefix, fields):
    if len(fields) < 2 or not fields[1].strip():
        fail(errors, lineno, line, f"{prefix} 缺少匹配值")
        return
    value = fields[1].strip()

    for extra in fields[2:]:
        extra = extra.strip()
        if extra not in ALLOWED_FLAGS:
            fail(
                errors,
                lineno,
                line,
                f"RULE-SET 文件不能写策略名，只允许 {sorted(ALLOWED_FLAGS)}，发现 {extra!r}",
            )

    if prefix.startswith("DOMAIN"):
        if not DOMAIN_RE.match(value):
            fail(errors, lineno, line, f"域名格式可疑：{value!r}")
    elif prefix == "IP-CIDR":
        if not IPV4_RE.match(value):
            fail(errors, lineno, line, f"IPv4 CIDR 格式可疑：{value!r}")
    elif prefix == "IP-CIDR6":
        if not IPV6_RE.match(value):
            fail(errors, lineno, line, f"IPv6 CIDR 格式可疑：{value!r}")
    elif prefix == "IP-ASN":
        if not re.match(r"^(AS)?\d+$", value, re.IGNORECASE):
            fail(errors, lineno, line, f"ASN 必须是数字或 AS+数字：{value!r}")


def main():
    if not RULESET.exists():
        print(f"找不到规则集文件：{RULESET}")
        return 1

    errors = []
    seen = {}
    counter = Counter()

    for lineno, raw in enumerate(RULESET.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", "//", ";")):
            continue

        if line.upper().startswith("FINAL"):
            fail(errors, lineno, line, "RULE-SET 文件不允许出现 FINAL")
            continue
        if "pre-matching" in line:
            fail(errors, lineno, line, "RULE-SET 文件不允许 pre-matching")
            continue

        prefix = line.split(",", 1)[0].strip()
        upper = prefix.upper()

        if upper in LOGICAL_PREFIXES:
            if line.count("(") != line.count(")"):
                fail(errors, lineno, line, "逻辑规则括号不配对")
            elif not line.rstrip().endswith(")"):
                fail(errors, lineno, line, "逻辑规则末尾不能带策略名")
            else:
                counter[upper] += 1
            continue

        if upper not in ALLOWED_PREFIXES:
            fail(errors, lineno, line, f"未知的规则类型 {prefix!r}")
            continue

        fields = line.split(",")
        check_simple(errors, lineno, line, prefix, fields)
        counter[upper] += 1

        key = ",".join(f.strip().lower() for f in fields)
        if key in seen:
            fail(errors, lineno, line, f"与第 {seen[key]} 行重复")
        else:
            seen[key] = lineno

    total = sum(counter.values())
    if errors:
        print(f"✗ 发现 {len(errors)} 个问题：\n")
        for e in errors:
            print("  " + e)
        return 1

    print(f"✓ {RULESET.name} 校验通过，共 {total} 条规则")
    for prefix, n in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {prefix:<16} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
