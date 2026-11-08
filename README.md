# polars-to-hprimxml

> **Dépôt archivé, package non maintenu.** Utilisez [pyhprimxml](https://github.com/GuillaumePressiat/pyhprimxml) de Guillaume Pressiat : depuis sa version 0.2.0, il écrit aussi les messages hprimXML (actes CCAM, états patient, PMSI) depuis des DataFrames polars, avec validation XSD, et il les relit.
>
> ```bash
> pip install git+https://github.com/GuillaumePressiat/pyhprimxml
> ```
>
> Voir son guide [Écrire depuis des tables](https://github.com/GuillaumePressiat/pyhprimxml/blob/main/doc/guide/ecriture.md).
>
> Les messages produits par polars-to-hprimxml ne sont pas conformes aux XSD hprimXML 2.00.

Convertit un DataFrame [polars](https://pola.rs) en messages [hprimXML](https://www.interopsante.org/hprim) 2.00 :

- actes CCAM (`evenementsServeurActes`) ;
- états patient (`evenementsServeurEtatsPatient`) ;
- PMSI (`evenementsPMSI`).

> **Sans garantie.** Les messages ne sont pas validés contre les XSD hprimXML : vérifiez-les avec votre logiciel récepteur.

## Installation

```bash
pip install polars-to-hprimxml
```

Python ≥ 3.9. Seule dépendance : polars ≥ 1.0.

## Principe

- Une ligne donne un message : un acte (actes), un diagnostic (états patient) ou une injection sur un RUM (PMSI). Chaque fonction retourne une `list[str]`, dans l'ordre des lignes.
- Pour le PMSI, le paramètre `content` choisit ce que chaque ligne injecte : `"dp_dr"` (DP avec ou sans DR), `"das"` (un DAS) ou `"actes"` (un acte).
- Une colonne obligatoire absente ou nulle lève une `ValueError`. Une colonne optionnelle absente ou nulle fait omettre la balise. Les autres colonnes sont ignorées.
- Les dates sont des colonnes `pl.Date` ou `pl.Datetime`. Le package les formate et découpe un `pl.Datetime` en `<date>` + `<heure>` quand la balise l'exige.
- Les valeurs d'attributs sont écrites telles quelles (`"oui"`, `"non"`, `"creation"`, `"M"`…).
- Sortie : UTF-8, déclaration `standalone="yes"`, namespace `http://www.hprim.org/hprimXML`, version `2.00`, indentation par tabulations.

## Paramètres

Signature commune : `(df, sender, receiver=None, expect_ack=False, produced_at=None)`. `pmsi_to_hprimxml` prend en plus `content`, juste après `sender`.

| Paramètre | Rôle | Défaut |
|---|---|---|
| `df` | DataFrame polars, une ligne par message | — |
| `sender` | code de l'application émettrice (`enteteMessage/emetteur/agents/agent/code`) | obligatoire |
| `content` | PMSI seulement : `"dp_dr"`, `"das"` ou `"actes"` | obligatoire |
| `receiver` | code de l'application destinataire | `None` : `<agent categorie="application" />` sans code |
| `expect_ack` | attribut `acquittementAttendu` (`"oui"` / `"non"`) | `False` |
| `produced_at` | `enteteMessage/dateHeureProduction` | date et heure de l'appel |

## Exemples

### Actes CCAM

```python
from datetime import datetime
from pathlib import Path

import polars as pl

from polars_hprimxml import actes_to_hprimxml

actes = pl.DataFrame(
    {
        "identifiant_message": ["acte_0001", "acte_0002"],
        "id_acte": ["121212", "121213"],
        "code_acte": ["EBLA003", "YYYY033"],
    }
).with_columns(
    ipp=pl.lit("123456789"),
    nom_usuel=pl.lit("SANDWICK"),
    prenom=pl.lit("JOHN"),
    nda=pl.lit("987654321"),
    action=pl.lit("creation"),
    code_activite=pl.lit("1"),
    code_phase=pl.lit("0"),
    date_execution=pl.lit(datetime(2024, 1, 1, 8, 10)),
    uf_executant=pl.lit("4321"),
)

xmls = actes_to_hprimxml(actes, sender="MON_APPLI")

sortie = Path("sortie")
sortie.mkdir(exist_ok=True)
for identifiant, xml in zip(actes["identifiant_message"], xmls):
    (sortie / f"{identifiant}.xml").write_text(xml, encoding="utf-8")
```

Contenu de `sortie/acte_0001.xml` (affiché ici avec deux espaces, le fichier est indenté par tabulations) :

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<evenementsServeurActes acquittementAttendu="non" version="2.00" xmlns="http://www.hprim.org/hprimXML">
  <enteteMessage>
    <identifiantMessage>acte_0001</identifiantMessage>
    <dateHeureProduction>2024-01-02T09:30:00</dateHeureProduction>
    <emetteur>
      <agents>
        <agent categorie="application">
          <code>MON_APPLI</code>
        </agent>
      </agents>
    </emetteur>
    <destinataire>
      <agents>
        <agent categorie="application" />
      </agents>
    </destinataire>
  </enteteMessage>
  <evenementServeurActe>
    <patient>
      <identifiant>
        <emetteur>
          <valeur>123456789</valeur>
        </emetteur>
      </identifiant>
      <personnePhysique>
        <nomUsuel>SANDWICK</nomUsuel>
        <prenoms>
          <prenom>JOHN</prenom>
        </prenoms>
      </personnePhysique>
    </patient>
    <venue>
      <identifiant>
        <emetteur>
          <valeur>987654321</valeur>
        </emetteur>
      </identifiant>
    </venue>
    <actesCCAM>
      <acteCCAM action="creation">
        <identifiant>
          <emetteur>121212</emetteur>
        </identifiant>
        <codeActe>EBLA003</codeActe>
        <codeActivite>1</codeActivite>
        <codePhase>0</codePhase>
        <execute>
          <date>2024-01-01</date>
          <heure>08:10:00</heure>
        </execute>
        <executant>
          <uniteFonctionnelle>
            <code>4321</code>
          </uniteFonctionnelle>
        </executant>
      </acteCCAM>
    </actesCCAM>
  </evenementServeurActe>
</evenementsServeurActes>
```

Sans colonne d'intervention, la balise `intervention` est omise.

### États patient : DP, DR et DAS

```python
from polars_hprimxml import etats_patient_to_hprimxml

diagnostics = pl.DataFrame(
    {
        "identifiant_message": ["esep_0001", "esep_0002", "esep_0003"],
        "type_diagnostic": ["dp", "dr", "ds"],
        "code_cim10": ["Z511", "C10", "E119"],
    }
).with_columns(
    ipp=pl.lit("123456789"),
    nda=pl.lit("987654321"),
    action=pl.lit("creation"),
    date_action=pl.lit(datetime(2024, 1, 1, 8, 10)),
)

xmls = etats_patient_to_hprimxml(diagnostics, sender="MON_APPLI")  # 3 messages
```

Le DAS passe par `type_diagnostic="ds"` (voir [À confirmer](#à-confirmer)).

### PMSI : DP/DR, DAS et actes sur un RUM

```python
from polars_hprimxml import pmsi_to_hprimxml

rum = {
    "ipp": "123456789",
    "nda": "987654321",
    "action": "creation",
    "id_rum": "98765",
    "date_action": datetime(2024, 1, 1, 8, 10),
    "um": "4321",
}

dp_dr = pl.DataFrame(
    [{**rum, "identifiant_message": "pmsi_dp_0001", "dp": "Z511", "dr": "C10"}]
)
das = pl.DataFrame(
    [
        {**rum, "identifiant_message": "pmsi_das_0001", "das": "E119"},
        {**rum, "identifiant_message": "pmsi_das_0002", "das": "I10"},
    ]
)
actes_rum = pl.DataFrame(
    [
        {
            **rum,
            "identifiant_message": "pmsi_acte_0001",
            "code_acte": "EBLA003",
            "code_activite": "1",
            "code_phase": "0",
            "date_realisation": datetime(2024, 1, 1, 8, 10),
        }
    ]
)

xmls = (
    pmsi_to_hprimxml(dp_dr, sender="MON_APPLI", content="dp_dr")
    + pmsi_to_hprimxml(das, sender="MON_APPLI", content="das")
    + pmsi_to_hprimxml(actes_rum, sender="MON_APPLI", content="actes")
)
```

Quatre messages ciblent le RUM `98765` : un pour le DP et le DR, un par DAS, un pour l'acte. Les fichiers s'écrivent comme pour les actes.

## Colonnes

### Communes aux trois types

| Colonne | Type | Obligatoire | Balise |
|---|---|---|---|
| `identifiant_message` | texte | non (uuid4 par défaut) | `enteteMessage/identifiantMessage` |
| `ipp` | texte | oui | `patient/identifiant/emetteur/valeur` |
| `anonyme` | texte | non | `patient/@anonyme` |
| `confidentiel` | texte | non | `patient/@confidentiel` |
| `sexe` | texte | non | `patient/personnePhysique/@sexe` |
| `nom_usuel` | texte | non | `patient/personnePhysique/nomUsuel` |
| `nom_naissance` | texte | non | `patient/personnePhysique/nomNaissance` |
| `prenom` | texte | non | `patient/personnePhysique/prenoms/prenom` |
| `date_naissance` | `pl.Date` | non | `patient/personnePhysique/dateNaissance/date` |
| `nda` | texte | oui | `venue/identifiant/emetteur/valeur` |
| `prive` | texte | non | `venue/@prive` |
| `date_entree` | `pl.Datetime` | non | `venue/entree/dateHeureOptionnelle/date` + `heure` |
| `mode_entree` | texte | non | `venue/entree/modeEntree/code` |
| `uf_responsable` | texte | non | `venue/entree/uniteFonctionnelleResponsable/code` |

### Actes : `actes_to_hprimxml`

Balises sous `evenementServeurActe`.

| Colonne | Type | Obligatoire | Balise |
|---|---|---|---|
| `action` | texte | oui | `actesCCAM/acteCCAM/@action` |
| `facturable` | texte | non | `actesCCAM/acteCCAM/@facturable` |
| `valide` | texte | non | `actesCCAM/acteCCAM/@valide` |
| `id_acte` | texte | oui | `actesCCAM/acteCCAM/identifiant/emetteur` |
| `code_acte` | texte | oui | `actesCCAM/acteCCAM/codeActe` |
| `code_activite` | texte | oui | `actesCCAM/acteCCAM/codeActivite` |
| `code_phase` | texte | oui | `actesCCAM/acteCCAM/codePhase` |
| `date_execution` | `pl.Datetime` | oui | `actesCCAM/acteCCAM/execute/date` + `heure` |
| `medecin_executant` | texte | non | `actesCCAM/acteCCAM/executant/medecins/medecinExecutant/medecin/identification/code`, avec `principal="oui"` |
| `uf_executant` | texte | non | `actesCCAM/acteCCAM/executant/uniteFonctionnelle/code` |
| `quantite` | entier ou texte | non | `actesCCAM/acteCCAM/quantite` |
| `id_intervention` | texte | non | `intervention/identifiant/emetteur` |
| `debut_intervention` | `pl.Datetime` | non | `intervention/debut/date` + `heure` |
| `fin_intervention` | `pl.Datetime` | non | `intervention/fin/date` + `heure` |
| `uf_intervention` | texte | non | `intervention/uniteFonctionnelle/code` |
| `date_prescription` | `pl.Datetime` | non | `intervention/demande/datePrescription/date` + `heure` |
| `uf_demande` | texte | non | `intervention/demande/uniteFonctionnelle/code` |

### États patient : `etats_patient_to_hprimxml`

Balises sous la racine `evenementsServeurEtatsPatient`.

| Colonne | Type | Obligatoire | Balise |
|---|---|---|---|
| `action` | texte | oui | `Diagnostics/diagnostic/@action` |
| `type_diagnostic` | texte | oui | `Diagnostics/diagnostic/@type` (`"dp"`, `"dr"`, `"ds"`…) |
| `code_cim10` | texte | oui | `Diagnostics/diagnostic/codeCim10` |
| `date_action` | `pl.Datetime` | oui | `Diagnostics/diagnostic/dateAction` |
| `id_intervention` | texte | non | `intervention/identifiant/emetteur` |
| `uf_intervention` | texte | non | `intervention/uniteFonctionnelle/code` |

### PMSI : `pmsi_to_hprimxml`

Une ligne donne un message qui cible un RUM : un `evenementPMSI` dont le `rss` contient un seul `rum`. Le paramètre `content` choisit ce que la ligne injecte ; les colonnes des autres contenus sont ignorées. Balises sous `evenementPMSI/rss`.

| Colonne | Contenu | Type | Obligatoire | Balise |
|---|---|---|---|---|
| `id_rss` | tous | texte | non | `identifiantRSS/emetteur` |
| `action` | tous | texte | oui | `rum/@action` |
| `classant` | tous | texte | non | `rum/@classant` |
| `prestation_inter_etablissement_a` | tous | texte | non | `rum/@prestationInterEtablissementA` |
| `date_action` | tous | `pl.Datetime` | oui | `rum/dateAction` |
| `id_rum` | tous | texte | oui | `rum/identifiant/emetteur` |
| `medecin_responsable` | tous | texte | non | `rum/medecinResponsable/identification/code` |
| `um` | tous | texte | oui | `rum/uniteMedicale/code` |
| `date_entree_um` | tous | `pl.Datetime` | non | `rum/uniteMedicale/entree/date` + `heure` |
| `mode_entree_um` | tous | texte | non | `rum/uniteMedicale/entree/@mode` |
| `dp` | `dp_dr` | texte | oui | `rum/diagnostics/diagnosticPrincipal/codeCim10` |
| `dr` | `dp_dr` | texte | non | `rum/diagnostics/diagnosticRelie/codeCim10` |
| `das` | `das` | texte | oui | `rum/diagnostics/diagnosticsSignificatifs/diagnosticSignificatif/codeCim10` (à confirmer) |
| `code_acte` | `actes` | texte | oui | `rum/actes/acte/CCAM/codeActe` |
| `code_phase` | `actes` | texte | oui | `rum/actes/acte/CCAM/codePhase` |
| `code_activite` | `actes` | texte | oui | `rum/actes/acte/CCAM/codeActivite` |
| `quantite` | `actes` | entier ou texte | non | `rum/actes/acte/CCAM/quantite` |
| `date_realisation` | `actes` | `pl.Datetime` | oui | `rum/actes/acte/CCAM/dateRealisation` |
| `externe` | `actes` | texte | non | `rum/actes/acte/@externe` |
| `remboursement_exceptionnel` | `actes` | texte | non | `rum/actes/acte/CCAM/@remboursementExceptionnel` |

## Non géré

Identifiants `recepteur` ; attributs `etat`, `portee` et `referent` des identifiants ; `commentaireMessage` et `modeTraitement` ; `radiotherapie` et `seance` ; nom et prénom du médecin responsable ; sortie d'UM ; plusieurs RUM, DAS ou actes dans un même message PMSI (une ligne = une injection) ; DAD dans le RUM (ils passent par les états patient) ; actes NGAP et LPP ; validation XSD.

## À confirmer

- Le code `"ds"` des DAS dans les états patient vient de Mediboard 4 (hprimXML 1.0x), pas de la norme 2.00.
- La balise des DAS dans le RUM, `diagnosticsSignificatifs/diagnosticSignificatif`, vient aussi de Mediboard 4, où elle figure sous `diagnosticsRum`.
- Code des DAD : aucune source trouvée. `type_diagnostic` est écrit tel quel, il suffit donc de passer le bon code.
- L'ordre et le contenu des balises reprennent les fichiers d'exemple de pyhprimxml (`data/xml_tests`), pas les XSD.

## Tests

```bash
cd polars-to-hprimxml
pip install -e ".[test]"
pytest
```

## Licence

GPL-3.0-or-later, voir [`LICENSE`](LICENSE).
