#!/usr/bin/env python3
"""Validate locale parity, page metadata, navigation, and local links."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("ru", "en", "id", "ko", "zh-CN")
CANONICAL_LOCALE = "ru"
NOTICE_MARKER = "<!-- ai-translation-notice -->"
DATE_PATTERN = re.compile(r"^updated:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SUMMARY_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+\.md(?:#[^)]+)?)\)")


def locale_pages(locale: str) -> set[Path]:
    locale_root = ROOT / locale
    if not locale_root.is_dir():
        return set()
    return {
        path.relative_to(locale_root)
        for path in locale_root.rglob("*.md")
        if path.name != "SUMMARY.md"
    }


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def target_path(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
    if target.startswith(("http://", "https://", "mailto:", "#", "/")):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return None
    return (source.parent / target).resolve()


def main() -> int:
    errors: list[str] = []
    pages_by_locale = {locale: locale_pages(locale) for locale in LOCALES}
    canonical_pages = pages_by_locale[CANONICAL_LOCALE]

    if not canonical_pages:
        errors.append("ru: no content pages found")

    for locale, pages in pages_by_locale.items():
        missing = sorted(canonical_pages - pages)
        extra = sorted(pages - canonical_pages)
        if missing:
            errors.append(f"{locale}: missing pages: {', '.join(map(str, missing))}")
        if extra:
            errors.append(f"{locale}: extra pages: {', '.join(map(str, extra))}")

    for relative_page in sorted(canonical_pages):
        dates: dict[str, str] = {}
        for locale in LOCALES:
            page = ROOT / locale / relative_page
            if not page.is_file():
                continue
            if not relative_page.as_posix().isascii():
                errors.append(f"{page.relative_to(ROOT)}: filename must be ASCII")

            content = read(page)
            date_match = DATE_PATTERN.search(content)
            if not date_match:
                errors.append(f"{page.relative_to(ROOT)}: missing updated: YYYY-MM-DD")
            else:
                value = date_match.group(1)
                try:
                    date.fromisoformat(value)
                except ValueError:
                    errors.append(f"{page.relative_to(ROOT)}: invalid updated date {value}")
                dates[locale] = value

            if locale != CANONICAL_LOCALE and NOTICE_MARKER not in content:
                errors.append(f"{page.relative_to(ROOT)}: missing AI translation notice")

            for raw_link in LINK_PATTERN.findall(content):
                target = target_path(page, raw_link)
                if target is not None and not target.exists():
                    errors.append(
                        f"{page.relative_to(ROOT)}: broken link {raw_link!r}"
                    )

        if len(set(dates.values())) > 1:
            values = ", ".join(f"{locale}={value}" for locale, value in dates.items())
            errors.append(f"{relative_page}: locale update dates differ: {values}")

    canonical_summary = ROOT / CANONICAL_LOCALE / "SUMMARY.md"
    canonical_targets: set[str] = set()
    if not canonical_summary.is_file():
        errors.append(f"{CANONICAL_LOCALE}/SUMMARY.md: file not found")
    else:
        canonical_targets = {
            target.split("#", 1)[0] for target in SUMMARY_LINK_PATTERN.findall(read(canonical_summary))
        }

    for locale in LOCALES:
        summary = ROOT / locale / "SUMMARY.md"
        if not summary.is_file():
            errors.append(f"{locale}/SUMMARY.md: file not found")
            continue
        targets = {
            target.split("#", 1)[0] for target in SUMMARY_LINK_PATTERN.findall(read(summary))
        }
        if targets != canonical_targets:
            errors.append(f"{locale}/SUMMARY.md: navigation differs from ru/SUMMARY.md")
        for raw_target in targets:
            target = target_path(summary, raw_target)
            if target is not None and not target.exists():
                errors.append(f"{locale}/SUMMARY.md: broken link {raw_target!r}")

    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    total = len(canonical_pages)
    print(f"Documentation validation passed: {total} page(s) across {len(LOCALES)} locales")
    return 0


if __name__ == "__main__":
    sys.exit(main())
