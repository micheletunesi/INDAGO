"""Scrollable About page and offline documentation viewer for INDAGO."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from . import APP_NAME, APP_FULL_NAME, __version__

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = {'README': 'README.md', 'Changelog': 'CHANGELOG.md', 'License': 'LICENSE'}
LICENSE_NAME = 'Creative Commons Attribution 4.0 International (CC BY 4.0)'
LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/'
ETYMOLOGY = (
    'INDAGO è l’acronimo di Indentation Data Analysis, Graphing & Overview. '
    'Il nome richiama «indago», prima persona singolare del presente indicativo '
    'del verbo italiano «indagare»: cercare con metodo per conoscere e comprendere. '
    'Indagare deriva dal latino indagare, legato a indago, «indagine». '
    'Il richiamo esprime lo scopo del programma: esplorare i dati di indentazione '
    'e ricavarne informazioni sulle proprietà dei materiali.'
)
ABSTRACT = (
    'INDAGO is a local Python desktop application for exploring nanoindentation '
    'measurements and reported cycle results. It loads folders of instrument text '
    'exports, displays force–depth and depth–time curves, and links curve selection '
    'across raw and cycle-result plots. Curves can be included or excluded from '
    'analysis. Results can be plotted against contact depth, cycle number, peak '
    'force, or dimensionless depth derived from a calibrated area function and film '
    'thickness. Cycle averages include capped uncertainty bars of ±2s/√n. In '
    'normalized view, cycle-range selection supports linear regression, intercept '
    'extrapolation to zero depth, and fit statistics. A per-indentation, per-cycle '
    'Excel summary preserves the reported properties and inclusion status. '
    'Measurement processing and documentation viewing work offline.'
)


def open_document(owner, title):
    """Read bundled documents in the app, without a Markdown file association."""
    path = PROJECT_ROOT / DOCUMENTS[title]
    try:
        content = path.read_text(encoding='utf-8')
    except OSError as exc:
        messagebox.showerror('Document unavailable', str(exc), parent=owner)
        return
    window = tk.Toplevel(owner)
    window.title(f'{APP_NAME} — {title}')
    window.geometry('950x680')
    text = tk.Text(window, wrap='word', padx=18, pady=18, font=('Consolas', 11))
    scrollbar = ttk.Scrollbar(window, command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')
    text.pack(fill='both', expand=True)
    text.insert('1.0', content)
    text.configure(state='disabled')


def build_about(owner, parent):
    canvas = tk.Canvas(parent, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)
    content = ttk.Frame(canvas, padding=(6, 6, 24, 24))
    item = canvas.create_window((0, 0), window=content, anchor='nw')
    content.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
    wrapped = []

    def resize(event):
        canvas.itemconfigure(item, width=event.width)
        for label in wrapped:
            label.configure(wraplength=max(280, event.width-60))

    canvas.bind('<Configure>', resize)

    def paragraph(text, **options):
        label = ttk.Label(content, text=text, wraplength=1000, justify='left', **options)
        label.pack(anchor='w', pady=(0, 12))
        wrapped.append(label)
        return label

    def heading(text):
        paragraph(text, font=('Segoe UI', 12, 'bold'))

    def link(text, command):
        label = ttk.Label(content, text=text, foreground='#176b94', cursor='hand2')
        label.pack(anchor='w', pady=3)
        label.bind('<Button-1>', lambda event: command())
        return label

    paragraph(f'{APP_NAME} v{__version__}', font=('Segoe UI', 24, 'bold'))
    paragraph(APP_FULL_NAME, font=('Segoe UI', 13))
    heading('Produced by Michele Tunesi')
    paragraph('DIGEP — Dipartimento di Ingegneria Gestionale e della Produzione\n'
              'Department of Management and Production Engineering\nPolitecnico di Torino')
    heading('Etimologia del nome')
    paragraph(ETYMOLOGY)
    link('Fonte etimologica: Treccani — indagare',
         lambda: webbrowser.open('https://www.treccani.it/vocabolario/indagare/'))
    heading('Abstract')
    paragraph(ABSTRACT)
    heading('Documentation')
    for title in DOCUMENTS:
        link(title, lambda name=title: open_document(owner, name))
    heading('License')
    paragraph(f'© 2026 Michele Tunesi. {LICENSE_NAME}.\n'
              'The project code and documentation are licensed with attribution. '
              'Institutional logos and third-party dependencies retain their own rights and licenses.')
    link('CC BY 4.0 — official terms', lambda: webbrowser.open(LICENSE_URL))
    link('DIGEP website', lambda: webbrowser.open('https://www.digep.polito.it/en'))
    link('Michele Tunesi — Politecnico di Torino',
         lambda: webbrowser.open('https://www.polito.it/personale?p=michele.tunesi'))
    logos = ttk.Frame(content)
    logos.pack(fill='x', pady=20)
    owner.logo_images = []
    files = sorted(p for p in (PROJECT_ROOT / 'assets' / 'logos').glob('*')
                   if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif'))
    for i in range(max(2, len(files))):
        slot = ttk.LabelFrame(logos, text='Institution logo' if i == 0 else 'Additional logo', padding=12)
        slot.grid(row=i//2, column=i%2, sticky='nsew', padx=(0, 12), pady=(0, 12))
        logos.columnconfigure(i%2, weight=1)
        if i < len(files):
            try:
                from PIL import Image, ImageTk
                with Image.open(files[i]) as source:
                    source.thumbnail((400, 160))
                    picture = ImageTk.PhotoImage(source.copy(), master=owner)
                owner.logo_images.append(picture)
                ttk.Label(slot, image=picture).pack(expand=True)
            except (ImportError, OSError, tk.TclError):
                ttk.Label(slot, text=f'Logo: {files[i].name}\nPreview unavailable').pack(padx=16, pady=35)
        else:
            ttk.Label(slot, text='Logo placeholder', foreground='#888888').pack(padx=55, pady=55)

    def wheel(event):
        bounds = canvas.bbox('all')
        if bounds and bounds[3] > canvas.winfo_height():
            canvas.yview_scroll(-int(event.delta/120), 'units')
        return 'break'

    def bind_wheel(widget):
        widget.bind('<MouseWheel>', wheel)
        for child in widget.winfo_children():
            bind_wheel(child)

    bind_wheel(parent)
