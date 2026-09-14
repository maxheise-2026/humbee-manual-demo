---
id: upload-fehler
title: Fehlermeldungen beim Dokumenten-Upload
summary: Bedeutung und Behebung der häufigsten Fehlermeldungen beim Hochladen von Dokumenten in humbee.
version: "2026.9"
updated: 2026-09-14
status: freigegeben
tags: [dokument, upload, fehler, fehlermeldung, support]
audience: [anwender, support]
wiki: true
print: false          # Troubleshooting-Katalog – im Druck nur Ballast
---

# Fehlermeldungen beim Dokumenten-Upload

## „Die Datei überschreitet die maximale Größe von 100 MB"

Die hochgeladene Datei ist zu groß. Verkleinern Sie PDF-Dateien über die
Funktion *Dateigröße reduzieren* Ihres PDF-Programms oder teilen Sie das
Dokument auf. Videodateien gehören nicht in humbee, sondern in die Mediathek.

## „Dieser Dateityp ist nicht zugelassen"

Ausführbare Dateien (`.exe`, `.bat`, `.msi`) und Archive mit Passwortschutz
werden aus Sicherheitsgründen abgewiesen. Packen Sie den Inhalt in ein
unverschlüsseltes ZIP-Archiv oder laden Sie die Einzeldateien hoch.

## „Das Dokument konnte nicht indexiert werden"

Der Upload war erfolgreich, aber die Texterkennung ist fehlgeschlagen. Das
Dokument ist vorhanden und lesbar, taucht jedoch nicht in der Volltextsuche auf.
Ursache sind meist sehr schlechte Scans. Scannen Sie mit mindestens 300 dpi neu
oder ergänzen Sie einen aussagekräftigen Betreff, damit das Dokument über die
Metadaten auffindbar bleibt.

## „Sie haben keine Berechtigung, Dokumente in diesem Vorgang abzulegen"

Ihr Benutzerkonto darf den Vorgang lesen, aber nicht verändern. Das ist bei
abgeschlossenen Vorgängen und bei Vorgängen fremder Abteilungen normal. Wenden
Sie sich an die zuständige Sachbearbeitung oder an Ihre Administration.
