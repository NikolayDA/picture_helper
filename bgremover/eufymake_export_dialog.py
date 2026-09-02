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
from bgremover.eufymake_profile import (
    DEFAULT_PROFILE_REGISTRY,
    DEFAULT_TARGET_PROFILE,
    EufyMakeTargetProfile,
    ProfileStatus,
)
from bgremover.eufymake_validate import (
    ExportFinding,
    format_finding,
    split_findings,
    validate_export,
)
from bgremover.i18n import tr
from bgremover.project_model import LayerRole, Project


class EufyMakeExportDialog(QDialog):
    """Optionen + Live-Prüfung für den EufyMake-Studio-Import-Export."""

    def __init__(
        self,
        project: Project,
        *,
        include_height: bool = True,
        include_gloss: bool = True,
        bit_depth: int = DEFAULT_TARGET_PROFILE.default_height_bit_depth,
        dest_dir: str = "",
        profile: EufyMakeTargetProfile = DEFAULT_TARGET_PROFILE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project = project
        self._initial_profile = profile
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

        lay.addWidget(self._build_profile_group())
        lay.addWidget(self._build_assets_group(include_height, include_gloss))
        lay.addWidget(self._build_target_group(bit_depth))
        self._profile_combo.currentIndexChanged.connect(self._profile_changed)
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

    def _build_profile_group(self) -> QGroupBox:
        grp = QGroupBox(tr("eufymake.dialog.section.profile"))
        box = QVBoxLayout(grp)
        self._profile_combo = QComboBox()
        profiles = list(DEFAULT_PROFILE_REGISTRY.profiles())
        if self._initial_profile not in profiles:
            profiles.append(self._initial_profile)
        selected_index = 0
        for index, profile in enumerate(profiles):
            self._profile_combo.addItem(
                tr(
                    "eufymake.dialog.profile.option",
                    name=profile.display_name,
                    version=profile.profile_version,
                ),
                profile,
            )
            if profile == self._initial_profile:
                selected_index = index
        self._profile_combo.setCurrentIndex(selected_index)
        box.addWidget(self._profile_combo)
        self._environment_label = _hint("")
        box.addWidget(self._environment_label)
        self._update_environment_text()
        return grp

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
        self._populate_bit_depths(bit_depth)
        index = self._bit_combo.findData(bit_depth)
        self._bit_combo.setCurrentIndex(index if index >= 0 else 0)
        self._bit_combo.currentIndexChanged.connect(self._recompute)
        depth_row.addWidget(self._bit_combo, 1)
        box.addLayout(depth_row)

        w, h = self._project.size
        box.addWidget(_hint(tr("eufymake.dialog.size", w=w, h=h)))
        self._physical_label = _hint(self._physical_text())
        box.addWidget(self._physical_label)
        return grp

    def _populate_bit_depths(self, preferred: int) -> None:
        """Füllt die HEIGHT-Tiefen ausschließlich aus dem gewählten Profil."""
        previous_block = self._bit_combo.blockSignals(True)
        self._bit_combo.clear()
        for depth in self.selected_profile().height_bit_depths:
            if depth == 8:
                label = tr("eufymake.dialog.bit_depth.8")
            elif depth == 16:
                label = tr("eufymake.dialog.bit_depth.16")
            else:
                label = f"{depth} Bit"
            self._bit_combo.addItem(label, depth)
        index = self._bit_combo.findData(preferred)
        if index < 0:
            index = self._bit_combo.findData(self.selected_profile().default_height_bit_depth)
        self._bit_combo.setCurrentIndex(max(index, 0))
        self._bit_combo.blockSignals(previous_block)

    def _profile_changed(self, _index: int = -1) -> None:
        previous = self.selected_bit_depth()
        self._populate_bit_depths(previous)
        self._update_environment_text()
        self._recompute()

    def _update_environment_text(self) -> None:
        profile = self.selected_profile()
        status = (
            tr("eufymake.dialog.profile.status.provisional")
            if profile.status is ProfileStatus.PROVISIONAL
            else profile.status.value
        )
        environment = profile.target_environment
        self._environment_label.setText(
            tr(
                "eufymake.dialog.profile.environment",
                device=environment.device,
                studio=environment.studio_version,
                status=status,
            )
        )

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
            target = derive_export_target(
                self._project,
                bit_depth=self.selected_bit_depth(),
                profile=self.selected_profile(),
            )
        except EufyMakeExportError:
            # Ungültige physische Metadaten o. Ä. zeigt die Befundliste; hier nur
            # neutral „nicht gesetzt", statt den Dialogaufbau abzubrechen.
            return tr("eufymake.dialog.physical.unset")
        if target.physical_size_mm is None or target.dpi is None:
            return tr("eufymake.dialog.physical.unset")
        mw, mh = target.physical_size_mm
        x_dpi, y_dpi = target.dpi
        return tr(
            "eufymake.dialog.physical",
            w=f"{mw:g}",
            h=f"{mh:g}",
            x_dpi=f"{x_dpi:.1f}",
            y_dpi=f"{y_dpi:.1f}",
        )

    def _recompute(self) -> None:
        """Berechnet die Befunde neu und aktualisiert Anzeige + Buttons."""
        findings = validate_export(
            self._project,
            requested_optional_roles=self.selected_optional_roles(),
            bit_depth=self.selected_bit_depth(),
            profile=self.selected_profile(),
        )
        self._physical_label.setText(self._physical_text())
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

    def selected_profile(self) -> EufyMakeTargetProfile:
        """Das Profilobjekt, das Prüfung und Writer unverändert weiterreichen."""
        profile = self._profile_combo.currentData()
        if not isinstance(profile, EufyMakeTargetProfile):  # pragma: no cover - UI-Invariante
            raise RuntimeError("EufyMake-Dialog ohne gültiges Zielprofil")
        return profile

    def selected_destination(self) -> str:
        return self._dest_edit.text().strip()

    def warnings_confirmed(self) -> bool:
        return bool(self._warnings) and self._confirm.isChecked()

    def current_findings(self) -> tuple[ExportFinding, ...]:
        """Die zuletzt berechneten Befunde – Fehler zuerst, dann Warnungen.

        Öffentliche Abfrage desselben Bestands, den die Befundanzeige
        formatiert (#869). Aufrufer prüfen damit den stabilen
        ``ExportCheckCode`` statt den übersetzten Labeltext.
        """
        return (*self._errors, *self._warnings)


def _hint(text: str) -> QLabel:
    """Kleines, gedämpftes Hinweis-Label."""
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color: #888; font-size: 11px;")
    return label
