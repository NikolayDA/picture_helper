"""Dialog „Assets für EufyMake Studio exportieren…" (#355).

Bedient den konservativen Import-Workflow aus #352–#354: BgRemover schreibt
**Import-Assets** (Farbmotiv-PNG, optionale Höhenkarte, optionale Gloss-Maske),
**kein** natives ``.empf``. Der Dialog sammelt die Optionen (welche optionalen
Assets, Bittiefe), zeigt die abgeleiteten Zielparameter, blendet **live** die
Konsistenzbefunde aus #354 ein (Fehler blockieren, Warnungen erfordern bewusste
Bestätigung) und lässt den Zielordner wählen. Geschrieben wird erst danach im
Hauptfenster über ``eufymake_writer.write_export``.

Alle nutzersichtbaren Strings laufen über ``i18n.py`` und sprechen konsequent von
**Import-Assets / Studio-Import**, nie von einem fertigen EufyMake-Projekt.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from bgremover.eufymake_export import EufyMakeExportError, derive_export_target
from bgremover.eufymake_validate import format_finding, split_findings, validate_export
from bgremover.i18n import tr
from bgremover.project_model import LayerRole, Project

# Auswählbare Bittiefen: (Wert, i18n-Key des Labels). 8 Bit ist Standard, 16 Bit
# ist ausdrücklich experimentell/unbestätigt (löst eine #354-Warnung aus).
_BIT_DEPTHS: tuple[tuple[int, str], ...] = (
    (8, "eufymake.dialog.bit_depth.8"),
    (16, "eufymake.dialog.bit_depth.16"),
)


class EufyMakeExportDialog(QDialog):
    """Optionen + Live-Prüfung für den EufyMake-Studio-Import-Export."""

    def __init__(
        self,
        project: Project,
        *,
        include_height: bool = True,
        include_gloss: bool = True,
        bit_depth: int = 8,
        dest_dir: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project = project
        self._has_height = project.layer_by_role(LayerRole.HEIGHT_MAP) is not None
        self._has_gloss = project.layer_by_role(LayerRole.GLOSS_MASK) is not None
        self.setWindowTitle(tr("eufymake.dialog.title"))
        self.setMinimumWidth(460)
        self._build_ui(include_height, include_gloss, bit_depth, dest_dir)
        self._recompute()

    # ── Aufbau ──────────────────────────────────────────────────────────
    def _build_ui(
        self, include_height: bool, include_gloss: bool, bit_depth: int, dest_dir: str
    ) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        intro = QLabel(tr("eufymake.dialog.intro"))
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #bbb;")
        lay.addWidget(intro)

        lay.addWidget(self._build_assets_group(include_height, include_gloss))
        lay.addWidget(self._build_target_group(bit_depth))
        lay.addWidget(self._build_dest_group(dest_dir))

        findings_grp = QGroupBox(tr("eufymake.dialog.section.findings"))
        findings_lay = QVBoxLayout(findings_grp)
        self._findings_label = QLabel()
        self._findings_label.setWordWrap(True)
        self._findings_label.setTextFormat(Qt.TextFormat.PlainText)
        findings_lay.addWidget(self._findings_label)
        lay.addWidget(findings_grp)

        self._confirm = QCheckBox(tr("eufymake.dialog.confirm_warnings"))
        self._confirm.toggled.connect(self._update_buttons)
        lay.addWidget(self._confirm)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton(tr("eufymake.dialog.cancel"))
        cancel.clicked.connect(self.reject)
        self._export_btn = QPushButton(tr("eufymake.dialog.export"))
        self._export_btn.setDefault(True)
        self._export_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel)
        btn_row.addWidget(self._export_btn)
        lay.addLayout(btn_row)

    def _build_assets_group(self, include_height: bool, include_gloss: bool) -> QGroupBox:
        grp = QGroupBox(tr("eufymake.dialog.section.assets"))
        box = QVBoxLayout(grp)

        motif = QLabel(tr("eufymake.dialog.color_motif"))
        motif.setStyleSheet("font-weight: bold;")
        box.addWidget(motif)
        box.addWidget(_hint(tr("eufymake.dialog.color_motif.hint")))

        self._height_cb = QCheckBox(tr("eufymake.dialog.height"))
        self._height_cb.setEnabled(self._has_height)
        self._height_cb.setChecked(self._has_height and include_height)
        self._height_cb.toggled.connect(self._recompute)
        box.addWidget(self._height_cb)
        height_hint = (
            tr("eufymake.dialog.height.hint")
            if self._has_height
            else tr("eufymake.dialog.height.unavailable")
        )
        box.addWidget(_hint(height_hint))

        self._gloss_cb = QCheckBox(tr("eufymake.dialog.gloss"))
        self._gloss_cb.setEnabled(self._has_gloss)
        self._gloss_cb.setChecked(self._has_gloss and include_gloss)
        self._gloss_cb.toggled.connect(self._recompute)
        box.addWidget(self._gloss_cb)
        gloss_hint = (
            tr("eufymake.dialog.gloss.hint")
            if self._has_gloss
            else tr("eufymake.dialog.gloss.unavailable")
        )
        box.addWidget(_hint(gloss_hint))
        return grp

    def _build_target_group(self, bit_depth: int) -> QGroupBox:
        grp = QGroupBox(tr("eufymake.dialog.section.target"))
        box = QVBoxLayout(grp)

        depth_row = QHBoxLayout()
        depth_row.addWidget(QLabel(tr("eufymake.dialog.bit_depth")))
        self._bit_combo = QComboBox()
        # Literale tr(...) je Eintrag, damit die i18n-Key-Hygiene die Nutzung sieht.
        self._bit_combo.addItem(tr("eufymake.dialog.bit_depth.8"), 8)
        self._bit_combo.addItem(tr("eufymake.dialog.bit_depth.16"), 16)
        index = self._bit_combo.findData(bit_depth)
        self._bit_combo.setCurrentIndex(index if index >= 0 else 0)
        self._bit_combo.currentIndexChanged.connect(self._recompute)
        depth_row.addWidget(self._bit_combo, 1)
        box.addLayout(depth_row)

        w, h = self._project.size
        box.addWidget(_hint(tr("eufymake.dialog.size", w=w, h=h)))
        box.addWidget(_hint(self._physical_text()))
        return grp

    def _build_dest_group(self, dest_dir: str) -> QGroupBox:
        grp = QGroupBox(tr("eufymake.dialog.section.dest"))
        box = QVBoxLayout(grp)
        box.addWidget(QLabel(tr("eufymake.dialog.dest.label")))
        row = QHBoxLayout()
        self._dest_edit = QLineEdit(dest_dir)
        self._dest_edit.setPlaceholderText(tr("eufymake.dialog.dest.placeholder"))
        self._dest_edit.textChanged.connect(self._update_buttons)
        row.addWidget(self._dest_edit, 1)
        browse = QPushButton(tr("eufymake.dialog.dest.browse"))
        browse.clicked.connect(self._pick_dest)
        row.addWidget(browse)
        box.addLayout(row)
        self._dest_hint = _hint(tr("eufymake.dialog.dest.is_file"))
        self._dest_hint.setStyleSheet("color: #d66; font-size: 11px;")
        self._dest_hint.setVisible(False)
        box.addWidget(self._dest_hint)
        return grp

    # ── Live-Prüfung ────────────────────────────────────────────────────
    def _physical_text(self) -> str:
        try:
            target = derive_export_target(self._project, bit_depth=self.selected_bit_depth())
        except EufyMakeExportError:
            # Ungültige physische Metadaten o. Ä. zeigt die Befundliste; hier nur
            # neutral „nicht gesetzt", statt den Dialogaufbau abzubrechen.
            return tr("eufymake.dialog.physical.unset")
        if target.physical_size_mm is None or target.dpi is None:
            return tr("eufymake.dialog.physical.unset")
        mw, mh = target.physical_size_mm
        dpi = (target.dpi[0] + target.dpi[1]) / 2
        return tr("eufymake.dialog.physical", w=f"{mw:g}", h=f"{mh:g}", dpi=f"{dpi:.0f}")

    def _recompute(self) -> None:
        """Berechnet die Befunde neu und aktualisiert Anzeige + Buttons."""
        findings = validate_export(
            self._project,
            requested_optional_roles=self.selected_optional_roles(),
            bit_depth=self.selected_bit_depth(),
        )
        self._errors, self._warnings = split_findings(findings)
        if not findings:
            self._findings_label.setText(tr("eufymake.dialog.findings.ok"))
        else:
            lines = [
                tr("eufymake.dialog.finding.error", msg=format_finding(f))
                for f in self._errors
            ] + [
                tr("eufymake.dialog.finding.warning", msg=format_finding(f))
                for f in self._warnings
            ]
            self._findings_label.setText("\n".join(lines))
        has_warn = bool(self._warnings)
        self._confirm.setVisible(has_warn)
        if not has_warn:
            self._confirm.setChecked(False)
        self._update_buttons()

    def _update_buttons(self) -> None:
        dest = self._dest_edit.text().strip()
        dest_is_file = bool(dest) and Path(dest).exists() and not Path(dest).is_dir()
        self._dest_hint.setVisible(dest_is_file)
        ready = (
            not self._errors
            and bool(dest)
            and not dest_is_file
            and (not self._warnings or self._confirm.isChecked())
        )
        self._export_btn.setEnabled(ready)

    def _pick_dest(self) -> None:
        start = self._dest_edit.text().strip() or str(Path.home())
        path, _ = QFileDialog.getSaveFileName(
            self, tr("eufymake.dialog.dest.dialog_title"), start)
        if path:
            self._dest_edit.setText(path)

    # ── Ergebnis ────────────────────────────────────────────────────────
    def selected_optional_roles(self) -> list[LayerRole]:
        """Die vom Nutzer einbezogenen optionalen Rollen (nur aktivierte)."""
        roles: list[LayerRole] = []
        if self._height_cb.isChecked():
            roles.append(LayerRole.HEIGHT_MAP)
        if self._gloss_cb.isChecked():
            roles.append(LayerRole.GLOSS_MASK)
        return roles

    def selected_bit_depth(self) -> int:
        return int(self._bit_combo.currentData())

    def selected_destination(self) -> str:
        return self._dest_edit.text().strip()

    def warnings_confirmed(self) -> bool:
        return bool(self._warnings) and self._confirm.isChecked()


def _hint(text: str) -> QLabel:
    """Kleines, gedämpftes Hinweis-Label."""
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color: #888; font-size: 11px;")
    return label
