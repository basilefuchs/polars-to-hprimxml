# SPDX-License-Identifier: GPL-3.0-or-later
"""evenementsServeurActes: one message per row, one acteCCAM per message."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

import polars as pl

from polars_hprimxml._common import (
    add_patient,
    add_venue,
    check_required,
    new_message,
    put,
    put_date_heure,
    serialize,
)

REQUIRED = [
    "ipp",
    "nda",
    "action",
    "id_acte",
    "code_acte",
    "code_activite",
    "code_phase",
    "date_execution",
]


def actes_to_hprimxml(
    df: pl.DataFrame,
    sender: str,
    receiver: str | None = None,
    expect_ack: bool = False,
    produced_at: datetime | None = None,
) -> list[str]:
    """Convert CCAM acts, one per row, into evenementsServeurActes messages."""
    check_required(df, REQUIRED)
    produced_at = produced_at or datetime.now()
    messages = []
    for row in df.iter_rows(named=True):
        root = new_message(
            "evenementsServeurActes",
            row.get("identifiant_message"),
            sender,
            receiver,
            expect_ack,
            produced_at,
        )
        event = put(root, "evenementServeurActe")
        add_patient(event, row)
        add_venue(event, row)
        _add_intervention(event, row)
        _add_acte(event, row)
        messages.append(serialize(root))
    return messages


def _add_intervention(event: ET.Element, row: dict) -> None:
    intervention = put(event, "intervention")
    put(intervention, "identifiant/emetteur", row.get("id_intervention"))
    put_date_heure(intervention, "debut", row.get("debut_intervention"))
    put_date_heure(intervention, "fin", row.get("fin_intervention"))
    put(intervention, "uniteFonctionnelle/code", row.get("uf_intervention"))
    put_date_heure(
        intervention, "demande/datePrescription", row.get("date_prescription")
    )
    put(intervention, "demande/uniteFonctionnelle/code", row.get("uf_demande"))


def _add_acte(event: ET.Element, row: dict) -> None:
    acte = put(
        event,
        "actesCCAM/acteCCAM",
        action=row["action"],
        facturable=row.get("facturable"),
        valide=row.get("valide"),
    )
    put(acte, "identifiant/emetteur", row["id_acte"])
    put(acte, "codeActe", row["code_acte"])
    put(acte, "codeActivite", row["code_activite"])
    put(acte, "codePhase", row["code_phase"])
    put_date_heure(acte, "execute", row["date_execution"])
    if row.get("medecin_executant") is not None:
        put(acte, "executant/medecins/medecinExecutant", principal="oui")
        put(
            acte,
            "executant/medecins/medecinExecutant/medecin/identification/code",
            row["medecin_executant"],
        )
    put(acte, "executant/uniteFonctionnelle/code", row.get("uf_executant"))
    put(acte, "quantite", row.get("quantite"))
