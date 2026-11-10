# -*- coding: utf-8 -*-
"""A tiny YAML subset parser.

Supports only the structures used by sources.yaml:
- nested maps by indentation
- lists of scalars
- lists of maps
- strings and booleans
- comments starting with #
"""


def parse(text):
    lines = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))
    if not lines:
        return {}
    value, _ = _parse_block(lines, 0, lines[0][0])
    return value


def _parse_block(lines, index, indent):
    if index >= len(lines):
        return {}, index
    if lines[index][1].startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_map(lines, index, indent):
    result = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError("unexpected indentation: %r" % content)
        if content.startswith("- "):
            break
        key, sep, value = content.partition(":")
        if not sep:
            raise ValueError("expected key:value, got %r" % content)
        key = key.strip()
        value = value.strip()
        index += 1
        if value:
            result[key] = _scalar(value)
        else:
            if index < len(lines) and lines[index][0] > indent:
                child, index = _parse_block(lines, index, lines[index][0])
                result[key] = child
            else:
                result[key] = {}
    return result, index


def _parse_list(lines, index, indent):
    result = []
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError("unexpected indentation: %r" % content)
        if not content.startswith("- "):
            break
        item = content[2:].strip()
        index += 1
        if not item:
            if index < len(lines) and lines[index][0] > indent:
                child, index = _parse_block(lines, index, lines[index][0])
                result.append(child)
            else:
                result.append(None)
        elif "://" not in item and ":" in item:
            key, _, value = item.partition(":")
            entry = {key.strip(): _scalar(value.strip())}
            if index < len(lines) and lines[index][0] > indent:
                child, index = _parse_map(lines, index, lines[index][0])
                entry.update(child)
            result.append(entry)
        else:
            result.append(_scalar(item))
    return result, index


def _scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value
