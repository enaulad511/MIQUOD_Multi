#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MIQUOD command-line interface.

Quantify mixing from an image: particle data (blob detection, striation thickness, PNN scale of
segregation) and/or concentration data (intensity of segregation, variograms, mean length scales,
exposure). See docs/usage.md.

Examples::

    python MIQUOD_v1.py                                       # sample image, particle data
    python MIQUOD_v1.py image.png --roi 24 82 2700 2120 --mode both
    python MIQUOD_v1.py image.png --select-roi --mode concentration --dark
    python MIQUOD_v1.py image.png --roi 0 0 500 500 --roi 600 0 500 500 --color blue --threshold 60 --show

The ROI is ``X Y WIDTH HEIGHT`` with ``X`` the column and ``Y`` the row of the top-left corner, the
same order that ``cv2.selectROI`` prints. Results are written to ``--out-dir`` (``results.json`` plus
the intermediate images of the particle detection and the concentration arrays as ``.npy``).
"""
__author__ = 'Edisson Naula'
__version__ = '2.1.0'

import argparse
import json
import os
import sys
import time

import cv2
import numpy as np

import Mixing_QMPD as Mf

# Windows consoles often default to cp1252, which cannot encode the Greek letters in the
# result labels (σ, σ_fpp) and would make the prints raise UnicodeEncodeError.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IMAGE = os.path.join(SCRIPT_DIR, '3colors_unmixed.png')
# Default target of the sample image (2752 x 2208 px): columns 24-2723, rows 82-2201.
DEFAULT_ROI = (24, 82, 2700, 2120)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='MIQUOD_v1.py',
        description='MIQUOD %s: quantify mixing from an image.' % __version__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='examples:\n'
               '  python MIQUOD_v1.py\n'
               '  python MIQUOD_v1.py image.png --roi 24 82 2700 2120 --mode both\n'
               '  python MIQUOD_v1.py image.png --select-roi --mode concentration --dark\n'
               '  python MIQUOD_v1.py image.png --roi 0 0 500 500 --roi 600 0 500 500 --color blue --show\n')
    parser.add_argument('image', nargs='?', default=DEFAULT_IMAGE,
                        help='image to analyse (default: the sample 3colors_unmixed.png next to this script)')
    parser.add_argument('--roi', action='append', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                        help='target area, repeatable. X/Y are the column/row of the top-left corner. '
                             'Default: the sample target for the sample image, otherwise the whole image')
    parser.add_argument('--select-roi', action='store_true',
                        help='draw the target(s) with the mouse (ENTER/SPACE confirms a rectangle, ESC finishes)')
    parser.add_argument('--mode', choices=['particles', 'concentration', 'both'], default='particles',
                        help='which measures to compute (default: particles)')
    parser.add_argument('--threshold', type=int, default=50, metavar='0-255',
                        help='gray threshold applied before blob detection (default: 50)')
    parser.add_argument('--color', action='append', type=parse_color, metavar='COLOUR',
                        help='particle colour: %s, or hue:H[:TOL[:SMIN[:VMIN]]] for a custom hue (OpenCV scale '
                             '0-179, default tolerance 10, S and V at least 100). Give it once for every '
                             'target or once for all (default: red)' % ', '.join(sorted(Mf.COLOR_RANGES)))
    parser.add_argument('--dark', action='store_true',
                        help='concentration data: dark areas carry the higher concentration')
    parser.add_argument('--out-dir', default='miquod_output', metavar='DIR',
                        help='where results.json, the intermediate images and the arrays are written '
                             '(default: ./miquod_output)')
    parser.add_argument('--no-images', action='store_true', help='do not write the intermediate images')
    parser.add_argument('--show', action='store_true',
                        help='display the intermediate images of the particle detection (blocks until closed)')
    parser.add_argument('--quiet', action='store_true', help='print only errors and the output location')
    parser.add_argument('--version', action='version', version='MIQUOD %s' % __version__)
    args = parser.parse_args(argv)
    if not 0 <= args.threshold <= 255:
        parser.error('--threshold must be between 0 and 255')
    return args


def parse_color(text):
    """Colour argument: a name of ``COLOR_RANGES`` or ``hue:H[:TOL[:SMIN[:VMIN]]]``."""
    if text in Mf.COLOR_RANGES:
        return text
    if text.startswith('hue:'):
        try:
            values = [int(part) for part in text.split(':')[1:]]
        except ValueError:
            values = []
        if 1 <= len(values) <= 4:
            return dict(zip(('hue', 'tolerance', 's_min', 'v_min'), values))
    raise argparse.ArgumentTypeError('colour must be one of %s or hue:H[:TOL[:SMIN[:VMIN]]], got %r'
                                     % (', '.join(sorted(Mf.COLOR_RANGES)), text))


def resolve_colors(args, targets):
    """One colour specification per target: a single --color applies to all targets."""
    colors = args.color or ['red']
    if len(colors) == 1:
        return colors * len(targets)
    if len(colors) != len(targets):
        raise ValueError('give one --color per target or a single --color for all (%d targets, %d colours)'
                         % (len(targets), len(colors)))
    return colors


def select_rois_interactively(image):
    """Let the user draw one or more rectangles with OpenCV; returns a list of (x, y, w, h)."""
    scale = min(1.0, 1200.0 / max(image.shape[0], image.shape[1]))
    shown = cv2.resize(image, None, fx=scale, fy=scale) if scale < 1.0 else image
    window = 'MIQUOD: draw the target(s); ENTER/SPACE confirms, ESC finishes'
    rois = cv2.selectROIs(window, shown, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()
    out = []
    for x, y, w, h in np.asarray(rois).reshape(-1, 4):
        if w > 0 and h > 0:
            out.append((int(round(x / scale)), int(round(y / scale)), int(round(w / scale)), int(round(h / scale))))
    return out


def resolve_targets(args, image):
    if args.roi:
        rois = [tuple(r) for r in args.roi]
    elif args.select_roi:
        rois = select_rois_interactively(image)
        if not rois:
            raise ValueError('no target area was selected')
        print('Selected ROI(s): ' + ', '.join('--roi %d %d %d %d' % r for r in rois))
    elif os.path.abspath(args.image) == os.path.abspath(DEFAULT_IMAGE):
        rois = [DEFAULT_ROI]
    else:
        rois = [(0, 0, image.shape[1], image.shape[0])]
    bitmap = Mf.BitMap(image)
    targets = []
    for roi in rois:
        rect = Mf.Rectangle(*roi)
        bitmap.check_rectangle(rect)
        targets.append(rect)
    return targets


def main(argv=None):
    args = parse_args(argv)
    verbose = not args.quiet
    image = cv2.imread(args.image)
    if image is None:
        sys.exit('Could not read the image: %s' % args.image)
    try:
        targets = resolve_targets(args, image)
        colors = resolve_colors(args, targets)
    except ValueError as exc:
        sys.exit('Error: %s' % exc)
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    image_dir = None if args.no_images else out_dir
    if verbose:
        print('MIQUOD %s' % __version__)
        print('Image: %s (%d columns x %d rows)' % (args.image, image.shape[1], image.shape[0]))
        for j, rect in enumerate(targets):
            print('Target %d: %r, particle colour %s' % (j, rect, Mf.color_label(colors[j])))

    report = {'miquod_version': __version__, 'image': os.path.abspath(args.image),
              'image_size': {'columns': int(image.shape[1]), 'rows': int(image.shape[0])},
              'targets': [{'rectangle': t.as_tuple(), 'color': Mf.color_label(c), 'color_spec': c}
                          for t, c in zip(targets, colors)],
              'mode': args.mode}
    started = time.time()
    try:
        if args.mode in ('particles', 'both'):
            report['particle_settings'] = {'threshold': args.threshold,
                                           'colors': [Mf.color_label(c) for c in colors],
                                           'detector': Mf.DEFAULT_DETECTOR_SETTINGS}
            if verbose:
                print('\nParticle data (threshold %d)' % args.threshold)
            particles = Mf.run_particle_analysis(image, targets, args.threshold, out_dir=image_dir, show=args.show,
                                                 verbose=verbose, colors=colors)
            report['particles'] = particles
            if image_dir:
                annotated = image
                for j, rect in enumerate(targets):
                    annotated = Mf.draw_particles(annotated, particles['particle_positions'][0][j],
                                                  color=Mf.color_for_drawing(colors[j]), rect=rect)
                cv2.imwrite(os.path.join(image_dir, 'particles_full_image.jpg'), annotated)
        if args.mode in ('concentration', 'both'):
            report['concentration_settings'] = {'dark_areas_higher_concentration': args.dark}
            if verbose:
                print('\nConcentration data (%s)' % ('dark areas = higher concentration' if args.dark
                                                      else 'bright areas = higher concentration'))
            concentration = Mf.run_concentration_analysis(image, targets, args.dark, verbose=verbose,
                                                          collect_stages=bool(image_dir))
            report['concentration'] = concentration
            for j, array in enumerate(concentration['concentration_data'][0]):
                np.save(os.path.join(out_dir, 'concentration_target%d.npy' % j), array)
            if image_dir:
                for j, stages in enumerate(concentration['concentration_stages'][0]):
                    for k, (name, im) in enumerate(stages.items(), start=1):
                        cv2.imwrite(os.path.join(image_dir, 'concentration_target%d_%d_%s.jpg' % (j, k, name)), im)
                    cv2.imwrite(os.path.join(image_dir, 'concentration_target%d_sequence.jpg' % j),
                                Mf.montage_images(stages))
    except ValueError as exc:
        sys.exit('Error: %s' % exc)
    report['elapsed_seconds'] = round(time.time() - started, 2)

    # The concentration arrays are saved as .npy and the images as .jpg; everything else goes into results.json.
    export = dict(report)
    if 'concentration' in export:
        concentration = dict(export['concentration'])
        concentration.pop('concentration_data', None)
        concentration.pop('concentration_stages', None)
        concentration['concentration_data_files'] = ['concentration_target%d.npy' % j for j in range(len(targets))]
        export['concentration'] = concentration
    with open(os.path.join(out_dir, 'results.json'), 'w', encoding='utf-8') as handle:
        json.dump(Mf.to_jsonable(export), handle, indent=2)
    print('\nResults written to %s (results.json%s)' % (out_dir, '' if args.no_images else ' and images'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
