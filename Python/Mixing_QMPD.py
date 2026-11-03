# -*- coding: utf-8 -*-
"""
Mixing_QMPD
===========

Python implementation of the MIQUOD mixing-quantification measures.

Adapted from MIQUOD v1.0 (C#, Hector Betancourt Cervantes, 2017) by Edisson Naula (2020).

Version 2.1 (2026) keeps the function names and the nested-list result layout of the original
port, and changes the following:

* Coordinates follow the C# / OpenCV convention (column first, see below) and particle
  positions are absolute image coordinates, as in the C# original.
* Every pixel and particle loop is vectorised with numpy. The formulas are unchanged, so the
  results are the same up to floating-point rounding, but a full-size image now takes seconds
  instead of hours on the concentration path.
* Runs with several images, several targets per image and calibration no longer crash.
* Invalid inputs (image not read, target outside the image, no particles detected, ...) raise
  ``ValueError`` with an explicit message instead of failing deep inside a loop.
* ``mixing_dim_particle_data`` and ``mixing_dim_concentration_data`` return their results as
  dictionaries (and still print a summary when ``verbose`` is true).
* The variogram term is ``(a - b)**2`` as in the C# original (the first port had ``a - b**2``).

Coordinate conventions (identical to C# ``System.Drawing`` and OpenCV)
----------------------------------------------------------------------
* ``Rectangle(X, Y, Width, Height)``: ``X`` is the column of the left edge, ``Y`` the row of the
  top edge, ``Width`` the number of columns and ``Height`` the number of rows. This is exactly
  the tuple returned by ``cv2.selectROI``.
* ``Point(X, Y)``: ``X`` is a column, ``Y`` a row. Particle positions are absolute coordinates of
  the full image, never relative to the target.
* ``BitMap.Width`` is the number of columns (``img.shape[1]``) and ``BitMap.Height`` the number
  of rows (``img.shape[0]``).
* Concentration arrays are indexed ``[x][y]``: the first index runs along the image width. Their
  shape is therefore ``(Width, Height)``, the transpose of the numpy crop, and the *horizontal*
  variogram runs along axis 0. This matches the ``[x, y]`` arrays of the C# code.

Result containers are nested lists indexed ``[image_index][target_index]``. Images that have no
concentration data (for example reference images used only for calibration) hold an empty list.
"""
__author__ = 'Edisson Naula'
__version__ = '2.1.0'

import math
import os
import warnings
from typing import Dict, List

import cv2
import numpy as np

# region C-like structures


class Point:
    """A point with ``X`` = column and ``Y`` = row (``System.Drawing.Point``)."""

    def __init__(self, *args):
        if len(args) == 1:
            self.init_from_hex(args[0])
        elif len(args) == 2:
            self.init_from_points(args[0], args[1])
        else:
            self.X = 0
            self.Y = 0

    def init_from_points(self, xin, yin):
        self.X = xin
        self.Y = yin

    def init_from_hex(self, dw):
        """Build the point from a packed 32-bit integer (low word X, high word Y), like C#."""
        tmp = hex(dw).split('x')
        if 4 < len(tmp[1]) < 9:
            lower = tmp[1][len(tmp[1]) - 4:]
            upper = tmp[1][0:len(tmp[1]) - 4]
        elif len(tmp[1]) < 4:
            lower = tmp[1]
            upper = '0'
        else:
            lower = tmp[1][len(tmp[1]) - 4:]
            upper = tmp[1][0:len(tmp[1]) - 8]
        self.X = int(lower, 16)
        self.Y = int(upper, 16)

    def as_tuple(self):
        return self.X, self.Y

    def __repr__(self):
        return 'Point(X=%r, Y=%r)' % (self.X, self.Y)


class ListPoints:
    def __init__(self, xin, yin):
        self.point = Point(xin, yin)

    def list_points(self, num):
        return [self.point for _ in range(num)]


class Rectangle:
    """Axis-aligned rectangle: ``X``/``Y`` top-left column/row, ``Width`` columns, ``Height`` rows."""

    def __init__(self, xin, yin, width, height):
        self.X = int(xin)
        self.Y = int(yin)
        self.Width = int(width)
        self.Height = int(height)
        if self.Width <= 0 or self.Height <= 0:
            raise ValueError('Rectangle width and height must be positive, got %r' % (self,))

    @property
    def right(self):
        """Column of the last pixel inside the rectangle."""
        return self.X + self.Width - 1

    @property
    def bottom(self):
        """Row of the last pixel inside the rectangle."""
        return self.Y + self.Height - 1

    @property
    def area(self):
        return self.Width * self.Height

    def contains(self, x, y):
        return self.X <= x <= self.right and self.Y <= y <= self.bottom

    def as_tuple(self):
        return self.X, self.Y, self.Width, self.Height

    def __repr__(self):
        return 'Rectangle(X=%d, Y=%d, Width=%d, Height=%d)' % self.as_tuple()


class Coordinate:
    def __init__(self, xin, yin):
        self.X = xin
        self.Y = yin

    def __repr__(self):
        return 'Coordinate(X=%r, Y=%r)' % (self.X, self.Y)


class Transect:
    def __init__(self, t_area, rect_in, msp):
        self.TargetArea = t_area
        self.Rect = rect_in
        self.MeanSpacingOfPart = msp


class RefImg:
    """Reference image used for calibration: ``ImageIndex`` into the image list, ``Concentration`` in %."""

    def __init__(self, idx, con):
        self.ImageIndex = idx
        self.Concentration = con

    def __repr__(self):
        return 'RefImg(ImageIndex=%r, Concentration=%r)' % (self.ImageIndex, self.Concentration)


class BitMap:
    """Wrapper around a numpy image with C#-like ``Width``/``Height``/``Clone``/``GetPixel`` semantics."""

    def __init__(self, img):
        if img is None:
            raise ValueError('BitMap received None: the image could not be read. '
                             'Check the path given to cv2.imread and the working directory.')
        img = np.asarray(img)
        if img.ndim not in (2, 3):
            raise ValueError('BitMap expects a 2-D (grayscale) or 3-D (colour) array, got shape %r' % (img.shape,))
        self.Img = img
        self.Height = int(img.shape[0])  # rows
        self.Width = int(img.shape[1])  # columns
        if img.ndim == 2:
            self.Dimension = 2
            self.R = img[0, 0]
            self.G = img[0, 0]
            self.B = img[0, 0]
        else:
            self.Dimension = int(img.shape[2])
            self.B = img[0, 0][0]
            self.G = img[0, 0][1]
            self.R = img[0, 0][2]

    def check_rectangle(self, rect, what='target area'):
        """Raise ``ValueError`` if ``rect`` does not lie completely inside the image."""
        if rect.X < 0 or rect.Y < 0 or rect.right >= self.Width or rect.bottom >= self.Height:
            raise ValueError('%s %r lies outside the image (%d columns x %d rows): columns %d-%d, rows %d-%d. '
                             'Rectangle is (X=column, Y=row, Width, Height) as returned by cv2.selectROI.'
                             % (what, rect, self.Width, self.Height, rect.X, rect.right, rect.Y, rect.bottom))

    def clone(self, rect):
        """Return the crop of ``rect`` (a view, like ``Bitmap.Clone``)."""
        self.check_rectangle(rect)
        return self.Img[rect.Y:rect.Y + rect.Height, rect.X:rect.X + rect.Width]

    def pixel(self, xin, yin, layer=''):
        """Pixel at column ``xin``, row ``yin``. ``layer`` selects 'R', 'G' or 'B' of a BGR image."""
        if self.Dimension == 2:
            return self.Img[yin, xin]
        channel = {'R': 2, 'G': 1, 'B': 0}.get(layer, 2)
        return self.Img[yin, xin][channel]

    def bitmaps(self, num):
        # type: (int) -> List[np.ndarray]
        return [self.Img for _ in range(num)]


# HSV ranges (OpenCV scale: H 0-179, S 0-255, V 0-255) used to isolate the dye of the particles.
# Each colour is a list of (lower, upper) bounds; red needs two because its hue wraps around 0.
COLOR_RANGES = {
    'red': [(np.array([0, 100, 100]), np.array([10, 255, 255])),
            (np.array([170, 100, 100]), np.array([179, 255, 255]))],
    'blue': [(np.array([85, 100, 100]), np.array([130, 255, 255]))],
    'green': [(np.array([50, 100, 100]), np.array([65, 255, 255]))],
    'yellow': [(np.array([18, 100, 100]), np.array([38, 255, 255]))],
}
# BGR colours used to draw the particles of each dye colour.
COLOR_DRAW = {'red': (0, 0, 255), 'blue': (255, 0, 0), 'green': (0, 255, 0), 'yellow': (0, 255, 255)}


def hsv_ranges_from_hue(hue, tolerance=10, s_min=100, v_min=100):
    """
    HSV ``(lower, upper)`` bounds for ``hue ± tolerance`` on OpenCV's 0-179 hue scale, with saturation and
    value of at least ``s_min`` and ``v_min``. Two ranges are returned when the interval wraps around 0.
    This is the rule of the Android app (``calculateHSVThreshold``) applied to the hue of the dye colour.
    """
    hue = int(round(hue)) % 180
    tolerance = int(tolerance)
    if tolerance < 0:
        raise ValueError('the hue tolerance must be positive')
    s_min, v_min = int(s_min), int(v_min)

    def bounds(low, high):
        return np.array([low, s_min, v_min]), np.array([high, 255, 255])

    if tolerance >= 90:
        return [bounds(0, 179)]
    low, high = hue - tolerance, hue + tolerance
    if low < 0:
        return [bounds(0, high), bounds(180 + low, 179)]
    if high > 179:
        return [bounds(low, 179), bounds(0, high - 180)]
    return [bounds(low, high)]


def resolve_color(color):
    """
    Turn a colour specification into a list of HSV ``(lower, upper)`` ranges. Accepted: a key of
    ``COLOR_RANGES``, one ``(lower, upper)`` pair, a list of pairs, or a dict with ``hue`` and optional
    ``tolerance``, ``s_min``, ``v_min`` (see ``hsv_ranges_from_hue``).
    """
    if isinstance(color, str):
        if color not in COLOR_RANGES:
            raise ValueError('unknown colour %r; choose one of %s' % (color, sorted(COLOR_RANGES)))
        return list(COLOR_RANGES[color])
    if isinstance(color, dict):
        return hsv_ranges_from_hue(color['hue'], color.get('tolerance', 10), color.get('s_min', 100),
                                   color.get('v_min', 100))
    ranges = list(color)
    if len(ranges) == 2 and np.ndim(ranges[0]) == 1:  # a single (lower, upper) pair
        ranges = [tuple(ranges)]
    return [(np.asarray(lower), np.asarray(upper)) for lower, upper in ranges]


def color_mask(hsv, color):
    """Binary mask (0/255) of the pixels of an HSV image that fall inside any range of the colour."""
    mask = None
    for lower, upper in resolve_color(color):
        part = cv2.inRange(hsv, lower, upper)
        mask = part if mask is None else cv2.bitwise_or(mask, part)
    return mask


def color_label(color):
    """Short text for a colour specification: 'red', 'hue 60 ±10' or 'custom'."""
    if isinstance(color, str):
        return color
    if isinstance(color, dict):
        return 'hue %d ±%d' % (int(round(color['hue'])) % 180, int(color.get('tolerance', 10)))
    return 'custom'


def color_for_drawing(color):
    """BGR colour used to draw the particles of a colour specification (the hue itself for custom hues)."""
    if isinstance(color, str):
        return COLOR_DRAW.get(color, (255, 255, 255))
    if isinstance(color, dict):
        pixel = np.array([[[int(round(color['hue'])) % 180, 255, 255]]], dtype=np.uint8)
        return tuple(int(v) for v in cv2.cvtColor(pixel, cv2.COLOR_HSV2BGR)[0, 0])
    return 255, 255, 255

# Blob detector settings used by MIQUOD for particle counting.
DEFAULT_DETECTOR_SETTINGS = dict(threshold=[150, 255], flag_area=True, limit_area=[1, 50],
                                 flag_circularity=False, min_cir=0.05, flag_convexity=False,
                                 convexity=[0.01, 1], flag_inertia=False, ratio_inertia=[0.0, 1],
                                 flag_color=False)


class BlobDetector:
    """
    Wrapper around ``cv2.SimpleBlobDetector`` tuned for this project.

    :param threshold: ``[minThreshold, maxThreshold]`` of the internal binarisation steps.
    :param flag_area: filter blobs by area, between ``limit_area[0]`` and ``limit_area[1]`` pixels.
    :param flag_circularity: filter by circularity (4*pi*Area/perimeter^2), minimum ``min_cir``.
    :param flag_convexity: filter by convexity (area / convex hull area) within ``convexity``.
    :param flag_inertia: filter by inertia ratio (elongation) within ``ratio_inertia``.
    :param flag_color: filter by colour; ``blobColor`` is 0 (dark blobs).
    """

    def __init__(self, threshold=None, flag_area=False, limit_area=None, flag_circularity=False, min_cir=0.1,
                 flag_convexity=False, convexity=None, flag_inertia=True, ratio_inertia=None,
                 flag_color=False):
        if ratio_inertia is None:
            ratio_inertia = [0.0, 0.5]
        if convexity is None:
            convexity = [0.0, 10]
        if limit_area is None:
            limit_area = [25, 25 * 35]
        if threshold is None:
            threshold = [120, 255]
        params = cv2.SimpleBlobDetector_Params()
        # Current OpenCV rejects a minimum of exactly 0 for these ratios, even when the filter is disabled.
        min_ratio = 1e-6

        params.minThreshold = threshold[0]
        params.maxThreshold = threshold[1]

        params.filterByArea = flag_area
        params.minArea = limit_area[0]
        params.maxArea = limit_area[1]

        params.filterByCircularity = flag_circularity
        params.minCircularity = max(min_cir, min_ratio)

        params.filterByConvexity = flag_convexity
        params.minConvexity = max(convexity[0], min_ratio)
        params.maxConvexity = convexity[1]

        params.filterByInertia = flag_inertia
        params.minInertiaRatio = max(ratio_inertia[0], min_ratio)
        params.maxInertiaRatio = ratio_inertia[1]

        params.filterByColor = flag_color
        params.blobColor = 0

        ver = cv2.__version__.split('.')
        if int(ver[0]) < 3:
            self.detector = cv2.SimpleBlobDetector(params)
        else:
            self.detector = cv2.SimpleBlobDetector_create(params)

    def detect_blobs(self, img):
        return self.detector.detect(img)

    @staticmethod
    def rectangles(points):
        return [Rectangle(int(item.pt[0] - item.size / 2), int(item.pt[1] - item.size / 2), item.size, item.size)
                for item in points]


# endregion
# region numpy helpers


def _points_to_array(points):
    """List of ``Point`` -> float array of shape (n, 2) with columns (X, Y)."""
    if len(points) == 0:
        return np.zeros((0, 2), dtype=np.float64)
    return np.array([(p.X, p.Y) for p in points], dtype=np.float64)


def _min_sq_dist_to_set(query, pts, exclude_self=False, chunk=512):
    """Minimum squared distance from each row of ``query`` to the rows of ``pts`` (chunked)."""
    out = np.empty(len(query), dtype=np.float64)
    for start in range(0, len(query), chunk):
        q = query[start:start + chunk]
        d2 = (q[:, None, 0] - pts[None, :, 0]) ** 2 + (q[:, None, 1] - pts[None, :, 1]) ** 2
        if exclude_self:
            idx = np.arange(len(q))
            d2[idx, start + idx] = np.inf
        out[start:start + chunk] = d2.min(axis=1)
    return out


def _crop(array, rect):
    """Crop a numpy image (rows, cols, ...) with a ``Rectangle``."""
    return array[rect.Y:rect.Y + rect.Height, rect.X:rect.X + rect.Width]


# endregion
# region Particle detection


def detect_particles_in_target(crop_bgr, threshold_value, color='red', detector=None, hsv_range=None):
    """
    Detect the particles of one target area.

    The pipeline is the one of MIQUOD v2.0: HSV mask of the dye colour, grayscale, 2x2 dilation and
    erosion, inverse binary threshold at ``threshold_value``, then ``cv2.SimpleBlobDetector``.

    :param crop_bgr: BGR crop of the target area.
    :param threshold_value: gray threshold (0-255) applied before blob detection.
    :param color: colour specification accepted by ``resolve_color``: a key of ``COLOR_RANGES`` ('red',
                  'blue', 'green', 'yellow'), HSV ``(lower, upper)`` ranges, or ``{'hue': h, ...}``.
    :param detector: a ``BlobDetector``; defaults to ``BlobDetector(**DEFAULT_DETECTOR_SETTINGS)``.
    :param hsv_range: optional colour specification overriding ``color`` (kept for compatibility).
    :return: ``(key_points, stages)`` where ``stages`` is an ordered dict of the intermediate images
             ('crop', 'mask', 'color', 'gray', 'binary', 'particles') relative to the crop.
    """
    if crop_bgr is None or crop_bgr.ndim != 3:
        raise ValueError('detect_particles_in_target needs a BGR colour image')
    if detector is None:
        detector = BlobDetector(**DEFAULT_DETECTOR_SETTINGS)
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    mask = color_mask(hsv, color if hsv_range is None else hsv_range)
    masked = cv2.bitwise_and(crop_bgr, crop_bgr, mask=mask)
    gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((2, 2), np.uint8)
    morph = cv2.dilate(gray, kernel, iterations=1)
    morph = cv2.erode(morph, kernel, iterations=1)
    _, binary = cv2.threshold(morph, threshold_value, 255, cv2.THRESH_BINARY_INV)
    key_points = detector.detect_blobs(binary)
    annotated = annotate_particles(crop_bgr, key_points)
    stages = {'crop': crop_bgr, 'mask': mask, 'color': masked, 'gray': gray, 'binary': binary,
              'particles': annotated}
    return key_points, stages


def annotate_particles(image_bgr, key_points, color=(255, 255, 255), thickness=4):
    """Return a copy of ``image_bgr`` with a circle drawn around each key point."""
    out = image_bgr.copy()
    for point in key_points:
        cv2.circle(out, (int(point.pt[0]), int(point.pt[1])), max(int(point.size), 1), color, thickness)
    return out


def draw_particles(image_bgr, points, radius=4, color=(255, 255, 255), thickness=2, rect=None):
    """Draw absolute particle positions (list of ``Point``) on a copy of the full image, optionally with the target."""
    out = image_bgr.copy()
    for p in points:
        cv2.circle(out, (int(p.X), int(p.Y)), radius, color, thickness)
    if rect is not None:
        cv2.rectangle(out, (rect.X, rect.Y), (rect.right, rect.bottom), (0, 255, 255), 3)
    return out


def show_detection_stages(stages, title=''):
    """Display the intermediate images of ``detect_particles_in_target`` with matplotlib (blocking)."""
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for ax, (name, im) in zip(axes.flat, stages.items()):
        if im.ndim == 3:
            ax.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        else:
            ax.imshow(im, cmap='gray')
        ax.set_title(name)
        ax.axis('off')
    fig.suptitle(title)
    plt.tight_layout()
    plt.show()


def montage_images(images, tile_width=480, columns=3, labels=True):
    """
    Arrange named images (dict name -> gray or BGR array) into one labelled BGR sheet, ``columns`` tiles
    per row, every tile scaled to ``tile_width`` pixels wide.
    """
    if not images:
        raise ValueError('montage_images needs at least one image')
    pad = 8
    label_h = 32 if labels else 0
    names = list(images)
    tiles = []
    for name in names:
        image = np.asarray(images[name])
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        h, w = image.shape[:2]
        tile_h = max(int(round(h * tile_width / float(w))), 1)
        tiles.append(cv2.resize(image, (tile_width, tile_h), interpolation=cv2.INTER_AREA))
    tile_height = max(tile.shape[0] for tile in tiles)
    columns = max(1, min(columns, len(tiles)))
    rows = (len(tiles) + columns - 1) // columns
    sheet = np.full((rows * (tile_height + label_h) + (rows + 1) * pad, columns * tile_width + (columns + 1) * pad, 3),
                    255, dtype=np.uint8)
    for idx, (name, tile) in enumerate(zip(names, tiles)):
        r, c = divmod(idx, columns)
        x0 = pad + c * (tile_width + pad)
        y0 = pad + r * (tile_height + label_h + pad) + label_h
        sheet[y0:y0 + tile.shape[0], x0:x0 + tile_width] = tile
        if labels:
            cv2.putText(sheet, str(name), (x0, y0 - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA)
    return sheet


def concentration_to_image(concentration, colormap=cv2.COLORMAP_JET):
    """
    Colour-map a concentration array (indexed ``[x][y]``, shape ``(Width, Height)``) into a BGR image
    oriented like the image crop (rows, columns). Values are scaled between their minimum and maximum.
    """
    data = np.asarray(concentration, dtype=np.float64).T
    finite = np.isfinite(data)
    if finite.any():
        lo, hi = float(data[finite].min()), float(data[finite].max())
    else:
        lo, hi = 0.0, 1.0
    scaled = (data - lo) / (hi - lo) if hi > lo else np.zeros_like(data)
    gray = np.clip(np.round(np.nan_to_num(scaled) * 255), 0, 255).astype(np.uint8)
    return cv2.applyColorMap(gray, colormap)


def concentration_stages(image_bgr, rect, concentration):
    """
    Intermediate images of the concentration path of one target: the crop, the median-filtered gray crop
    and the colour-mapped concentration array (dict 'crop', 'filtered', 'concentration').
    """
    bitmap = BitMap(image_bgr)
    crop = bitmap.clone(rect)
    filtered = filter_image(bitmap).clone(rect)
    return {'crop': crop, 'filtered': filtered, 'concentration': concentration_to_image(concentration)}


def blob_detection_image(img_to_process, threshold_value, store_target_areas, color='red', detector=None,
                         show=False, out_dir=None, verbose=True, stages_out=None, colors=None):
    """
    Detect the particles of every target of every image.

    :param img_to_process: list of ``BitMap``.
    :param threshold_value: gray threshold (0-255) applied before blob detection.
    :param store_target_areas: ``store_target_areas[image][target]`` -> ``Rectangle``.
    :param color: dye colour of the particles for every target (specification for ``resolve_color``).
    :param colors: optional nested list ``colors[image][target]`` of colour specifications, one per target,
                   which overrides ``color``.
    :param detector: optional ``BlobDetector`` (default ``DEFAULT_DETECTOR_SETTINGS``).
    :param show: display the intermediate images of each target with matplotlib (blocks).
    :param out_dir: if given, write the intermediate images there as
                    ``img{i}_target{j}_{k}_{stage}.jpg``.
    :param verbose: print the number of particles found in each target.
    :param stages_out: optional list; receives the intermediate images of every target as
                       ``stages_out[image][target]`` (dict, see ``detect_particles_in_target``).
    :return: ``(store_part_pos, store_blob_rectangles)``, both indexed ``[image][target]``.
             Particle positions are absolute ``Point(column, row)`` of the full image.
    """
    store_blob_rectangles = []  # type: List[List[List[Rectangle]]]
    store_part_pos = []  # type: List[List[List[Point]]]
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    for index, img in enumerate(img_to_process):
        if not isinstance(img, BitMap):
            raise TypeError('img_to_process must contain BitMap objects, got %r' % type(img))
        store_blob_rectangles.append([])
        store_part_pos.append([])
        if stages_out is not None:
            stages_out.append([])
        for trg_ind, area in enumerate(store_target_areas[index]):
            spec = color if colors is None else colors[index][trg_ind]
            crop = img.clone(area)
            key_points, stages = detect_particles_in_target(crop, threshold_value, spec, detector)
            if stages_out is not None:
                stages_out[index].append(stages)
            positions = [Point(area.X + int(kp.pt[0]), area.Y + int(kp.pt[1])) for kp in key_points]
            rectangles = [Rectangle(area.X + int(kp.pt[0] - kp.size / 2), area.Y + int(kp.pt[1] - kp.size / 2),
                                    max(kp.size, 1), max(kp.size, 1)) for kp in key_points]
            store_part_pos[index].append(positions)
            store_blob_rectangles[index].append(rectangles)
            if verbose:
                print('Image %d, target %d (%r, colour %s): %d particles detected'
                      % (index, trg_ind, area, color_label(spec), len(positions)))
            if len(positions) == 0:
                warnings.warn('Image %d, target %d: no particles detected; the particle measures cannot be '
                              'computed for this target (try another threshold or colour).' % (index, trg_ind))
            if out_dir:
                for k, (name, im) in enumerate(stages.items(), start=1):
                    cv2.imwrite(os.path.join(out_dir, 'img%d_target%d_%d_%s.jpg' % (index, trg_ind, k, name)), im)
                cv2.imwrite(os.path.join(out_dir, 'img%d_target%d_sequence.jpg' % (index, trg_ind)),
                            montage_images(stages))
            if show:
                show_detection_stages(stages, 'Image %d, target %d: %d particles' % (index, trg_ind, len(positions)))
    return store_part_pos, store_blob_rectangles


# endregion
# region Mixing quantification measures: particle data


def mixing_dim_particle_data(store_trg_areas, loaded_img_info, store_part_pos, max_striation_thick, verbose=True):
    """
    Compute every particle-data measure and return them in a dictionary.

    Keys: ``particle_concentration``, ``intensity_measures`` (``[σ, CoV, M, Cm, Cmax, Cmin, n, N]``),
    ``max_striation_thickness``, ``pnn_distribution``, ``scale_segregation_indexes``
    (``[σ_fpp, i_dis, xg]``) and ``pnn_parameters``; all indexed ``[image][target]``.
    """
    store_con_particle_data = get_concentration_from_particles(store_trg_areas, loaded_img_info, store_part_pos,
                                                               max_striation_thick)
    intensity_measures = segregation_intensity_ifp(store_con_particle_data, store_part_pos, store_trg_areas)
    store_max_str_thick = maximum_striation_thickness(max_striation_thick)
    pnn_distribution = pnn_method_distribution(store_trg_areas, store_part_pos)
    scl_segregation_ind, pnn_parameters = _scale_segregation_with_parameters(store_trg_areas, store_part_pos,
                                                                              pnn_distribution)
    results = {
        'particle_concentration': store_con_particle_data,
        'intensity_measures': intensity_measures,
        'max_striation_thickness': store_max_str_thick,
        'pnn_distribution': pnn_distribution,
        'scale_segregation_indexes': scl_segregation_ind,
        'pnn_parameters': pnn_parameters,
    }
    if verbose:
        print(summarize_particle_results(results, loaded_img_info))
    return results


def summarize_particle_results(results, loaded_img_info=None):
    """Human-readable summary of the dictionary returned by ``mixing_dim_particle_data``."""
    lines = []
    for i, per_image in enumerate(results['intensity_measures']):
        name = loaded_img_info[i] if loaded_img_info and i < len(loaded_img_info) else 'Img%d' % (i + 1)
        for j, im in enumerate(per_image):
            lines.append('%s, target %d (particle data)' % (name, j))
            lines.append('  Particles N: %d   quadrats n: %d   max. striation thickness: %s px'
                         % (im[7], im[6], results['max_striation_thickness'][i][j]))
            lines.append('  σ: %.6g   CoV: %.6g   M: %.6g' % (im[0], im[1], im[2]))
            lines.append('  Cm: %.6g   Cmax: %.6g   Cmin: %.6g' % (im[3], im[4], im[5]))
            s = results['scale_segregation_indexes'][i][j]
            lines.append('  σ_fpp: %.6g   i_dis: %.6g   xg: %.6g' % (s[0], s[1], s[2]))
    return '\n'.join(lines)


'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        REDUCTION IN THE SEGREGATION OF CONCENTRATION
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'''


def segregation_intensity_ifp(store_con_particle_data, store_part_positions, store_trg_areas):
    """
    CALCULATION OF SEGREGATION INTENSITY INDEX MEASURES (particle data)

    Input: concentration matrix (particles / area in each quadrat).
    Output: ``intensity_measures[image][target] = [σ, CoV, M, Cm, Cmax, Cmin, n, N]``
    (standard deviation, coefficient of variation, mixing index clamped at 0, mean concentration,
    maximum and minimum quadrat concentration, number of quadrats, number of particles).
    """
    intensity_measures = []
    for i, per_image in enumerate(store_con_particle_data):
        intensity_measures.append([])
        for j, item in enumerate(per_image):
            num_of_part = len(store_part_positions[i][j])
            tgt_area = store_trg_areas[i][j].Width * store_trg_areas[i][j].Height
            stat_measure = statistical_measures_particles(item, tgt_area, num_of_part)
            cm = stat_measure[0]
            st_dev = stat_measure[1]
            cov = 0
            m = 1
            if st_dev > 0:
                cov = st_dev / cm
                m = 1 - cov
                m = 0 if m < 0 else m
            intensity_measures[i].append([st_dev, cov, m, cm, stat_measure[3], stat_measure[2], stat_measure[4],
                                          num_of_part])
    return intensity_measures


'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        REDUCTION IN THE SCALE OF CONCENTRATION
   %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'''


def maximum_striation_thickness(max_str_thick):
    """Copy ``max_str_thick[image][target]`` (kept for compatibility with the original flow)."""
    return [[int(item) for item in per_image] for per_image in max_str_thick]


def pnn_method_distribution(store_trg_areas, store_part_pos):
    """
    CALCULATION OF THE PNN METHOD (Kukukova, 2011)

    For every point of the ideal hexagonal grid of a target, the distance ``xi`` to the closest
    detected particle (bounded by the target diagonal).
    Output: ``pnn_distribution[image][target]`` = numpy array of ``xi``.
    """
    pnn_distribution = []
    for i, per_image in enumerate(store_trg_areas):
        pnn_distribution.append([])
        for j, item in enumerate(per_image):
            pts = _points_to_array(store_part_pos[i][j])
            if len(pts) == 0:
                raise ValueError('Image %d, target %d: no particles detected, the PNN distribution cannot be '
                                 'computed' % (i, j))
            grid = _points_to_array(ideal_particle_position(item, len(pts)))
            bound = math.sqrt(math.pow(item.Width, 2) + math.pow(item.Height, 2))
            xi = np.minimum(np.sqrt(_min_sq_dist_to_set(grid, pts)), bound)
            pnn_distribution[i].append(xi)
    return pnn_distribution


def _scale_of_segregation(num_of_part, item, xi):
    """Scale-of-segregation indexes of one target plus the intermediate PNN parameters."""
    k = int(math.sqrt(num_of_part))
    m = len(xi)
    if k < 2 or m < 2:
        raise ValueError('At least 4 particles are needed for the scale of segregation (PNN method), '
                         '%d detected' % num_of_part)
    dx = item.Width / (k * 1.0)
    dy = item.Height / (k * 1.0)
    xg = float((dx + 2 * math.sqrt(dx * dx + dy * dy)) / (3 * 1.0))  # spatial resolution
    xr = xg / 2  # one half of the spatial resolution
    above = xi[xi >= xr]
    xs = float(np.sum((above - xr) ** 2))
    xi_mean = float(np.sum(xi)) / (m * 1.0)
    var_fpp = xs / ((m * 1.0) - 1)
    if xi_mean == 0:
        raise ValueError('Every grid point coincides with a particle: the index of dispersion is undefined')
    i_dis = var_fpp / xi_mean
    params = {'xr': xr, 'xg': xg, 'dx': dx, 'dy': dy, 'k': k, 'xs': xs, 'var_fpp': var_fpp,
              'xi_mean': xi_mean, 'm': m}
    return [math.sqrt(var_fpp), i_dis, xg], params


def _scale_segregation_with_parameters(store_trg_areas, store_part_pos, pnn_distribution):
    scl_segregation_ind = []
    parameters = []
    for i, per_image in enumerate(store_trg_areas):
        scl_segregation_ind.append([])
        parameters.append([])
        for j, item in enumerate(per_image):
            scale_dim, params = _scale_of_segregation(len(store_part_pos[i][j]), item, pnn_distribution[i][j])
            scl_segregation_ind[i].append(scale_dim)
            parameters[i].append(params)
    return scl_segregation_ind, parameters


def scale_segregation_for_particles(store_trg_areas, store_part_pos, pnn_distribution):
    """
    CALCULATION OF SCALE OF SEGREGATION MEASURES (Kukukova 2011)

    Output: ``scl_segregation_ind[image][target] = [σ_fpp, i_dis, xg]``
    (filtered point-particle deviation, index of dispersion, spatial resolution).
    """
    return _scale_segregation_with_parameters(store_trg_areas, store_part_pos, pnn_distribution)[0]


# endregion
# region Auxiliary functions for particle tracking calculations


def calculate_mean_spacing(img_ind, trg, img_to_process, store_part_pos):
    """
    Twice the mean (integer-truncated) nearest-neighbour distance between the particles of a target.
    The distance of each particle is bounded by the image diagonal, as in the C# original.
    """
    pts = _points_to_array(store_part_pos[img_ind][trg])
    n = len(pts)
    if n < 2:
        raise ValueError('Image %d, target %d: at least two particles are needed to compute the mean spacing, '
                         '%d detected' % (img_ind, trg, n))
    image = img_to_process[img_ind]
    bound = int(math.sqrt(math.pow(image.Width, 2) + math.pow(image.Height, 2)))
    nearest = np.floor(np.sqrt(_min_sq_dist_to_set(pts, pts, exclude_self=True)))
    mean_s = np.minimum(nearest, bound)
    mean_spa = int(mean_s.sum() / n)
    return mean_spa * 2


def _striation_from_sorted(values, m_part_spacing):
    """Maximum striation thickness of sorted 1-D coordinates: longest run of gaps <= spacing."""
    if values.size <= 1:
        return int(m_part_spacing)
    gaps = np.diff(values)
    cut = np.flatnonzero(gaps > m_part_spacing)
    starts = np.concatenate(([0], cut + 1))
    ends = np.concatenate((cut, [values.size - 1]))
    mst = int((values[ends] - values[starts]).max())
    return max(mst, int(m_part_spacing))


def _max_striation_in_transect(pts, transect, horizontal, m_part_spacing):
    inside = ((pts[:, 0] >= transect.X) & (pts[:, 0] <= transect.right) &
              (pts[:, 1] >= transect.Y) & (pts[:, 1] <= transect.bottom))
    values = np.sort(pts[inside, 0] if horizontal else pts[inside, 1])
    return _striation_from_sorted(values, m_part_spacing)


def _scan_transects(pts, rect, mean_s, horizontal=True):
    """Slide a transect of thickness ``mean_s`` over the target; return the largest striation and its transect."""
    x, y, width_t, height_t = rect.X, rect.Y, rect.Width, rect.Height
    if horizontal:
        height, width, ini, limit = mean_s, width_t, y, y + height_t - 1 - mean_s
        axis, other, lo_other, hi_other = 1, 0, x, rect.right
    else:
        height, width, ini, limit = height_t, mean_s, x, x + width_t - 1 - mean_s
        axis, other, lo_other, hi_other = 0, 1, y, rect.bottom
    keep = (pts[:, other] >= lo_other) & (pts[:, other] <= hi_other)
    p = pts[keep]
    p = p[np.argsort(p[:, axis], kind='stable')]
    band = p[:, axis]
    thickness = height if horizontal else width
    mst = int(mean_s)
    best = None
    last = None
    for j in range(ini, limit):
        lo = np.searchsorted(band, j, 'left')
        hi = np.searchsorted(band, j + thickness - 1, 'right')
        mst_evl = _striation_from_sorted(np.sort(p[lo:hi, other]), mean_s)
        last = Rectangle(x, j, width, height) if horizontal else Rectangle(j, y, width, height)
        if mst_evl > mst:
            mst = mst_evl
            best = last
    if best is None:
        best = last if last is not None else Rectangle(x, y, width, height)
    return mst, best


def initiate_max_str_thickness(img_to_process, store_part_pos, store_trg_areas, horizontal=True):
    """
    Mean particle spacing and maximum striation thickness of every target.

    Transects of thickness equal to the mean spacing are slid over the whole target (row by row for
    ``horizontal``) and the largest striation thickness found is kept.
    :return: ``(mean_spacing, defined_transects, max_str_thickness)``, each indexed ``[image][target]``.
             ``defined_transects`` holds the transect where the maximum was found.
    """
    defined_transects = []
    m_part_spacing = []
    max_str_thickness = []
    for img_ind in range(len(img_to_process)):
        defined_transects.append([])
        max_str_thickness.append([])
        m_part_spacing.append([])
        for tgt_ind, rect in enumerate(store_trg_areas[img_ind]):
            img_to_process[img_ind].check_rectangle(rect)
            mean_s = calculate_mean_spacing(img_ind, tgt_ind, img_to_process, store_part_pos)
            pts = _points_to_array(store_part_pos[img_ind][tgt_ind])
            mst, transect = _scan_transects(pts, rect, mean_s, horizontal)
            m_part_spacing[img_ind].append(mean_s)
            defined_transects[img_ind].append(transect)
            max_str_thickness[img_ind].append(mst)
    return m_part_spacing, defined_transects, max_str_thickness


def calculate_max_str_thickness(img_ind, trg_ind, m_part_spacing, store_part_pos, defined_transects, store_trg_areas):
    """Maximum striation thickness of the particles inside ``defined_transects[img_ind][trg_ind]``."""
    transect = defined_transects[img_ind][trg_ind]
    horizontal = transect.Height != store_trg_areas[img_ind][trg_ind].Height
    pts = _points_to_array(store_part_pos[img_ind][trg_ind])
    return _max_striation_in_transect(pts, transect, horizontal, m_part_spacing)


def get_concentration_from_particles(store_target_areas, loaded_image_info, store_part_positions,
                                     max_striation_thickness):
    """
    Particle concentration matrix of every target: the target is divided into square quadrats of
    side equal to the maximum striation thickness (centred in the target) and each quadrat holds
    ``particles / quadrat area``. Output shape is ``(columns, rows)`` of quadrats, indexed ``[x][y]``.
    """
    store_con_particle_data = []
    for i, per_image in enumerate(store_target_areas):
        store_con_particle_data.append([])
        for j, item in enumerate(per_image):
            mst = int(max_striation_thickness[i][j])
            width, height = item.Width, item.Height
            col = math.floor(width / mst)
            row = math.floor(height / mst)
            if col < 1 or row < 1:
                raise ValueError('Image %d, target %d: the maximum striation thickness (%d px) is larger than the '
                                 'target (%d x %d px); no quadrat fits' % (i, j, mst, width, height))
            pts = _points_to_array(store_part_positions[i][j]).astype(np.int64)
            # quadrat (m-1, n-1) covers x in [X + dist_x + (m-1)*mst - 1, X + dist_x + m*mst - 1)
            # with dist_x = (width - col*mst) / 2; computed with integers (times 2) to avoid rounding.
            bx = (2 * pts[:, 0] - 2 * item.X - (width - col * mst) + 2) // (2 * mst)
            by = (2 * pts[:, 1] - 2 * item.Y - (height - row * mst) + 2) // (2 * mst)
            valid = (bx >= 0) & (bx < col) & (by >= 0) & (by < row)
            counts = np.zeros((col, row), dtype=np.float64)
            np.add.at(counts, (bx[valid], by[valid]), 1.0)
            store_con_particle_data[i].append(counts / float(mst * mst))
    return store_con_particle_data


def statistical_measures_particles(data, target_area, num_of_particles):
    """
    ``[μ, σ, x_min, x_max, n]`` of a particle concentration matrix, where ``μ`` is the global
    concentration ``num_of_particles / target_area`` and ``σ`` the population deviation about it.
    """
    data = np.asarray(data, dtype=np.float64)
    if data.size == 0:
        raise ValueError('the particle concentration matrix is empty')
    mean_v = num_of_particles / float(target_area)
    st_dev = math.sqrt(float(np.sum((data - mean_v) ** 2)) / data.size)
    x_max = max(0.0, float(data.max()))
    x_min = float(data.min())
    return [mean_v, st_dev, x_min, x_max, data.size]


def ideal_particle_position(tgt_area, num_of_part):
    """
    Ideal hexagonal grid of ``k*k`` points (``k = int(sqrt(num_of_part))``) inside the target.
    Odd rows are shifted by half the horizontal spacing. Returns a list of ``Point`` (floats).
    """
    k = int(num_of_part ** 0.5)
    if k < 1:
        raise ValueError('at least one particle is needed to build the hexagonal grid')
    x, y, width, height = tgt_area.X, tgt_area.Y, tgt_area.Width, tgt_area.Height
    dist_x = width / (k * 1.0)
    dist = (width - int(math.ceil((dist_x - 1) / 2.0)) - (k - 1) * dist_x) / 2.0
    ini_x = x + int(math.ceil(dist))
    dist_y = height / (k * 1.0)
    dist = int(math.ceil(((height - dist_y * k) / 2.0)))
    ini_y = y + dist + int(math.ceil(dist_y / 2.0))
    n = np.arange(k)[:, None]
    m = np.arange(k)[None, :]
    y_part = np.broadcast_to(ini_y + n * dist_y, (k, k))
    x_part = np.where(n % 2 == 0, ini_x + m * dist_x, (ini_x + dist_x / 2) + (m * dist_x))
    return [Point(float(xp), float(yp)) for xp, yp in zip(x_part.ravel(), y_part.ravel())]


# endregion
# region Mixing quantification measures: concentration data


def mixing_dim_concentration_data(img_to_process, store_target_areas, store_concentration_data=None,
                                  images_with_references=None, loaded_img_info=None, dark_checkbox=False,
                                  intensity_measures=None, hor_var_diagrams=None, ver_var_diagrams=None,
                                  verbose=True):
    """
    Compute every concentration-data measure and return them in a dictionary.

    ``store_concentration_data``, ``intensity_measures``, ``hor_var_diagrams`` and ``ver_var_diagrams``
    are accepted for compatibility with MIQUOD v2.0 scripts and ignored.

    Keys: ``concentration_data``, ``intensity_measures`` (``[σ, CoV, M, Cm, Cmax, Cmin, n]``),
    ``horizontal_variograms``, ``vertical_variograms``, ``mean_length_scales`` (``Coordinate`` with
    ``X`` horizontal and ``Y`` vertical), ``exposure_indexes`` and ``need_for_inlets``.
    """
    concentration = concentration_matrix(img_to_process, store_target_areas, None, images_with_references,
                                         loaded_img_info, dark_checkbox)
    measures = segregation_intensity_index_factors(None, img_to_process, concentration)
    hor = horizontal_var_diagram(None, concentration, img_to_process, measures)
    ver = vertical_var_diagram(None, img_to_process, concentration, measures)
    lengths = mean_length_scales(img_to_process, concentration, measures, hor, ver)
    exposure = calculate_exposure_indexes(img_to_process, concentration)
    need_for_inlets = any(item[1] > 1 for per_image in measures for item in per_image)
    results = {
        'concentration_data': concentration,
        'intensity_measures': measures,
        'horizontal_variograms': hor,
        'vertical_variograms': ver,
        'mean_length_scales': lengths,
        'exposure_indexes': exposure,
        'need_for_inlets': need_for_inlets,
    }
    if verbose:
        print(summarize_concentration_results(results, loaded_img_info))
    return results


def summarize_concentration_results(results, loaded_img_info=None):
    """Human-readable summary of the dictionary returned by ``mixing_dim_concentration_data``."""
    lines = []
    for i, per_image in enumerate(results['intensity_measures']):
        name = loaded_img_info[i] if loaded_img_info and i < len(loaded_img_info) else 'Img%d' % (i + 1)
        for j, im in enumerate(per_image):
            lines.append('%s, target %d (concentration data)' % (name, j))
            lines.append('  σ: %.6g   CoV: %.6g   M: %.6g   n: %d' % (im[0], im[1], im[2], im[6]))
            lines.append('  Cm: %.6g   Cmax: %.6g   Cmin: %.6g' % (im[3], im[4], im[5]))
            lms = results['mean_length_scales'][i][j]
            lines.append('  mean length scale horizontal: %.6g   vertical: %.6g' % (lms.X, lms.Y))
            lines.append('  exposure: %.6g' % results['exposure_indexes'][i][j])
    if results.get('need_for_inlets'):
        lines.append('There are negative mixing indexes (M < 0): define the unmixed condition (inlets) to '
                     'normalise the CoV.')
    return '\n'.join(lines)


def _same_sizes_for_calibration(img_to_process, store_trg_areas, images_with_references):
    """True when every image has the same size and target sizes as its reference images."""
    for i, refs in enumerate(images_with_references):
        for ref in refs:
            a, b = img_to_process[i], img_to_process[ref.ImageIndex]
            if a.Width != b.Width or a.Height != b.Height:
                return False
            if len(store_trg_areas[ref.ImageIndex]) < len(store_trg_areas[i]):
                return False
            for j, rect in enumerate(store_trg_areas[i]):
                other = store_trg_areas[ref.ImageIndex][j]
                if rect.Width != other.Width or rect.Height != other.Height:
                    return False
    return True


def concentration_matrix(img_to_process, store_trg_areas, store_concentration_data=None, images_with_references=None,
                         loaded_image_info=None, dark_checkbox=False):
    """
    Concentration array of every target, indexed ``[image][target]`` with shape ``(Width, Height)``.

    * Without calibration (any image with a single reference, or not enough references), the gray
      intensity of the median-filtered image is normalised with the minimum and maximum intensity of
      the whole image: ``c = (I - Imin) / (Imax - Imin)`` (``1 - c`` when ``dark_checkbox``).
    * With calibration, every image to be calibrated needs at least two ``RefImg`` (reference images of
      known concentration, in %). If all images and targets have the same size a linear regression
      intensity -> concentration is fitted pixel by pixel ("complex" calibration); otherwise one
      regression per target uses the mean intensity of the reference targets ("simple" calibration).
      Images without references (the reference images themselves) get an empty list.
    """
    n_img = len(img_to_process)
    if images_with_references is None:
        images_with_references = [[] for _ in range(n_img)]
    if loaded_image_info is None:
        loaded_image_info = ['Img%d' % (i + 1) for i in range(n_img)]
    result = [[] for _ in range(n_img)]  # type: List[List[np.ndarray]]
    for i in range(n_img):
        for rect in store_trg_areas[i]:
            img_to_process[i].check_rectangle(rect)

    # Determine whether the images have to be calibrated (same rules as MIQUOD v1.0).
    cal_performed = True
    ims_in_calibration = 0
    for refs in images_with_references:
        if len(refs) == 1:
            cal_performed = False
        if len(refs) > 1:
            ims_in_calibration = ims_in_calibration + len(refs) + 1
    if ims_in_calibration < len(loaded_image_info):
        cal_performed = False

    if cal_performed:
        filtered_cache = {}  # type: Dict[int, np.ndarray]

        def filtered(index):
            if index not in filtered_cache:
                filtered_cache[index] = filter_image(img_to_process[index]).Img.astype(np.float64)
            return filtered_cache[index]

        same_sizes = _same_sizes_for_calibration(img_to_process, store_trg_areas, images_with_references)
        for img in range(n_img):
            refs = images_with_references[img]
            if len(refs) == 0:
                continue
            kk = len(refs)
            c = np.array([ref.Concentration / 100.0 for ref in refs], dtype=np.float64)
            c_mean = float(np.sum(c)) / kk
            sc = float(np.sum((c - c_mean) ** 2))
            assessed = filtered(img)
            for j, rect in enumerate(store_trg_areas[img]):
                intensity = _crop(assessed, rect)
                if same_sizes:
                    # COMPLEX calibration: one linear regression per pixel.
                    stack = np.stack([_crop(filtered(ref.ImageIndex), rect) for ref in refs])  # (kk, rows, cols)
                    i_mean = np.sum(stack, axis=0) / kk
                    dev = stack - i_mean
                    si = np.sum(dev ** 2, axis=0)
                    r = np.sum((c - c_mean)[:, None, None] * dev, axis=0)
                    con = np.full(intensity.shape, c_mean, dtype=np.float64)
                    ok = (si != 0) & (sc != 0)
                    if np.any(ok):
                        r_ok = r[ok] / np.sqrt(sc * si[ok])
                        b = r_ok * math.sqrt(sc / (kk - 1)) / np.sqrt(si[ok] / (kk - 1))
                        a = c_mean - b * i_mean[ok]
                        con[ok] = b * intensity[ok] + a
                else:
                    # SIMPLE calibration: one regression per target on the mean intensity of the references.
                    means = []
                    for ref in refs:
                        if j >= len(store_trg_areas[ref.ImageIndex]):
                            raise ValueError('Reference image %d has no target %d; every reference needs the same '
                                             'number of targets as the image it calibrates' % (ref.ImageIndex, j))
                        means.append(get_mean_intensity_value(ref.ImageIndex, j, img_to_process, store_trg_areas))
                    means = np.array(means, dtype=np.float64)
                    i_mean = float(np.sum(means)) / kk
                    si = float(np.sum((means - i_mean) ** 2))
                    r = float(np.sum((c - c_mean) * (means - i_mean)))
                    if sc == 0 or si == 0:
                        con = np.full(intensity.shape, c_mean, dtype=np.float64)
                    else:
                        r = r / math.sqrt(sc * si)
                        b = r * math.sqrt(sc / (kk - 1)) / math.sqrt(si / (kk - 1))
                        a = c_mean - b * i_mean
                        con = b * intensity + a
                result[img].append(np.ascontiguousarray(con.T))
    else:
        # Without calibration: normalisation of the gray intensities of each image.
        for i in range(n_img):
            filtered_image = filter_image(img_to_process[i])
            i_max_min = get_intensity_max_min(filtered_image)
            i_max = float(i_max_min.X)
            i_min = float(i_max_min.Y)
            if i_max == i_min:
                raise ValueError('Image %d (%s) has a uniform intensity (%g); it cannot be normalised'
                                 % (i, loaded_image_info[i], i_max))
            gray = filtered_image.Img.astype(np.float64)
            for rect in store_trg_areas[i]:
                con = (_crop(gray, rect) - i_min) / ((i_max - i_min) * 1.0)
                if dark_checkbox:
                    con = 1 - con  # dark areas carry the higher concentration
                result[i].append(np.ascontiguousarray(con.T))
    return result


'''/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
REDUCTION IN THE SEGREGATION OF CONCENTRATION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/'''


def segregation_intensity_index_factors(intensity_measures, img_to_process, store_con_data):
    """
    CALCULATION OF SEGREGATION INTENSITY INDEX MEASURES (concentration data)

    Output: ``intensity_measures[image][target] = [σ, CoV, M, Cm, Cmax, Cmin, n]``
    (standard deviation, coefficient of variation, mixing index ``1 - CoV``, mean concentration,
    maximum and minimum concentration, number of pixels). ``intensity_measures`` (first argument) is
    ignored and kept for compatibility.

    Hector Betancourt Cervantes, 2017
    """
    result = []
    for i in range(len(img_to_process)):
        result.append([])
        if i >= len(store_con_data):
            continue
        for j, item in enumerate(store_con_data[i]):
            stat_measure = statistical_measures(item)
            cm = stat_measure[0] * 1.0
            st_dev = stat_measure[1] * 1.0
            cov = 0.0
            m = 1.0
            if st_dev > 0:
                if cm == 0:
                    raise ValueError('Image %d, target %d: the mean concentration is zero, the coefficient of '
                                     'variation is undefined' % (i, j))
                cov = st_dev / cm
                m = 1 - cov
            result[i].append([st_dev, cov, m, cm, stat_measure[3] * 1.0, stat_measure[2] * 1.0,
                              stat_measure[4] * 1.0])
    return result


'''/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
REDUCTION IN THE SCALE OF CONCENTRATION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/'''


def _variogram(standard_data, axis):
    """γ(h) = Σ (z(s) - z(s+h))² / (2 N(h)) for h = 0 .. floor(length/2) along ``axis``."""
    data = np.ascontiguousarray(standard_data if axis == 0 else standard_data.T, dtype=np.float64)
    length, other = data.shape
    max_h = int(math.floor(length / 2.0))
    variogram = np.zeros(max_h + 1)
    for dist in range(1, max_h + 1):
        diff = data[dist:, :] - data[:-dist, :]
        nh = (length - dist) * other
        variogram[dist] = float(np.einsum('ij,ij->', diff, diff)) / (2 * nh)
    return variogram


def horizontal_var_diagram(hor_var_diagrams, store_con_data, img_to_process, intensity_measures):
    """
    HORIZONTAL VARIOGRAM (Kukukova, 2010) of the standardised concentration matrix, along the image width
    (axis 0 of the ``[x][y]`` arrays). ``hor_var_diagrams`` is ignored (compatibility).
    Output: ``[image][target]`` -> numpy array ``γx(h)``, ``h = 0 .. Width // 2``.
    """
    result = []
    for i in range(len(img_to_process)):
        result.append([])
        if i >= len(store_con_data):
            continue
        for j in range(len(store_con_data[i])):
            result[i].append(_variogram(standarized_array(i, j, store_con_data, intensity_measures), axis=0))
    return result


def vertical_var_diagram(ver_var_diagrams, img_to_process, store_con_data, intensity_measures):
    """
    VERTICAL VARIOGRAM (Kukukova, 2010) of the standardised concentration matrix, along the image height
    (axis 1 of the ``[x][y]`` arrays). ``ver_var_diagrams`` is ignored (compatibility).
    Output: ``[image][target]`` -> numpy array ``γy(h)``, ``h = 0 .. Height // 2``.
    """
    result = []
    for i in range(len(img_to_process)):
        result.append([])
        if i >= len(store_con_data):
            continue
        for j in range(len(store_con_data[i])):
            result[i].append(_variogram(standarized_array(i, j, store_con_data, intensity_measures), axis=1))
    return result


def mean_length_scales(img_to_process, store_concentration_data, intensity_measures, hor_var_diagrams,
                       ver_var_diagrams):
    """
    MEAN LENGTH SCALE (Kukukova, 2010): ``L = p / (dγ/dh at h=0)`` with ``p`` the mean concentration
    and the slope taken as ``γ(1) - γ(0)``. Output: ``[image][target]`` -> ``Coordinate(X=horizontal,
    Y=vertical)`` in pixels.
    """
    result = []
    for i in range(len(img_to_process)):
        result.append([])
        if i >= len(store_concentration_data):
            continue
        for j in range(len(store_concentration_data[i])):
            p = intensity_measures[i][j][3]
            hor, ver = hor_var_diagrams[i][j], ver_var_diagrams[i][j]
            if len(hor) < 2 or len(ver) < 2:
                raise ValueError('Image %d, target %d: the target is too small for a variogram (needs at least '
                                 '2 x 2 pixels)' % (i, j))
            scales = []
            for name, variogram in (('horizontal', hor), ('vertical', ver)):
                slope = variogram[1] - variogram[0]
                if slope == 0:
                    # No variation along this direction (for example perfect stripes): the length scale is
                    # unbounded, as the C# double division gives Infinity.
                    warnings.warn('Image %d, target %d: the %s variogram slope at h=1 is zero, the %s mean '
                                  'length scale is infinite' % (i, j, name, name))
                    scales.append(math.inf if p >= 0 else -math.inf)
                else:
                    scales.append(p * (1 / slope))
            result[i].append(Coordinate(scales[0], scales[1]))
    return result


'''/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
RATE OF CHANGE IN SEGREGATION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/'''


def calculate_exposure_indexes(img_to_process, store_concentration_data):
    """
    EXPOSURE (Kukukova, 2009): ``E = Σ Σ ½ |Ci - Cj|`` over the 4-neighbours of every pixel, which equals
    the sum of the absolute concentration differences between every pair of adjacent pixels.
    Output: ``[image][target]`` -> float.
    """
    result = []
    for i in range(len(img_to_process)):
        result.append([])
        if i >= len(store_concentration_data):
            continue
        for data in store_concentration_data[i]:
            data = np.asarray(data, dtype=np.float64)
            exp = float(np.sum(np.abs(np.diff(data, axis=0)))) + float(np.sum(np.abs(np.diff(data, axis=1))))
            result[i].append(exp)
    return result


# endregion
# region Auxiliary functions and intensity information arrays


def filter_image(img_ori):
    """Median filter (5x5) followed by grayscale conversion; returns a ``BitMap``."""
    filtered_image = img_ori.clone(Rectangle(0, 0, img_ori.Width, img_ori.Height))
    filtered_image = cv2.medianBlur(np.ascontiguousarray(filtered_image), 5)
    if filtered_image.ndim == 3:
        filtered_image = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2GRAY)
    return BitMap(filtered_image)


def get_mean_intensity_value(img_index, target, img_to_process, store_target_areas):
    """Mean gray intensity of a target of a (reference) image after ``filter_image``."""
    rect = store_target_areas[img_index][target]
    filtered = filter_image(img_to_process[img_index])
    return float(np.mean(filtered.clone(rect).astype(np.float64)))


def get_intensity_max_min(filtered_image):
    """``Point(X=max, Y=min)`` gray intensity of a filtered image (bounded to 0..255 like the original)."""
    data = filtered_image.Img
    return Point(max(0, data.max()), min(255, data.min()))


def statistical_measures(data):
    """
    ``[μ, σ, x_min, x_max, n]`` of an array: mean, population standard deviation, minimum, maximum
    (never below 0, as in the original) and number of values.
    """
    data = np.asarray(data, dtype=np.float64)
    if data.ndim == 1:
        data = data.reshape((len(data), 1))
    if data.size == 0:
        raise ValueError('cannot compute statistics of an empty array')
    n = float(data.size)
    mean = float(np.sum(data)) / n
    st_dev = math.sqrt(float(np.sum((data - mean) ** 2)) / n)
    return [mean, st_dev, float(data.min()), max(0.0, float(data.max())), n]


def standarized_array(image_index, target, store_con_data, intensity_measures):
    """Standardised concentration array ``(x - μ) / σ`` of a target."""
    data = np.asarray(store_con_data[image_index][target], dtype=np.float64)
    mean = intensity_measures[image_index][target][3]
    st_dev = intensity_measures[image_index][target][0]
    if st_dev == 0:
        raise ValueError('Image %d, target %d: the concentration is uniform (σ = 0), it cannot be standardised'
                         % (image_index, target))
    return (data - mean) / st_dev


def get_intensity_array(image_index, target_area, img_to_process2, store_target_areas2):
    """Gray intensity array of a target after ``filter_image``, indexed ``[x][y]`` (shape ``(Width, Height)``)."""
    filtered = filter_image(img_to_process2[image_index])
    rect = store_target_areas2[image_index][target_area]
    return np.ascontiguousarray(filtered.clone(rect).astype(np.float64).T)


def full_image_data_array(image_index, img_to_process2):
    """Gray intensity array of the whole image after ``filter_image``, indexed ``[x][y]``."""
    filtered = filter_image(img_to_process2[image_index])
    return np.ascontiguousarray(filtered.Img.astype(np.float64).T)


# endregion
# region High-level helpers (CLI / GUI)


class NotEnoughParticles(ValueError):
    """
    Raised by ``run_particle_analysis`` when a target has fewer than four particles. It carries what was
    detected so a caller can show it: ``positions`` and ``rectangles`` (indexed ``[image][target]``) and
    ``stages`` (``[image][target]`` dicts of intermediate images, or ``None`` when not collected).
    """

    def __init__(self, message, positions=None, rectangles=None, stages=None):
        super().__init__(message)
        self.positions = positions
        self.rectangles = rectangles
        self.stages = stages


def run_particle_analysis(image_bgr, targets, threshold_value=50, color='red', detector=None, out_dir=None,
                          show=False, verbose=False, horizontal=True, collect_stages=False, colors=None):
    """
    Full particle-data pipeline for one image and a list of ``Rectangle`` targets.

    :param color: colour specification used for every target (see ``resolve_color``).
    :param colors: optional list with one colour specification per target, overriding ``color``.
    :return: the dictionary of ``mixing_dim_particle_data`` plus ``particle_positions``,
             ``blob_rectangles``, ``mean_spacing``, ``transects``, ``targets``, ``colors`` (label per
             target) and ``color_ranges``; with ``collect_stages`` also ``detection_stages``.
    """
    img_to_process = [BitMap(image_bgr)]
    store_target_areas = [list(targets)]
    for rect in targets:
        img_to_process[0].check_rectangle(rect)
    if colors is not None and len(colors) != len(targets):
        raise ValueError('one colour per target is needed: %d targets, %d colours' % (len(targets), len(colors)))
    per_target = list(colors) if colors is not None else [color] * len(targets)
    stages_out = [] if collect_stages else None
    positions, rectangles = blob_detection_image(img_to_process, threshold_value, store_target_areas, color=color,
                                                 detector=detector, show=show, out_dir=out_dir, verbose=verbose,
                                                 stages_out=stages_out, colors=[per_target])
    for j, pts in enumerate(positions[0]):
        if len(pts) < 4:
            raise NotEnoughParticles('Target %d (%r): only %d particles detected; at least 4 are needed. Try '
                                     'another threshold or colour.' % (j, targets[j], len(pts)),
                                     positions=positions, rectangles=rectangles, stages=stages_out)
    mean_spacing, transects, max_striation = initiate_max_str_thickness(img_to_process, positions,
                                                                        store_target_areas, horizontal)
    results = mixing_dim_particle_data(store_target_areas, ['Img1'], positions, max_striation, verbose=verbose)
    results.update({'particle_positions': positions, 'blob_rectangles': rectangles, 'mean_spacing': mean_spacing,
                    'transects': transects, 'targets': store_target_areas})
    if collect_stages:
        results['detection_stages'] = stages_out
    results['colors'] = [[color_label(spec) for spec in per_target]]
    results['color_ranges'] = [[resolve_color(spec) for spec in per_target]]
    return results


def run_particle_analysis_by_color(image_bgr, targets, colors, threshold_value=50, detector=None, out_dir=None,
                                   show=False, verbose=False, horizontal=True, collect_stages=False):
    """
    ``run_particle_analysis`` once per dye colour, as the Android application does.

    :param colors: list of colour names, or dict ``label -> colour specification`` (see ``resolve_color``).
    :return: dict ``label -> results``. When a colour has too few particles its entry holds ``error`` (the
             message) with ``particle_positions``, ``blob_rectangles`` and ``detection_stages`` instead of
             the measures. With ``out_dir`` the images of each colour go to ``out_dir/<label>``.
    """
    if not isinstance(colors, dict):
        colors = {str(c): c for c in colors}
    if not colors:
        raise ValueError('select at least one particle colour')
    results = {}
    for label, spec in colors.items():
        label_dir = os.path.join(out_dir, str(label)) if out_dir else None
        if verbose:
            print('Particle colour: %s' % label)
        try:
            results[label] = run_particle_analysis(image_bgr, targets, threshold_value, spec, detector, label_dir,
                                                   show, verbose, horizontal, collect_stages)
        except NotEnoughParticles as exc:
            if verbose:
                print('  not computed: %s' % exc)
            results[label] = {'error': str(exc), 'particle_positions': exc.positions,
                              'blob_rectangles': exc.rectangles, 'detection_stages': exc.stages,
                              'targets': [list(targets)], 'colors': [[color_label(spec)] * len(targets)],
                              'color_ranges': [[resolve_color(spec)] * len(targets)]}
    return results


def run_concentration_analysis(image_bgr, targets, dark_areas_higher=False, verbose=False, collect_stages=False):
    """
    Full concentration-data pipeline (no calibration) for one image and a list of ``Rectangle`` targets.

    With ``collect_stages`` the result also holds ``concentration_stages`` (crop, filtered crop and
    colour-mapped concentration of every target, see ``concentration_stages``).
    """
    img_to_process = [BitMap(image_bgr)]
    store_target_areas = [list(targets)]
    results = mixing_dim_concentration_data(img_to_process, store_target_areas, None, [[RefImg(0, 1)]], ['Img1'],
                                            dark_areas_higher, verbose=verbose)
    results['targets'] = store_target_areas
    if collect_stages:
        results['concentration_stages'] = [[concentration_stages(image_bgr, rect, results['concentration_data'][0][j])
                                            for j, rect in enumerate(targets)]]
    return results


def to_jsonable(obj):
    """Recursively convert results (numpy arrays, Points, Rectangles, ...) into JSON-serialisable values."""
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, (Point, Coordinate)):
        return {'X': to_jsonable(obj.X), 'Y': to_jsonable(obj.Y)}
    if isinstance(obj, Rectangle):
        return {'X': obj.X, 'Y': obj.Y, 'Width': obj.Width, 'Height': obj.Height}
    if isinstance(obj, RefImg):
        return {'ImageIndex': obj.ImageIndex, 'Concentration': obj.Concentration}
    return obj


# endregion
