# Changelog

## 0.1.1 — 2026-11-02

Maintenance release with a small feature and a bug fix.

### Added

- **Open plot in new window** opens an independent snapshot of the selected cycle property (HIT, EIT or any available property), preserving averages, uncertainty bars, regression overlays and current axis limits. Resize or maximize the window, use its zoom/pan/save toolbar, or press F11 for full screen and Escape to exit. Open a new snapshot to capture later analysis changes.

### Fixed

- Measurement files and numbered subfolders use natural numeric ordering: 1, 2, 3, …, 10, 11, 12. Text comparisons remain case-insensitive; zero-padded names have deterministic ordering.

### Maintenance

- Moved automated tests from `assets/tests` to the top-level `tests` directory; assets now contain only application images.
- Shortened the README by removing obsolete repository-creation instructions and keeping detailed history and proposed work in this changelog.
- GitHub Actions now installs Matplotlib so the plot snapshot test runs rather than being skipped.
- Made the suggested attribution in LICENSE independent of the application version; license terms are unchanged.

## 0.1.0 — 2026-10-29

Initial local desktop release, developed by Michele Tunesi.

- Folder loading for nanoindentation text exports, including subfolders and parsing notices.
- Linked raw measurement and cycle-result plots with selectable axes and properties.
- Curve inclusion/exclusion, with excluded curves retained in gray.
- Cycle-wise averages with capped uncertainty bars of ±2s/√n.
- Contact-depth and normalized-depth axes, configurable contact-area function and film thickness.
- Ideal Berkovich area function and 1000 nm film thickness as startup defaults.
- Normalized-axis reference at x=1.5.
- Cycle-range sliders for linear regression before or after averaging, excluding rejected curves.
- Aligned cycle-range controls with synchronized sliders and editable numeric spinboxes.
- Red fit line, top Fit-/Fit+ bounds, intercept ±2SE, and fit statistics.
- Excel summary export with one row per indentation and cycle.
- Analysis and About tabs, institutional logo support and offline documentation links.
- Italian etymology, application abstract, creator attribution and CC BY 4.0 license notice.
- Consolidated Python package and automated tests in assets/tests.
- Final application name: INDAGO — Indentation Data Analysis, Graphing & Overview.
  Earlier development labels CMC Curve Explorer and INDIGO were renamed within 0.1.0;
  they are not separate numbered releases.

## Planned versions

The following ideas are proposals, not released features or delivery commitments.

### 0.2.0 — proposed

- Save and restore area-function, thickness, inclusion and regression settings.
- Export computed averages and regression statistics alongside the cycle summary.
- Improve plot export controls and documentation.

### Later — proposed

- Support additional instrument export formats and per-indentation film thickness.
- Evaluate weighted and robust regression methods with explicit statistical assumptions.
