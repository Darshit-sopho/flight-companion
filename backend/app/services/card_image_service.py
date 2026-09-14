"""Renders a shareable "card" PNG for a flight (docs/features/status-card-requirements.md#SC-D3),
scoped to casual share-to-chat for this pass (see docs/PLANNED_WORK.md for the deferred OpenGraph reuse).

This is a from-scratch draw of the flight's key fields, NOT a screenshot of the web card -- it
deliberately reuses only the underlying data (the same FlightSnapshot the JSON status endpoint already
serves), not the React/CSS rendering. No new cache: rendering from an already-fetched row takes
single-digit milliseconds, so there's nothing worth caching for a "click a button" cold path.

1200x630 is the OpenGraph standard link-preview size -- chosen now, at no extra cost, so a future
auto-generated link-preview image (see docs/PLANNED_WORK.md) can reuse this without a resize.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from app.db.models import FlightSnapshot
from app.services.operator_names import get_operator_name

_WIDTH = 1200
_HEIGHT = 630
_MARGIN = 48

_BG = "#0b1220"
_SURFACE = "#131c2e"
_BORDER = "#253247"
_TEXT = "#e6ecf5"
_MUTED = "#93a2b8"
_ACCENT = "#4f7cff"

_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Inter.ttf"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(_FONT_PATH), size=size)
    font.set_variation_by_name("Bold" if bold else "Regular")
    return font


def _format_time(dt: datetime | None, tz_name: str | None) -> str | None:
    if dt is None:
        return None
    localized = dt.astimezone(ZoneInfo(tz_name)) if tz_name else dt
    text = localized.strftime("%I:%M %p").lstrip("0")
    return text


def _dynamic_time_label_and_value(
    scheduled: datetime | None,
    estimated: datetime | None,
    actual: datetime | None,
    tz_name: str | None,
    *,
    is_cancelled: bool,
) -> tuple[str, str | None]:
    if is_cancelled:
        return "Cancelled", None
    if actual is not None:
        return "Actual", _format_time(actual, tz_name)
    return "Estimated", _format_time(estimated, tz_name)


def _delay_text(delay_minutes: int | None) -> str:
    if delay_minutes is None:
        return "No delay data yet"
    if delay_minutes <= 15:
        return f"On time ({delay_minutes}m)"
    return f"Delayed {delay_minutes}m"


def _duration_text(total_minutes: int | None) -> str | None:
    if total_minutes is None or total_minutes < 0:
        return None
    hours, minutes = divmod(total_minutes, 60)
    if hours == 0:
        return f"{minutes}m"
    if minutes == 0:
        return f"{hours}h"
    return f"{hours}h {minutes}m"


def _distance_text(miles: int | None) -> str | None:
    if miles is None:
        return None
    return f"{miles:,} mi"


def render_card(snapshot: FlightSnapshot) -> bytes:
    image = Image.new("RGB", (_WIDTH, _HEIGHT), _BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        [_MARGIN, _MARGIN, _WIDTH - _MARGIN, _HEIGHT - _MARGIN], radius=20, fill=_SURFACE, outline=_BORDER
    )

    pad = _MARGIN + 40
    y = _MARGIN + 36

    status = snapshot.status.value if hasattr(snapshot.status, "value") else snapshot.status
    is_cancelled = status == "cancelled"
    is_diverted = status == "diverted"

    draw.text((pad, y), f"{snapshot.ident}  ·  {status.capitalize()}", font=_font(34, bold=True), fill=_TEXT)
    draw.text(
        (_WIDTH - pad, y),
        _delay_text(snapshot.delay_minutes),
        font=_font(24),
        fill=_TEXT,
        anchor="ra",
    )
    y += 70

    origin_code = snapshot.origin_iata or snapshot.origin_code or "—"
    destination_code = snapshot.destination_iata or snapshot.destination_code or "—"
    draw.text((pad, y), f"{origin_code}   →   {destination_code}", font=_font(56, bold=True), fill=_TEXT)
    y += 66
    draw.text(
        (pad, y),
        f"{snapshot.origin_name or snapshot.origin_city or ''}  →  "
        f"{snapshot.destination_name or snapshot.destination_city or ''}",
        font=_font(20),
        fill=_MUTED,
    )
    y += 56

    origin_label, origin_value = _dynamic_time_label_and_value(
        snapshot.scheduled_departure,
        snapshot.estimated_departure,
        snapshot.actual_departure,
        snapshot.origin_timezone,
        is_cancelled=is_cancelled,
    )
    dest_label, dest_value = _dynamic_time_label_and_value(
        snapshot.scheduled_arrival,
        snapshot.estimated_arrival,
        snapshot.actual_arrival,
        snapshot.destination_timezone,
        is_cancelled=is_cancelled,
    )
    column_width = (_WIDTH - 2 * pad) / 2
    _draw_leg_column(
        draw,
        x=pad,
        y=y,
        scheduled_text=_format_time(snapshot.scheduled_departure, snapshot.origin_timezone),
        dynamic_label=origin_label,
        dynamic_value=origin_value,
        gate=snapshot.departure_gate,
        terminal=snapshot.departure_terminal,
        muted=is_diverted,
    )
    _draw_leg_column(
        draw,
        x=pad + column_width,
        y=y,
        scheduled_text=_format_time(snapshot.scheduled_arrival, snapshot.destination_timezone),
        dynamic_label=dest_label,
        dynamic_value=dest_value,
        gate=snapshot.arrival_gate,
        terminal=snapshot.arrival_terminal,
        muted=is_diverted,
    )
    y += 150

    if is_diverted and snapshot.diverted_destination_code:
        diverted_label, diverted_value = _dynamic_time_label_and_value(
            snapshot.diverted_scheduled_arrival,
            snapshot.diverted_estimated_arrival,
            snapshot.diverted_actual_arrival,
            snapshot.diverted_destination_timezone,
            is_cancelled=False,
        )
        draw.text(
            (pad, y),
            f"Diverted to {snapshot.diverted_destination_iata or snapshot.diverted_destination_code}"
            f" ({snapshot.diverted_destination_name or snapshot.diverted_destination_city or ''})",
            font=_font(24, bold=True),
            fill=_ACCENT,
        )
        y += 34
        if diverted_value:
            draw.text((pad, y), f"{diverted_label} {diverted_value}", font=_font(20), fill=_TEXT)
        y += 46

    summary_parts = []
    operator_name = get_operator_name(snapshot.operator_icao)
    if snapshot.operator_icao:
        summary_parts.append(f"Operated by {operator_name or snapshot.operator_icao}")
    duration_text = _duration_text(snapshot.flight_duration_minutes)
    if duration_text:
        summary_parts.append(duration_text)
    distance_text = _distance_text(snapshot.route_distance)
    if distance_text:
        summary_parts.append(distance_text)
    if summary_parts:
        draw.text((pad, y), "  ·  ".join(summary_parts), font=_font(20), fill=_MUTED)
        y += 32

    if snapshot.registration:
        aircraft_type = snapshot.aircraft_type or "unknown type"
        aircraft_text = f"Aircraft: {snapshot.registration} ({aircraft_type})"
        draw.text((pad, y), aircraft_text, font=_font(20), fill=_MUTED)

    draw.text(
        (_WIDTH - pad, _HEIGHT - _MARGIN - 32),
        "Flight Companion",
        font=_font(18, bold=True),
        fill=_MUTED,
        anchor="ra",
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _draw_leg_column(
    draw: ImageDraw.ImageDraw,
    *,
    x: float,
    y: float,
    scheduled_text: str | None,
    dynamic_label: str,
    dynamic_value: str | None,
    gate: str | None,
    terminal: str | None,
    muted: bool,
) -> None:
    color = _MUTED if muted else _TEXT
    line_y = y
    draw.text((x, line_y), f"Scheduled: {scheduled_text or 'not yet available'}", font=_font(20), fill=color)
    line_y += 30
    value_text = dynamic_value or ("—" if dynamic_label == "Cancelled" else "not yet available")
    draw.text((x, line_y), f"{dynamic_label}: {value_text}", font=_font(20), fill=color)
    line_y += 30
    draw.text(
        (x, line_y),
        f"Gate {gate or 'not yet available'} / Terminal {terminal or '—'}",
        font=_font(20),
        fill=color,
    )
