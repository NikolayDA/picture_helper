"""Zentrale Sammlung aller Status-Meldungsstrings.

Die Attribute bleiben für bestehende Aufrufer bewusst gleich, werden aber
über ``bgremover.i18n.tr`` aufgelöst. Damit kann ein späterer Sprach-Rollout
die Statusleiste umstellen, ohne jeden Aufruf im Canvas/MainWindow erneut
anzufassen.
"""
from __future__ import annotations

from bgremover.i18n import tr


class _StatusMessages:
    # ── Laden & Speichern ────────────────────────────────────
    @property
    def KEIN_BILD_GELADEN(self) -> str:
        return tr("status.no_image_loaded")

    @property
    def KEIN_BILD_ZUM_SPEICHERN(self) -> str:
        return tr("status.no_image_to_save")

    @property
    def LAEDT_BEREITS(self) -> str:
        return tr("status.already_loading")

    @property
    def LADEERGEBNIS_VERWORFEN(self) -> str:
        return tr("status.load_result_discarded")

    # ── KI ───────────────────────────────────────────────────
    @property
    def KI_LAEUFT_BEREITS(self) -> str:
        return tr("status.ai_already_running")

    @property
    def KI_VERARBEITET(self) -> str:
        return tr("status.ai_processing")

    @property
    def KI_BEREIT(self) -> str:
        return tr("status.ai_ready")

    @property
    def KI_MODELL_LADEN(self) -> str:
        return tr("status.ai_model_loading")

    @property
    def KI_FEHLER_WARMUP(self) -> str:
        return tr("status.ai_warmup_failed")

    @property
    def KI_ABBRUCH_WARTET(self) -> str:
        return tr("status.ai_cancelling")

    @property
    def KI_ABGEBROCHEN(self) -> str:
        return tr("status.ai_cancelled")

    @property
    def KI_ERGEBNIS_VERWORFEN(self) -> str:
        return tr("status.ai_result_discarded")

    # ── Zauberstab ───────────────────────────────────────────
    @property
    def ZAUBERSTAB_ARBEITET(self) -> str:
        return tr("status.wand_busy")

    @property
    def AUSWAHL_BERECHNUNG(self) -> str:
        return tr("status.selection_calculating")

    @property
    def WAND_VERWORFEN(self) -> str:
        return tr("status.wand_discarded")

    # ── Auswahl ──────────────────────────────────────────────
    @property
    def KEINE_AUSWAHL(self) -> str:
        return tr("status.no_selection")

    # ── Start-Hinweis ────────────────────────────────────────
    @property
    def START_HINWEIS(self) -> str:
        return tr("status.start_hint")

    # ── Beenden ──────────────────────────────────────────────
    @property
    def BEENDE(self) -> str:
        return tr("status.quitting")

    @property
    def BEENDEN_FEHLGESCHLAGEN(self) -> str:
        return tr("status.shutdown_failed")

    # ── Dynamisch (mit eingesetzten Werten) ──────────────────
    def LAEDT(self, name: str) -> str:
        return tr("status.loading", name=name)

    def LADEFEHLER(self, msg: str) -> str:
        return tr("status.load_error", msg=msg)

    def DATEI_NICHT_VORHANDEN(self, name: str) -> str:
        return tr("status.file_missing", name=name)

    def KI_FEHLER(self, msg: str) -> str:
        return tr("status.ai_error", msg=msg)


StatusMessages = _StatusMessages()
