"""Height-Map-Tab (#349): Beschaffen, Bearbeiten und Optimieren von Höhenkarten.

Schließt das Height-Map-Epic (#344) ab: macht die Bausteine aus #346–#348 über
das rechte Panel bedienbar. Aufbau analog zu :mod:`bgremover.layer_panel` – eine
zustandsbehaftete Klasse mit ``build()`` (Tab-Aufbau) und ``refresh(layers)``
(moduskontextuelle Anzeige). Alle Interaktionen laufen über die Callbacks in
:class:`HeightMapActions`; das Panel kennt weder Canvas noch MainWindow.

Moduskontext: Die **Bearbeiten**- und **Optimieren**-Steuerungen sind genau dann
aktiv, wenn die aktive Ebene ``LayerKind.HEIGHT`` besitzt – unabhängig davon, ob
sie bereits die Rolle ``HEIGHT_MAP`` trägt. Damit folgt der Tab demselben
Kind-Vertrag wie der Canvas (#364), sodass die UI keine Operation anbietet, die
der Canvas anschließend ablehnt. Die **Beschaffen**-Aktionen (erzeugen/
importieren) sind aktiv, sobald ein Projekt geladen ist.

Optimierungs-Operationen werden als reine ``HeightField → HeightField``-Closures
(``height_ops``, die ihre Reglerwerte beim Aufruf lesen) an ``preview_op``/
``apply_op`` übergeben; die Live-Vorschau läuft transient im Canvas (#348).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bgremover import height_ops
from bgremover.canvas import LayerInfo
from bgremover.height_map import HeightField, scale_8bit_height_value
from bgremover.i18n import tr
from bgremover.project_model import LayerKind
from bgremover.relief_mesh import MeshQuality
from bgremover.right_panel_tabs import (
    _make_hdivider,
    _make_label,
    _make_neutral_btn,
    _make_primary_btn,
    _make_scroll_tab,
    _make_section,
    _make_slider,
    _PanelSpinBox,
    _set_button_selected,
    _style_spin_box,
)

# Reine Höhen-Operation; die Closures lesen ihre Reglerwerte beim Aufruf.
HeightOp = Callable[[HeightField], HeightField]

# Logarithmische Überhöhungs-Slider-Abbildung (UX §4: 0,1×–10×, Default 1,0×):
# Slider 0..100 → 0,1 · 10^(pos/50); 0→0,1×, 50→1,0×, 100→10×.
_EXAGG_SLIDER_MAX = 100


def exaggeration_from_slider(pos: int) -> float:
    """Bildet die Slider-Position logarithmisch auf den Überhöhungsfaktor ab."""
    return 0.1 * (10.0 ** (pos / 50.0))


def slider_from_exaggeration(value: float) -> int:
    """Inverse Abbildung (für die Reset-Synchronisierung)."""
    import math

    if value <= 0.0:
        return 0
    pos = 50.0 * math.log10(value / 0.1)
    return max(0, min(_EXAGG_SLIDER_MAX, int(round(pos))))


@dataclass(frozen=True)
class HeightMapActions:
    """Callbacks des Height-Map-Tabs – ohne Abhängigkeit vom MainWindow."""

    generate: Callable[[], None]
    import_file: Callable[[], None]
    lighten: Callable[[int], None]
    darken: Callable[[int], None]
    set_height: Callable[[int], None]
    invert: Callable[[], None]
    preview_op: Callable[[HeightOp], None]
    apply_op: Callable[[HeightOp], None]
    cancel_preview: Callable[[], None]


@dataclass(frozen=True)
class Preview3DActions:
    """Callbacks des 3D-Abschnitts im Höhen-Tab (UX-Vertrag §1, #594).

    Rein visuelle Steuerung: ``set_mode_3d`` schaltet 2D↔3D, die übrigen Regler
    sind Anzeige-Uniforms bzw. Qualität. Der Höhen-/Bild-/Exportzustand bleibt
    unberührt.
    """

    set_mode_3d: Callable[[bool], None]
    set_exaggeration: Callable[[float], None]
    set_light: Callable[[float, float], None]
    set_quality: Callable[[MeshQuality], None]
    fit_view: Callable[[], None]
    reset_view: Callable[[], None]


def _spin(lo: int, hi: int, value: int, *, suffix: str = "", width: int = 72) -> QSpinBox:
    """Einheitlich gestylte Ganzzahl-Eingabe für das Höhen-Panel.

    Höhenwert-Eingaben behalten die vertraute ``0..255``-Skala als
    Bedienoberfläche; der Tooltip macht die proportionale Abbildung auf den
    kanonischen 16-Bit-Wertebereich sichtbar (#589) – so bleibt die
    Feinsteuerung handhabbar, ohne 65536 Einzelschritte zu verlangen.
    """
    box = _PanelSpinBox()
    box.setRange(lo, hi)
    box.setValue(value)
    if suffix:
        box.setSuffix(suffix)
    box.setFixedWidth(width)
    if hi == 255:
        box.setToolTip(tr("right_panel.height.scale_hint"))
    _style_spin_box(box)
    return box


class HeightMapPanel:
    """Baut und pflegt den Höhen-Tab; ``refresh`` schaltet den Moduskontext."""

    def __init__(
        self, actions: HeightMapActions, preview3d: Preview3DActions | None = None,
    ) -> None:
        self._actions = actions
        self._preview3d = preview3d
        # Aktiv nur mit geladenem Projekt (Beschaffen) bzw. aktiver HEIGHT-Ebene.
        self._acquire_widgets: list[QWidget] = []
        self._height_widgets: list[QWidget] = []
        # 3D-Regler (Überhöhung/Licht/Qualität/Buttons) – nur im 3D-Modus aktiv.
        self._preview3d_param_widgets: list[QWidget] = []
        self._quality_buttons: dict[MeshQuality, QPushButton] = {}
        self._selected_quality = MeshQuality.STANDARD
        self._btn_2d: QPushButton | None = None
        self._btn_3d: QPushButton | None = None
        self._exagg_slider: QSlider | None = None
        self._exagg_label: QLabel | None = None
        self._azimuth_slider: QSlider | None = None
        self._azimuth_label: QLabel | None = None
        self._elevation_slider: QSlider | None = None
        self._elevation_label: QLabel | None = None
        self._light_azimuth = 315
        self._light_elevation = 45
        # Benannte Widgets für Tests/Introspektion (Prefix ``height_``).
        self._refs: dict[str, QWidget] = {}

    # ── Aufbau ───────────────────────────────────────────────────────────
    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()
        if self._preview3d is not None:
            layout.addWidget(self._build_preview3d(self._preview3d))
        layout.addWidget(self._build_acquire())
        layout.addWidget(_make_label(tr("right_panel.height.hint"), "#777", 11))
        layout.addWidget(self._build_edit())
        layout.addWidget(self._build_optimize())
        layout.addStretch()
        self.refresh([])
        self.set_preview3d_active(False)
        return outer, self._refs

    # ── 3D-Abschnitt (UX-Vertrag §1) ─────────────────────────────────────
    def _build_preview3d(self, actions: Preview3DActions) -> QWidget:
        section, body = _make_section(tr("preview3d.section"))

        # Zeile „Darstellung"  [2D | 3D]
        body.addWidget(_make_label(tr("preview3d.display"), "#aaa"))
        seg_row = QHBoxLayout(); seg_row.setSpacing(6)
        btn_2d = _make_neutral_btn(tr("preview3d.display.2d"))
        btn_3d = _make_neutral_btn(tr("preview3d.display.3d"))
        btn_2d.setCheckable(True); btn_3d.setCheckable(True)
        btn_2d.clicked.connect(lambda _=False: actions.set_mode_3d(False))
        btn_3d.clicked.connect(lambda _=False: actions.set_mode_3d(True))
        seg_row.addWidget(btn_2d, 1); seg_row.addWidget(btn_3d, 1)
        body.addLayout(seg_row)
        self._btn_2d, self._btn_3d = btn_2d, btn_3d
        self._refs.update(preview3d_2d=btn_2d, preview3d_3d=btn_3d)

        body.addWidget(_make_hdivider())

        # Überhöhung (logarithmisch), rein visuell.
        exagg_label = _make_label(tr("preview3d.exaggeration", value="1.0"), "#aaa")
        exagg = _make_slider(
            0, _EXAGG_SLIDER_MAX, slider_from_exaggeration(1.0),
            tr("preview3d.exaggeration.hint"))

        def on_exagg(pos: int) -> None:
            value = exaggeration_from_slider(pos)
            exagg_label.setText(tr("preview3d.exaggeration", value=f"{value:.1f}"))
            actions.set_exaggeration(value)

        exagg.valueChanged.connect(on_exagg)
        body.addWidget(exagg_label)
        body.addWidget(exagg)
        body.addWidget(_make_label(tr("preview3d.exaggeration.hint"), "#777", 11))
        self._refs.update(preview3d_exaggeration=exagg)
        self._exagg_slider, self._exagg_label = exagg, exagg_label

        # Licht-Azimut / Licht-Höhe (Uniforms).
        azimuth_label = _make_label(
            tr("preview3d.light_azimuth", value=self._light_azimuth), "#aaa")
        azimuth = _make_slider(0, 360, self._light_azimuth)
        elevation_label = _make_label(
            tr("preview3d.light_elevation", value=self._light_elevation), "#aaa")
        elevation = _make_slider(15, 90, self._light_elevation)

        def on_azimuth(value: int) -> None:
            self._light_azimuth = value
            azimuth_label.setText(tr("preview3d.light_azimuth", value=value))
            actions.set_light(float(value), float(self._light_elevation))

        def on_elevation(value: int) -> None:
            self._light_elevation = value
            elevation_label.setText(tr("preview3d.light_elevation", value=value))
            actions.set_light(float(self._light_azimuth), float(value))

        azimuth.valueChanged.connect(on_azimuth)
        elevation.valueChanged.connect(on_elevation)
        body.addWidget(azimuth_label); body.addWidget(azimuth)
        body.addWidget(elevation_label); body.addWidget(elevation)
        self._refs.update(preview3d_azimuth=azimuth, preview3d_elevation=elevation)
        self._azimuth_slider, self._azimuth_label = azimuth, azimuth_label
        self._elevation_slider, self._elevation_label = elevation, elevation_label

        body.addWidget(_make_hdivider())

        # Qualität (löst Rebuild aus).
        body.addWidget(_make_label(tr("preview3d.quality"), "#aaa"))
        quality_row = QHBoxLayout(); quality_row.setSpacing(6)
        for quality, label in (
            (MeshQuality.REDUCED, tr("preview3d.quality.reduced")),
            (MeshQuality.STANDARD, tr("preview3d.quality.standard")),
            (MeshQuality.HIGH, tr("preview3d.quality.high")),
        ):
            btn = _make_neutral_btn(label)
            btn.clicked.connect(lambda _=False, q=quality: self._on_quality(actions, q))
            quality_row.addWidget(btn, 1)
            self._quality_buttons[quality] = btn
            self._refs[f"preview3d_quality_{quality.value}"] = btn
        body.addLayout(quality_row)
        self._select_quality(MeshQuality.STANDARD)

        # Einpassen / Zurücksetzen.
        action_row = QHBoxLayout(); action_row.setSpacing(6)
        btn_fit = _make_neutral_btn(tr("preview3d.fit"))
        btn_reset = _make_neutral_btn(tr("preview3d.reset"))
        btn_fit.clicked.connect(lambda _=False: actions.fit_view())
        btn_reset.clicked.connect(lambda _=False: actions.reset_view())
        action_row.addWidget(btn_fit, 1); action_row.addWidget(btn_reset, 1)
        body.addLayout(action_row)
        self._refs.update(preview3d_fit=btn_fit, preview3d_reset=btn_reset)

        self._preview3d_param_widgets += [
            exagg, azimuth, elevation, btn_fit, btn_reset,
            *self._quality_buttons.values(),
        ]
        return section

    def _on_quality(self, actions: Preview3DActions, quality: MeshQuality) -> None:
        self._select_quality(quality)
        actions.set_quality(quality)

    def _select_quality(self, quality: MeshQuality) -> None:
        self._selected_quality = quality
        for q, btn in self._quality_buttons.items():
            _set_button_selected(btn, q is quality)

    def sync_preview3d_state(
        self,
        *,
        quality: MeshQuality,
        exaggeration: float,
        light: tuple[float, float],
    ) -> None:
        """Spiegelt den kanonischen Controller-Zustand ohne Callback-Schleifen.

        Wird nach Start, Reset und jedem Panel-Neuaufbau aufgerufen. Dadurch
        zeigen QSettings, Controller und Regler stets dieselben Werte.
        """
        azimuth = max(0, min(360, int(round(light[0]))))
        elevation = max(15, min(90, int(round(light[1]))))
        self._light_azimuth = azimuth
        self._light_elevation = elevation

        widgets = (
            self._exagg_slider,
            self._azimuth_slider,
            self._elevation_slider,
        )
        for widget in widgets:
            if widget is not None:
                widget.blockSignals(True)
        try:
            if self._exagg_slider is not None:
                self._exagg_slider.setValue(slider_from_exaggeration(exaggeration))
            if self._azimuth_slider is not None:
                self._azimuth_slider.setValue(azimuth)
            if self._elevation_slider is not None:
                self._elevation_slider.setValue(elevation)
        finally:
            for widget in widgets:
                if widget is not None:
                    widget.blockSignals(False)

        if self._exagg_label is not None:
            self._exagg_label.setText(
                tr("preview3d.exaggeration", value=f"{exaggeration:.1f}")
            )
        if self._azimuth_label is not None:
            self._azimuth_label.setText(tr("preview3d.light_azimuth", value=azimuth))
        if self._elevation_label is not None:
            self._elevation_label.setText(
                tr("preview3d.light_elevation", value=elevation)
            )
        self._select_quality(quality)

    def set_preview3d_active(self, is_3d: bool) -> None:
        """Spiegelt den 2D/3D-Segmentzustand und schaltet die 3D-Regler frei."""
        if self._btn_2d is not None:
            _set_button_selected(self._btn_2d, not is_3d)
        if self._btn_3d is not None:
            _set_button_selected(self._btn_3d, is_3d)
        for widget in self._preview3d_param_widgets:
            widget.setEnabled(is_3d)

    def set_preview3d_available(self, available: bool, tooltip: str = "") -> None:
        """Aktiviert/deaktiviert das 3D-Segment (Capability-/HEIGHT-Gating)."""
        if self._btn_3d is not None:
            self._btn_3d.setEnabled(available)
            self._btn_3d.setToolTip(tooltip)

    def _build_acquire(self) -> QWidget:
        section, body = _make_section(tr("right_panel.height.section.acquire"))
        # Primärbutton wie im Prototyp/Spec §9 Schritt 5 (Issue #416: derselbe
        # blaue Verlauf wie die übrigen Primärbuttons, kein Lila-Sonderton mehr).
        btn_gen = _make_primary_btn(
            tr("right_panel.height.generate"),
            tr("right_panel.height.generate.tooltip"))
        btn_gen.clicked.connect(lambda _=False: self._actions.generate())
        btn_imp = _make_neutral_btn(
            tr("right_panel.height.import"),
            tr("right_panel.height.import.tooltip"), icon_name="height_import")
        btn_imp.clicked.connect(lambda _=False: self._actions.import_file())
        body.addWidget(btn_gen)
        body.addWidget(btn_imp)
        self._acquire_widgets += [btn_gen, btn_imp]
        self._refs.update(height_generate=btn_gen, height_import=btn_imp)
        return section

    def _build_edit(self) -> QWidget:
        section, body = _make_section(tr("right_panel.height.section.edit"))

        # Interne Bit-Tiefe sichtbar machen (#590): HEIGHT-Ebenen führen ihre
        # Höhen kanonisch als 16 Bit – die 0–255-Regler sind nur die Bedienskala.
        body.addWidget(_make_label(tr("right_panel.height.depth_info"), "#777", 11))

        strength = _spin(1, 255, 32)
        row_s = QHBoxLayout(); row_s.setSpacing(6)
        row_s.addWidget(_make_label(tr("right_panel.height.strength"), "#aaa"), 1)
        row_s.addWidget(strength)
        body.addLayout(row_s)

        row_ld = QHBoxLayout(); row_ld.setSpacing(6)
        btn_light = _make_neutral_btn(
            tr("right_panel.height.lighten"),
            tr("right_panel.height.lighten.tooltip"))
        btn_light.clicked.connect(lambda _=False: self._actions.lighten(strength.value()))
        btn_dark = _make_neutral_btn(
            tr("right_panel.height.darken"),
            tr("right_panel.height.darken.tooltip"))
        btn_dark.clicked.connect(lambda _=False: self._actions.darken(strength.value()))
        row_ld.addWidget(btn_light, 1)
        row_ld.addWidget(btn_dark, 1)
        body.addLayout(row_ld)

        body.addWidget(_make_hdivider())
        set_value = _spin(0, 255, 128)
        row_set = QHBoxLayout(); row_set.setSpacing(6)
        row_set.addWidget(_make_label(tr("right_panel.height.set_value"), "#aaa"), 1)
        row_set.addWidget(set_value)
        body.addLayout(row_set)
        btn_set = _make_neutral_btn(
            tr("right_panel.height.set"),
            tr("right_panel.height.set.tooltip"))
        btn_set.clicked.connect(lambda _=False: self._actions.set_height(set_value.value()))
        body.addWidget(btn_set)

        btn_inv = _make_neutral_btn(
            tr("right_panel.height.invert"),
            tr("right_panel.height.invert.tooltip"))
        btn_inv.clicked.connect(lambda _=False: self._actions.invert())
        body.addWidget(btn_inv)

        self._height_widgets += [strength, btn_light, btn_dark, set_value, btn_set, btn_inv]
        self._refs.update(
            height_strength=strength, height_lighten=btn_light, height_darken=btn_dark,
            height_set_value=set_value, height_set=btn_set, height_invert=btn_inv)
        return section

    def _build_optimize(self) -> QWidget:
        section, body = _make_section(tr("right_panel.height.section.optimize"))

        # Tonwert (Schwarz-/Weißpunkt)
        black = _spin(0, 254, 0)
        white = _spin(1, 255, 255)

        def levels_op(f: HeightField) -> HeightField:
            return height_ops.levels(
                f,
                scale_8bit_height_value(black.value(), f),
                scale_8bit_height_value(white.value(), f),
            )
        body.addWidget(_make_label(tr("right_panel.height.levels"), "#aaa"))
        self._op_row([black, white], levels_op, body, "levels")
        self._refs.update(height_levels_black=black, height_levels_white=white)

        # Gamma (×100)
        gamma = _spin(10, 300, 100, suffix=" %", width=86)

        def gamma_op(f: HeightField) -> HeightField:
            return height_ops.gamma(f, gamma.value() / 100.0)
        body.addWidget(_make_label(tr("right_panel.height.gamma"), "#aaa"))
        self._op_row([gamma], gamma_op, body, "gamma")
        self._refs["height_gamma"] = gamma

        # Glättung: Gauß + Median
        body.addWidget(_make_hdivider())
        gauss = _spin(1, 20, 2)

        def gauss_op(f: HeightField) -> HeightField:
            return height_ops.gaussian_blur(f, float(gauss.value()))
        body.addWidget(_make_label(tr("right_panel.height.gaussian"), "#aaa"))
        self._op_row([gauss], gauss_op, body, "gauss")
        self._refs["height_gauss"] = gauss

        median = _spin(1, 10, 1)

        def median_op(f: HeightField) -> HeightField:
            return height_ops.median_blur(f, median.value())
        body.addWidget(_make_label(tr("right_panel.height.median"), "#aaa"))
        self._op_row([median], median_op, body, "median")
        self._refs["height_median"] = median

        # Schwelle + Stufen
        body.addWidget(_make_hdivider())
        thresh = _spin(0, 255, 128)

        def thresh_op(f: HeightField) -> HeightField:
            return height_ops.threshold(f, scale_8bit_height_value(thresh.value(), f))
        body.addWidget(_make_label(tr("right_panel.height.threshold"), "#aaa"))
        self._op_row([thresh], thresh_op, body, "threshold")
        self._refs["height_threshold"] = thresh

        steps = _spin(2, 32, 4)

        def steps_op(f: HeightField) -> HeightField:
            return height_ops.quantize(f, steps.value())
        body.addWidget(_make_label(tr("right_panel.height.steps"), "#aaa"))
        self._op_row([steps], steps_op, body, "steps")
        self._refs["height_steps"] = steps

        # Höhenbereich-Clamp
        body.addWidget(_make_hdivider())
        rng_lo = _spin(0, 254, 0)
        rng_hi = _spin(1, 255, 255)

        def range_op(f: HeightField) -> HeightField:
            return height_ops.clamp_range(
                f,
                scale_8bit_height_value(rng_lo.value(), f),
                scale_8bit_height_value(rng_hi.value(), f),
            )
        body.addWidget(_make_label(tr("right_panel.height.range"), "#aaa"))
        self._op_row([rng_lo, rng_hi], range_op, body, "range")
        self._refs.update(height_range_lo=rng_lo, height_range_hi=rng_hi)

        body.addWidget(_make_hdivider())
        btn_cancel = _make_neutral_btn(
            tr("right_panel.height.discard_preview"),
            tr("right_panel.height.discard_preview.tooltip"))
        btn_cancel.clicked.connect(lambda _=False: self._actions.cancel_preview())
        body.addWidget(btn_cancel)

        self._height_widgets.append(btn_cancel)
        self._refs["height_discard"] = btn_cancel
        return section

    def _op_row(
        self, spins: list[QSpinBox], op: HeightOp, body: QVBoxLayout, key: str,
    ) -> None:
        """Baut eine Operationszeile: Parameter-Spins, Live-Vorschau, „Anwenden".

        Jede Reglerbewegung aktualisiert die Vorschau (``preview_op``); der
        Button committet die Operation undo-fähig (``apply_op``). Die ``op``-Closure
        liest ihre Werte erst beim Aufruf, also stets aktuell.
        """
        btn = _make_neutral_btn(
            tr("right_panel.height.apply"),
            tr("right_panel.height.apply.tooltip"))
        btn.clicked.connect(lambda _=False: self._actions.apply_op(op))
        row = QHBoxLayout(); row.setSpacing(6)
        for spin in spins:
            spin.valueChanged.connect(lambda _v=0: self._actions.preview_op(op))
            row.addWidget(spin)
        row.addWidget(btn, 1)
        body.addLayout(row)
        self._height_widgets += [*spins, btn]
        self._refs[f"height_apply_{key}"] = btn

    # ── Moduskontext ─────────────────────────────────────────────────────
    def refresh(self, layers: list[LayerInfo]) -> None:
        """Schaltet Beschaffen (Projekt vorhanden) bzw. Höhenwerkzeuge (HEIGHT aktiv).

        Höhenwerkzeuge sind ausschließlich an ``LayerKind.HEIGHT`` gebunden – die
        Rolle ``HEIGHT_MAP`` allein genügt nicht (Vertrag #364).
        """
        active = next((info for info in layers if info.active), None)
        has_project = bool(layers)
        is_height = active is not None and active.kind is LayerKind.HEIGHT
        for widget in self._acquire_widgets:
            widget.setEnabled(has_project)
        for widget in self._height_widgets:
            widget.setEnabled(is_height)
