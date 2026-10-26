---
name: kiro-credits-update
description: >
  Aktualisiert die Kiro-Credits-Statusleiste in Obsidian (Skala 0-1000 mit Prozentwert) und
  traegt den Stand optional in eine Verlaufstabelle ein. Verwenden, wenn der Nutzer
  "Credits aktualisieren", "Kiro Credits updaten", "Statusbar aktualisieren", "Usage eintragen"
  sagt oder einen Verbrauchswert nennt bzw. die Ausgabe von /usage einfuegt.
---

# Kiro Credits Update

Aktualisiert die permanente Statusleisten-Anzeige "Kiro" in Obsidian (Plugin
`kiro-credits-bar`).

## Hintergrund
- Die Anzeige wird vom Plugin `.obsidian/plugins/kiro-credits-bar/` gerendert und liest
  `usage.json` im selben Ordner (alle ~5 s, kein Neustart noetig).
- Der Verbrauchswert ist **nicht automatisch abrufbar**. `/usage` ist ein interaktiver
  Slash-Command der Kiro-CLI-Chat-Session; der Agent kann ihn nicht ausloesen, und es gibt
  keinen nicht-interaktiven Befehl (`kiro-cli usage` existiert nicht). Der Wert kommt deshalb
  vom Nutzer.
- **Bequemster Weg:** Der Nutzer fuehrt `/usage` aus und fuegt die **komplette Ausgabe** in den
  Chat ein. Das Skript parst daraus selbst Verbrauch, Prozent, Plan und Reset-Datum.

## Pfade / Portabilitaet
Das Skript findet den Vault **automatisch** (erste Fundstelle gewinnt):

1. `--data PFAD` – direkter Pfad zur `usage.json`
2. `--vault PFAD` – Vault-Wurzel (Ordner mit `.obsidian/`)
3. Env `KIRO_CREDITS_DATA` – direkter Pfad zur `usage.json`
4. Env `KIRO_CREDITS_VAULT` – Vault-Wurzel
5. aufwaerts vom Skript-Standort – erster Parent mit `.obsidian/`
6. aufwaerts vom aktuellen Arbeitsverzeichnis – erster Parent mit `.obsidian/`

Liegt das Skript innerhalb des Vaults (z. B. in `09 Skills/...`), greift Regel 5 von selbst –
dann ist **keine** Pfadangabe noetig. Andernfalls `--vault` setzen oder `KIRO_CREDITS_VAULT`
exportieren.

> Ersetze `<SCRIPT>` unten durch den tatsaechlichen Pfad zu `scripts/update_usage.py`.

## Ablauf

1. **Komplette `/usage`-Ausgabe entgegennehmen.** Beispiel:
   ```
   Estimated Usage | resets on 2026-11-01 | KIRO PRO
   Credits (74.79 of 1000 covered in plan)
   Additional credits: Add-on credits available for purchase
   ```
   Fehlt der Wert: kurz nachfragen ("Bitte `/usage` ausfuehren und die komplette Ausgabe
   einfuegen").

2. **Skript ausfuehren.** Komplette Ausgabe per stdin uebergeben (erkennt Verbrauch + Plan +
   Reset-Datum automatisch):

   ```bash
   printf '%s' "<HIER DIE KOMPLETTE /usage-AUSGABE>" | python3 "<SCRIPT>" --stdin
   ```

   Vault explizit angeben (falls Auto-Findung nicht greift):
   ```bash
   printf '%s' "<...>" | python3 "<SCRIPT>" --stdin --vault "/pfad/zum/Vault"
   ```

   Alternativen:
   ```bash
   # Einzelne /usage-Zeile als Argument
   python3 "<SCRIPT>" --parse "Credits (74.79 of 1000 covered in plan)"
   # Nur die reine Zahl
   python3 "<SCRIPT>" --used 74.79
   # Erst pruefen, nichts schreiben
   python3 "<SCRIPT>" --stdin --dry-run
   ```

   Optionale Parameter: `--limit` (Skalenende, Standard 1000), `--plan "Kiro Pro"`,
   `--note "Text"` (ueberschreibt erkanntes Reset-Datum), `--no-note` (Verlaufstabelle nicht
   ergaenzen), `--note-file "Notiz.md"` (Verlaufs-Notiz, absolut oder relativ zur Vault-Wurzel),
   `--dry-run` (nur anzeigen).

3. **Ergebnis bestaetigen:** Verbrauch, Prozentwert und ob eine Verlaufstabelle ergaenzt wurde.
   Die Statusleiste aktualisiert sich innerhalb von ~5 s selbst (oder sofort per Klick).

## Automatisch erkannt (bei `--stdin` / `--parse`)
- **Verbrauch & Limit:** aus `(X of Y covered in plan)` oder `(X used)`
- **Plan:** aus `KIRO PRO` / `KIRO PRO+` / `KIRO FREE` / `KIRO POWER` / `KIRO ENTERPRISE`
- **Reset-Datum:** aus `resets on 2026-11-01` oder `resets on Nov 1, 2026`; als Notiz
  `Reset <Datum>` uebernommen

## Verlaufstabelle (optional)
Standardmaessig wird **keine** Notiz geschrieben. Soll ein Verlauf gefuehrt werden, eine Notiz
mit einer Ueberschrift `## Verlauf` und einer Markdown-Tabelle anlegen und per `--note-file`
bzw. Env `KIRO_CREDITS_NOTE` referenzieren. Die neue Zeile wird unter die bestehende Tabelle
eingefuegt; eine leere Platzhalterzeile mit gleichem Datum wird ersetzt.

## Hinweise
- Farbe der Leiste: gruen < 70 %, gelb ab 70 %, rot ab 90 %.
- Klick auf die Leiste liest die Datei sofort neu ein.
- Ist ein anderes Limit als 1000 in der `/usage`-Ausgabe, wird dieses als Skalenende verwendet.
  Soll die Skala fix 0-1000 bleiben, `--limit 1000` mitgeben.
- Plugin muss in Obsidian unter Einstellungen -> Community-Plugins aktiviert sein.
- Benoetigt Python 3.8+ (keine externen Abhaengigkeiten).
