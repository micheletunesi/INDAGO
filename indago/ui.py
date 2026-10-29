"""Run with: python indago_app.py"""
import math
from pathlib import Path
from queue import Queue, Empty
from threading import Thread
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from .parser import read_curve
from .analysis import (cycle_averages, cycle_x, read_parameters, normalized_depth,
                       regression_points, linear_regression)
from .export import export_summary
from . import __version__ as VERSION, APP_NAME
from .about import build_about



class IndagoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'{APP_NAME} v{VERSION}')
        self.geometry('1280x850')
        self.minsize(900, 650)
        self.curves, self.artists = [], []
        self.selected = None
        self.events = Queue()
        self.details = 'No folder loaded.'
        self.mode = tk.StringVar(value='Force vs depth')
        self.prop = tk.StringVar(value='HIT')
        self.xaxis = tk.StringVar(value='Contact depth (hc)')
        self.average_mode = tk.BooleanVar(value=False)
        self.area_coefficients = [tk.StringVar(value=value) for value in ('24.5', '0', '0', '0', '0')]
        self.thickness = tk.StringVar(value='1000')
        self.depth_notice = tk.StringVar()
        self.regression_enabled = tk.BooleanVar(value=False)
        self.first_cycle = tk.IntVar(value=1)
        self.last_cycle = tk.IntVar(value=26)
        self.status = tk.StringVar(value='Select a folder containing instrument text exports.')
        tabs = ttk.Notebook(self)
        tabs.pack(fill='both', expand=True)
        analysis_tab = ttk.Frame(tabs)
        about_tab = ttk.Frame(tabs, padding=24)
        tabs.add(analysis_tab, text='Analysis')
        tabs.add(about_tab, text='About')
        build_about(self, about_tab)
        top = ttk.Frame(analysis_tab, padding=14)
        top.pack(fill='x')
        ttk.Label(top, text=f'{APP_NAME} v{VERSION}', font=('Segoe UI', 18, 'bold')).pack(side='left')
        self.open_button = ttk.Button(top, text='Select folder…', command=self.open_folder)
        self.open_button.pack(side='right')
        ttk.Button(top, text='Export Excel summary…', command=self.export_excel).pack(side='right', padx=10)
        body = ttk.Panedwindow(analysis_tab, orient='horizontal')
        body.pack(fill='both', expand=True, padx=12)
        side = ttk.Frame(body, padding=8)
        body.add(side, weight=0)
        self.count = ttk.Label(side, text='Curves', font=('Segoe UI', 11, 'bold'))
        self.count.pack(anchor='w', pady=8)
        box = ttk.Frame(side)
        box.pack(fill='both', expand=True)
        self.listbox = tk.Listbox(box, width=32, exportselection=False, activestyle='none', selectbackground='#177d79')
        scroll = ttk.Scrollbar(box, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.select)
        self.listbox.bind('<Button-3>', self.list_menu)
        self.curve_menu = tk.Menu(self, tearoff=False)
        self.curve_menu.add_command(label='Include', command=lambda: self.set_included(True))
        self.curve_menu.add_command(label='Exclude', command=lambda: self.set_included(False))
        ttk.Button(side, text='Show all equally', command=self.clear).pack(fill='x', pady=8)
        ttk.Button(side, text='Load details…', command=self.show_details).pack(fill='x')
        regression_panel = self.regression_panel = ttk.LabelFrame(side, text='Linear regression results', padding=8)
        self.regression_text = tk.Text(regression_panel, width=32, height=19, wrap='word',
                                       font=('Consolas', 9), relief='flat', background='#f4f7fa')
        regression_scroll = ttk.Scrollbar(regression_panel, command=self.regression_text.yview)
        self.regression_text.configure(yscrollcommand=regression_scroll.set)
        regression_scroll.pack(side='right', fill='y')
        self.regression_text.pack(side='left', fill='both', expand=True)
        self.set_regression_text('Enable Linear regression to fit the selected cycle range.')
        right = ttk.Frame(body)
        body.add(right, weight=1)
        controls = ttk.Frame(right, padding=6)
        controls.pack(fill='x')
        self.combo(controls, 'Raw plot', self.mode, ['Force vs depth', 'Depth vs time'], 20)
        controls2 = ttk.Frame(right, padding=6)
        controls2.pack(fill='x')
        self.property_box = self.combo(controls2, 'Cycle property', self.prop, [], 22)
        self.combo(controls2, 'Against', self.xaxis, ['Contact depth (hc)', 'Normalized depth', 'Cycle number', 'Maximum depth (hmax)', 'Peak force (Fmax)'], 24)
        self.depth_frame = ttk.LabelFrame(right, text='Normalized depth: √(A(hc)/π) / film thickness', padding=6)
        area_row = ttk.Frame(self.depth_frame)
        area_row.pack(fill='x', pady=3)
        ttk.Label(area_row, text='A(hc) =').pack(side='left')
        for i, (power, variable) in enumerate(zip(['hc²', 'hc', 'hc^(1/2)', 'hc^(1/4)', 'hc^(1/8)'], self.area_coefficients)):
            if i:
                ttk.Label(area_row, text=' + ').pack(side='left')
            entry = ttk.Entry(area_row, textvariable=variable, width=7)
            entry.pack(side='left')
            ttk.Label(area_row, text=' · '+power).pack(side='left')
            entry.bind('<Return>', lambda event: self.draw())
            entry.bind('<FocusOut>', lambda event: self.draw())
            entry.bind('<KeyRelease>', self.schedule_depth_draw)
        thickness_row = ttk.Frame(self.depth_frame)
        thickness_row.pack(fill='x', pady=3)
        ttk.Label(thickness_row, text='Film thickness (nm): ').pack(side='left')
        entry = ttk.Entry(thickness_row, textvariable=self.thickness, width=12)
        entry.pack(side='left')
        ttk.Label(thickness_row, text='   hc in nm; area in nm²; blank coefficients = 0').pack(side='left')
        entry.bind('<Return>', lambda event: self.draw())
        entry.bind('<FocusOut>', lambda event: self.draw())
        entry.bind('<KeyRelease>', self.schedule_depth_draw)
        ttk.Label(self.depth_frame, textvariable=self.depth_notice, foreground='#9a4b16', wraplength=650).pack(anchor='w')
        self.depth_redraw = None
        results_controls = self.results_controls = ttk.Frame(right, padding=6)
        results_controls.pack(fill='x')
        self.average_button = ttk.Button(results_controls, text='Show averages ± uncertainty', command=self.toggle_averages)
        self.average_button.pack(side='left')
        ttk.Label(results_controls, text='Included curves only · uncertainty = 2 × s / √n').pack(side='left', padx=12)
        fit_controls = self.fit_controls = ttk.Frame(right, padding=(6, 0))
        fit_controls.columnconfigure((0, 1), weight=1, uniform='cycle_bounds')
        ttk.Checkbutton(fit_controls, text='Linear regression', variable=self.regression_enabled,
                        command=self.draw).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 4))
        self.cycle_sliders = []
        self.cycle_entries = []
        self.cycle_texts = []
        self.cycle_limits = (1, 26)
        integer_input = (self.register(lambda value: not value or value.isascii() and value.isdigit()), '%P')
        for index, (title, variable) in enumerate([('First cycle', self.first_cycle), ('Last cycle', self.last_cycle)]):
            frame = ttk.Frame(fit_controls, padding=(0 if index == 0 else 12, 0, 12 if index == 0 else 0, 4))
            frame.grid(row=1, column=index, sticky='ew')
            frame.columnconfigure(0, weight=1)
            ttk.Label(frame, text=title).grid(row=0, column=0, sticky='w')
            text = tk.StringVar(value=str(variable.get()))
            self.cycle_texts.append(text)
            entry = ttk.Spinbox(frame, from_=1, to=26, increment=1, width=7,
                                textvariable=text, justify='center', validate='key',
                                validatecommand=integer_input, command=lambda i=index: self.commit_cycle(i))
            entry.grid(row=0, column=1, sticky='e', pady=(0, 3))
            entry.bind('<Return>', lambda event, i=index: self.commit_cycle(i))
            entry.bind('<FocusOut>', lambda event, i=index: self.commit_cycle(i))
            self.cycle_entries.append(entry)
            slider = ttk.Scale(frame, from_=1, to=26, orient='horizontal',
                               command=lambda value, i=index: self.cycle_slider_changed(i, value))
            slider.set(variable.get())
            slider.grid(row=1, column=0, columnspan=2, sticky='ew')
            self.cycle_sliders.append(slider)
        self.figure = Figure(figsize=(9, 7), constrained_layout=True)
        self.raw_ax, self.cycle_ax = self.figure.subplots(2, 1)
        self.canvas = FigureCanvasTkAgg(self.figure, master=right)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        NavigationToolbar2Tk(self.canvas, right).update()
        ttk.Label(analysis_tab, textvariable=self.status, padding=10, wraplength=1150).pack(fill='x')
        self.canvas.mpl_connect('motion_notify_event', self.hover)
        self.canvas.mpl_connect('button_press_event', self.plot_menu)
        self.draw()

    def combo(self, parent, label, var, values, width):
        ttk.Label(parent, text=label).pack(side='left', padx=(0, 6))
        box = ttk.Combobox(parent, textvariable=var, values=values, width=width, state='readonly')
        box.pack(side='left', padx=(0, 16))
        box.bind('<<ComboboxSelected>>', lambda event: self.draw())
        return box

    def schedule_depth_draw(self, _event):
        if self.depth_redraw is not None:
            self.after_cancel(self.depth_redraw)
        self.depth_redraw = self.after(350, self.redraw_depth)

    def redraw_depth(self):
        self.depth_redraw = None
        self.draw()

    def set_regression_text(self, text):
        self.regression_text.configure(state='normal')
        self.regression_text.delete('1.0', 'end')
        self.regression_text.insert('1.0', text)
        self.regression_text.configure(state='disabled')

    def cycle_slider_changed(self, index, value):
        low, high = self.cycle_limits
        value = max(low, min(high, round(float(value))))
        (self.first_cycle, self.last_cycle)[index].set(value)
        self.cycle_texts[index].set(str(value))
        if hasattr(self, 'canvas'):
            self.schedule_depth_draw(None)

    def commit_cycle(self, index):
        variable = (self.first_cycle, self.last_cycle)[index]
        low, high = self.cycle_limits
        try:
            value = int(self.cycle_texts[index].get())
            if not low <= value <= high:
                raise ValueError
        except ValueError:
            self.cycle_texts[index].set(str(variable.get()))
            self.status.set(f'Enter a cycle number from {low} to {high}.')
            return
        variable.set(value)
        self.cycle_sliders[index].set(value)
        self.cycle_texts[index].set(str(value))
        self.schedule_depth_draw(None)

    def open_folder(self):
        folder = filedialog.askdirectory(parent=self, title='Choose data folder')
        if folder:
            self.open_button.configure(state='disabled')
            self.status.set('Scanning folder…')
            Thread(target=self.load, args=(Path(folder),), daemon=True).start()
            self.after(100, self.poll)

    def load(self, folder):
        curves, notices = [], []
        try:
            files = sorted((p for p in folder.rglob('*') if p.is_file()
                            and not any(s.startswith('.') for s in p.relative_to(folder).parts)), key=lambda p: str(p).lower())
            for i, path in enumerate(files):
                name = str(path.relative_to(folder))
                self.events.put(('progress', f'Reading {i+1}/{len(files)}: {name}'))
                try:
                    if path.stat().st_size > 100 * 1024 * 1024:
                        raise ValueError('File exceeds 100 MB limit.')
                    curve = read_curve(path, name)
                    curves.append(curve)
                    notices.extend(f'{name}: {w}' for w in curve['warnings'])
                except (OSError, ValueError) as exc:
                    notices.append(f'Skipped {name}: {exc}')
            self.events.put(('done', (curves, notices, str(folder))))
        except Exception as exc:
            self.events.put(('error', str(exc)))

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'progress':
                    self.status.set(data)
                elif kind == 'error':
                    self.open_button.configure(state='normal')
                    self.status.set('Loading failed.')
                    messagebox.showerror('Loading error', data, parent=self)
                    return
                else:
                    self.curves, notices, folder = data
                    self.selected = None
                    for c in self.curves:
                        c['included'] = True
                    self.refresh_list()
                    numbers = [p['cycle'] for c in self.curves for p in c['cycles']]
                    low, high = (min(numbers), max(numbers)) if numbers else (1, 1)
                    self.cycle_limits = (low, high)
                    for slider in self.cycle_sliders:
                        slider.configure(from_=low, to=max(low+1, high))
                    for entry in self.cycle_entries:
                        entry.configure(from_=low, to=high)
                    self.first_cycle.set(low)
                    self.last_cycle.set(high)
                    for slider, text, value in zip(self.cycle_sliders, self.cycle_texts, (low, high)):
                        slider.set(value)
                        text.set(str(value))
                    keys = list(dict.fromkeys(k for c in self.curves for cycle in c['cycles'] for k in cycle['values']))
                    self.property_box.configure(values=keys)
                    if self.prop.get() not in keys:
                        self.prop.set('HIT' if 'HIT' in keys else keys[0] if keys else '')
                    summary = f"Loaded {len(self.curves)} curves · {sum(len(c['raw']) for c in self.curves):,} samples · {sum(len(c['cycles']) for c in self.curves)} cycles."
                    if notices:
                        summary += f' {len(notices)} notices — see Load details.'
                    self.status.set(summary)
                    self.details = folder + '\n\n' + summary + '\n\n' + '\n'.join(notices)
                    self.open_button.configure(state='normal')
                    self.draw()
                    return
        except Empty:
            self.after(100, self.poll)

    def show_details(self):
        window = tk.Toplevel(self)
        window.title('Load details')
        window.geometry('800x450')
        text = tk.Text(window, wrap='word', padx=12, pady=12)
        scroll = ttk.Scrollbar(window, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        text.pack(fill='both', expand=True)
        text.insert('1.0', self.details)
        text.configure(state='disabled')

    def export_excel(self):
        if not any(c['cycles'] for c in self.curves):
            messagebox.showinfo('Export Excel', 'Load curves with cycle results first.', parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title='Export cycle results',
                                          defaultextension='.xlsx', initialfile='INDAGO_summary.xlsx',
                                          filetypes=[('Excel workbook', '*.xlsx')])
        if not path:
            return
        try:
            rows = export_summary(self.curves, path)
        except (OSError, ValueError) as exc:
            messagebox.showerror('Export failed', str(exc), parent=self)
            return
        self.status.set(f'Exported {rows} cycle results to {path}')

    def select(self, event):
        selection = self.listbox.curselection()
        self.selected = selection[0] if selection else None
        self.draw()

    def clear(self):
        self.listbox.selection_clear(0, 'end')
        self.selected = None
        self.draw()

    def refresh_list(self):
        self.listbox.delete(0, 'end')
        for i, curve in enumerate(self.curves):
            included = curve.get('included', True)
            self.listbox.insert('end', curve['name'] + ('' if included else ' [excluded]'))
            self.listbox.itemconfigure(i, foreground='#203747' if included else '#888888',
                                      selectforeground='white' if included else '#cccccc')
        if self.selected is not None:
            self.listbox.selection_set(self.selected)
        n = sum(c.get('included', True) for c in self.curves)
        self.count.configure(text=f'Curves ({n}/{len(self.curves)} included)')

    def list_menu(self, event):
        index = self.listbox.nearest(event.y)
        bounds = self.listbox.bbox(index) if self.curves else None
        if bounds and bounds[1] <= event.y <= bounds[1] + bounds[3]:
            self.show_curve_menu(index, event.x_root, event.y_root)

    def show_curve_menu(self, index, x, y):
        self.selected = index
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set(index)
        self.draw()
        included = self.curves[index].get('included', True)
        self.curve_menu.entryconfigure('Include', state='disabled' if included else 'normal')
        self.curve_menu.entryconfigure('Exclude', state='normal' if included else 'disabled')
        try:
            self.curve_menu.tk_popup(x, y)
        finally:
            self.curve_menu.grab_release()

    def plot_menu(self, event):
        if event.button != 3 or event.inaxes not in (self.raw_ax, self.cycle_ax):
            return
        candidates = []
        for artist, name, active, index in self.artists:
            if index is None or artist.axes is not event.inaxes:
                continue
            hit, info = artist.contains(event)
            if hit:
                x, y = artist.get_data()
                for j in info.get('ind', []):
                    px, py = artist.get_transform().transform((x[j], y[j]))
                    candidates.append(((px-event.x)**2 + (py-event.y)**2, index))
        if candidates:
            index = min(candidates)[1]
            widget = self.canvas.get_tk_widget()
            self.show_curve_menu(index, widget.winfo_pointerx(), widget.winfo_pointery())

    def set_included(self, included):
        if self.selected is None:
            return
        self.curves[self.selected]['included'] = included
        self.refresh_list()
        self.draw()

    def toggle_averages(self):
        self.average_mode.set(not self.average_mode.get())
        self.average_button.configure(text='Show individual data points' if self.average_mode.get()
                                      else 'Show averages ± uncertainty')
        self.draw()

    def label(self, key):
        unit = next((c['units'][key] for c in self.curves if key in c['units']), '')
        return f'{key} ({unit})' if unit else key

    def draw_regression(self, key, xkey):
        if self.xaxis.get() != 'Normalized depth':
            return
        if not self.regression_enabled.get():
            self.set_regression_text('Enable Linear regression to fit the selected cycle range.')
            return
        first, last = self.first_cycle.get(), self.last_cycle.get()
        if first > last:
            self.set_regression_text('First cycle must be ≤ last cycle.')
            return
        averaged = self.average_mode.get()
        points = regression_points(self.curves, key, xkey, first, last, averaged)
        if points:
            xs, _ys = zip(*points)
            for x, text, align in [(min(xs), 'Fit-', 'right'), (max(xs), 'Fit+', 'left')]:
                self.cycle_ax.axvline(x, color='#b55757', linestyle='--', linewidth=1, zorder=3)
                self.cycle_ax.annotate(text, xy=(x, 1),
                                       xycoords=self.cycle_ax.get_xaxis_transform(),
                                       xytext=(-3 if align == 'right' else 3, 5),
                                       textcoords='offset points', va='bottom', ha=align,
                                       fontsize=9, color='#a13333', annotation_clip=False)
        try:
            fit = linear_regression(points)
        except ValueError as exc:
            self.set_regression_text(f'Cycles {first}–{last}\n{len(points)} valid points\n\n{exc}')
            return
        left, right = min(0., fit['xmin']), max(0., fit['xmax'])
        self.cycle_ax.plot([left, right], [fit['intercept']+fit['slope']*x for x in (left, right)],
                           color='red', linewidth=1.8, zorder=7)
        self.cycle_ax.errorbar([0], [fit['intercept']], yerr=[2*fit['intercept_se']],
                               fmt='none', ecolor='red', capsize=4, zorder=8)
        def fmt(value):
            return f'{value:.6g}' if math.isfinite(value) else 'undefined'
        self.set_regression_text(
            f"Unweighted OLS: y = b + m·x\n{'Cycle averages' if averaged else 'Individual included points'}\n"
            f"y: {self.label(key)}\n"
            f"Cycles: {first}–{last}\nN = {fit['n']}; df = {fit['df']}\n"
            f"x: {fmt(fit['xmin'])} to {fmt(fit['xmax'])}\n\n"
            f"Intercept at x=0:\n{fmt(fit['intercept'])} ± {fmt(2*fit['intercept_se'])}\n"
            f"Intercept SE: {fmt(fit['intercept_se'])}\n"
            f"Slope: {fmt(fit['slope'])}\nSlope SE: {fmt(fit['slope_se'])}\n"
            f"R: {fmt(fit['r'])}\nR²: {fmt(fit['r2'])}\nAdjusted R²: {fmt(fit['adjusted_r2'])}\n"
            f"Residual SD: {fmt(fit['residual_sd'])}\nRMSE: {fmt(fit['rmse'])}\nSSE: {fmt(fit['sse'])}\n\n"
            '± is 2×OLS standard error,\nnot an exact 95% interval.\nOLS assumes independent errors.\n'
            'Excluded curves never fitted.\nDashed: fitted x extent.\nRed line extends to x=0.')

    def draw(self):
        self.artists = []
        for ax in (self.raw_ax, self.cycle_ax):
            ax.clear()
            ax.grid(alpha=.22)
        force = self.mode.get() == 'Force vs depth'
        self.raw_ax.set(title='Raw measurements', xlabel='Depth (nm)' if force else 'Time (s)', ylabel='Force (mN)' if force else 'Depth (nm)')
        if self.xaxis.get() == 'Normalized depth':
            if not self.fit_controls.winfo_manager():
                self.fit_controls.pack(fill='x', before=self.canvas.get_tk_widget())
                self.regression_panel.pack(fill='x', pady=(14, 0))
            if not self.depth_frame.winfo_manager():
                self.depth_frame.pack(fill='x', before=self.results_controls, padx=6, pady=4)
            try:
                coefficients, thickness = read_parameters([v.get() for v in self.area_coefficients], self.thickness.get())
                xkey = lambda cycle: normalized_depth(cycle['values'].get('hc', math.nan), coefficients, thickness)
                skipped = sum(not math.isfinite(cycle_x(p, xkey)) for c in self.curves for p in c['cycles'])
                self.depth_notice.set('Blank coefficients = 0. ' + (f'{skipped} cycle(s) omitted: missing/invalid hc or negative/nonfinite area.' if skipped else ''))
            except ValueError as exc:
                self.depth_notice.set(str(exc))
                xkey = lambda cycle: math.nan
            xlabel = 'Normalized depth √(A(hc)/π) / thickness (dimensionless)'
        else:
            self.depth_frame.pack_forget()
            self.fit_controls.pack_forget()
            self.regression_panel.pack_forget()
            xkey = {'Contact depth (hc)': 'hc', 'Cycle number': None, 'Maximum depth (hmax)': 'hmax', 'Peak force (Fmax)': 'Fmax'}[self.xaxis.get()]
            xlabel = self.label(xkey) if xkey else 'Cycle number'
        key = self.prop.get()
        self.cycle_ax.set(xlabel=xlabel, ylabel=self.label(key))
        self.cycle_ax.set_title('Cycle analysis', pad=26)
        for i in sorted(range(len(self.curves)), key=lambda n: n == self.selected):
            c = self.curves[i]
            active = self.selected is None or i == self.selected
            included = c.get('included', True)
            style = dict(color=f'C{i % 10}' if included else '#999999',
                         alpha=(1 if active else .17) if included else .45,
                         zorder=4 if i == self.selected else 2)
            line, = self.raw_ax.plot([p[1] if force else p[0] for p in c['raw']], [p[2] if force else p[1] for p in c['raw']], linewidth=2.2 if i == self.selected else 1, **style)
            self.artists.append((line, c['name'], active, i))
            points = [(cycle_x(p, xkey), p['values'].get(key, math.nan)) for p in c['cycles']]
            points = [(x, y) for x, y in points if math.isfinite(x) and math.isfinite(y)]
            if not self.average_mode.get() or not included:
                dots, = self.cycle_ax.plot([p[0] for p in points], [p[1] for p in points], linestyle='none', marker='o', markersize=6 if i == self.selected else 4, **style)
                self.artists.append((dots, c['name'], active, i))
        if self.average_mode.get():
            rows = cycle_averages(self.curves, key, xkey)
            self.cycle_ax.set_title('Cycle averages — included curves only', pad=26)
            if rows:
                xs, ys = [r['x'] for r in rows], [r['y'] for r in rows]
                line, = self.cycle_ax.plot(xs, ys, 'o-', color='#177d79', label='Mean', zorder=5)
                self.artists.append((line, 'Average', True, None))
                self.average_rows = rows
                valid = [r for r in rows if r['n'] > 1]
                if valid:
                    self.cycle_ax.errorbar([r['x'] for r in valid], [r['y'] for r in valid],
                                           yerr=[r['uncertainty'] for r in valid], fmt='none',
                                           ecolor='#177d79', capsize=4, zorder=5,
                                           label='± 2s/√n (sample s; n ≥ 2)')
                if any(r['n'] == 1 for r in rows):
                    self.cycle_ax.text(.01, .98, 'n = 1: mean shown, uncertainty undefined',
                                       transform=self.cycle_ax.transAxes, va='top', fontsize=8)
                self.cycle_ax.legend(loc='best', fontsize=8)
            else:
                self.cycle_ax.text(.5, .5, 'No included results to average',
                                   transform=self.cycle_ax.transAxes, ha='center', color='#607080')
        for ax in (self.raw_ax, self.cycle_ax):
            if not ax.has_data() and not (ax is self.cycle_ax and self.average_mode.get()):
                ax.text(.5, .5, 'No results for this property / axis' if self.curves else 'Select a folder to load curves', transform=ax.transAxes, ha='center', color='#607080')
        if self.selected is not None:
            self.raw_ax.set_title('Raw measurements — ' + self.curves[self.selected]['name'], fontsize=10)
        self.draw_regression(key, xkey)
        if self.xaxis.get() == 'Normalized depth':
            self.cycle_ax.axvline(1.5, color='#999999', alpha=.35, linewidth=1, zorder=.5)
            self.cycle_ax.text(1.5, .99, ' x = 1.5', transform=self.cycle_ax.get_xaxis_transform(),
                               va='top', color='#888888', alpha=.65, fontsize=8)
        self.canvas.draw_idle()

    def hover(self, event):
        if event.inaxes not in (self.raw_ax, self.cycle_ax):
            return
        for artist, name, active, index in reversed(self.artists):
            if active and artist.axes is event.inaxes:
                hit, info = artist.contains(event)
                if hit and len(info.get('ind', [])):
                    i = info['ind'][0]
                    x, y = artist.get_data()
                    extra = ''
                    if index is None:
                        row = self.average_rows[i]
                        u = row['uncertainty']
                        extra = f" | n={row['n']} | uncertainty: " + (f'±{u:.6g}' if math.isfinite(u) else 'undefined (n=1)')
                    self.status.set(f'{name} | {event.inaxes.get_xlabel()}: {x[i]:.6g} | {event.inaxes.get_ylabel()}: {y[i]:.6g}' + extra)
                    return

