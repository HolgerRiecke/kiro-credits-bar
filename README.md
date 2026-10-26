# Kiro Credits Bar

Eine Obsidian-Statusleiste, die den Credit-Verbrauch der **Kiro CLI** als Skala
(0–1000) mit Prozentwert permanent unten in Obsidian anzeigt.

So sieht die Leiste unten in Obsidian aus:

```
Kiro  0 ▓▓▓▓▓░░░░░░░░░░░░░░░░ 1000  25 %
```

(grün < 70 %, gelb ab 70 %, rot ab 90 %; Klick = sofort neu einlesen)

Das Projekt besteht aus zwei Teilen:

| Teil | Zweck |
| --- | --- |
| **Plugin** `kiro-credits-bar` | Zeichnet die Statusleiste. Liest `usage.json`. |
| **Skill** `kiro-credits-update` | Schreibt `usage.json` aus der `/usage`-Ausgabe der Kiro CLI. |

Du kannst das Plugin **auch allein** nutzen und `usage.json` von Hand pflegen. Der
Skill ist optionaler Komfort für Nutzer der Kiro CLI.

---

## 1. Plugin installieren

### Variante A: BRAT (empfohlen, mit Auto-Updates)

1. In Obsidian das Community-Plugin **BRAT** installieren und aktivieren.
2. BRAT → *Add Beta plugin* → dieses Repo angeben:
   `HolgerRiecke/kiro-credits-bar`
3. Danach unter **Einstellungen → Community-Plugins** das Plugin
   *Kiro Credits Bar* aktivieren.

BRAT holt künftige Versionen automatisch (gesteuert über `manifest.json` +
`versions.json`).

### Variante B: Manuell

1. Im Vault den Ordner `.obsidian/plugins/kiro-credits-bar/` anlegen.
2. Die drei Dateien `main.js`, `manifest.json`, `styles.css` aus diesem Repo
   dort hineinkopieren.
3. Obsidian neu laden (oder Community-Plugins aus/einschalten) und das Plugin
   aktivieren.

Direkt nach der Installation zeigt die Leiste `– %`, weil noch keine `usage.json`
existiert. Das ist normal.

---

## 2. Wert setzen

### Von Hand (ohne Skill)

Lege `.obsidian/plugins/kiro-credits-bar/usage.json` an:

```json
{
  "used": 85.04,
  "limit": 1000,
  "percent": 8.5,
  "plan": "Kiro Pro",
  "updated": "2026-10-26 20:24",
  "note": "Reset 2026-11-01"
}
```

Die Leiste aktualisiert sich innerhalb von ~5 s selbst. `percent`, `plan`, `note`,
`updated` sind optional; Pflicht sind nur `used` (und sinnvollerweise `limit`).

### Mit dem Skill (Kiro CLI)

1. Den Ordner `skill/` dieses Repos als Skill installieren – also nach
   `~/.kiro/skills/kiro-credits-update/` kopieren oder dorthin verlinken:

   ```bash
   # Beispiel (Pfad zum geklonten Repo anpassen):
   ln -s "$PWD/skill" ~/.kiro/skills/kiro-credits-update
   ```

2. In der Kiro-CLI-Chat-Session `/usage` ausführen und die **komplette Ausgabe**
   einfügen. Sag z. B. „Kiro Credits aktualisieren". Der Skill parst Verbrauch,
   Plan und Reset-Datum automatisch und schreibt `usage.json`.

Das Skript findet den Vault automatisch, wenn es innerhalb des Vaults liegt.
Andernfalls `--vault` angeben oder `KIRO_CREDITS_VAULT` setzen – Details in
[`skill/SKILL.md`](skill/SKILL.md).

Manueller Direktaufruf (ohne Kiro CLI):

```bash
printf '%s' "Credits (85.04 of 1000 covered in plan)" \
  | python3 skill/scripts/update_usage.py --stdin --vault "/pfad/zum/Vault"
```

Benötigt Python 3.8+ (keine externen Abhängigkeiten).

---

## Anzeige / Farben

- grün < 70 %, gelb ab 70 %, rot ab 90 %
- Klick auf die Leiste liest `usage.json` sofort neu ein
- Tooltip zeigt Verbrauch, Plan, Stand und Notiz

---

## Warum nicht vollautomatisch?

`/usage` ist ein **interaktiver** Slash-Command der Kiro CLI. Es gibt keinen
nicht-interaktiven Befehl (`kiro-cli usage` existiert nicht) und keine lokale
Datei, aus der sich der Wert zuverlässig ziehen ließe. Deshalb fügt man die
`/usage`-Ausgabe einmalig ein; der Rest läuft automatisch.

---

## Lizenz

[MIT](LICENSE)
