# SPDX-License-Identifier: GPL-3.0-or-later
"""evenementsPMSI: one message per row, each injecting one content into one RUM.

`content` picks what a row injects: "dp_dr" (DP and optional DR), "das"
(one DAS) or "actes" (one CCAM act). Columns of the other contents are ignored.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Literal

import polars as pl

from polars_hprimxml._common import (
    add_patient,
    add_venue,
    check_required,
    fmt_datetime,
    new_message,
    put,
    put_date_heure,
    serialize,
)

REQUIRED = ["ipp", "nda", "action", "id_rum", "date_action", "um"]
REQUIRED_BY_CONTENT = {
    "dp_dr": ["dp"],
    "das": ["das"],
    "actes": ["code_acte", "code_activite", "code_phase", "date_realisation"],
}


def pmsi_to_hprimxml(
    df: pl.DataFrame,
    sender: str,
    content: Literal["dp_dr", "das", "actes"],
    receiver: str | None = None,
    expect_ack: bool = False,
    produced_at: datetime | None = None,
) -> list[str]:
    """Convert rows into evenementsPMSI messages, one per row, targeting one RUM."""
    if content not in REQUIRED_BY_CONTENT:
        raise ValueError(
            f"content must be one of {list(REQUIRED_BY_CONTENT)}, got {content!r}"
        )
    check_required(df, REQUIRED + REQUIRED_BY_CONTENT[content])
    produced_at = produced_at or datetime.now()
    messages = []
    for row in df.iter_rows(named=True):
        root = new_message(
            "evenementsPMSI",
            row.get("identifiant_message"),
            sender,
            receiver,
            expect_ack,
            produced_at,
        )
        event = put(root, "evenementPMSI")
        add_patient(event, row)
        add_venue(event, row)
        rss = put(event, "rss")
        put(rss, "identifiantRSS/emetteur", row.get("id_rss"))
        rum = _add_rum(rss, row)
        if content == "dp_dr":
            put(rum, "diagnostics/diagnosticPrincipal/codeCim10", row["dp"])
            put(rum, "diagnostics/diagnosticRelie/codeCim10", row.get("dr"))
        elif content == "das":
            # TO CONFIRM: tag taken from Mediboard 4 (hprimXML 1.0x, diagnosticsRum).
            put(
                rum,
                "diagnostics/diagnosticsSignificatifs/diagnosticSignificatif/codeCim10",
                row["das"],
            )
        elif content == "actes":
            _add_acte(rum, row)
        messages.append(serialize(root))
    return messages


def _add_rum(rss: ET.Element, row: dict) -> ET.Element:
    rum = put(
        rss,
        "rum",
        action=row["action"],
        classant=row.get("classant"),
        prestationInterEtablissementA=row.get("prestation_inter_etablissement_a"),
    )
    put(rum, "dateAction", fmt_datetime(row["date_action"]))
    put(rum, "identifiant/emetteur", row["id_rum"])
    put(rum, "medecinResponsable/identification/code", row.get("medecin_responsable"))
    put(rum, "uniteMedicale/code", row["um"])
    put(rum, "uniteMedicale/entree", mode=row.get("mode_entree_um"))
    put_date_heure(rum, "uniteMedicale/entree", row.get("date_entree_um"))
    return rum


def _add_acte(rum: ET.Element, row: dict) -> None:
    acte = put(rum, "actes/acte", externe=row.get("externe"))
    ccam = put(
        acte, "CCAM", remboursementExceptionnel=row.get("remboursement_exceptionnel")
    )
    put(ccam, "codeActe", row["code_acte"])
    put(ccam, "codePhase", row["code_phase"])
    put(ccam, "codeActivite", row["code_activite"])
    put(ccam, "quantite", row.get("quantite"))
    put(ccam, "dateRealisation", fmt_datetime(row["date_realisation"]))
