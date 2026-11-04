# Contribuer

Chaque évolution suit trois étapes : une issue, une branche, une pull request.

## 1. Ouvrir une issue

Décrire l'évolution ou le bug dans une [issue](https://github.com/basilefuchs/polars-to-hprimxml/issues/new). Elle porte un numéro, repris aux étapes suivantes.

## 2. Créer une branche dédiée

Une branche par issue, créée depuis `dev`. Son nom commence par le numéro de l'issue, suivi d'un résumé court :

```bash
git switch dev
git pull
git switch -c 12-actes-ngap
```

Le lien « Create a branch » de l'issue sur GitHub donne le même format.

## 3. Ouvrir une pull request

- Cible : `dev`.
- La description cite l'issue avec `Closes #12`.
- Les tests passent, depuis la racine du dépôt :

```bash
pip install -e ".[test]"
pytest
```

- Si les colonnes ou les balises changent, le [README](README.md) est mis à jour.
