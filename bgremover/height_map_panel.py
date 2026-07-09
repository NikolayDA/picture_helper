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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bgremover import height_ops
from bgremover.canvas import LayerInfo
from bgremover.height_map import HeightField
from bgremover.i18n import tr
from bgremover.project_model import LayerKind
from bgremover.right_panel_tabs import (
    _make_hdivider,
    _make_label,
    _make_neutral_btn,
    _make_primary_btn,
    _make_scroll_tab,
    _make_section,
    _PanelSpinBox,
    _style_spin_box,
)

# Reine Höhen-Operation; die Closures lesen ihre Reglerwerte beim Aufruf.
HeightOp = Callable[[HeightField], HeightField]


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


def _spin(lo: int, hi: int, value: int, *, suffix: str = "", width: int = 72) -> QSpinBox:
    """Einheitlich gestylte Ganzzahl-Eingabe für das Höhen-Panel."""
    box = _PanelSpinBox()
    box.setRange(lo, hi)
    box.setValue(value)
    if suffix:
        box.setSuffix(suffix)
    box.setFixedWidth(width)
    _style_spin_box(box)
    return box


class HeightMapPanel:
    """Baut und pflegt den Höhen-Tab; ``refresh`` schaltet den Moduskontext."""

    def __init__(self, actions: HeightMapActions) -> None:
        self._actions = actions
        # Aktiv nur mit geladenem Projekt (Beschaffen) bzw. aktiver HEIGHT-Ebene.
        self._acquire_widgets: list[QWidget] = []
        self._height_widgets: list[QWidget] = []
        # Benannte Widgets für Tests/Introspektion (Prefix ``height_``).
        self._refs: dict[str, QWidget] = {}

    # ── Aufbau ───────────────────────────────────────────────────────────
    def build(self) -> tuple[QWidget, dict[str, QWidget]]:
        outer, layout = _make_scroll_tab()
        layout.addWidget(self._build_acquire())
        layout.addWidget(_make_label(tr("right_panel.height.hint"), "#777", 11))
        layout.addWidget(self._build_edit())
        layout.addWidget(self._build_optimize())
        layout.addStretch()
        self.refresh([])
        return outer, self._refs

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
            return height_ops.levels(f, black.value(), white.value())
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
            return height_ops.threshold(f, thresh.value())
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
            return height_ops.clamp_range(f, rng_lo.value(), rng_hi.value())
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
