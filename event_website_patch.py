# ==========================================================
# Melanated AZ Bot - Event Website / Hyperlink Support
# ==========================================================

import html
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

import event_router
import event_private_flow

WEBSITE_FIELD = "website"
WEBSITE_LABEL = "🌐 Website"

_original_fields = event_router._fields
_original_missing = event_router._missing
_original_parse_fields = event_router._parse_fields
_original_install_private = event_private_flow.install_application


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
    required_missing = [key for key in _original_missing(fields) if key != WEBSITE_FIELD]
    if required_missing:
        return required_missing
    if not fields.get(WEBSITE_FIELD):
        return [WEBSITE_FIELD]
    return []


def _parse_fields(text):
    fields = _original_parse_fields(text)
    text = str(text or "")
    match = re.search(r"(?i)\bhttps?://[^\s<>\]\[()]+", text)
    if not match:
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
    for key in ("event", "date", "time", "location"):
        value = fields.get(key)
        label = event_router.FIELD_LABELS.get(key, key.title())
        lines.append(f"{label}: {html.escape(str(value)) if value else '❌ Missing'}")

    website = fields.get(WEBSITE_FIELD)
    if website and re.match(r"^https?://", str(website), re.IGNORECASE):
        safe_url = html.escape(str(website), quote=True)
        visible = html.escape(str(website))
        lines.append(f'{WEBSITE_LABEL}: <a href="{safe_url}">{visible}</a>')
    elif website:
        lines.append(f"{WEBSITE_LABEL}: {html.escape(str(website))}")
    else:
        lines.append(f"{WEBSITE_LABEL}: None provided")

    return "\n".join(lines)


def _private_keyboard(submission_id, website_missing=False):
    rows = [
        [InlineKeyboardButton("✏️ EDIT / FILL IN", callback_data=f"event_private_edit_{submission_id}")],
    ]
    if website_missing:
        rows.append([
            InlineKeyboardButton("🚫 NO WEBSITE / SKIP", callback_data=f"event_private_skip_website_{submission_id}")
        ])
    else:
        rows.append([
            InlineKeyboardButton("✅ CONFIRM & SUBMIT", callback_data=f"event_private_confirm_{submission_id}")
        ])
    return InlineKeyboardMarkup(rows)


async def _wrapped_private_form(context, user_id, submission_id, intro=False):
    row = event_router._get_submission(int(submission_id))
    if not row or row["user_id"] != user_id:
        return False
    if row["status"] not in {"member_input", "awaiting_confirmation"}:
        return False

    fields = event_router._fields(row)
    event_private_flow._set_context(context, submission_id)

    if intro:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔒 <b>PRIVATE EVENT SUBMISSION</b>\n\n"
                "Your Event information is being collected privately. "
                "Nothing you enter will be visible to the group while you fill this out.\n\n"
                "I will send the completed event to the admins for approval."
            ),
            parse_mode="HTML",
        )

    missing = event_router._missing(fields)
    if missing:
        field = missing[0]
        event_private_flow._set_context(context, submission_id, field)
        if field == WEBSITE_FIELD:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🌐 <b>EVENT WEBSITE</b>\n\n"
                    "Does this event have a website or registration page?\n\n"
                    "Send the full link (for example, https://example.com), or tap <b>NO WEBSITE / SKIP</b>."
                ),
                parse_mode="HTML",
                reply_markup=_private_keyboard(submission_id, website_missing=True),
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🔒 <b>EVENT INFORMATION</b>\n\n"
                    + event_router._format_fields(fields)
                    + f"\n\nPlease send the <b>{event_router.FIELD_LABELS[field]}</b>."
                ),
                parse_mode="HTML",
            )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔎 <b>VERIFY YOUR EVENT</b>\n\n"
                + event_router._format_fields(fields)
                + "\n\nEverything is ready. Review it below, then confirm."
            ),
            parse_mode="HTML",
            reply_markup=_private_keyboard(submission_id),
        )
    return True


async def _handle_private_text(update, context):
    message = update.effective_message
    user = update.effective_user
    if message and user and message.chat.type == "private":
        field = context.user_data.get("event_private_waiting_for")
        if field == WEBSITE_FIELD:
            submission_id = context.user_data.get("event_private_submission_id")
            if submission_id:
                row = event_router._get_submission(int(submission_id))
                if row and row["user_id"] == user.id:
                    value = message.text.strip()
                    if not value:
                        await message.reply_text("Please send a website link or tap NO WEBSITE / SKIP.")
                        raise event_private_flow.ApplicationHandlerStop

                    if value.lower() in {"none", "no", "n/a", "na", "skip", "no website", "no website / skip"}:
                        value = "No website provided"
                    elif not re.match(r"^https?://", value, re.IGNORECASE):
                        if re.match(r"^www\.", value, re.IGNORECASE):
                            value = "https://" + value
                        else:
                            await message.reply_text(
                                "Please send a complete link starting with https:// or http://, or tap NO WEBSITE / SKIP."
                            )
                            raise event_private_flow.ApplicationHandlerStop

                    fields = event_router._fields(row)
                    fields[WEBSITE_FIELD] = value
                    event_router._update_submission(submission_id, fields=fields, status="awaiting_confirmation")
                    event_private_flow._set_context(context, submission_id)
                    await message.reply_text(
                        "🔎 <b>VERIFY YOUR EVENT</b>\n\n"
                        + event_router._format_fields(fields)
                        + "\n\nIf everything is correct, tap <b>CONFIRM & SUBMIT</b>.",
                        parse_mode="HTML",
                        reply_markup=_private_keyboard(submission_id),
                    )
                    raise event_private_flow.ApplicationHandlerStop

    return await event_private_flow._original_private_text(update, context)


async def _skip_website(update, context):
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    match = re.fullmatch(r"event_private_skip_website_(\d+)", query.data or "")
    if not match:
        return

    submission_id = int(match.group(1))
    row = event_router._get_submission(submission_id)
    if not row or row["user_id"] != user.id:
        await query.answer("This Event submission is not yours.", show_alert=True)
        raise event_private_flow.ApplicationHandlerStop

    fields = event_router._fields(row)
    fields[WEBSITE_FIELD] = "No website provided"
    event_router._update_submission(submission_id, fields=fields, status="awaiting_confirmation")
    event_private_flow._set_context(context, submission_id)

    await query.answer("Website skipped.")
    await query.message.reply_text(
        "🔎 <b>VERIFY YOUR EVENT</b>\n\n"
        + event_router._format_fields(fields)
        + "\n\nIf everything is correct, tap <b>CONFIRM & SUBMIT</b>.",
        parse_mode="HTML",
        reply_markup=_private_keyboard(submission_id),
    )
    raise event_private_flow.ApplicationHandlerStop


def install():
    event_router.FIELD_ORDER = tuple(
        key for key in event_router.FIELD_ORDER if key != WEBSITE_FIELD
    ) + (WEBSITE_FIELD,)
    event_router.FIELD_LABELS[WEBSITE_FIELD] = WEBSITE_LABEL
    event_router._fields = _fields
    event_router._missing = _missing
    event_router._parse_fields = _parse_fields
    event_router._format_fields = _format_fields

    event_private_flow._original_private_text = event_private_flow.handle_private_text
    event_private_flow._private_keyboard = _private_keyboard
    event_private_flow._send_private_form = _wrapped_private_form
    event_private_flow.handle_private_text = _handle_private_text

    if not getattr(event_private_flow, "_website_install_wrapped", False):
        async def _install_with_website_handler(application):
            result = _original_install_private(application)
            application.add_handler(
                CallbackQueryHandler(
                    _skip_website,
                    pattern=r"^event_private_skip_website_\d+$",
                ),
                group=0,
            )
            return result

        # install_application is synchronous; keep the wrapper synchronous.
        def _install_with_website_handler_sync(application):
            result = _original_install_private(application)
            application.add_handler(
                CallbackQueryHandler(
                    _skip_website,
                    pattern=r"^event_private_skip_website_\d+$",
                ),
                group=0,
            )
            return result

        event_private_flow.install_application = _install_with_website_handler_sync
        event_private_flow._website_install_wrapped = True
