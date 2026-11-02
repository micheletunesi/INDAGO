# INDAGO v0.1.1

**Indentation Data Analysis, Graphing & Overview**

Developed by Michele Tunesi · DIGEP · Politecnico di Torino.

## Creator

**Michele Tunesi** — DIGEP, Dipartimento di Ingegneria Gestionale e della Produzione, Politecnico di Torino.

[Institutional profile](https://www.polito.it/personale?p=michele.tunesi) · [DIGEP](https://www.digep.polito.it/en)

INDAGO è anche «io indago»: il nome richiama il verbo italiano *indagare*, dal latino *indagare*, e l'idea di esaminare i dati con metodo per comprenderli. [Fonte: Treccani](https://www.treccani.it/vocabolario/indagare/).

## Start

The desktop version uses Python 3.10+, Tkinter and Matplotlib. From this folder run:

```powershell
python -m pip install -r requirements.txt
python indago_app.py
```

Use `py` instead of `python` if you use the Windows Python launcher. Tkinter is included with standard Windows Python installations. After installing Matplotlib, the app works fully offline.

Once installed, double-click **Start INDAGO.bat** to launch the app. The launcher checks Python and dependencies and keeps error messages visible if startup fails.

Select a folder, choose the raw plot mode and cycle property, then click a filename to highlight it in both panels. Cycle properties can be plotted against cycle number, maximum depth or peak force. The Matplotlib toolbar provides zoom, pan, reset and figure saving. Hover over data to see values in the status bar. **Load details…** shows skipped files and warnings. Folder loading runs in a background thread; subfolders are included.

The launcher is `indago_app.py`; application code is organized in the `indago` package. Reported properties are preserved; averaging, normalization and regression are applied only when selected. Data remains on your computer.

Right-click a filename or an individual curve/point in either plot for **Include** and **Exclude**. Excluded curves remain gray in the list and plots and can be included again. Exclusions last until another folder is loaded.

The results x-axis defaults to **Contact depth (hc)**. Cycle number, maximum depth and peak force remain available in the dropdown. Normalization starts with the ideal Berkovich area function `A(hc) = 24.5*hc²` (other coefficients zero) and film thickness **1000 nm**; these remain editable.

Choose **Normalized depth** in Against to show the area-function fields:
`A(hc) = a*hc² + b*hc + c*hc^(1/2) + d*hc^(1/4) + e*hc^(1/8)`.
Blank coefficients mean zero. Enter film thickness in nm (required, greater than zero). Coefficients must be calibrated for hc in nm and A in nm². The x coordinate is `sqrt(A(hc)/pi)/thickness`, dimensionless. Changes update after typing, pressing Enter or leaving a field. Missing/negative hc and negative/nonfinite areas are omitted and reported beside the inputs. Invalid inputs leave the raw plot available and clear normalized results until corrected. In average mode, normalized depths are calculated for each curve first, then averaged by cycle. Settings remain when switching axes during the session. The Excel summary continues to export the original reported properties.

Click **Show averages ± uncertainty** to switch the cycle-results panel to averages across included curves, grouped by matching cycle number. Capped vertical error bars show **mean ± 2 × sample standard deviation / √n**, where n is the number of included curves with valid results for that cycle and the chosen axes. There is no shaded band. Depth/force horizontal coordinates are averaged over those same contributions; no interpolation is performed. Cycles with n=1 show the mean without uncertainty. Hover over a mean for n and uncertainty. Excluded results remain gray for reference. Click **Show individual data points** to return.

Click **Export Excel summary…** to save an `.xlsx` workbook with one row per indentation and cycle. It includes all reported properties (HIT, EIT, hc, etc.), units in column headers, the source filename and inclusion status. All loaded curves are exported, including excluded curves, which appear gray and are marked No in the Included column. Missing values remain blank. This exports the reported cycle summaries, independent of the selected plot property or average view. The header is frozen and filterable. Export uses Python's standard library and needs no additional installation.

Files are listed in natural numeric order: for example, sample1, sample2, sample3, …, sample10, sample11. This also applies to numbered subfolders.

## Linear regression

Select **Normalized depth** to reveal **Linear regression**, its results and the **First cycle** and **Last cycle** sliders. These controls and regression overlays hide on every other axis. In normalized view a faint gray vertical reference marks **x = 1.5** behind the data. Adjust the sliders to choose an inclusive cycle range (for example 2–12). The fit automatically follows the property, normalization parameters and inclusion flags. A crossed range shows a message until corrected. In individual mode the fit pools all valid included points; in average mode it fits one valid mean per cycle. The fit is unweighted in both modes, and selecting a filename for highlighting does not limit the fit to that file. Regression settings are retained when switching axes.

Cycle controls use two aligned, equal-width columns. You can drag a slider, use the arrow buttons beside its number, or type a cycle number and press Enter (or leave the field). Values must be within the loaded cycle range; invalid entries restore the previous value. Sliders and number fields stay synchronized.

Dashed vertical bounds labeled **Fit-** and **Fit+** above the plot mark the fitted points' minimum/maximum x coordinates, and a red line shows the fitted model extended to x=0. Individual fit points receive no extra highlighting. Excluded gray curves contribute neither to the fit nor to its bounds, in individual and averaged modes. The intercept's capped uncertainty bar appears at x=0.

The scrollable **Linear regression results** area shows intercept, intercept standard error, slope, slope standard error, Pearson R, R², adjusted R², N, residual degrees of freedom, residual standard deviation, RMSE, SSE and fitted x range. Intercept uncertainty is **±2 × its OLS standard error**, estimated from residual variance using N−2 degrees of freedom; it is not an exact 95% Student-t interval. Ordinary least squares assumes independent errors; repeated cycles within an indentation may be correlated. At least three valid points and two distinct x values are required. A constant property has undefined R and R². Regression results are displayed in the app; Excel export remains the reported per-cycle summary.

Click **Open plot in new window** beside the averages button to open the current cycle-property plot (HIT, EIT or any selected property) as an independent snapshot. It includes regression overlays, uncertainty bars, exclusions, highlighting and current axis limits. Resize or maximize the window, or press **F11** for full screen and **Escape** to exit full screen. Its toolbar supports zoom, pan and saving. Changes in the main analysis do not change an existing snapshot; click the button again for a new snapshot. This button is available on every results axis.

## About tab

The scrollable **About** tab shows **INDAGO v0.1.1**, its expanded name, creator and institutional affiliation, an Italian explanation of the name, and an abstract of the application's capabilities. **README**, **Changelog** and **License** links open bundled documents inside the app, offline. The license is identified as Creative Commons Attribution 4.0 International (CC BY 4.0), with an additional link to its official terms. Department, author and etymology sources link to the official websites. Logos are read from `assets/logos` beside the app, including the supplied `PoliTO_DIGEP.jpg`; an additional logo placeholder is shown until another image is provided. PNG, JPG/JPEG and GIF images are supported. Logo preview uses Pillow, included as a Matplotlib dependency.

## Release notes

Version **0.1.1** adds an independent cycle-plot window with full-screen viewing and fixes numeric filename ordering. See [CHANGELOG.md](CHANGELOG.md) for release history and proposed future work.

## License

Copyright © 2026 Michele Tunesi. The original project code and documentation are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. See [LICENSE](LICENSE) and the [official legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en). Reuse and modification, including commercial use, require appropriate attribution, a license link and indication of changes under the license terms.

Institutional logos and third-party dependencies retain their own rights and licenses. Processing a measurement file does not change ownership or license its data or results under this project license.

Suggested attribution: *INDAGO v0.1.1 — Indentation Data Analysis, Graphing & Overview, by Michele Tunesi, licensed under CC BY 4.0.*

## Project layout

```text
indago_app.py        Python entry point
Start INDAGO.bat    Windows launcher
requirements.txt    Runtime dependency
indago/             Application code: UI, analysis, parsing and export
assets/logos/       About-tab images
tests/              Automated tests (not needed to run the app)
.github/workflows/  Automated checks on GitHub
README.md           User guide
CHANGELOG.md        Release history and proposed future work
LICENSE             License notice
```

The About tab reads README.md, CHANGELOG.md and LICENSE at runtime, so keep these documents alongside the entry point. Keep `.gitignore` and `.gitattributes` in the repository to exclude generated files and preserve cross-platform line endings.

## Development checks

Install the runtime dependency, then run:

```powershell
python -B -m unittest discover -s tests -v
```

The numerical, parser and export tests use only the standard library. The plot snapshot test also uses Matplotlib; it is skipped if Matplotlib is missing. Tests run without opening desktop windows. GitHub Actions installs the runtime dependency and runs the suite on Windows and Linux with Python 3.10 and 3.14.

For a release, commit the update, push the branch, and create a matching version tag (for example `v0.1.1`). Use the corresponding changelog entry for release notes. Keep generated caches, local measurement files and exported workbooks out of version control.
