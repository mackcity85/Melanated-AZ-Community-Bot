# ==========================================================
# Melanated AZ Bot - Event Website / Hyperlink Support
# ==========================================================

import html
import re

import event_router

WEBSITE_FIELD = "website"
WEBSITE_LABEL = "🌐 Website"

_original_fields = event_router._fields
_original_missing = event_router._missing
_original_parse_fields = event_router._parse_fields
_original_format_fields = event_router._format_fields


def _fields(row):
    fields = _original_fields(row)
    try:
        import json
        data = json.loads(row["fields_json"] or "{}")
        fields[WEBSITE_FIELD] = str(data.get(WEBSITE_FIELD) or "").strip() or None
    except Exception:
        fields[WEBSITE_FIELD] = None
    return fields


def _missing(fields):
    # Event, Date, Time and Location remain required.
    required_missing = _original_missing(fields)
    if required_missing:
        return required_missing

    # Website is optional, but we give the submitter the opportunity to add one.
    # The private flow recognizes SKIP/NONE and continues to confirmation.
    if not fields.get(WEBSITE_FIELD):
        return [WEBSITE_FIELD]

    return []


def _parse_fields(text):
    fields = _original_parse_fields(text)
    text = str(text or "")

    # Pick up a normal web URL from flyer OCR or caption.
    match = re.search(r"(?i)\bhttps?://[^\s<>\]\[()]+", text)
    if not match:
        # Also recognize www.example.com.
        match = re.search(r"(?i)\bwww\.[^\s<>\]\[()]+", text)

    if match:
        url = match.group(0).rstrip(".,;:!?)\"")
        if url.lower().startswith("www."):
            url = "https://" + url
        fields[WEBSITE_FIELD] = url
    else:
        fields[WEBSITE_FIELD] = None

    return fields


def _format_fields(fields):
    lines = []

    for key in event_router.FIELD_ORDER:
        value = fields.get(key)
        if key == WEBSITE_FIELD:
            continue
        label = event_router.FIELD_LABELS.get(key, key.title())
        lines.append(f"{label}: {html.escape(str(value)) if value else '❌ Missing'}")

    website = fields.get(WEBSITE_FIELD)
    if website:
        safe_url = html.escape(str(website), quote=True)
        lines.append(f'{WEBSITE_LABEL}: <a href="{safe_url}">{html.escape(str(website))}</a>')
    else:
        lines.append(f"{WEBSITE_LABEL}: None provided")

    return "\n".join(lines)


def install():
    event_router.FIELD_ORDER = tuple(
        key for key in event_router.FIELD_ORDER if key != WEBSITE_FIELD
    ) + (WEBSITE_FIELD,)
    event_router.FIELD_LABELS[WEBSITE_FIELD] = WEBSITE_LABEL
    event_router._fields = _fields
    event_router._missing = _missing
    event_router._parse_fields = _parse_fields
    event_router._format_fields = _format_fields
