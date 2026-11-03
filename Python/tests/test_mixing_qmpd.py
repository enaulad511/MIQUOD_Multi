# -*- coding: utf-8 -*-
"""
Tests for Mixing_QMPD.

The vectorised functions are checked against direct transcriptions of the loops of the C# original
(MICalculatorForm.cs) and of the first Python port, run on small random inputs. Run with::

    cd Python
    ..\\.venv\\Scripts\\python -m pytest -q

Set ``MIQUOD_RUN_SLOW=1`` to also run the regression test on the sample image (about one minute).
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Mixing_QMPD as Mf  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_IMAGE = os.path.join(os.path.dirname(HERE), '3colors_unmixed.png')


# ----------------------------------------------------------------------------------------------
# Oracles: literal transcriptions of the reference loops (absolute column/row coordinates)
# ----------------------------------------------------------------------------------------------

def oracle_mean_spacing(points, img_w, img_h):
    """C# CalculateMeanSpacing."""
    mean_spa = 0
    for p in points:
        mean_s = int(math.sqrt(math.pow(img_w, 2) + math.pow(img_h, 2)))
        for q in points:
            if p is not q:
                dist = int(math.sqrt(math.pow(p[0] - q[0], 2) + math.pow(p[1] - q[1], 2)))
                if dist < mean_s:
                    mean_s = dist
        mean_spa = mean_spa + mean_s
    mean_spa = int(mean_spa / len(points))
    return mean_spa * 2


def oracle_max_striation(points, transect, horizontal, ms):
    """C# CalculateMaxStrThickness for one transect."""
    x1, x2 = transect.X, transect.X + transect.Width - 1
    y1, y2 = transect.Y, transect.Y + transect.Height - 1
    arr = [p[0] if horizontal else p[1] for p in points if x1 <= p[0] <= x2 and y1 <= p[1] <= y2]
    if len(arr) > 1:
        arr.sort()
        mst = 0
        start = arr[0]
        for i in range(1, len(arr)):
            striation = arr[i] - arr[i - 1]
            if striation > ms:
                if arr[i - 1] - start > mst:
                    mst = arr[i - 1] - start
                start = arr[i]
            if i == len(arr) - 1:
                if arr[i] - start > mst:
                    mst = arr[i] - start
        if mst < ms:
            mst = ms
    else:
        mst = ms
    return mst


def oracle_scan(points, rect, ms, horizontal=True):
    """Python v2.0 initiate_max_str_thickness: slide the transect over the target, keep the maximum."""
    x, y = rect.X, rect.Y
    if horizontal:
        height, width, ini, limit = ms, rect.Width, y, y + rect.Height - 1 - ms
    else:
        height, width, ini, limit = rect.Height, ms, x, x + rect.Width - 1 - ms
    mst = ms
    for j in range(ini, limit):
        t = Mf.Rectangle(x, j, width, height) if horizontal else Mf.Rectangle(j, y, width, height)
        e = oracle_max_striation(points, t, horizontal, ms)
        if e > mst:
            mst = e
    return mst


def oracle_particle_concentration(points, rect, mst):
    """Python v2.0 get_concentration_from_particles (C# equivalent) for one target."""
    width, height = rect.Width, rect.Height
    col = math.floor(width / mst)
    dist_x = (width - col * mst) / 2
    row = math.floor(height / mst)
    dist_y = (height - row * mst) / 2
    conc = np.zeros((col, row))
    for n in range(1, row + 1):
        y_cmp = rect.Y + dist_y
        y_start = y_cmp + (n - 1) * mst - 1
        y_limit = y_cmp + n * mst - 1
        for m in range(1, col + 1):
            x_comp = rect.X + dist_x
            x_start = x_comp + (m - 1) * mst - 1
            x_limit = x_comp + m * mst - 1
            nn = sum(1 for (x, y) in points if x_start <= x < x_limit and y_start <= y < y_limit)
            conc[m - 1][n - 1] = nn / (mst * mst * 1.0)
    return conc


def oracle_ideal_positions(rect, num_of_part):
    """Python v2.0 ideal_particle_position."""
    k = int(num_of_part ** 0.5)
    x, y, width, height = rect.X, rect.Y, rect.Width, rect.Height
    dist_x = width / (k * 1.0)
    dist = (width - int(math.ceil((dist_x - 1) / 2.0)) - (k - 1) * dist_x) / 2.0
    ini_x = x + int(math.ceil(dist))
    dist_y = height / (k * 1.0)
    dist = int(math.ceil(((height - dist_y * k) / 2.0)))
    ini_y = y + dist + int(math.ceil(dist_y / 2.0))
    out = []
    for n in range(k):
        y_part = ini_y + n * dist_y
        for m in range(k):
            if n % 2 == 0:
                x_part = ini_x + m * dist_x
            else:
                x_part = (ini_x + dist_x / 2) + (m * dist_x)
            out.append((x_part, y_part))
    return out


def oracle_pnn(grid, points, rect):
    """C# CalculatePNNMethodDistribution for one target."""
    xi = []
    for gx, gy in grid:
        best = math.sqrt(math.pow(rect.Width, 2) + math.pow(rect.Height, 2))
        for px, py in points:
            d = math.sqrt(math.pow(gx - px, 2) + math.pow(gy - py, 2))
            if d < best:
                best = d
        xi.append(best)
    return np.array(xi)


def oracle_scale(num_of_part, rect, xi):
    """Python v2.0 scale_segregation_for_particles for one target."""
    k = int(math.sqrt(num_of_part))
    dx = rect.Width / (k * 1.0)
    dy = rect.Height / (k * 1.0)
    xg = float((dx + 2 * math.sqrt(dx * dx + dy * dy)) / (3 * 1.0))
    m = len(xi)
    xs = 0
    xr = xg / 2
    xi_mean = 0
    for v in xi:
        if v >= xr:
            xs = xs + math.pow(v - xr, 2)
        xi_mean = xi_mean + v
    xi_mean = xi_mean / (m * 1.0)
    var_fpp = xs / ((m * 1.0) - 1)
    return [math.sqrt(var_fpp), var_fpp / xi_mean, xg]


def oracle_variogram(s, axis):
    """C# CalculateHorizontalvariograms / CalculateVerticalvariograms with Math.Pow(a - b, 2)."""
    if axis == 1:
        s = s.T
    max_h = int(math.floor(s.shape[0] / 2.0))
    g = np.zeros(max_h + 1)
    for dist in range(1, max_h + 1):
        sum2 = 0.0
        nh = 0
        for yy in range(s.shape[1]):
            for xx in range(s.shape[0] - dist):
                sum2 = sum2 + math.pow(s[xx][yy] - s[xx + dist][yy], 2)
                nh = nh + 1
        g[dist] = sum2 / (2 * nh)
    return g


def oracle_exposure(data):
    """Python v2.0 calculate_exposure_indexes for one target."""
    xf, yf = data.shape
    exp = 0.0
    for x in range(xf):
        for y in range(yf):
            if x != 0:
                exp = exp + 0.5 * abs(data[x][y] - data[x - 1][y])
            if y != 0:
                exp = exp + 0.5 * abs(data[x][y] - data[x][y - 1])
            if x != xf - 1:
                exp = exp + 0.5 * abs(data[x][y] - data[x + 1][y])
            if y != yf - 1:
                exp = exp + 0.5 * abs(data[x][y] - data[x][y + 1])
    return exp


def oracle_statistics(data):
    """Python v2.0 statistical_measures."""
    mean = 0.0
    st_dev = 0.0
    x_max = 0.0
    x_min = data[0][0]
    n = 0.0
    for xc in range(data.shape[0]):
        for yc in range(data.shape[1]):
            if x_max < data[xc][yc]:
                x_max = data[xc][yc]
            if x_min > data[xc][yc]:
                x_min = data[xc][yc]
            mean = mean + data[xc][yc]
            n = n + 1
    mean = mean / n
    for xc in range(data.shape[0]):
        for yc in range(data.shape[1]):
            st_dev = st_dev + ((data[xc][yc] - mean) ** 2)
    st_dev = (st_dev / n) ** 0.5
    return [mean, st_dev, x_min, x_max, n]


# ----------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------

def random_points(rng, rect, n):
    xs = rng.integers(rect.X, rect.X + rect.Width, size=n)
    ys = rng.integers(rect.Y, rect.Y + rect.Height, size=n)
    return [(int(x), int(y)) for x, y in zip(xs, ys)]


def as_points(tuples):
    return [Mf.Point(x, y) for x, y in tuples]


def synthetic_particle_image(shape=(300, 400), dots=(), radius=3, color=(0, 0, 255)):
    """Black BGR image with filled circles (BGR ``color``) centred at the given (column, row) positions."""
    import cv2
    img = np.zeros(shape + (3,), dtype=np.uint8)
    for (x, y) in dots:
        cv2.circle(img, (int(x), int(y)), radius, color, -1)
    return img


# ----------------------------------------------------------------------------------------------
# Data structures and conventions
# ----------------------------------------------------------------------------------------------

def test_rectangle_rejects_empty():
    with pytest.raises(ValueError):
        Mf.Rectangle(0, 0, 0, 5)


def test_bitmap_is_column_first():
    img = np.arange(6 * 4 * 3, dtype=np.uint8).reshape(6, 4, 3)  # 6 rows, 4 columns
    bm = Mf.BitMap(img)
    assert (bm.Width, bm.Height) == (4, 6)
    crop = bm.clone(Mf.Rectangle(1, 2, 2, 3))  # columns 1-2, rows 2-4
    assert crop.shape == (3, 2, 3)
    np.testing.assert_array_equal(crop, img[2:5, 1:3])
    assert bm.pixel(3, 5, 'B') == img[5, 3, 0]
    assert bm.pixel(3, 5, 'R') == img[5, 3, 2]


def test_bitmap_rejects_none_and_outside_rectangles():
    with pytest.raises(ValueError, match='could not be read'):
        Mf.BitMap(None)
    bm = Mf.BitMap(np.zeros((10, 20, 3), dtype=np.uint8))
    with pytest.raises(ValueError, match='outside the image'):
        bm.clone(Mf.Rectangle(0, 0, 21, 5))
    with pytest.raises(ValueError, match='outside the image'):
        bm.clone(Mf.Rectangle(0, 5, 5, 6))
    assert bm.clone(Mf.Rectangle(0, 0, 20, 10)).shape == (10, 20, 3)


def test_to_jsonable_round_trip():
    import json
    obj = {'a': np.arange(3), 'p': Mf.Point(1, 2), 'r': Mf.Rectangle(1, 2, 3, 4), 'c': Mf.Coordinate(1.5, 2.5),
           'n': np.float64(1.25), 'l': [np.int64(3)]}
    text = json.dumps(Mf.to_jsonable(obj))
    assert json.loads(text) == {'a': [0, 1, 2], 'p': {'X': 1, 'Y': 2}, 'r': {'X': 1, 'Y': 2, 'Width': 3, 'Height': 4},
                                'c': {'X': 1.5, 'Y': 2.5}, 'n': 1.25, 'l': [3]}


# ----------------------------------------------------------------------------------------------
# Particle path
# ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize('seed', range(5))
def test_mean_spacing_matches_oracle(seed):
    rng = np.random.default_rng(seed)
    rect = Mf.Rectangle(30, 20, 250, 160)
    pts = random_points(rng, rect, 60)
    image = Mf.BitMap(np.zeros((200, 400, 3), dtype=np.uint8))
    got = Mf.calculate_mean_spacing(0, 0, [image], [[as_points(pts)]])
    assert got == oracle_mean_spacing(pts, 400, 200)


def test_mean_spacing_needs_two_particles():
    image = Mf.BitMap(np.zeros((50, 50, 3), dtype=np.uint8))
    with pytest.raises(ValueError, match='at least two particles'):
        Mf.calculate_mean_spacing(0, 0, [image], [[[Mf.Point(1, 1)]]])


@pytest.mark.parametrize('seed', range(5))
def test_transect_scan_matches_oracle(seed):
    rng = np.random.default_rng(seed)
    rect = Mf.Rectangle(15, 10, 120, 90)
    pts = random_points(rng, rect, 40)
    for ms in (4, 9, 15):
        for horizontal in (True, False):
            mst, transect = Mf._scan_transects(np.array(pts, dtype=float), rect, ms, horizontal)
            assert mst == oracle_scan(pts, rect, ms, horizontal)
            assert isinstance(transect, Mf.Rectangle)


@pytest.mark.parametrize('seed', range(5))
def test_max_striation_for_given_transect_matches_oracle(seed):
    rng = np.random.default_rng(seed)
    rect = Mf.Rectangle(5, 5, 100, 80)
    pts = random_points(rng, rect, 50)
    horizontal_transect = Mf.Rectangle(5, 30, 100, 12)
    vertical_transect = Mf.Rectangle(40, 5, 12, 80)
    for transect, horizontal in ((horizontal_transect, True), (vertical_transect, False)):
        for ms in (3, 8, 20):
            got = Mf.calculate_max_str_thickness(0, 0, ms, [[as_points(pts)]], [[transect]], [[rect]])
            assert got == oracle_max_striation(pts, transect, horizontal, ms)


@pytest.mark.parametrize('seed', range(5))
def test_particle_concentration_matches_oracle(seed):
    rng = np.random.default_rng(seed)
    rect = Mf.Rectangle(24, 82, 270, 218)
    pts = random_points(rng, rect, 300)
    for mst in (7, 10, 27, 33):
        got = Mf.get_concentration_from_particles([[rect]], ['Img1'], [[as_points(pts)]], [[mst]])[0][0]
        np.testing.assert_array_equal(got, oracle_particle_concentration(pts, rect, mst))


def test_particle_concentration_rejects_striation_larger_than_target():
    with pytest.raises(ValueError, match='larger than the target'):
        Mf.get_concentration_from_particles([[Mf.Rectangle(0, 0, 10, 10)]], ['Img1'], [[[Mf.Point(1, 1)]]], [[20]])


@pytest.mark.parametrize('num', [4, 9, 50, 63, 100, 4956])
def test_ideal_positions_match_oracle(num):
    rect = Mf.Rectangle(24, 82, 2700, 2180)
    got = [(p.X, p.Y) for p in Mf.ideal_particle_position(rect, num)]
    assert got == oracle_ideal_positions(rect, num)


@pytest.mark.parametrize('seed', range(3))
def test_pnn_and_scale_match_oracle(seed):
    rng = np.random.default_rng(seed)
    rect = Mf.Rectangle(10, 20, 200, 150)
    pts = random_points(rng, rect, 80)
    grid = oracle_ideal_positions(rect, len(pts))
    expected_xi = oracle_pnn(grid, pts, rect)
    got_xi = Mf.pnn_method_distribution([[rect]], [[as_points(pts)]])[0][0]
    np.testing.assert_allclose(got_xi, expected_xi, rtol=1e-12, atol=0)
    got_scale = Mf.scale_segregation_for_particles([[rect]], [[as_points(pts)]], [[got_xi]])[0][0]
    np.testing.assert_allclose(got_scale, oracle_scale(len(pts), rect, expected_xi), rtol=1e-12)


def test_scale_needs_four_particles():
    rect = Mf.Rectangle(0, 0, 50, 50)
    pts = [[as_points([(1, 1), (10, 10), (20, 20)])]]
    xi = Mf.pnn_method_distribution([[rect]], pts)
    with pytest.raises(ValueError, match='At least 4 particles'):
        Mf.scale_segregation_for_particles([[rect]], pts, xi)


def test_statistical_measures_particles():
    data = np.array([[1.0, 2.0], [0.0, 5.0]])
    mean, st_dev, x_min, x_max, n = Mf.statistical_measures_particles(data, 100, 20)
    assert mean == 0.2
    assert st_dev == pytest.approx(math.sqrt(((1 - .2) ** 2 + (2 - .2) ** 2 + (0 - .2) ** 2 + (5 - .2) ** 2) / 4))
    assert (x_min, x_max, n) == (0.0, 5.0, 4)


def test_blob_detection_returns_absolute_positions():
    dots = [(120, 70), (150, 90), (180, 110), (210, 130), (140, 150), (190, 160)]
    img = synthetic_particle_image((300, 400), dots)
    target = Mf.Rectangle(100, 50, 150, 130)
    positions, rects = Mf.blob_detection_image([Mf.BitMap(img)], 50, [[target]], verbose=False)
    assert len(positions) == 1 and len(positions[0]) == 1
    found = sorted((p.X, p.Y) for p in positions[0][0])
    assert len(found) == len(dots)
    for (fx, fy), (dx, dy) in zip(found, sorted(dots)):
        assert abs(fx - dx) <= 2 and abs(fy - dy) <= 2
    for r in rects[0][0]:
        assert target.contains(r.X + r.Width / 2, r.Y + r.Height / 2)


def test_blob_detection_multi_image_multi_target_structure():
    dots_a = [(30 + 12 * i, 40 + 7 * i) for i in range(8)]
    dots_b = [(230 + 11 * i, 150 + 9 * i) for i in range(10)]
    img1 = synthetic_particle_image((300, 400), dots_a + dots_b)
    img2 = synthetic_particle_image((300, 400), dots_a)
    targets = [Mf.Rectangle(20, 30, 120, 100), Mf.Rectangle(220, 140, 130, 110)]
    positions, _ = Mf.blob_detection_image([Mf.BitMap(img1), Mf.BitMap(img2)], 50, [targets, targets], verbose=False)
    assert [len(t) for t in positions[0]] == [8, 10]
    assert [len(t) for t in positions[1]] == [8, 0]


def test_full_particle_pipeline_on_synthetic_image():
    # Two vertical bands of dots on a 12 px grid (columns 60-156 and 240-336), 12 rows 20 px apart.
    target = Mf.Rectangle(40, 30, 320, 240)
    rows = range(40, 261, 20)
    dots = [(x, y) for y in rows for x in range(60, 157, 12)] + [(x, y) for y in rows for x in range(240, 337, 12)]
    img = synthetic_particle_image((300, 400), dots)
    results = Mf.run_particle_analysis(img, [target], threshold_value=50, color='red', collect_stages=True)
    assert len(results['particle_positions'][0][0]) == len(dots) == 216
    assert results['mean_spacing'][0][0] == 24  # nearest neighbour 12 px, times two
    assert results['max_striation_thickness'][0][0] == 96  # width of a band: 156 - 60
    measures = results['intensity_measures'][0][0]
    assert measures[7] == 216 and measures[6] == (320 // 96) * (240 // 96)
    assert results['particle_concentration'][0][0].shape == (3, 2)
    sigma_fpp, i_dis, xg = results['scale_segregation_indexes'][0][0]
    assert sigma_fpp >= 0 and i_dis >= 0 and xg > 0
    assert len(results['pnn_distribution'][0][0]) == int(math.sqrt(216)) ** 2
    assert list(results['detection_stages'][0][0]) == ['crop', 'mask', 'color', 'gray', 'binary', 'particles']
    import json
    results.pop('detection_stages')
    json.dumps(Mf.to_jsonable(results))


def test_particle_pipeline_errors_are_explicit():
    img = synthetic_particle_image((100, 100), [])
    with pytest.raises(ValueError, match='only 0 particles'):
        Mf.run_particle_analysis(img, [Mf.Rectangle(0, 0, 100, 100)])
    with pytest.raises(ValueError, match='outside the image'):
        Mf.run_particle_analysis(img, [Mf.Rectangle(50, 50, 100, 100)])
    with pytest.raises(ValueError, match='unknown colour'):
        Mf.detect_particles_in_target(img, 50, color='purple')


# ----------------------------------------------------------------------------------------------
# Concentration path
# ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize('seed', range(3))
def test_statistical_measures_matches_oracle(seed):
    rng = np.random.default_rng(seed)
    data = rng.random((7, 5))
    got = Mf.statistical_measures(data)
    np.testing.assert_allclose(got, oracle_statistics(data), rtol=1e-12)
    assert Mf.statistical_measures(np.array([1.0, 3.0]))[0] == 2.0


@pytest.mark.parametrize('seed', range(3))
def test_variograms_match_oracle(seed):
    rng = np.random.default_rng(seed)
    data = rng.random((12, 9))
    measures = [[Mf.statistical_measures(data)]]
    im = [[[measures[0][0][1], 0, 0, measures[0][0][0], 0, 0, 0]]]
    s = Mf.standarized_array(0, 0, [[data]], im)
    np.testing.assert_allclose(s, (data - data.mean()) / data.std(), rtol=1e-12)
    hor = Mf.horizontal_var_diagram(None, [[data]], [None], im)[0][0]
    ver = Mf.vertical_var_diagram(None, [None], [[data]], im)[0][0]
    assert len(hor) == 12 // 2 + 1 and len(ver) == 9 // 2 + 1
    np.testing.assert_allclose(hor, oracle_variogram(s, 0), rtol=1e-12)
    np.testing.assert_allclose(ver, oracle_variogram(s, 1), rtol=1e-12)
    lms = Mf.mean_length_scales([None], [[data]], im, [[hor]], [[ver]])[0][0]
    assert lms.X == pytest.approx(data.mean() / (hor[1] - hor[0]))
    assert lms.Y == pytest.approx(data.mean() / (ver[1] - ver[0]))


@pytest.mark.parametrize('seed', range(3))
def test_exposure_matches_oracle(seed):
    rng = np.random.default_rng(seed)
    data = rng.random((10, 6))
    got = Mf.calculate_exposure_indexes([None], [[data]])[0][0]
    assert got == pytest.approx(oracle_exposure(data), rel=1e-12)


def test_concentration_without_calibration_orientation_and_dark_flag():
    rows, cols = 60, 90
    gradient = np.tile(np.linspace(20, 220, cols, dtype=np.float64), (rows, 1)).astype(np.uint8)
    img = np.stack([gradient] * 3, axis=-1)  # gray gradient along the columns
    bm = Mf.BitMap(img)
    rect = Mf.Rectangle(10, 5, 50, 40)
    con = Mf.concentration_matrix([bm], [[rect]], None, [[Mf.RefImg(0, 1)]], ['Img1'], False)[0][0]
    assert con.shape == (rect.Width, rect.Height)
    assert con.min() >= 0 and con.max() <= 1
    # the gradient varies along the image width (axis 0 of the [x][y] array) only
    assert np.allclose(con, con[:, :1])
    assert con[-1, 0] > con[0, 0]
    dark = Mf.concentration_matrix([bm], [[rect]], None, [[Mf.RefImg(0, 1)]], ['Img1'], True)[0][0]
    np.testing.assert_allclose(dark, 1 - con)
    with pytest.warns(UserWarning, match='vertical mean length scale is infinite'):
        results = Mf.run_concentration_analysis(img, [rect])
    hor, ver = results['horizontal_variograms'][0][0], results['vertical_variograms'][0][0]
    assert hor[1] > 0 and ver[1:].max() == 0
    lms = results['mean_length_scales'][0][0]
    assert math.isfinite(lms.X) and lms.X > 0 and math.isinf(lms.Y)
    assert set(results) >= {'intensity_measures', 'mean_length_scales', 'exposure_indexes', 'need_for_inlets'}


def test_concentration_two_targets_and_two_images():
    rng = np.random.default_rng(3)
    imgs = [Mf.BitMap(rng.integers(0, 255, (80, 100, 3), dtype=np.uint8)) for _ in range(2)]
    targets = [[Mf.Rectangle(0, 0, 30, 20), Mf.Rectangle(50, 40, 40, 30)], [Mf.Rectangle(5, 5, 20, 20)]]
    results = Mf.mixing_dim_concentration_data(imgs, targets, None, [[Mf.RefImg(0, 1)], [Mf.RefImg(1, 1)]],
                                               ['A', 'B'], False, verbose=False)
    assert [len(t) for t in results['intensity_measures']] == [2, 1]
    assert results['concentration_data'][0][1].shape == (40, 30)
    assert [len(t) for t in results['exposure_indexes']] == [2, 1]
    assert isinstance(results['mean_length_scales'][0][1], Mf.Coordinate)


def _calibration_images(size=(40, 50)):
    def uniform(value):
        return Mf.BitMap(np.full(size + (3,), value, dtype=np.uint8))
    # image 0 is assessed (intensity 100); images 1 and 2 are references with 0 % and 100 % concentration
    return [uniform(100), uniform(50), uniform(150)]


def test_calibration_complex_same_sizes():
    imgs = _calibration_images()
    rect = Mf.Rectangle(5, 5, 20, 15)
    refs = [[Mf.RefImg(1, 0), Mf.RefImg(2, 100)], [], []]
    con = Mf.concentration_matrix(imgs, [[rect], [rect], [rect]], None, refs, ['a', 'r0', 'r100'], False)
    assert con[1] == [] and con[2] == []
    assert con[0][0].shape == (20, 15)
    np.testing.assert_allclose(con[0][0], 0.5)
    measures = Mf.segregation_intensity_index_factors(None, imgs, con)
    assert [len(t) for t in measures] == [1, 0, 0]


def test_calibration_simple_different_sizes():
    imgs = _calibration_images()
    imgs[1] = Mf.BitMap(np.full((30, 30, 3), 50, dtype=np.uint8))  # different image size -> simple calibration
    rect = Mf.Rectangle(2, 2, 10, 10)
    refs = [[Mf.RefImg(1, 0), Mf.RefImg(2, 100)], [], []]
    con = Mf.concentration_matrix(imgs, [[rect], [rect], [rect]], None, refs, ['a', 'r0', 'r100'], False)
    np.testing.assert_allclose(con[0][0], 0.5)


def test_uniform_image_cannot_be_normalised():
    bm = Mf.BitMap(np.full((20, 20, 3), 7, dtype=np.uint8))
    with pytest.raises(ValueError, match='uniform intensity'):
        Mf.concentration_matrix([bm], [[Mf.Rectangle(0, 0, 10, 10)]], None, [[Mf.RefImg(0, 1)]], ['a'], False)


# ----------------------------------------------------------------------------------------------
# Regression on the sample image (slow)
# ----------------------------------------------------------------------------------------------

@pytest.mark.skipif(not os.path.exists(SAMPLE_IMAGE) or os.environ.get('MIQUOD_RUN_SLOW') != '1',
                    reason='set MIQUOD_RUN_SLOW=1 to run the sample-image regression (about one minute)')
def test_sample_image_regression():
    import cv2
    im = cv2.imread(SAMPLE_IMAGE)
    # Same crop as the v2.0 default run (rows 24-2207, columns 82-2261): the detection is unchanged.
    old_crop = Mf.run_particle_analysis(im, [Mf.Rectangle(82, 24, 2180, 2184)], 50, 'red')
    assert len(old_crop['particle_positions'][0][0]) == 4956
    assert old_crop['mean_spacing'][0][0] == 22
    # Default configuration of MIQUOD_v1.py (v2.1).
    results = Mf.run_particle_analysis(im, [Mf.Rectangle(24, 82, 2700, 2120)], 50, 'red')
    assert len(results['particle_positions'][0][0]) == REFERENCE['particles']
    assert results['max_striation_thickness'][0][0] == REFERENCE['max_striation_thickness']
    assert results['intensity_measures'][0][0][1] == pytest.approx(REFERENCE['cov'], rel=1e-9)
    s = results['scale_segregation_indexes'][0][0]
    assert s[0] == pytest.approx(REFERENCE['sigma_fpp'], rel=1e-9)
    assert s[1] == pytest.approx(REFERENCE['i_dis'], rel=1e-9)
    assert s[2] == pytest.approx(REFERENCE['xg'], rel=1e-9)


# Reference values of the default particle run of MIQUOD_v1.py (v2.1), see docs/changes.md.
REFERENCE = {'particles': 5589, 'max_striation_thickness': 361, 'cov': 0.9094732599597147,
             'sigma_fpp': 195.40994717593975, 'i_dis': 354.44239558450107, 'xg': 43.08866115949653}
