#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MIQUOD desktop application (tkinter).

Same flow as the Android app: open an image, draw the target areas, set the parameters, process,
read and export the results. Run it with::

    cd Python
    python miquod_gui.py [image]

Requires the packages of requirements.txt (Pillow renders the images in the window).
"""
__author__ = 'Edisson Naula'
__version__ = '2.1.0'

import json
import os
import queue
import sys
import threading
import traceback
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Mixing_QMPD as Mf  # noqa: E402

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAVE_MATPLOTLIB = True
except Exception:  # pragma: no cover - matplotlib is optional for the GUI
    HAVE_MATPLOTLIB = False

STAGE_NAMES = ['crop', 'mask', 'color', 'gray', 'binary', 'particles']
TARGET_COLOURS = ['#ffd400', '#00e5ff', '#ff7bff', '#8cff00', '#ff8c00', '#ffffff']


class ImageCanvas(ttk.Frame):
    """Shows a BGR image scaled to fit; optionally lets the user drag rectangles (image coordinates)."""

    def __init__(self, master, on_rectangle=None):
        super().__init__(master)
        self.canvas = tk.Canvas(self, bg='#202020', highlightthickness=0,
                                cursor='crosshair' if on_rectangle else 'arrow')
        self.canvas.pack(fill='both', expand=True)
        self.on_rectangle = on_rectangle
        self.image_bgr = None
        self.photo = None
        self.scale = 1.0
        self.offset = (0, 0)
        self.rectangles = []
        self.selected = None
        self._drag_start = None
        self._drag_item = None
        self.canvas.bind('<Configure>', lambda event: self.redraw())
        if on_rectangle:
            self.canvas.bind('<ButtonPress-1>', self._press)
            self.canvas.bind('<B1-Motion>', self._motion)
            self.canvas.bind('<ButtonRelease-1>', self._release)

    # -- geometry ------------------------------------------------------------------------------
    def to_image(self, cx, cy):
        h, w = self.image_bgr.shape[:2]
        x = int(round((cx - self.offset[0]) / self.scale))
        y = int(round((cy - self.offset[1]) / self.scale))
        return min(max(x, 0), w - 1), min(max(y, 0), h - 1)

    def to_canvas(self, x, y):
        return self.offset[0] + x * self.scale, self.offset[1] + y * self.scale

    # -- drawing -------------------------------------------------------------------------------
    def set_image(self, image_bgr):
        self.image_bgr = image_bgr
        self.redraw()

    def set_rectangles(self, rectangles, selected=None):
        self.rectangles = list(rectangles)
        self.selected = selected
        self.redraw()

    def redraw(self):
        self.canvas.delete('all')
        if self.image_bgr is None:
            return
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        h, w = self.image_bgr.shape[:2]
        self.scale = min(cw / float(w), ch / float(h))
        dw, dh = max(int(w * self.scale), 1), max(int(h * self.scale), 1)
        resized = cv2.resize(self.image_bgr, (dw, dh), interpolation=cv2.INTER_AREA)
        if resized.ndim == 2:
            rgb = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        self.photo = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.offset = ((cw - dw) // 2, (ch - dh) // 2)
        self.canvas.create_image(self.offset[0], self.offset[1], anchor='nw', image=self.photo)
        for i, rect in enumerate(self.rectangles):
            x0, y0 = self.to_canvas(rect.X, rect.Y)
            x1, y1 = self.to_canvas(rect.right + 1, rect.bottom + 1)
            colour = TARGET_COLOURS[i % len(TARGET_COLOURS)]
            width = 3 if i == self.selected else 2
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=colour, width=width)
            self.canvas.create_text(x0 + 4, y0 + 4, anchor='nw', text='Target %d' % i, fill=colour,
                                    font=('TkDefaultFont', 10, 'bold'))

    # -- mouse ---------------------------------------------------------------------------------
    def _press(self, event):
        if self.image_bgr is None:
            return
        self._drag_start = (event.x, event.y)
        self._drag_item = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='#ffffff',
                                                       dash=(4, 2), width=2)

    def _motion(self, event):
        if self._drag_item is not None:
            self.canvas.coords(self._drag_item, self._drag_start[0], self._drag_start[1], event.x, event.y)

    def _release(self, event):
        if self._drag_item is None:
            return
        self.canvas.delete(self._drag_item)
        self._drag_item = None
        x0, y0 = self.to_image(*self._drag_start)
        x1, y1 = self.to_image(event.x, event.y)
        self._drag_start = None
        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        if right - left >= 2 and bottom - top >= 2:
            self.on_rectangle(Mf.Rectangle(left, top, right - left + 1, bottom - top + 1))


class MiquodApp(tk.Tk):
    def __init__(self, image_path=None):
        super().__init__()
        self.title('MIQUOD %s - Mixing quantification from images' % __version__)
        self.geometry('1320x820')
        self.minsize(1000, 650)
        self.image = None
        self.image_path = None
        self.targets = []
        self.results = None
        self.queue = queue.Queue()
        self._build_ui()
        self.after(100, self._poll_queue)
        if image_path:
            self.open_image(image_path)

    # ------------------------------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------------------------------
    def _build_ui(self):
        paned = ttk.Panedwindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True)
        left = ttk.Frame(paned, padding=8)
        right = ttk.Notebook(paned)
        paned.add(left, weight=0)
        paned.add(right, weight=1)
        self.notebook = right

        # 1. Image
        box = ttk.LabelFrame(left, text='1. Image', padding=6)
        box.pack(fill='x', pady=(0, 6))
        ttk.Button(box, text='Open image...', command=self.open_image).pack(fill='x')
        self.image_label = ttk.Label(box, text='No image loaded', wraplength=300)
        self.image_label.pack(fill='x', pady=(4, 0))

        # 2. Targets
        box = ttk.LabelFrame(left, text='2. Target areas', padding=6)
        box.pack(fill='x', pady=(0, 6))
        ttk.Label(box, text='Drag on the image to draw a target, or type it below.', wraplength=300).pack(fill='x')
        self.target_list = tk.Listbox(box, height=4, exportselection=False)
        self.target_list.pack(fill='x', pady=4)
        self.target_list.bind('<<ListboxSelect>>', lambda event: self._refresh_targets())
        entry_row = ttk.Frame(box)
        entry_row.pack(fill='x')
        self.target_vars = []
        for label in ('X', 'Y', 'W', 'H'):
            ttk.Label(entry_row, text=label).pack(side='left')
            var = tk.StringVar()
            self.target_vars.append(var)
            ttk.Entry(entry_row, textvariable=var, width=6).pack(side='left', padx=(2, 6))
        button_row = ttk.Frame(box)
        button_row.pack(fill='x', pady=(4, 0))
        ttk.Button(button_row, text='Add', command=self.add_target_from_entries).pack(side='left', fill='x', expand=True)
        ttk.Button(button_row, text='Whole image', command=self.add_whole_image).pack(side='left', fill='x', expand=True)
        ttk.Button(button_row, text='Remove', command=self.remove_target).pack(side='left', fill='x', expand=True)
        ttk.Button(button_row, text='Clear', command=self.clear_targets).pack(side='left', fill='x', expand=True)

        # 3. Parameters
        box = ttk.LabelFrame(left, text='3. Parameters', padding=6)
        box.pack(fill='x', pady=(0, 6))
        self.mode_var = tk.StringVar(value='particles')
        mode_row = ttk.Frame(box)
        mode_row.pack(fill='x')
        ttk.Label(mode_row, text='Data:').pack(side='left')
        for value, text in (('particles', 'Particles'), ('concentration', 'Concentration'), ('both', 'Both')):
            ttk.Radiobutton(mode_row, text=text, value=value, variable=self.mode_var).pack(side='left', padx=4)
        grid = ttk.Frame(box)
        grid.pack(fill='x', pady=(6, 0))
        ttk.Label(grid, text='Particle colour').grid(row=0, column=0, sticky='w')
        self.color_var = tk.StringVar(value='red')
        ttk.Combobox(grid, textvariable=self.color_var, values=sorted(Mf.COLOR_RANGES), state='readonly',
                     width=10).grid(row=0, column=1, sticky='w', padx=4, pady=2)
        ttk.Label(grid, text='Gray threshold (0-255)').grid(row=1, column=0, sticky='w')
        self.threshold_var = tk.IntVar(value=50)
        ttk.Spinbox(grid, from_=0, to=255, textvariable=self.threshold_var, width=8).grid(row=1, column=1, sticky='w',
                                                                                          padx=4, pady=2)
        ttk.Label(grid, text='Blob area min / max (px)').grid(row=2, column=0, sticky='w')
        area_row = ttk.Frame(grid)
        area_row.grid(row=2, column=1, sticky='w', padx=4, pady=2)
        self.area_min_var = tk.IntVar(value=Mf.DEFAULT_DETECTOR_SETTINGS['limit_area'][0])
        self.area_max_var = tk.IntVar(value=Mf.DEFAULT_DETECTOR_SETTINGS['limit_area'][1])
        ttk.Spinbox(area_row, from_=1, to=100000, textvariable=self.area_min_var, width=6).pack(side='left')
        ttk.Spinbox(area_row, from_=1, to=100000, textvariable=self.area_max_var, width=6).pack(side='left', padx=(4, 0))
        self.dark_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(grid, text='Dark areas = higher concentration', variable=self.dark_var).grid(
            row=3, column=0, columnspan=2, sticky='w', pady=2)

        # 4. Process
        box = ttk.LabelFrame(left, text='4. Process', padding=6)
        box.pack(fill='x', pady=(0, 6))
        self.process_button = ttk.Button(box, text='Process', command=self.process)
        self.process_button.pack(fill='x')
        self.progress = ttk.Progressbar(box, mode='indeterminate')
        self.progress.pack(fill='x', pady=(4, 0))
        self.status_var = tk.StringVar(value='Open an image to start.')
        ttk.Label(box, textvariable=self.status_var, wraplength=300).pack(fill='x', pady=(4, 0))

        # 5. Results
        box = ttk.LabelFrame(left, text='5. Results', padding=6)
        box.pack(fill='x')
        self.export_button = ttk.Button(box, text='Export results (JSON)...', command=self.export_json, state='disabled')
        self.export_button.pack(fill='x')
        self.save_image_button = ttk.Button(box, text='Save annotated image...', command=self.save_annotated,
                                            state='disabled')
        self.save_image_button.pack(fill='x', pady=(4, 0))

        # Right side: tabs
        self.canvas = ImageCanvas(right, on_rectangle=self.add_target)
        right.add(self.canvas, text='Image')
        results_tab = ttk.Frame(right)
        right.add(results_tab, text='Results')
        self.results_text = tk.Text(results_tab, wrap='word', font=('Consolas', 10))
        scroll = ttk.Scrollbar(results_tab, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.results_text.pack(fill='both', expand=True)
        self._set_results_text(
            'MIQUOD %s\n\n1. Open an image.\n2. Draw one or more target areas on it.\n3. Choose the data type and '
            'the parameters.\n4. Press Process.\n\nThe measures appear here; the Detection tab shows the '
            'intermediate images of the particle detection and the Variograms tab the variograms of the '
            'concentration data.' % __version__)
        detection_tab = ttk.Frame(right)
        right.add(detection_tab, text='Detection')
        bar = ttk.Frame(detection_tab, padding=4)
        bar.pack(fill='x')
        ttk.Label(bar, text='Target').pack(side='left')
        self.stage_target_var = tk.StringVar()
        self.stage_target_box = ttk.Combobox(bar, textvariable=self.stage_target_var, state='readonly', width=8)
        self.stage_target_box.pack(side='left', padx=4)
        ttk.Label(bar, text='Stage').pack(side='left')
        self.stage_var = tk.StringVar(value='particles')
        self.stage_box = ttk.Combobox(bar, textvariable=self.stage_var, values=STAGE_NAMES, state='readonly', width=10)
        self.stage_box.pack(side='left', padx=4)
        self.stage_target_box.bind('<<ComboboxSelected>>', lambda event: self._show_stage())
        self.stage_box.bind('<<ComboboxSelected>>', lambda event: self._show_stage())
        self.stage_canvas = ImageCanvas(detection_tab)
        self.stage_canvas.pack(fill='both', expand=True)
        variogram_tab = ttk.Frame(right)
        right.add(variogram_tab, text='Variograms')
        if HAVE_MATPLOTLIB:
            self.figure = Figure(figsize=(6, 4), dpi=100)
            self.figure_canvas = FigureCanvasTkAgg(self.figure, master=variogram_tab)
            self.figure_canvas.get_tk_widget().pack(fill='both', expand=True)
        else:
            self.figure = None
            ttk.Label(variogram_tab, text='matplotlib is not installed; variograms are only exported.').pack(pady=20)

    # ------------------------------------------------------------------------------------------
    # Image and targets
    # ------------------------------------------------------------------------------------------
    def open_image(self, path=None):
        if path is None:
            path = filedialog.askopenfilename(
                title='Open image', filetypes=[('Images', '*.png *.jpg *.jpeg *.bmp *.tif *.tiff'), ('All files', '*')])
            if not path:
                return
        image = cv2.imread(path)
        if image is None:
            messagebox.showerror('MIQUOD', 'Could not read the image:\n%s' % path)
            return
        self.image = image
        self.image_path = path
        self.targets = []
        self.results = None
        self.export_button.configure(state='disabled')
        self.save_image_button.configure(state='disabled')
        self.image_label.configure(text='%s\n%d columns x %d rows' % (os.path.basename(path), image.shape[1],
                                                                       image.shape[0]))
        self.canvas.set_image(image)
        self._refresh_targets()
        self.notebook.select(0)
        self.status_var.set('Draw a target area on the image (click and drag).')

    def add_target(self, rect):
        if self.image is None:
            return
        try:
            Mf.BitMap(self.image).check_rectangle(rect)
        except ValueError as exc:
            messagebox.showerror('MIQUOD', str(exc))
            return
        self.targets.append(rect)
        self._refresh_targets(selected=len(self.targets) - 1)
        self.status_var.set('%d target(s). Set the parameters and press Process.' % len(self.targets))

    def add_target_from_entries(self):
        if self.image is None:
            messagebox.showinfo('MIQUOD', 'Open an image first.')
            return
        try:
            values = [int(var.get()) for var in self.target_vars]
            rect = Mf.Rectangle(*values)
        except (ValueError, TypeError):
            messagebox.showerror('MIQUOD', 'Enter integer X, Y, width and height (X = column, Y = row).')
            return
        self.add_target(rect)

    def add_whole_image(self):
        if self.image is None:
            messagebox.showinfo('MIQUOD', 'Open an image first.')
            return
        self.add_target(Mf.Rectangle(0, 0, self.image.shape[1], self.image.shape[0]))

    def remove_target(self):
        selection = self.target_list.curselection()
        if not selection:
            return
        del self.targets[selection[0]]
        self._refresh_targets()

    def clear_targets(self):
        self.targets = []
        self._refresh_targets()

    def _refresh_targets(self, selected=None):
        if selected is None:
            selection = self.target_list.curselection()
            selected = selection[0] if selection else None
        self.target_list.delete(0, 'end')
        for i, rect in enumerate(self.targets):
            self.target_list.insert('end', 'Target %d: X=%d Y=%d W=%d H=%d' % (i, rect.X, rect.Y, rect.Width,
                                                                              rect.Height))
        if selected is not None and selected < len(self.targets):
            self.target_list.selection_clear(0, 'end')
            self.target_list.selection_set(selected)
            rect = self.targets[selected]
            for var, value in zip(self.target_vars, rect.as_tuple()):
                var.set(str(value))
        self.canvas.set_rectangles(self.targets, selected)

    # ------------------------------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------------------------------
    def _settings(self):
        threshold = int(self.threshold_var.get())
        if not 0 <= threshold <= 255:
            raise ValueError('The gray threshold must be between 0 and 255.')
        area_min, area_max = int(self.area_min_var.get()), int(self.area_max_var.get())
        if area_min < 1 or area_max < area_min:
            raise ValueError('The blob area limits must satisfy 1 <= min <= max.')
        return {'mode': self.mode_var.get(), 'color': self.color_var.get(), 'threshold': threshold,
                'area': [area_min, area_max], 'dark': bool(self.dark_var.get())}

    def process(self):
        if self.image is None:
            messagebox.showinfo('MIQUOD', 'Open an image first.')
            return
        if not self.targets:
            messagebox.showinfo('MIQUOD', 'Draw at least one target area on the image.')
            return
        try:
            settings = self._settings()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror('MIQUOD', str(exc))
            return
        self.process_button.configure(state='disabled')
        self.export_button.configure(state='disabled')
        self.save_image_button.configure(state='disabled')
        self.progress.start(12)
        self.status_var.set('Processing... particle data takes a few seconds, concentration data about half a '
                            'minute on large targets.')
        worker = threading.Thread(target=self._worker, args=(self.image, list(self.targets), settings), daemon=True)
        worker.start()

    def _worker(self, image, targets, settings):
        try:
            output = {'settings': settings}
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                if settings['mode'] in ('particles', 'both'):
                    detector = Mf.BlobDetector(**dict(Mf.DEFAULT_DETECTOR_SETTINGS, limit_area=settings['area']))
                    output['particles'] = Mf.run_particle_analysis(image, targets, settings['threshold'],
                                                                   settings['color'], detector=detector,
                                                                   collect_stages=True)
                if settings['mode'] in ('concentration', 'both'):
                    output['concentration'] = Mf.run_concentration_analysis(image, targets, settings['dark'])
            output['warnings'] = [str(w.message) for w in caught]
            self.queue.put(('ok', output))
        except Exception as exc:  # shown to the user, never swallowed
            self.queue.put(('error', str(exc), traceback.format_exc()))

    def _poll_queue(self):
        try:
            message = self.queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_queue)
            return
        self.progress.stop()
        self.process_button.configure(state='normal')
        if message[0] == 'ok':
            self.results = message[1]
            self._show_results()
            self.status_var.set('Done. See the Results tab; export with the buttons below.')
        else:
            self.status_var.set('Error: %s' % message[1])
            messagebox.showerror('MIQUOD', message[1])
            print(message[2], file=sys.stderr)
        self.after(100, self._poll_queue)

    # ------------------------------------------------------------------------------------------
    # Results display and export
    # ------------------------------------------------------------------------------------------
    def _set_results_text(self, text):
        self.results_text.configure(state='normal')
        self.results_text.delete('1.0', 'end')
        self.results_text.insert('1.0', text)
        self.results_text.configure(state='disabled')

    def _show_results(self):
        results = self.results
        settings = results['settings']
        lines = ['MIQUOD %s' % __version__, 'Image: %s' % self.image_path]
        for j, rect in enumerate(self.targets):
            lines.append('Target %d: X=%d Y=%d W=%d H=%d (X = column, Y = row)' % ((j,) + rect.as_tuple()))
        lines.append('')
        if 'particles' in results:
            lines.append('PARTICLE DATA (colour %s, threshold %d, blob area %d-%d px)' % (
                settings['color'], settings['threshold'], settings['area'][0], settings['area'][1]))
            lines.append(Mf.summarize_particle_results(results['particles'], ['Image']))
            for j, spacing in enumerate(results['particles']['mean_spacing'][0]):
                lines.append('  target %d: mean particle spacing %d px, transect %r' % (
                    j, spacing, results['particles']['transects'][0][j]))
            lines.append('')
        if 'concentration' in results:
            lines.append('CONCENTRATION DATA (%s)' % ('dark areas = higher concentration' if settings['dark']
                                                      else 'bright areas = higher concentration'))
            lines.append(Mf.summarize_concentration_results(results['concentration'], ['Image']))
            lines.append('')
        if results.get('warnings'):
            lines.append('Warnings:')
            lines.extend('  ' + w for w in results['warnings'])
        lines.append('')
        lines.append('Legend: σ standard deviation, CoV coefficient of variation, M mixing index (1 - CoV), '
                     'Cm/Cmax/Cmin mean/max/min concentration, n number of quadrats or pixels, N particles, '
                     'σ_fpp filtered point-particle deviation, i_dis index of dispersion, xg spatial resolution. '
                     'See docs/method.md.')
        self._set_results_text('\n'.join(lines))

        annotated = self.image
        if 'particles' in results:
            for j, rect in enumerate(self.targets):
                annotated = Mf.draw_particles(annotated, results['particles']['particle_positions'][0][j],
                                              radius=max(2, int(round(min(self.image.shape[:2]) / 400.0))), rect=rect)
            self.canvas.set_image(annotated)
            self.stage_target_box.configure(values=['%d' % j for j in range(len(self.targets))])
            self.stage_target_var.set('0')
            self._show_stage()
        else:
            self.canvas.set_image(self.image)
            self.stage_canvas.set_image(None)
        self.annotated = annotated
        self._plot_variograms()
        self.export_button.configure(state='normal')
        self.save_image_button.configure(state='normal')
        self.notebook.select(1)

    def _show_stage(self):
        if not self.results or 'particles' not in self.results:
            return
        try:
            j = int(self.stage_target_var.get())
        except ValueError:
            return
        stages = self.results['particles']['detection_stages'][0][j]
        image = stages.get(self.stage_var.get(), stages['particles'])
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        self.stage_canvas.set_image(image)

    def _plot_variograms(self):
        if self.figure is None:
            return
        self.figure.clear()
        if self.results and 'concentration' in self.results:
            conc = self.results['concentration']
            ax1 = self.figure.add_subplot(1, 2, 1)
            ax2 = self.figure.add_subplot(1, 2, 2)
            for j in range(len(self.targets)):
                ax1.plot(conc['horizontal_variograms'][0][j], label='target %d' % j)
                ax2.plot(conc['vertical_variograms'][0][j], label='target %d' % j)
            for ax, title in ((ax1, 'Horizontal variogram γx(h)'), (ax2, 'Vertical variogram γy(h)')):
                ax.set_title(title)
                ax.set_xlabel('h (pixels)')
                ax.set_ylabel('γ(h)')
                ax.grid(True, alpha=0.3)
                ax.legend()
            self.figure.tight_layout()
        else:
            ax = self.figure.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, 'Variograms are computed for concentration data.', ha='center', va='center')
            ax.axis('off')
        self.figure_canvas.draw()

    def export_json(self):
        if not self.results:
            return
        path = filedialog.asksaveasfilename(title='Export results', defaultextension='.json',
                                            filetypes=[('JSON', '*.json')], initialfile='miquod_results.json')
        if not path:
            return
        report = {'miquod_version': __version__, 'image': self.image_path,
                  'image_size': {'columns': int(self.image.shape[1]), 'rows': int(self.image.shape[0])},
                  'targets': [t.as_tuple() for t in self.targets], 'settings': self.results['settings'],
                  'warnings': self.results.get('warnings', [])}
        base = os.path.splitext(path)[0]
        if 'particles' in self.results:
            particles = dict(self.results['particles'])
            particles.pop('detection_stages', None)
            report['particles'] = particles
        if 'concentration' in self.results:
            concentration = dict(self.results['concentration'])
            arrays = concentration.pop('concentration_data')
            files = []
            for j, array in enumerate(arrays[0]):
                file_name = '%s_concentration_target%d.npy' % (base, j)
                np.save(file_name, array)
                files.append(os.path.basename(file_name))
            concentration['concentration_data_files'] = files
            report['concentration'] = concentration
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(Mf.to_jsonable(report), handle, indent=2)
        self.status_var.set('Results exported to %s' % path)

    def save_annotated(self):
        if not self.results:
            return
        path = filedialog.asksaveasfilename(title='Save annotated image', defaultextension='.png',
                                            filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg')],
                                            initialfile='miquod_particles.png')
        if not path:
            return
        if not cv2.imwrite(path, self.annotated):
            messagebox.showerror('MIQUOD', 'Could not write %s' % path)
            return
        self.status_var.set('Annotated image saved to %s' % path)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    app = MiquodApp(argv[0] if argv else None)
    app.mainloop()


if __name__ == '__main__':
    main()
