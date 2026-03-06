---
name: transx-best-practices
description: Best practices for building i18n flows with TransX
---

# TransX Skill

Use this skill when working on projects that use `transx` for localization.

## 1) Preferred API usage

- Use `tx.tr()` for high-level runtime translation in app code.
- Use `tx.translate()` for low-level direct translation cases.
- For context-sensitive lookups, always provide explicit `context`.

## 2) Locale layout

Use standard gettext layout:

```text
<locales_root>/<locale>/LC_MESSAGES/messages.po
<locales_root>/<locale>/LC_MESSAGES/messages.mo
```

Examples:
- `./locales/zh_CN/LC_MESSAGES/messages.po`
- `./locales/ja_JP/LC_MESSAGES/messages.mo`

## 3) Multiple locale roots

`TransX` supports:

```python
TransX(locales_root=["./pkg_a/locales", "./pkg_b/locales"])
```

Rules:
- merge strategy: **first-wins** on duplicate `(msgid, context)`
- conflict behavior: log `WARNING`, do not raise by default
- backward compatibility: `locales_root` property still points to first root
- full roots list: use `locales_roots`

## 4) Extraction workflow

Use `PotExtractor` and keep keyword config explicit:

- standard: `tr`, `_`, `gettext`, `pgettext`, `npgettext`
- custom marker parity: add custom markers via `additional_keywords`

Recommended flow:
1. extract -> generate/update `.pot`
2. update -> sync `.po` files
3. compile -> build `.mo` files

## 5) Testing guidance

When adding i18n features:
- include cases for plain msgid and context (`msgctxt`)
- include fallback behavior tests
- include multi-root merge and duplicate conflict tests
- keep single-root behavior unchanged for compatibility

## 6) Practical checklist for AI agents

- Preserve backward-compatible APIs and defaults
- Avoid breaking gettext file conventions
- Keep warning messages actionable for translation conflicts
- Update both docs and runnable examples when adding features
