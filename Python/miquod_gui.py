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

    def __init__(self, master, on_rectangle=None, on_motion=None, on_right_click=None):
        super().__init__(master)
        self.canvas = tk.Canvas(self, bg='#202020', highlightthickness=0,
                                cursor='crosshair' if on_rectangle else 'arrow')
        self.canvas.pack(fill='both', expand=True)
        self.on_rectangle = on_rectangle
        self.on_motion = on_motion
        self.on_right_click = on_right_click
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
        if on_motion:
            self.canvas.bind('<Motion>', self._hover)
        if on_right_click:
            self.canvas.bind('<Button-3>', self._right_click)

    # -- geometry ------------------------------------------------------------------------------
    def to_image(self, cx, cy):
        h, w = self.image_bgr.shape[:2]
        x = int(round((cx - self.offset[0]) / self.scale))
        y = int(round((cy - self.offset[1]) / self.scale))
        return min(max(x, 0), w - 1), min(max(y, 0), h - 1)

    def _pixel_under(self, event):
        """Image coordinates under the pointer, or None when it is outside the displayed image."""
        if self.image_bgr is None:
            return None
        h, w = self.image_bgr.shape[:2]
        x = int((event.x - self.offset[0]) / self.scale)
        y = int((event.y - self.offset[1]) / self.scale)
        if 0 <= x < w and 0 <= y < h:
            return x, y
        return None

    def _hover(self, event):
        pixel = self._pixel_under(event)
        if pixel is not None:
            self.on_motion(*pixel)

    def _right_click(self, event):
        pixel = self._pixel_under(event)
        if pixel is not None:
            self.on_right_click(*pixel)

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


class SequenceGallery(ttk.Frame):
    """Scrollable grid of labelled thumbnails; ``on_click(name)`` is called when a thumbnail is clicked."""

    def __init__(self, master, on_click=None):
        super().__init__(master)
        self.on_click = on_click
        self.canvas = tk.Canvas(self, bg='#f4f4f4', highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.images = {}
        self.photos = []
        self.canvas.bind('<Configure>', lambda event: self.redraw())
        self.canvas.bind('<MouseWheel>', lambda event: self.canvas.yview_scroll(int(-event.delta / 120), 'units'))

    def set_images(self, images):
        self.images = dict(images)
        self.redraw()

    def redraw(self):
        self.canvas.delete('all')
        self.photos = []
        if not self.images:
            self.canvas.configure(scrollregion=(0, 0, 1, 1))
            return
        width = max(self.canvas.winfo_width(), 320)
        pad, label_h = 10, 22
        columns = 3 if len(self.images) > 4 else 2
        tile_w = max((width - pad * (columns + 1)) // columns, 80)
        thumbs = []
        for name, image in self.images.items():
            rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB if image.ndim == 2 else cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            tile_h = max(int(h * tile_w / float(w)), 1)
            rgb = cv2.resize(rgb, (tile_w, tile_h), interpolation=cv2.INTER_AREA)
            thumbs.append((name, ImageTk.PhotoImage(Image.fromarray(rgb)), tile_h))
        y = pad
        for start in range(0, len(thumbs), columns):
            row = thumbs[start:start + columns]
            row_h = max(item[2] for item in row)
            for c, (name, photo, tile_h) in enumerate(row):
                x = pad + c * (tile_w + pad)
                tag = 'tile_%d' % (start + c)
                self.canvas.create_text(x, y, anchor='nw', text='%d. %s' % (start + c + 1, name),
                                        font=('TkDefaultFont', 10, 'bold'), tags=tag)
                self.canvas.create_image(x, y + label_h, anchor='nw', image=photo, tags=tag)
                self.canvas.create_rectangle(x - 1, y + label_h - 1, x + tile_w, y + label_h + tile_h,
                                             outline='#999999', tags=tag)
                if self.on_click:
                    self.canvas.tag_bind(tag, '<Button-1>', lambda event, n=name: self.on_click(n))
                self.photos.append(photo)
            y += label_h + row_h + pad
        self.canvas.configure(scrollregion=(0, 0, width, y))


class MiquodApp(tk.Tk):
    def __init__(self, image_path=None):
        super().__init__()
        self.title('MIQUOD %s - Mixing quantification from images' % __version__)
        self.geometry('1320x820')
        self.minsize(1000, 650)
        self.image = None
        self.image_path = None
        self.targets = []
        self.target_colors = []  # one colour specification per target (name or {'hue': ...})
        self.target_areas = []  # one [min_area, max_area] per target
        self.target_split = []  # one "split touching particles" flag per target
        self.hsv = None
        self.results = None
        self.sequence = {}
        self.annotated = None
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
        colour_row = ttk.Frame(box)
        colour_row.pack(fill='x', pady=(6, 0))
        ttk.Label(colour_row, text='Particle colour').pack(side='left')
        self.color_var = tk.StringVar(value='red')
        self.color_box = ttk.Combobox(colour_row, textvariable=self.color_var, state='readonly', width=8,
                                      values=sorted(Mf.COLOR_RANGES) + ['custom'])
        self.color_box.pack(side='left', padx=4)
        self.color_box.bind('<<ComboboxSelected>>', lambda event: self._update_custom_state())
        ttk.Button(colour_row, text='Apply to selected target', command=self.apply_color_to_selected).pack(
            side='left', fill='x', expand=True)
        custom_row = ttk.Frame(box)
        custom_row.pack(fill='x', pady=(4, 0))
        self.hue_var = tk.IntVar(value=0)
        self.hue_tol_var = tk.IntVar(value=10)
        self.s_min_var = tk.IntVar(value=100)
        self.v_min_var = tk.IntVar(value=100)
        self.custom_widgets = []
        for text, var, upper in (('Hue', self.hue_var, 179), ('±', self.hue_tol_var, 90),
                                 ('S ≥', self.s_min_var, 255), ('V ≥', self.v_min_var, 255)):
            ttk.Label(custom_row, text=text).pack(side='left')
            spin = ttk.Spinbox(custom_row, from_=0, to=upper, textvariable=var, width=4)
            spin.pack(side='left', padx=(2, 6))
            self.custom_widgets.append(spin)
        area_row = ttk.Frame(box)
        area_row.pack(fill='x', pady=(4, 0))
        ttk.Label(area_row, text='Blob area min / max (px)').pack(side='left')
        self.area_min_var = tk.IntVar(value=Mf.DEFAULT_DETECTOR_SETTINGS['limit_area'][0])
        self.area_max_var = tk.IntVar(value=Mf.DEFAULT_DETECTOR_SETTINGS['limit_area'][1])
        ttk.Spinbox(area_row, from_=1, to=10000000, textvariable=self.area_min_var, width=7).pack(side='left',
                                                                                                padx=(4, 2))
        ttk.Spinbox(area_row, from_=1, to=10000000, textvariable=self.area_max_var, width=7).pack(side='left')
        self.split_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(box, text='Split touching particles (large beads in contact)',
                        variable=self.split_var).pack(anchor='w', pady=(4, 0))
        ttk.Label(box, text='New targets take this colour, area and option. Hover over the image to read the '
                            'H, S, V of a pixel; right-click a particle to use its hue as the custom colour and '
                            'its size to set the blob area limits.',
                  wraplength=300).pack(fill='x', pady=(4, 0))
        self._update_custom_state()

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
        ttk.Label(grid, text='Gray threshold (0-255)').grid(row=1, column=0, sticky='w')
        self.threshold_var = tk.IntVar(value=50)
        ttk.Spinbox(grid, from_=0, to=255, textvariable=self.threshold_var, width=8).grid(row=1, column=1, sticky='w',
                                                                                          padx=4, pady=2)
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
        self.export_images_button = ttk.Button(box, text='Export images (all stages)...', command=self.export_images,
                                               state='disabled')
        self.export_images_button.pack(fill='x', pady=(4, 0))

        # Right side: tabs
        image_tab = ttk.Frame(right)
        right.add(image_tab, text='Image')
        self.canvas = ImageCanvas(image_tab, on_rectangle=self.add_target, on_motion=self._on_hover,
                                  on_right_click=self._on_pick_color)
        self.canvas.pack(fill='both', expand=True)
        self.readout_var = tk.StringVar(value='Hover over the image to read the colour of a pixel (H S V); '
                                              'right-click to use its hue as the custom particle colour.')
        ttk.Label(image_tab, textvariable=self.readout_var, padding=(4, 2)).pack(fill='x')
        results_tab = ttk.Frame(right)
        right.add(results_tab, text='Results')
        self.results_text = tk.Text(results_tab, wrap='word', font=('Consolas', 10))
        scroll = ttk.Scrollbar(results_tab, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.results_text.pack(fill='both', expand=True)
        self._set_results_text(
            'MIQUOD %s\n\n1. Open an image.\n2. Draw one or more target areas on it; each target has its own '
            'particle colour (choose it before drawing, or select the target and apply another one).\n3. Choose '
            'the data type and the parameters.\n4. Press Process.\n\nThe measures appear here. The Detection tab shows one '
            'intermediate image at a time, the Sequence tab shows every image generated for a target in order, '
            'and the Variograms tab plots the variograms of the concentration data. The buttons under 5. Results '
            'export the measures (JSON), the annotated image and all the images.' % __version__)
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
        sequence_tab = ttk.Frame(right)
        right.add(sequence_tab, text='Sequence')
        bar = ttk.Frame(sequence_tab, padding=4)
        bar.pack(fill='x')
        ttk.Label(bar, text='Target').pack(side='left')
        self.sequence_target_var = tk.StringVar()
        self.sequence_target_box = ttk.Combobox(bar, textvariable=self.sequence_target_var, state='readonly', width=8)
        self.sequence_target_box.pack(side='left', padx=4)
        self.sequence_target_box.bind('<<ComboboxSelected>>', lambda event: self._show_sequence())
        ttk.Label(bar, text='Every image generated for the target, in processing order. '
                            'Click one to open it in the Detection tab.').pack(side='left', padx=12)
        self.gallery = SequenceGallery(sequence_tab, on_click=self._open_stage)
        self.gallery.pack(fill='both', expand=True)
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
        self.hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        self.image_path = path
        self.targets = []
        self.target_colors = []
        self.target_areas = []
        self.target_split = []
        self.results = None
        self.sequence = {}
        self.annotated = None
        for button in (self.export_button, self.save_image_button, self.export_images_button):
            button.configure(state='disabled')
        self.stage_canvas.set_image(None)
        self.gallery.set_images({})
        self.image_label.configure(text='%s\n%d columns x %d rows' % (os.path.basename(path), image.shape[1],
                                                                       image.shape[0]))
        self.canvas.set_image(image)
        self._refresh_targets()
        self.notebook.select(0)
        self.status_var.set('Draw a target area on the image (click and drag). Each target has its own particle '
                            'colour.')

    # -- colours -------------------------------------------------------------------------------
    def _update_custom_state(self):
        state = 'normal' if self.color_var.get() == 'custom' else 'disabled'
        for widget in self.custom_widgets:
            widget.configure(state=state)

    def _current_color_spec(self):
        """Colour specification selected in the controls: a name or a custom hue dict."""
        if self.color_var.get() != 'custom':
            return self.color_var.get()
        return {'hue': int(self.hue_var.get()) % 180, 'tolerance': int(self.hue_tol_var.get()),
                's_min': int(self.s_min_var.get()), 'v_min': int(self.v_min_var.get())}

    def _current_area(self):
        """Blob area limits selected in the controls, validated."""
        low, high = int(self.area_min_var.get()), int(self.area_max_var.get())
        if low < 1 or high < low:
            raise ValueError('The blob area limits must satisfy 1 <= min <= max.')
        return [low, high]

    def _current_particle_settings(self):
        """(colour specification, area limits, split flag) selected in the controls."""
        try:
            return self._current_color_spec(), self._current_area(), bool(self.split_var.get())
        except tk.TclError:
            raise ValueError('Enter integer values for the custom hue, tolerance, S, V and the blob area limits.')

    def _show_color_in_controls(self, spec, area=None, split=None):
        if isinstance(spec, dict):
            self.color_var.set('custom')
            self.hue_var.set(spec['hue'])
            self.hue_tol_var.set(spec.get('tolerance', 10))
            self.s_min_var.set(spec.get('s_min', 100))
            self.v_min_var.set(spec.get('v_min', 100))
        else:
            self.color_var.set(spec)
        if area is not None:
            self.area_min_var.set(area[0])
            self.area_max_var.set(area[1])
        if split is not None:
            self.split_var.set(split)
        self._update_custom_state()

    @staticmethod
    def _describe_target(spec, area, split):
        return '%s, area %d-%d px%s' % (Mf.color_label(spec), area[0], area[1], ', split' if split else '')

    def apply_color_to_selected(self):
        selection = self.target_list.curselection()
        if not selection:
            messagebox.showinfo('MIQUOD', 'Select a target in the list first.')
            return
        try:
            spec, area, split = self._current_particle_settings()
        except ValueError as exc:
            messagebox.showerror('MIQUOD', str(exc))
            return
        j = selection[0]
        self.target_colors[j], self.target_areas[j], self.target_split[j] = spec, area, split
        self._refresh_targets(selected=j)
        self.status_var.set('Target %d: %s.' % (j, self._describe_target(spec, area, split)))

    def _on_hover(self, x, y):
        if self.hsv is None:
            return
        h, s, v = (int(c) for c in self.hsv[y, x])
        b, g, r = (int(c) for c in self.image[y, x])
        self.readout_var.set('x=%d  y=%d      H=%d  S=%d  V=%d      R=%d  G=%d  B=%d' % (x, y, h, s, v, r, g, b))

    def _on_pick_color(self, x, y):
        if self.hsv is None:
            return
        h, s, v = (int(c) for c in self.hsv[y, x])
        self.hue_var.set(h)
        self.color_var.set('custom')
        self._update_custom_state()
        message = 'Hue %d picked at (%d, %d) (S=%d, V=%d): custom colour set' % (h, x, y, s, v)
        try:
            spec = self._current_color_spec()
            area = Mf.measure_blob_area_at(self.image, x, y, spec)
        except (ValueError, tk.TclError):
            area = 0
        if area > 0:
            self.area_min_var.set(max(1, area // 4))
            self.area_max_var.set(area * 4)
            message += ', particle area about %d px, blob area limits set to %d-%d' % (area, max(1, area // 4),
                                                                                       area * 4)
        else:
            message += ' (the pixel is not inside the colour mask: lower the S or V minimum if needed)'
        selection = self.target_list.curselection()
        if selection:
            try:
                spec, area_limits, split = self._current_particle_settings()
            except ValueError as exc:
                messagebox.showerror('MIQUOD', str(exc))
                return
            j = selection[0]
            self.target_colors[j], self.target_areas[j], self.target_split[j] = spec, area_limits, split
            self._refresh_targets(selected=j)
            message += '; applied to target %d.' % j
        else:
            message += '; new targets will use it.'
        self.status_var.set(message)

    # -- targets -------------------------------------------------------------------------------
    def add_target(self, rect, color=None):
        if self.image is None:
            return
        try:
            Mf.BitMap(self.image).check_rectangle(rect)
            spec, area, split = self._current_particle_settings()
            if color is not None:
                spec = color
        except ValueError as exc:
            messagebox.showerror('MIQUOD', str(exc))
            return
        self.targets.append(rect)
        self.target_colors.append(spec)
        self.target_areas.append(area)
        self.target_split.append(split)
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
        for items in (self.targets, self.target_colors, self.target_areas, self.target_split):
            del items[selection[0]]
        self._refresh_targets()

    def clear_targets(self):
        self.targets = []
        self.target_colors = []
        self.target_areas = []
        self.target_split = []
        self._refresh_targets()

    def _refresh_targets(self, selected=None):
        if selected is None:
            selection = self.target_list.curselection()
            selected = selection[0] if selection else None
        self.target_list.delete(0, 'end')
        for i, rect in enumerate(self.targets):
            self.target_list.insert('end', 'Target %d: X=%d Y=%d W=%d H=%d   %s' % (
                i, rect.X, rect.Y, rect.Width, rect.Height,
                self._describe_target(self.target_colors[i], self.target_areas[i], self.target_split[i])))
        if selected is not None and selected < len(self.targets):
            self.target_list.selection_clear(0, 'end')
            self.target_list.selection_set(selected)
            rect = self.targets[selected]
            for var, value in zip(self.target_vars, rect.as_tuple()):
                var.set(str(value))
            self._show_color_in_controls(self.target_colors[selected], self.target_areas[selected],
                                         self.target_split[selected])
        self.canvas.set_rectangles(self.targets, selected)

    # ------------------------------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------------------------------
    def _settings(self):
        threshold = int(self.threshold_var.get())
        if not 0 <= threshold <= 255:
            raise ValueError('The gray threshold must be between 0 and 255.')
        return {'mode': self.mode_var.get(), 'threshold': threshold, 'dark': bool(self.dark_var.get())}

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
        for button in (self.export_button, self.save_image_button, self.export_images_button):
            button.configure(state='disabled')
        self.progress.start(12)
        self.status_var.set('Processing... particle data takes a few seconds, concentration data about half a '
                            'minute on large targets.')
        worker = threading.Thread(target=self._worker,
                                  args=(self.image, list(self.targets), list(self.target_colors),
                                        [list(a) for a in self.target_areas], list(self.target_split), settings),
                                  daemon=True)
        worker.start()

    def _worker(self, image, targets, colors, areas, splits, settings):
        output = {'settings': settings, 'target_colors': colors, 'target_areas': areas, 'target_split': splits}
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                if settings['mode'] in ('particles', 'both'):
                    try:
                        output['particles'] = Mf.run_particle_analysis(image, targets, settings['threshold'],
                                                                       collect_stages=True, colors=colors,
                                                                       area_limits=areas, split_touching=splits)
                    except Mf.NotEnoughParticles as exc:
                        # Keep what was detected so the user can see the mask and binary images and retune.
                        output['particle_error'] = str(exc)
                        output['partial_particles'] = {'particle_positions': exc.positions,
                                                       'detection_stages': exc.stages}
                if settings['mode'] in ('concentration', 'both'):
                    output['concentration'] = Mf.run_concentration_analysis(image, targets, settings['dark'],
                                                                            collect_stages=True)
            output['warnings'] = [str(w.message) for w in caught]
            self.queue.put(('ok', output))
        except ValueError as exc:  # invalid input or parameters: the message is enough
            self.queue.put(('error', str(exc), None))
        except Exception as exc:  # unexpected: keep the traceback for the console
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
            if self.results.get('particle_error'):
                self.status_var.set('Particle data not computed: %s' % self.results['particle_error'])
                messagebox.showwarning('MIQUOD', self.results['particle_error'] + '\n\nThe Sequence and Detection '
                                       'tabs show the mask and the binary image of each target. Adjust the gray '
                                       'threshold, the particle colour or the blob area limits and process again.')
            else:
                self.status_var.set('Done. See the Results tab; export with the buttons below.')
        else:
            self.status_var.set('Error: %s' % message[1])
            messagebox.showerror('MIQUOD', message[1])
            if message[2]:
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
        colors = results.get('target_colors', self.target_colors)
        areas = results.get('target_areas', self.target_areas)
        splits = results.get('target_split', self.target_split)
        lines = ['MIQUOD %s' % __version__, 'Image: %s' % self.image_path]
        for j, rect in enumerate(self.targets):
            lines.append('Target %d: X=%d Y=%d W=%d H=%d (X = column, Y = row), particles: %s'
                         % ((j,) + rect.as_tuple() + (self._describe_target(colors[j], areas[j], splits[j]),)))
        lines.append('')
        if 'particles' in results or 'particle_error' in results:
            lines.append('PARTICLE DATA (gray threshold %d)' % settings['threshold'])
        if 'particles' in results:
            lines.append(Mf.summarize_particle_results(results['particles'], ['Image']))
            for j, spacing in enumerate(results['particles']['mean_spacing'][0]):
                lines.append('  target %d: mean particle spacing %d px, transect %r' % (
                    j, spacing, results['particles']['transects'][0][j]))
            lines.append('')
        elif 'particle_error' in results:
            lines.append('  Not computed: %s' % results['particle_error'])
            for j, pts in enumerate(results['partial_particles']['particle_positions'][0]):
                lines.append('  target %d (%s): %d particles detected' % (j, Mf.color_label(colors[j]), len(pts)))
            lines.append('  Check the mask and binary images in the Sequence tab, then adjust the gray threshold, '
                         'the particle colour or the blob area limits and process again.')
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
        positions = None
        if 'particles' in results:
            positions = results['particles']['particle_positions'][0]
        elif 'partial_particles' in results:
            positions = results['partial_particles']['particle_positions'][0]
        if positions is not None:
            for j, rect in enumerate(self.targets):
                annotated = Mf.draw_particles(annotated, positions[j],
                                              radius=max(2, int(round(min(self.image.shape[:2]) / 400.0))),
                                              color=Mf.color_for_drawing(colors[j]), rect=rect)
        self.canvas.set_image(annotated)
        self.annotated = annotated
        self.sequence = self._build_sequence(results)
        target_ids = ['%d' % j for j in range(len(self.targets))]
        self.stage_target_box.configure(values=target_ids)
        self.sequence_target_box.configure(values=target_ids)
        self.stage_target_var.set('0')
        self.sequence_target_var.set('0')
        names = list(self.sequence[0])
        self.stage_box.configure(values=names)
        if names and self.stage_var.get() not in names:
            self.stage_var.set(names[-1])
        self._show_stage()
        self._show_sequence()
        self._plot_variograms()
        for button in (self.export_button, self.save_image_button, self.export_images_button):
            button.configure(state='normal')
        self.notebook.select(1)

    def _build_sequence(self, results):
        """Every image generated for each target, in processing order: ``{target: {name: image}}``."""
        sequence = {}
        stages = None
        if 'particles' in results:
            stages = results['particles']['detection_stages']
        elif 'partial_particles' in results:
            stages = results['partial_particles']['detection_stages']
        for j in range(len(self.targets)):
            images = {}
            if stages:
                images.update(stages[0][j])
            if 'concentration' in results:
                for name, image in results['concentration']['concentration_stages'][0][j].items():
                    if name not in images:
                        images[name] = image
            sequence[j] = images
        return sequence

    def _current_sequence(self, var):
        try:
            return self.sequence[int(var.get())]
        except (ValueError, KeyError):
            return {}

    def _show_stage(self):
        images = self._current_sequence(self.stage_target_var)
        image = images.get(self.stage_var.get())
        if image is None:
            self.stage_canvas.set_image(None)
            return
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        self.stage_canvas.set_image(image)

    def _show_sequence(self):
        self.gallery.set_images(self._current_sequence(self.sequence_target_var))

    def _open_stage(self, name):
        """Open the clicked image of the Sequence tab in the Detection tab."""
        self.stage_target_var.set(self.sequence_target_var.get())
        self.stage_box.configure(values=list(self._current_sequence(self.stage_target_var)))
        self.stage_var.set(name)
        self._show_stage()
        self.notebook.select(2)

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
        colors = self.results.get('target_colors', self.target_colors)
        areas = self.results.get('target_areas', self.target_areas)
        splits = self.results.get('target_split', self.target_split)
        report = {'miquod_version': __version__, 'image': self.image_path,
                  'image_size': {'columns': int(self.image.shape[1]), 'rows': int(self.image.shape[0])},
                  'targets': [{'rectangle': t.as_tuple(), 'color': Mf.color_label(c), 'color_spec': c,
                               'blob_area': list(a), 'split_touching': bool(s)}
                              for t, c, a, s in zip(self.targets, colors, areas, splits)],
                  'settings': self.results['settings'], 'warnings': self.results.get('warnings', [])}
        base = os.path.splitext(path)[0]
        if 'particles' in self.results:
            particles = dict(self.results['particles'])
            particles.pop('detection_stages', None)
            report['particles'] = particles
        elif 'particle_error' in self.results:
            report['particle_error'] = self.results['particle_error']
            report['partial_particles'] = {
                'particle_positions': self.results['partial_particles']['particle_positions']}
        if 'concentration' in self.results:
            concentration = dict(self.results['concentration'])
            concentration.pop('concentration_stages', None)
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

    def export_images(self):
        """Write every generated image of every target, one sequence sheet per target and the annotated image."""
        if not self.results or not self.sequence:
            return
        folder = filedialog.askdirectory(title='Export the images to a folder', mustexist=True)
        if not folder:
            return
        written = 0
        for j, images in self.sequence.items():
            for k, (name, image) in enumerate(images.items(), start=1):
                written += self._write_image(os.path.join(folder, 'target%d_%d_%s.png' % (j, k, name)), image)
            written += self._write_image(os.path.join(folder, 'target%d_sequence.png' % j), Mf.montage_images(images))
        if self.annotated is not None:
            written += self._write_image(os.path.join(folder, 'annotated_full_image.png'), self.annotated)
        self.status_var.set('%d images exported to %s' % (written, folder))

    def _write_image(self, path, image):
        if cv2.imwrite(path, image):
            return 1
        messagebox.showerror('MIQUOD', 'Could not write %s' % path)
        return 0

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
