"""Zentrale Sammlung aller Status-Meldungsstrings.

Keine i18n-Bibliothek – nur ein Ort für alle sichtbaren Status-Texte,
damit eine spätere Lokalisierung die Strings ohne Streusuche findet.
"""


class StatusMessages:
    # ── Laden & Speichern ────────────────────────────────────
    KEIN_BILD_GELADEN       = "Kein Bild geladen"
    KEIN_BILD_ZUM_SPEICHERN = "Kein Bild zum Speichern"
    LAEDT_BEREITS           = "Lädt bereits ein Bild…"

    # ── KI ───────────────────────────────────────────────────
    KI_LAEUFT_BEREITS = "KI läuft bereits…"
    KI_VERARBEITET    = "🤖 KI verarbeitet Bild… (kann einige Sekunden dauern)"
    KI_BEREIT         = "🤖 KI bereit"
    KI_MODELL_LADEN   = "🤖 KI-Modell wird geladen…"
    KI_FEHLER_WARMUP  = "⚠️ KI-Modell konnte nicht geladen werden"
    KI_ERGEBNIS_VERWORFEN = "KI-Ergebnis verworfen – Bild wurde inzwischen geändert"

    # ── Zauberstab ───────────────────────────────────────────
    ZAUBERSTAB_ARBEITET = "Zauberstab arbeitet noch…"
    AUSWAHL_BERECHNUNG  = "⏳ Auswahl wird berechnet…"
    WAND_VERWORFEN      = "Wand-Auswahl verworfen – Bild wurde inzwischen geändert"

    # ── Auswahl ──────────────────────────────────────────────
    KEINE_AUSWAHL = (
        "Keine Auswahl – erst Bereich mit Zauberstab oder Pinsel auswählen"
    )

    # ── Start-Hinweis ────────────────────────────────────────
    START_HINWEIS = (
        "Bild öffnen: Datei → Öffnen  oder  per Drag & Drop auf die Arbeitsfläche"
    )

    # ── Beenden ──────────────────────────────────────────────
    BEENDE = "Beende…"
