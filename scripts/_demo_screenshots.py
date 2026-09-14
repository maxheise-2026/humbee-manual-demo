"""Erzeugt Platzhalter-Screenshots für die Demo. Im echten Repo ersetzt du
content/assets/img/*.png durch echte Aufnahmen - dieses Skript kann dann weg."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "content" / "assets" / "img"
OUT.mkdir(parents=True, exist_ok=True)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG, PANEL, LINE, TEXT, MUTED = "#f1f5f9", "#ffffff", "#d8dee7", "#1e293b", "#7d8ca3"
BRAND, BRAND_D = "#2563eb", "#1d4ed8"

def font(sz, bold=False):
    return ImageFont.truetype(FB if bold else F, sz)

def box(d, xy, fill=PANEL, outline=LINE, r=8, w=1):
    d.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=w)

def btn(d, x, y, w, h, label, primary=True):
    box(d, (x, y, x + w, y + h), fill=BRAND if primary else PANEL,
        outline=BRAND_D if primary else LINE, r=6)
    f = font(15, True)
    tw = d.textlength(label, font=f)
    d.text((x + (w - tw) / 2, y + (h - 19) / 2), label,
           font=f, fill="#ffffff" if primary else TEXT)

def field(d, x, y, w, label, value="", h=40):
    d.text((x, y), label, font=font(13), fill=MUTED)
    box(d, (x, y + 18, x + w, y + 18 + h), r=6)
    d.text((x + 12, y + 18 + (h - 19) / 2), value, font=font(15), fill=TEXT if value else MUTED)
    return y + 18 + h + 18

def chrome(w, h, title):
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 38), fill="#e2e8f0")
    for i, c in enumerate(("#f87171", "#fbbf24", "#4ade80")):
        d.ellipse((16 + i * 20, 14, 26 + i * 20, 24), fill=c)
    box(d, (90, 8, w - 16, 30), fill="#ffffff", r=5)
    d.text((102, 12), title, font=font(13), fill=MUTED)
    return img, d

def sidebar(d, h, active=0):
    d.rectangle((0, 38, 190, h), fill="#0f172a")
    d.text((22, 60), "humbee", font=font(21, True), fill="#ffffff")
    for i, name in enumerate(("Start", "Vorgänge", "Kontakte", "Dokumente", "Auswertungen")):
        y = 116 + i * 46
        if i == active:
            d.rounded_rectangle((12, y - 8, 178, y + 30), radius=6, fill=BRAND)
        d.rounded_rectangle((26, y + 2, 42, y + 18), radius=3,
                            outline="#ffffff" if i == active else "#64748b", width=2)
        d.text((56, y + 1), name, font=font(15, i == active),
               fill="#ffffff" if i == active else "#cbd5e1")

# --- 1: Anmeldemaske -------------------------------------------------------
img, d = chrome(900, 620, "https://ihr-unternehmen.humbee.de/login")
d.rectangle((0, 38, 900, 620), fill="#e8eef7")
box(d, (250, 110, 650, 540), r=14)
d.text((290, 152), "humbee", font=font(30, True), fill=BRAND_D)
d.text((290, 194), "Bitte melden Sie sich an", font=font(15), fill=MUTED)
y = field(d, 290, 246, 320, "Benutzername", "max.mustermann@firma.de")
y = field(d, 290, y, 320, "Passwort", "••••••••••••")
btn(d, 290, y + 8, 320, 46, "Anmelden")
d.text((290, y + 74), "Passwort vergessen?", font=font(14), fill=BRAND)
img.save(OUT / "anmeldung-maske.png")

# --- 2: Oberflächenübersicht ----------------------------------------------
img, d = chrome(1280, 760, "humbee – Vorgänge")
sidebar(d, 760, active=1)
d.rectangle((190, 38, 1280, 760), fill=BG)
box(d, (214, 62, 980, 736))
d.text((238, 86), "Vorgänge", font=font(22, True), fill=TEXT)
btn(d, 238, 128, 90, 36, "Neu")
btn(d, 340, 128, 96, 36, "Filtern", primary=False)
btn(d, 448, 128, 128, 36, "Exportieren", primary=False)
hdr = (("Nummer", 250), ("Betreff", 380), ("Beteiligter", 700), ("Frist", 880))
d.line((238, 190, 956, 190), fill=LINE)
for t, x in hdr:
    d.text((x, 196), t, font=font(13, True), fill=MUTED)
rows = [("V-2026-0418", "Angebot Wartungsvertrag", "Müller GmbH", "18.09.2026"),
        ("V-2026-0417", "Reklamation Lieferung 8841", "Schneider AG", "15.09.2026"),
        ("V-2026-0416", "Onboarding neuer Mitarbeiter", "Interne Abteilung", "30.09.2026"),
        ("V-2026-0415", "Rechnungsprüfung Q3", "Bauer & Co. KG", "22.09.2026"),
        ("V-2026-0414", "Vertragsverlängerung 2027", "Hoffmann Logistik", "05.10.2026")]
for i, r in enumerate(rows):
    y = 228 + i * 46
    if i % 2 == 0:
        d.rectangle((238, y - 8, 956, y + 30), fill="#f8fafc")
    for (t, x), v in zip(hdr, r):
        d.text((x, y), v, font=font(14), fill=TEXT)
    d.line((238, y + 30, 956, y + 30), fill="#eef2f7")
box(d, (1000, 62, 1256, 736))
d.text((1022, 86), "Infobereich", font=font(16, True), fill=TEXT)
for i, (t, n) in enumerate((("Dokumente", "4"), ("Offene Aufgaben", "2"), ("Verlauf", "17"))):
    y = 132 + i * 74
    box(d, (1022, y, 1234, y + 56), fill="#f8fafc", r=6)
    d.text((1038, y + 10), t, font=font(14, True), fill=TEXT)
    d.text((1038, y + 30), f"{n} Einträge", font=font(13), fill=MUTED)
# Bereichsmarkierungen
for x0, x1, label in ((0, 190, "Navigationsleiste"), (214, 980, "Arbeitsbereich"), (1000, 1256, "Infobereich")):
    d.text(((x0 + x1) / 2 - d.textlength(label, font=font(13, True)) / 2, 744),
           label, font=font(13, True), fill=BRAND_D)
img.save(OUT / "oberflaeche-uebersicht.png")

# --- 3: Dialog Neuer Vorgang ----------------------------------------------
img, d = chrome(940, 640, "humbee – Vorgänge")
d.rectangle((0, 38, 940, 640), fill="#8595ab")
box(d, (170, 108, 770, 566), r=12)
d.text((206, 142), "Neuer Vorgang", font=font(22, True), fill=TEXT)
d.line((206, 186, 734, 186), fill=LINE)
y = field(d, 206, 212, 528, "Vorgangstyp *", "Angebot  ▾")
y = field(d, 206, y, 528, "Betreff *", "Angebot Wartungsvertrag 2027")
y = field(d, 206, y, 528, "Zuständig", "Max Mustermann  ▾")
btn(d, 206, 478, 120, 44, "Anlegen")
btn(d, 340, 478, 120, 44, "Abbrechen", primary=False)
img.save(OUT / "vorgang-neu-dialog.png")

# --- 4: Vorgang mit Verlauf -----------------------------------------------
img, d = chrome(1280, 800, "humbee – V-2026-0418")
sidebar(d, 800, active=1)
d.rectangle((190, 38, 1280, 800), fill=BG)
box(d, (214, 62, 1256, 250))
d.text((238, 86), "V-2026-0418 · Angebot Wartungsvertrag", font=font(21, True), fill=TEXT)
box(d, (238, 124, 330, 152), fill="#dcfce7", outline="#86efac", r=14)
d.text((252, 129), "In Arbeit", font=font(13, True), fill="#15803d")
for i, (k, v) in enumerate((("Vorgangstyp", "Angebot"), ("Beteiligter", "Müller GmbH"),
                            ("Zuständig", "Max Mustermann"), ("Frist", "18.09.2026"))):
    x = 238 + (i % 4) * 250
    d.text((x, 178), k, font=font(12), fill=MUTED)
    d.text((x, 198), v, font=font(15, True), fill=TEXT)
box(d, (214, 274, 1256, 776))
d.text((238, 298), "Verlauf", font=font(18, True), fill=TEXT)
btn(d, 940, 292, 150, 34, "Buchung erfassen")
btn(d, 1102, 292, 132, 34, "Aufgabe", primary=False)
entries = [("14.09.2026 10:24", "Telefonat", "M. Mustermann",
            "Kunde bittet um Aufschlüsselung der Wartungspauschale."),
           ("13.09.2026 16:02", "Dokument", "M. Mustermann",
            "Angebot_Wartung_2027.pdf hinzugefügt (Version 2)."),
           ("12.09.2026 09:15", "Aufgabe", "System",
            "Aufgabe „Angebot kalkulieren\" an Vertrieb zugewiesen."),
           ("11.09.2026 08:40", "Notiz", "A. Schulz",
            "Rahmenvertrag aus 2023 als Grundlage verwenden.")]
for i, (ts, art, who, txt) in enumerate(entries):
    y = 348 + i * 102
    d.line((252, y, 252, y + 84), fill=LINE, width=2)
    d.ellipse((245, y + 8, 259, y + 22), fill=BRAND, outline="#ffffff", width=2)
    box(d, (282, y - 4, 1232, y + 84), fill="#f8fafc", r=8)
    d.text((300, y + 8), art, font=font(14, True), fill=BRAND_D)
    d.text((300 + d.textlength(art, font=font(14, True)) + 14, y + 9),
           f"· {ts} · {who}", font=font(13), fill=MUTED)
    d.text((300, y + 38), txt, font=font(14), fill=TEXT)
img.save(OUT / "vorgang-verlauf.png")

# --- 5: Dokumenten-Upload --------------------------------------------------
img, d = chrome(1100, 640, "humbee – V-2026-0418 · Dokumente")
d.rectangle((0, 38, 1100, 640), fill=BG)
box(d, (40, 66, 1060, 600))
d.text((66, 92), "Dokumente", font=font(20, True), fill=TEXT)
btn(d, 826, 86, 208, 36, "Dokument hinzufügen")
for i, (n, t, s) in enumerate((("Angebot_Wartung_2027.pdf", "Angebot", "1,2 MB"),
                               ("Rahmenvertrag_2023.pdf", "Vertrag", "840 KB"))):
    y = 148 + i * 62
    box(d, (66, y, 1034, y + 50), fill="#f8fafc", r=6)
    d.rounded_rectangle((82, y + 11, 104, y + 39), radius=3, outline="#ef4444", width=2)
    d.text((118, y + 8), n, font=font(14, True), fill=TEXT)
    d.text((118, y + 28), f"{t} · {s}", font=font(12), fill=MUTED)
d.rounded_rectangle((66, 292, 1034, 486), radius=10, outline=BRAND, width=3)
d.rounded_rectangle((66, 292, 1034, 486), radius=10, fill="#eff6ff", outline=BRAND, width=3)
d.text((550 - d.textlength("Dateien hier ablegen", font=font(20, True)) / 2, 352),
       "Dateien hier ablegen", font=font(20, True), fill=BRAND_D)
d.text((550 - d.textlength("oder klicken, um Dateien auszuwählen · max. 20 Dateien, je 100 MB", font=font(14)) / 2, 390),
       "oder klicken, um Dateien auszuwählen · max. 20 Dateien, je 100 MB", font=font(14), fill=MUTED)
box(d, (470, 424, 690, 462), fill="#ffffff", outline=BRAND, r=6)
d.rounded_rectangle((484, 432, 502, 454), radius=3, outline="#ef4444", width=2)
d.text((514, 434), "Rechnung_8841.pdf", font=font(14), fill=TEXT)
img.save(OUT / "dokument-upload.png")

print("erzeugt:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))
