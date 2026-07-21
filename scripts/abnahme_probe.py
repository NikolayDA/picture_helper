#!/usr/bin/env python3
"""GL-Provenance-Probe für die Release-Abnahme (#642/#643).

Ermittelt Vendor/Renderer/Version des OpenGL-Kontexts auf dem Runner und gibt
die Diagnose auf stdout aus (leer, wenn kein GL-Kontext verfügbar ist). Der
Renderer ist eine Eigenschaft der **Runner-Hardware**, nicht des gefrorenen
Artefakts – dieselbe Probe wie im Live-3D-Screenshot-Generator (#635). Läuft
bewusst mit nativer Qt-Plattform; ``--require`` lässt die Probe bei fehlendem
oder Software-Renderer mit Exit ≠ 0 scheitern (Abnahme-Modus).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bgremover.renderer_provenance import is_software_renderer  # noqa: E402


def probe_diagnostic() -> str:
    """GL-Diagnose über die Capability-Probe holen (leer bei Fallback)."""
    from bgremover.preview3d_capability import probe_3d_capability

    capability = probe_3d_capability(use_cache=False)
    return capability.diagnostic if capability.ok else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require",
        action="store_true",
        help="Exit != 0, wenn kein echter Hardware-Renderer vorliegt.",
    )
    args = parser.parse_args(argv)

    diagnostic = probe_diagnostic()
    print(diagnostic)

    if args.require:
        if not diagnostic:
            print("Kein OpenGL-Kontext verfügbar.", file=sys.stderr)
            return 2
        if is_software_renderer(diagnostic):
            print(f"Software-Renderer abgewiesen: {diagnostic}", file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
