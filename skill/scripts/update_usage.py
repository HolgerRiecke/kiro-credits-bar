#!/usr/bin/env python3
"""Aktualisiert die Kiro-Credits-Statusleiste (Plugin "kiro-credits-bar") in Obsidian.

Schreibt die Datei usage.json im Plugin-Ordner
(.obsidian/plugins/kiro-credits-bar/usage.json). Optional wird zusaetzlich eine
Zeile in eine Verlaufstabelle einer Markdown-Notiz eingetragen.

Der Vault wird AUTOMATISCH gefunden (siehe unten). Nichts ist fest verdrahtet,
das Skript ist in jedem Vault lauffaehig.

Vault-Findung (erste Fundstelle gewinnt):
  1. --data PFAD            -> direkter Pfad zur usage.json
  2. --vault PFAD           -> Vault-Wurzel (Ordner mit .obsidian/)
  3. Env KIRO_CREDITS_DATA  -> direkter Pfad zur usage.json
  4. Env KIRO_CREDITS_VAULT -> Vault-Wurzel
  5. Aufwaerts vom Skript   -> erster Parent-Ordner mit .obsidian/
  6. Aufwaerts vom CWD      -> erster Parent-Ordner mit .obsidian/

Aufrufe:
  echo "<komplette /usage-Ausgabe>" | update_usage.py --stdin
  update_usage.py --parse "Credits (74.79 of 1000 covered in plan)"
  update_usage.py --used 412.5 --plan "Kiro Pro"
  update_usage.py --used 412.5 --vault "/pfad/zum/Vault" --note-file "Kiro Credits.md"
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

PLUGIN_ID = "kiro-credits-bar"
DATA_REL = Path(".obsidian") / "plugins" / PLUGIN_ID / "usage.json"


# --------------------------------------------------------------------------- #
# Vault- / Pfad-Findung
# --------------------------------------------------------------------------- #
def find_vault_root(start):
    """Laeuft von 'start' aufwaerts und sucht einen Ordner mit .obsidian/."""
    start = start.resolve()
    for folder in [start, *start.parents]:
        if (folder / ".obsidian").is_dir():
            return folder
    return None


def resolve_data_path(args) -> Path:
    """Ermittelt den Zielpfad der usage.json nach obiger Reihenfolge."""
    # 1. expliziter Datei-Pfad
    if args.data:
        return Path(args.data).expanduser()
    # 2. expliziter Vault-Ordner
    if args.vault:
        return Path(args.vault).expanduser() / DATA_REL
    # 3. Env: direkter Datei-Pfad
    env_data = os.environ.get("KIRO_CREDITS_DATA")
    if env_data:
        return Path(env_data).expanduser()
    # 4. Env: Vault-Ordner
    env_vault = os.environ.get("KIRO_CREDITS_VAULT")
    if env_vault:
        return Path(env_vault).expanduser() / DATA_REL
    # 5. aufwaerts vom Skript-Standort
    root = find_vault_root(Path(__file__).parent)
    if root:
        return root / DATA_REL
    # 6. aufwaerts vom aktuellen Arbeitsverzeichnis
    root = find_vault_root(Path.cwd())
    if root:
        return root / DATA_REL
    sys.exit(
        "Fehler: Vault nicht gefunden. Bitte --vault PFAD oder --data PFAD angeben "
        "oder KIRO_CREDITS_VAULT setzen."
    )


def resolve_note_path(args, data_path):
    """Pfad zur Verlaufs-Notiz (optional). Ohne Angabe: keine Tabelle."""
    if args.no_note:
        return None
    if args.note_file:
        p = Path(args.note_file).expanduser()
        if p.is_absolute():
            return p
        # relativ zur Vault-Wurzel aufloesen
        vault = data_path.parent.parent.parent.parent  # .../usage.json -> Vault
        return vault / args.note_file
    env_note = os.environ.get("KIRO_CREDITS_NOTE")
    if env_note:
        return Path(env_note).expanduser()
    return None


# --------------------------------------------------------------------------- #
# Parsing der /usage-Ausgabe
# --------------------------------------------------------------------------- #
def num(text: str) -> float:
    """'1,000.50' / '1.000,50' / '412.5' -> float"""
    t = text.strip()
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    return float(t)


def parse_usage_text(text: str):
    """Liest '(X of Y ...' bzw. '(X used' aus der /usage-Ausgabe."""
    m = re.search(r"\(\s*([\d.,]+)\s+of\s+([\d.,]+)", text)
    if m:
        return num(m.group(1)), num(m.group(2))
    m = re.search(r"\(\s*([\d.,]+)\s+used", text)
    if m:
        return num(m.group(1)), None
    return None, None


def parse_plan(text: str):
    """Erkennt den Plan-Namen (z. B. 'KIRO PRO')."""
    m = re.search(r"\bKIRO\s+(PRO\+|PRO|FREE|POWER|ENTERPRISE)", text, re.IGNORECASE)
    if m:
        return "Kiro " + m.group(1).title()
    return None


def parse_reset(text: str):
    """Erkennt das Reset-Datum, z. B. 'resets on 2026-11-01' oder 'resets on Nov 1, 2026'."""
    m = re.search(r"resets?\s+on\s+([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"resets?\s+on\s+([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"expires?\s+([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})", text)
    if m:
        return "Add-on laeuft ab " + m.group(1).strip()
    return None


def fmt(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:.2f}".rstrip("0").rstrip(".")


# --------------------------------------------------------------------------- #
# Verlaufstabelle (optional)
# --------------------------------------------------------------------------- #
def update_note(note_path: Path, date: str, used: float, limit: float, note: str) -> bool:
    """Ergaenzt eine Zeile in der Verlaufstabelle unter '## Verlauf'. Optional."""
    if not note_path or not note_path.exists():
        return False
    lines = note_path.read_text(encoding="utf-8").splitlines()

    try:
        start = next(i for i, l in enumerate(lines) if l.strip().startswith("## Verlauf"))
    except StopIteration:
        return False
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))

    table_idx = [i for i in range(start, end) if lines[i].lstrip().startswith("|")]
    if not table_idx:
        return False

    pct = used / limit * 100
    row = f"| {date} | {fmt(used)} ({pct:.0f} %) | {fmt(limit)} | | | {note} |"

    # Leere Platzhalterzeile desselben Datums ersetzen
    for i in table_idx[2:]:
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if cells and cells[0] == date and len(cells) > 1 and cells[1] == "":
            lines[i] = row
            note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True

    lines.insert(table_idx[-1] + 1, row)
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


# --------------------------------------------------------------------------- #
# Hauptprogramm
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--used", type=str, help="Verbrauchte Credits/Requests")
    ap.add_argument("--limit", type=str, help="Skalenende (Standard 1000)")
    ap.add_argument("--plan", type=str, default=None)
    ap.add_argument("--note", type=str, default="")
    ap.add_argument("--parse", type=str, nargs="?", const="-", default=None,
                    help="Text der /usage-Ausgabe; zieht 'X of Y' heraus. "
                         "Ohne Wert (oder '-') wird von stdin gelesen.")
    ap.add_argument("--stdin", action="store_true", help="Komplette /usage-Ausgabe von stdin lesen")
    ap.add_argument("--no-note", action="store_true", help="Verlaufstabelle nicht ergaenzen")
    ap.add_argument("--vault", type=str, default=None, help="Vault-Wurzel (Ordner mit .obsidian/)")
    ap.add_argument("--data", type=str, default=None, help="Direkter Pfad zur usage.json")
    ap.add_argument("--note-file", type=str, default=None,
                    help="Verlaufs-Notiz (absolut oder relativ zur Vault-Wurzel)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Nur anzeigen, was passieren wuerde; nichts schreiben")
    a = ap.parse_args()

    # Text aus --parse bzw. stdin beschaffen
    parse_text = None
    if a.stdin or a.parse == "-":
        parse_text = sys.stdin.read()
    elif a.parse:
        parse_text = a.parse

    used = limit = None
    reset = None
    if parse_text:
        used, limit = parse_usage_text(parse_text)
        if a.plan is None:
            a.plan = parse_plan(parse_text)
        reset = parse_reset(parse_text)
    if a.used is not None:
        used = num(a.used)
    if a.limit is not None:
        limit = num(a.limit)

    if not a.note and reset:
        a.note = f"Reset {reset}"

    if used is None:
        sys.exit("Fehler: kein Verbrauchswert (--used, --parse mit '(X of Y ...' oder --stdin)")

    if limit is None or limit <= 0:
        limit = 1000.0

    data_path = resolve_data_path(a)
    note_path = resolve_note_path(a, data_path)

    now = datetime.now()
    pct = used / limit * 100
    payload = {
        "used": used,
        "limit": limit,
        "percent": round(pct, 1),
        "plan": a.plan,
        "updated": now.strftime("%Y-%m-%d %H:%M"),
        "note": a.note or None,
    }

    # Bestehenden Plan behalten, falls nicht uebergeben
    if a.plan is None and data_path.exists():
        try:
            old = json.loads(data_path.read_text(encoding="utf-8"))
            payload["plan"] = old.get("plan")
        except Exception:
            pass

    if a.dry_run:
        print("[DRY-RUN] usage.json ->", data_path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if note_path:
            print("[DRY-RUN] Verlaufs-Notiz:", note_path,
                  "(existiert)" if note_path.exists() else "(nicht vorhanden)")
        else:
            print("[DRY-RUN] Verlaufs-Notiz: keine (uebersprungen)")
        return

    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    in_note = False
    if note_path:
        in_note = update_note(note_path, now.strftime("%Y-%m-%d"), used, limit, a.note)

    print(f"OK: {fmt(used)} / {fmt(limit)} = {pct:.1f} %  ->  {data_path}")
    if note_path:
        print("Verlaufstabelle: " + ("ergaenzt" if in_note else "nicht ergaenzt"))
    else:
        print("Verlaufstabelle: keine konfiguriert (uebersprungen)")


if __name__ == "__main__":
    main()
