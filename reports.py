"""
AgriSense Report & Export Generator
====================================
Generates downloadable CSV datasets and ReportLab PDF engineering reports.
Adheres strictly to PRD Section 11.4, 15 (NFR-007), and Specification Lock v1.1.

Mandatory Compliance:
- Every export prominently includes: "SIMULATED DATA — Educational Prototype (AgriSense, Group 11)".
- Never claims physical sensor measurements or field yield savings.
- Handles empty DataFrames gracefully without throwing exceptions.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Optional, List, Any
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

from digital_core import StepSnapshot


DISCLAIMER_TEXT = (
    "SIMULATED DATA — Educational Prototype (AgriSense, Group 11). "
    "All sensor readings, soil hydrology, and actuator signals are generated "
    "by software models for DEC0101/DEC0151 coursework. No physical sensor accuracy "
    "or field agronomic performance is claimed."
)


def export_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Exports event history DataFrame to UTF-8 CSV bytes.
    Prepends mandatory simulated data declaration header.
    """
    header_comment = f"# SIMULATED DATA — Educational Prototype (AgriSense, Group 11)\n# Exported At: {datetime.now(timezone.utc).isoformat()}\n"
    csv_str = df.to_csv(index=False)
    full_output = header_comment + csv_str
    return full_output.encode("utf-8")


def export_pdf_bytes(snapshot: Optional[StepSnapshot], events_df: pd.DataFrame) -> bytes:
    """
    Compiles a structured A4 PDF simulation report using ReportLab.
    Returns the binary PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1b4d3e"),  # Forest Green
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#555555"),
        spaceAfter=10,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#8a3b00"),
        backColor=colors.HexColor("#fff3cd"),
        borderPadding=6,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1b4d3e"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#222222"),
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#111111"),
    )

    story: List[Any] = []

    # Title & Header
    story.append(Paragraph("AgriSense: Smart Irrigation Monitoring System", title_style))
    story.append(
        Paragraph(
            f"Developer Engineering Audit Report | Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Context: DEC0101 / DEC0151 PBL",
            subtitle_style,
        )
    )
    story.append(Paragraph(DISCLAIMER_TEXT, disclaimer_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1b4d3e"), spaceAfter=10))

    # Current System Snapshot Section
    story.append(Paragraph("1. Current Controller & Farm Snapshot", section_style))

    if snapshot is not None:
        pipo_str = f"Q3={snapshot.pipo.q3_valve1}, Q2={snapshot.pipo.q2_valve2}, Q1={snapshot.pipo.q1_fertigation}, Q0={snapshot.pipo.q0_alarm} ({snapshot.pipo.hex_str})"
        snapshot_data = [
            [
                Paragraph("<b>Parameter</b>", table_cell_style),
                Paragraph("<b>Value</b>", table_cell_style),
                Paragraph("<b>Parameter</b>", table_cell_style),
                Paragraph("<b>Value</b>", table_cell_style),
            ],
            [
                Paragraph("Zone 1 Moisture", table_cell_style),
                Paragraph(f"{snapshot.zone1_moisture:.1f}%", table_cell_style),
                Paragraph("FSM State", table_cell_style),
                Paragraph(f"{snapshot.fsm_state.value} ({snapshot.fsm_code})", table_cell_style),
            ],
            [
                Paragraph("Zone 2 Moisture", table_cell_style),
                Paragraph(f"{snapshot.zone2_moisture:.1f}%", table_cell_style),
                Paragraph("Pump Relay (P)", table_cell_style),
                Paragraph("ENERGIZED (1)" if snapshot.pump_output else "OFF (0)", table_cell_style),
            ],
            [
                Paragraph("Water Reservoir", table_cell_style),
                Paragraph(f"{snapshot.tank_level:.1f}%", table_cell_style),
                Paragraph("Alarm Output (A)", table_cell_style),
                Paragraph("ACTIVE (1)" if snapshot.alarm_output else "INACTIVE (0)", table_cell_style),
            ],
            [
                Paragraph("Rainfall Sensor (R)", table_cell_style),
                Paragraph("DETECTED (1)" if snapshot.rain_detected else "DRY (0)", table_cell_style),
                Paragraph("MOD-16 Counter", table_cell_style),
                Paragraph(f"{snapshot.counter} ({snapshot.counter_bin})", table_cell_style),
            ],
            [
                Paragraph("Manual Override (O)", table_cell_style),
                Paragraph(f"{'ON (1)' if snapshot.manual_override else 'OFF (0)'} -> {snapshot.manual_target_zone.value}", table_cell_style),
                Paragraph("PIPO Bus (Q3..Q0)", table_cell_style),
                Paragraph(pipo_str, table_cell_style),
            ],
        ]
        snap_table = Table(snapshot_data, colWidths=[120, 130, 130, 140])
        snap_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2efe9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(snap_table)

        # Recommendations
        if snapshot.recommendations:
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>Active Controller Advisories:</b>", body_style))
            for rec in snapshot.recommendations:
                story.append(Paragraph(f"• {rec}", table_cell_style))
    else:
        story.append(Paragraph("<i>No live snapshot available. Report generated from event archive.</i>", body_style))

    story.append(Spacer(1, 10))

    # Recent Event Log Section
    story.append(Paragraph("2. Simulation Event History", section_style))

    if events_df is None or events_df.empty:
        empty_data = [
            [Paragraph("<b>Status</b>", table_cell_style), Paragraph("<b>Details</b>", table_cell_style)],
            [
                Paragraph("Database Empty", table_cell_style),
                Paragraph("No historical events recorded in the SQLite log yet.", table_cell_style),
            ],
        ]
        empty_table = Table(empty_data, colWidths=[150, 370])
        empty_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(empty_table)
    else:
        # Display up to 15 most recent events
        display_df = events_df.tail(15)
        table_rows = [
            [
                Paragraph("<b>ID</b>", table_cell_style),
                Paragraph("<b>Timestamp (UTC)</b>", table_cell_style),
                Paragraph("<b>Z1/Z2</b>", table_cell_style),
                Paragraph("<b>Tank</b>", table_cell_style),
                Paragraph("<b>Pump</b>", table_cell_style),
                Paragraph("<b>State</b>", table_cell_style),
                Paragraph("<b>Cnt</b>", table_cell_style),
                Paragraph("<b>Message</b>", table_cell_style),
            ]
        ]
        for _, row in display_df.iterrows():
            ts_short = str(row.get("timestamp", ""))[-8:]  # HH:MM:SS
            table_rows.append([
                Paragraph(str(row.get("id", "")), table_cell_style),
                Paragraph(ts_short, table_cell_style),
                Paragraph(f"{float(row.get('zone1', 0)):.0f}/{float(row.get('zone2', 0)):.0f}%", table_cell_style),
                Paragraph(f"{float(row.get('tank', 0)):.0f}%", table_cell_style),
                Paragraph("ON" if row.get("pump") == 1 else "OFF", table_cell_style),
                Paragraph(str(row.get("fsm_state", "")), table_cell_style),
                Paragraph(str(row.get("counter", "")), table_cell_style),
                Paragraph(str(row.get("message", ""))[:45], table_cell_style),
            ])

        evt_table = Table(table_rows, colWidths=[25, 60, 55, 40, 35, 80, 25, 200])
        evt_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2efe9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        story.append(evt_table)

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa"), spaceAfter=6))
    story.append(
        Paragraph(
            "AgriSense PBL Verification Suite • First-Year B.Tech DEC0101 / DEC0151 • Group 11",
            subtitle_style,
        )
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
