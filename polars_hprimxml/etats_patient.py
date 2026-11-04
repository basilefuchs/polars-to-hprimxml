# SPDX-License-Identifier: GPL-3.0-or-later
"""evenementsServeurEtatsPatient: one message per row, one diagnostic per message."""

from __future__ import annotations

from datetime import datetime

import polars as pl

from polars_hprimxml._common import (
    add_patient,
    add_venue,
    check_required,
    fmt_datetime,
    new_message,
    put,
    serialize,
)

REQUIRED = ["ipp", "nda", "action", "type_diagnostic", "code_cim10", "date_action"]


def etats_patient_to_hprimxml(
    df: pl.DataFrame,
    sender: str,
    receiver: str | None = None,
    expect_ack: bool = False,
    produced_at: datetime | None = None,
) -> list[str]:
    """Convert diagnoses, one per row, into evenementsServeurEtatsPatient messages."""
    check_required(df, REQUIRED)
    produced_at = produced_at or datetime.now()
    messages = []
    for row in df.iter_rows(named=True):
        root = new_message(
            "evenementsServeurEtatsPatient",
            row.get("identifiant_message"),
            sender,
            receiver,
            expect_ack,
            produced_at,
        )
        add_patient(root, row)
        add_venue(root, row)
        put(root, "intervention/identifiant/emetteur", row.get("id_intervention"))
        put(root, "intervention/uniteFonctionnelle/code", row.get("uf_intervention"))
        # TO CONFIRM: type "ds" for DAS comes from Mediboard 4 (hprimXML 1.0x);
        # no source found for the DAD code. type_diagnostic is written as given.
        diagnostic = put(
            root,
            "Diagnostics/diagnostic",
            action=row["action"],
            type=row["type_diagnostic"],
        )
        put(diagnostic, "dateAction", fmt_datetime(row["date_action"]))
        put(diagnostic, "codeCim10", row["code_cim10"])
        messages.append(serialize(root))
    return messages
