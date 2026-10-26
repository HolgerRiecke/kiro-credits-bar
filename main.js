/* Kiro Credits Bar – zeigt den Credit-Verbrauch in der Obsidian-Statusleiste.
 * Datenquelle: usage.json im Plugin-Ordner (wird vom Skill "kiro-credits-update" geschrieben).
 * Die Datei wird alle paar Sekunden auf Änderungen geprüft – kein Neustart nötig.
 */
const { Plugin } = require('obsidian');

const DATA_FILE = 'usage.json';
const POLL_MS = 5000;
const DEFAULT_LIMIT = 1000;
const WARN_AT = 70;  // Prozent
const CRIT_AT = 90;  // Prozent

module.exports = class KiroCreditsBar extends Plugin {
  async onload() {
    this.statusEl = this.addStatusBarItem();
    this.statusEl.addClass('kiro-credits-bar');
    this.dataPath = `${this.manifest.dir}/${DATA_FILE}`;
    this.lastRaw = undefined;

    this.addCommand({
      id: 'refresh',
      name: 'Anzeige aktualisieren',
      callback: () => this.refresh(true),
    });
    this.statusEl.addEventListener('click', () => this.refresh(true));

    await this.refresh(true);
    this.registerInterval(window.setInterval(() => this.refresh(false), POLL_MS));
  }

  async refresh(force) {
    let raw = null;
    try {
      raw = await this.app.vault.adapter.read(this.dataPath);
    } catch (e) {
      raw = null; // Datei fehlt noch
    }
    if (!force && raw === this.lastRaw) return;
    this.lastRaw = raw;

    let data = null;
    try {
      data = raw ? JSON.parse(raw) : null;
    } catch (e) {
      data = null;
    }
    this.render(data);
  }

  render(data) {
    const el = this.statusEl;
    el.empty();

    const limit = Number(data && data.limit) > 0 ? Number(data.limit) : DEFAULT_LIMIT;
    const hasValue = data && data.used !== null && data.used !== undefined && !isNaN(Number(data.used));
    const used = hasValue ? Number(data.used) : null;
    const pct = hasValue ? (used / limit) * 100 : null;

    el.createSpan({ cls: 'kcb-label', text: 'Kiro' });
    el.createSpan({ cls: 'kcb-scale kcb-min', text: '0' });

    const track = el.createDiv({ cls: 'kcb-track' });
    const fill = track.createDiv({ cls: 'kcb-fill' });
    fill.style.width = hasValue ? `${Math.max(0, Math.min(100, pct))}%` : '0%';

    el.createSpan({ cls: 'kcb-scale kcb-max', text: String(limit) });

    const pctEl = el.createSpan({
      cls: 'kcb-pct',
      text: hasValue ? `${Math.round(pct)} %` : '– %',
    });

    el.removeClass('kcb-ok', 'kcb-warn', 'kcb-crit', 'kcb-empty');
    if (!hasValue) el.addClass('kcb-empty');
    else if (pct >= CRIT_AT) el.addClass('kcb-crit');
    else if (pct >= WARN_AT) el.addClass('kcb-warn');
    else el.addClass('kcb-ok');

    // Tooltip mit Details
    const lines = ['Kiro Credits'];
    if (hasValue) {
      lines.push(`Verbraucht: ${used} von ${limit} (${pct.toFixed(1)} %)`);
    } else {
      lines.push('Noch kein Wert gesetzt – Skill "kiro-credits-update" ausführen.');
    }
    if (data && data.plan) lines.push(`Plan: ${data.plan}`);
    if (data && data.updated) lines.push(`Stand: ${data.updated}`);
    if (data && data.note) lines.push(`Notiz: ${data.note}`);
    lines.push('(Klick = neu einlesen)');
    el.setAttr('aria-label', lines.join('\n'));
    el.setAttr('title', lines.join('\n'));
  }

  onunload() {
    if (this.statusEl) this.statusEl.remove();
  }
};
