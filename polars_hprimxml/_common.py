# SPDX-License-Identifier: GPL-3.0-or-later
"""Blocks shared by the three message types: header, patient, venue, serialization.

Tag order and content follow the sample files of pyhprimxml (data/xml_tests),
not the hprimXML XSD: messages are not validated.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import date, datetime

import polars as pl

NAMESPACE = "http://www.hprim.org/hprimXML"
VERSION = "2.00"
DECLARATION = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def check_required(df: pl.DataFrame, columns: list[str]) -> None:
    """Raise ValueError if a required column is missing or holds nulls."""
    bad = [c for c in columns if c not in df.columns or df[c].null_count() > 0]
    if bad:
        raise ValueError(f"required columns missing or null: {bad}")


def put(
    parent: ET.Element, path: str, text: object = None, **attrib: object
) -> ET.Element:
    """Find or create each tag of `path` ("a/b/c") under `parent`.

    `text` and the non-null `attrib` go on the last tag. Elements left empty
    are removed by `serialize`.
    """
    node = parent
    for tag in path.split("/"):
        child = node.find(tag)
        node = child if child is not None else ET.SubElement(node, tag)
    if text is not None:
        node.text = str(text)
    for key, value in attrib.items():
        if value is not None:
            node.set(key, str(value))
    return node


def put_date_heure(parent: ET.Element, path: str, value: date | None) -> None:
    """Write `value` as <path>/date and <path>/heure."""
    put(parent, f"{path}/date", fmt_date(value))
    put(parent, f"{path}/heure", fmt_heure(value))


def fmt_date(value: date | None) -> str | None:
    return None if value is None else value.strftime("%Y-%m-%d")


def fmt_heure(value: date | None) -> str | None:
    return None if value is None else value.strftime("%H:%M:%S")


def fmt_datetime(value: date | None) -> str | None:
    return None if value is None else value.strftime("%Y-%m-%dT%H:%M:%S")


def new_message(
    root_tag: str,
    message_id: str | None,
    sender: str,
    receiver: str | None,
    expect_ack: bool,
    produced_at: datetime,
) -> ET.Element:
    """Root element with its enteteMessage."""
    root = ET.Element(
        root_tag,
        {
            "acquittementAttendu": "oui" if expect_ack else "non",
            "version": VERSION,
            "xmlns": NAMESPACE,
        },
    )
    entete = put(root, "enteteMessage")
    put(entete, "identifiantMessage", message_id or uuid.uuid4().hex)
    put(entete, "dateHeureProduction", fmt_datetime(produced_at))
    put(entete, "emetteur/agents/agent", categorie="application")
    put(entete, "emetteur/agents/agent/code", sender)
    put(entete, "destinataire/agents/agent", categorie="application")
    put(entete, "destinataire/agents/agent/code", receiver)
    return root


def add_patient(parent: ET.Element, row: dict) -> None:
    patient = put(
        parent,
        "patient",
        anonyme=row.get("anonyme"),
        confidentiel=row.get("confidentiel"),
    )
    put(patient, "identifiant/emetteur/valeur", row["ipp"])
    put(patient, "personnePhysique", sexe=row.get("sexe"))
    put(patient, "personnePhysique/nomUsuel", row.get("nom_usuel"))
    put(patient, "personnePhysique/nomNaissance", row.get("nom_naissance"))
    put(patient, "personnePhysique/prenoms/prenom", row.get("prenom"))
    put(
        patient,
        "personnePhysique/dateNaissance/date",
        fmt_date(row.get("date_naissance")),
    )


def add_venue(parent: ET.Element, row: dict) -> None:
    venue = put(parent, "venue", prive=row.get("prive"))
    put(venue, "identifiant/emetteur/valeur", row["nda"])
    put_date_heure(venue, "entree/dateHeureOptionnelle", row.get("date_entree"))
    put(venue, "entree/modeEntree/code", row.get("mode_entree"))
    put(venue, "entree/uniteFonctionnelleResponsable/code", row.get("uf_responsable"))


def serialize(root: ET.Element) -> str:
    """Drop empty elements, indent with tabs, prepend the XML declaration."""
    _prune(root)
    ET.indent(root, space="\t")
    return DECLARATION + ET.tostring(root, encoding="unicode") + "\n"


def _prune(node: ET.Element) -> None:
    for child in list(node):
        _prune(child)
        if child.text is None and not child.attrib and len(child) == 0:
            node.remove(child)
