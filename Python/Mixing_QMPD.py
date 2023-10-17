# -*- coding: utf-8 -*-
"""
`Mixing_QMPD.py`
====================================================

Functions file adapted of:
    MIQUOD v1.0
    Mixing Quantification of Devices Software
    Author: Hector Betancourt Cervantes, 2017

* Author(s): 'Edisson Naula'


"""
__author__ = 'Edisson Naula'
__date__ = '$ 9/3/2020  at 17:04 $'

import math
import cv2
import numpy as np
import matplotlib.pyplot as plt

# region C-like Structures
from typing import List


class Point:
    def __init__(self, *args):
        # args -- tuple of anonymous arguments
        # kwargs -- dictionary of named arguments
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
        tmp = hex(dw).split('x')
        if 4 < tmp[1].__len__() < 9:
            lower = tmp[1][tmp[1].__len__() - 4:]
            upper = tmp[1][0:tmp[1].__len__() - 4]
        elif tmp[1].__len__() < 4:
            lower = tmp[1]
            upper = '0'
        else:
            lower = tmp[1][tmp[1].__len__() - 4:]
            upper = tmp[1][0:tmp[1].__len__() - 8]
        self.X = int(lower, 16)
        self.Y = int(upper, 16)


class ListPoints:
    def __init__(self, xin, yin):
        self.point = Point(xin, yin)

    def list_points(self, num):
        arr = []
        for i in range(num):
            arr.append(self.point)
        return arr


class Rectangle:
    def __init__(self, xin, yin, width, height):
        self.X = xin
        self.Y = yin
        self.Width = width
        self.Height = height


class Coordinate:
    def __init__(self, xin, yin):
        self.X = xin
        self.Y = yin


class Transect:
    def __init__(self, t_area, rect_in, msp):
        self.TargetArea = t_area
        self.Rect = rect_in
        self.MeanSpacingOfPart = msp


class RefImg:
    def __init__(self, idx, con):
        self.ImageIndex = idx
        self.Concentration = con


class BitMap:
    def __init__(self, img):
        self.Img = img
        size = img.shape
        self.Width = int(size[0])
        self.Height = int(size[1])
        if len(size) < 3:
            self.Dimension = 2
            self.R = img[0, 0]
            self.G = img[0, 0]
            self.B = img[0, 0]
        else:
            self.Dimension = int(size[2])
            self.R = img[0, 0][0]
            self.G = img[0, 0][1]
            self.B = img[0, 0][2]

    def clone(self, rect):
        return self.Img[rect.X:rect.X + rect.Width, rect.Y:rect.Y + rect.Height]

    def pixel(self, xin, yin, layer=''):
        if self.Dimension == 3:
            if layer == 'R':
                pix = self.Img[xin, yin][0]
            elif layer == 'G':
                pix = self.Img[xin, yin][1]
            else:
                pix = self.Img[xin, yin][2]
        else:
            pix = self.Img[xin, yin]
        return pix

    def bitmaps(self, num):
        # type: (int) -> List[np.ndarray]
        arr = []
        for i in range(num):
            arr.append(self.Img)
        return arr


class BlobDetector:
    """
    This generates a blob detector based on given parameters tuned for
    this particular project
    :param threshold: Convert the source to several binary images. Starting at minThreshold. These thresholds are
    incremented  by thresholdStep until maxThreshold.
    :param flag_area: if 1, and appropriate values for minArea  and maxArea. E.g.  setting minArea  = 100 will filter
    out all the blobs that have less then 100 pixels.
    :param limit_area: values of min and max area to filter
    :param flag_circularity: Set 1.  Then set appropriate values for minCircularity and maxCircularity.
    :param min_cir: Circularity is defined as 4*pi*Area/(perimeter^2). E.g. circle has 1 and square 0.785
    :param flag_convexity: , set 1, followed by setting 0 ≤ minConvexity ≤ 1 and maxConvexity ( ≤ 1)
    :param convexity: is defined as the (Area of the Blob / Area of it’s convex hull). Now, a circle is convex
    :param flag_inertia: set 1, and set 0 ≤ minInertiaRatio ≤ 1 and maxInertiaRatio (≤ 1 ) appropriately
    :param ratio_inertia: how elongated a shape is. E.g. for a circle_value is 1, ellipse is between 0 and 1, line is 0.
    :param flag_color: flag_color = 1. Set blobColor = 0 for darker blobs, and blobColor = 255 for lighter blobs.
    :return: blob detector

    """

    def __init__(self, threshold=None, flag_area=False, limit_area=None, flag_circularity=False, min_cir=0.1,
                 flag_convexity=False, convexity=None, flag_inertia=True, ratio_inertia=None,
                 flag_color=False):
        # Default values
        if ratio_inertia is None:
            ratio_inertia = [0.0, 0.5]
        if convexity is None:
            convexity = [0.0, 10]
        if limit_area is None:
            limit_area = [25, 25 * 35]
        if threshold is None:
            threshold = [120, 255]
        # Setup SimpleBlobDetector parameters.
        params = cv2.SimpleBlobDetector_Params()

        # Change thresholds
        params.minThreshold = threshold[0]
        params.maxThreshold = threshold[1]

        # Filter by Area. [4, 1000]
        params.filterByArea = flag_area
        params.minArea = limit_area[0]
        params.maxArea = limit_area[1]

        # Filter by Circularity
        params.filterByCircularity = flag_circularity
        params.minCircularity = min_cir

        # Filter by Convexity
        params.filterByConvexity = flag_convexity
        params.minConvexity = convexity[0]
        params.maxConvexity = convexity[1]

        # Filter by Inertia (ratio of widest to thinnest point)
        params.filterByInertia = flag_inertia
        params.minInertiaRatio = ratio_inertia[0]
        params.maxInertiaRatio = ratio_inertia[1]

        params.filterByColor = flag_color
        params.blobColor = 0

        # Create a detector with the parameters
        # noinspection PyUnresolvedReferences
        ver = cv2.__version__.split('.')
        if int(ver[0]) < 3:
            self.detector = cv2.SimpleBlobDetector(params)
        else:
            self.detector = cv2.SimpleBlobDetector_create(params)

    def detect_blobs(self, img):
        return self.detector.detect(img)

    @staticmethod
    def rectangles(points):
        aux = []
        for item in points:
            aux.append(
                Rectangle(int(item.pt[0] - item.size / 2), int(item.pt[1] - item.size / 2), item.size, item.size))
        return aux


# endregion
# region Mixing quantification measures Particle data
def mixing_dim_particle_data(store_trg_areas, loaded_img_info, store_part_pos, max_striation_thick):
    store_con_particle_data = get_concentration_from_particles(store_trg_areas, loaded_img_info, store_part_pos,
                                                               max_striation_thick)
    print('Concentration from particles')
    intensity_measures = segregation_intensity_ifp(store_con_particle_data, store_part_pos, store_trg_areas)
    print(intensity_measures)
    print("σ: ", intensity_measures[0][0][0])
    print("CoV: ", intensity_measures[0][0][1])
    print("M: ", intensity_measures[0][0][2])
    print("Cm: ", intensity_measures[0][0][3])
    print("Cmax: ", intensity_measures[0][0][4])
    print("Cmin: ", intensity_measures[0][0][5])
    print("n: ", intensity_measures[0][0][6])
    print("N: ", intensity_measures[0][0][7])
    store_max_str_thick = maximum_striation_thickness(max_striation_thick)
    print('Max str thickness: ', store_max_str_thick)
    pnn_distribution = pnn_method_distribution(store_trg_areas, store_part_pos)
    # print('PNN distribution: ', pnn_distribution)
    scl_segregation_ind = scale_segregation_for_particles(store_trg_areas, store_part_pos, pnn_distribution)
    print('Scale segregation index [σ_fpp, i_dis, xg]')
    print("σ_fpp:", scl_segregation_ind[0][0])
    print("i_dis:", scl_segregation_ind[0][1])
    print("xg:", scl_segregation_ind[0][2])


'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        REDUCTION IN THE SEGREGATION OF CONCENTRATION
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'''


# noinspection PyTypeChecker
def segregation_intensity_ifp(store_con_particle_data, store_part_positions, store_trg_areas):
    """
        CALCULATION OF SEGREGATION INTENSITY INDEX MEASURES
            Inputs:
            ∙ Concentration matrix (Particles/Area in a Quadrat)

            Output:
            ∙ Segregation Intensity Index factors = [σ, cov, m, ...] =
              [St. dev., Cof. of Variance, Mixing Index, ...]
            ∙ Other Target factors = [...,cm, c_max, c_min, n, NumOfParticles]
              [..., Mean Concentration, Max. Con. Value found, Min. Con. Value found, Number of measured points,
               Number of particles ]
        """
    # Define the  intensity_measures List
    intensity_measures = []
    i = 0
    for List1 in store_con_particle_data:
        # noinspection PyTypeChecker
        intensity_measures.append([[]])
        j = 0
        for item in List1:
            # Get number of particles and target area
            num_of_part = store_part_positions[i][j].__len__()
            tgt_area = store_trg_areas[i][j].Width * store_trg_areas[i][j].Height
            # Get mean and standard deviation of the previous matrix ----------------------------------------
            stat_measure = statistical_measures_particles(item, tgt_area, num_of_part)
            cm = stat_measure[0]
            st_dev = stat_measure[1]
            cov = 0
            m = 1
            if st_dev > 0:
                cov = st_dev / cm
                m = 1 - cov
                m = 0 if m < 0 else m
            c_max = stat_measure[3]
            c_min = stat_measure[2]
            n = stat_measure[4]
            int_measures = [st_dev, cov, m, cm, c_max, c_min, n, num_of_part]
            intensity_measures[i][j] = int_measures
            j = j + 1
        i = i + 1
    return intensity_measures
    # NormalizeCoV()
    # Defines intensity_measures[image_index][Target number]={σ, cov, m, cm, c_max, c_min, n, Num_Particles}


'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        REDUCTION IN THE SCALE OF CONCENTRATION
   %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'''


def maximum_striation_thickness(max_str_thick):
    """

    :rtype: list
    :param max_str_thick: max str thickness
    :return: store_max_str_thick
    """
    store_max_str_thick = []
    i = 0
    for List1 in max_str_thick:
        store_max_str_thick.append([])
        for item in List1:
            store_max_str_thick[i] = item
        i = i + 1
    return store_max_str_thick
    # Defines store_max_str_thick[image_index][Target number]=Max. Striation Thickness


def pnn_method_distribution(store_trg_areas, store_part_pos):
    """
    CALCULATION OF THE PNN METHOD
    Inputs: 
    ∙ Hexagonal grid 
    ∙ Particle positions

    Output: 
    ∙ PNN Distribution (Distance xi distribution from Grid Point to closest particles

    Kukukova, 2011
    """
    pnn_distribution = [[]]
    i = 0
    for List1 in store_trg_areas:
        pnn_distribution[i].append([])
        j = 0
        for item in List1:
            # Define ideal particle position points in an Hexagonal grid
            num_of_part = store_part_pos[i][j].__len__()
            # print('num oif part')
            # print(num_of_part)
            hexagonal_grid = ideal_particle_position(item, num_of_part)
            xi = np.zeros(hexagonal_grid.__len__())
            k = 0
            for point in hexagonal_grid:
                s = math.pow(item.Width, 2) + math.pow(item.Height, 2)
                xi[k] = math.sqrt(s)
                for point_eva in store_part_pos[i][j]:
                    s = math.pow(point.X - point_eva.X, 2) + math.pow(point.Y - point_eva.Y, 2)
                    dist = math.sqrt(s)
                    if dist < xi[k]:
                        xi[k] = dist
                k = k + 1
            pnn_distribution[i][j] = xi
            j = j + 1
        i = i + 1
    return pnn_distribution
    # Defines pnn_distribution[#of picture,#of target area]=>PNN Distribution


def scale_segregation_for_particles(store_trg_areas, store_part_pos, pnn_distribution):
    """
    CALCULATION OF SCALE OF SEGREGATION MEASURES
    Inputs:
    ∙ PNN Distribution
    ∙ Hexagonal grid dimensions


    Output:
    ∙ Scale of Segregation factors = [σ_fpp, i_dis, xg]
      [Filtered point-particle deviation, Index of dispersion, Spatial resolution]
    Kukukova 2011, 2017
    """
    scl_segregation_ind = []
    i = 0
    for List1 in store_trg_areas:
        scl_segregation_ind.append([])
        j = 0
        for item in List1:
            k = int(math.sqrt(store_part_pos[i][j].__len__()))
            # Hexagonal Grid dimensions
            dx = item.Width / (k * 1.0)
            dy = item.Height / (k * 1.0)
            # Calculate Spatial Resolution (xg)
            xg = float((dx + 2 * math.sqrt(dx * dx + dy * dy)) / (3 * 1.0))
            # Define array of indexes
            scale_dim = [0.0, 0.0, 0.0]
            m = pnn_distribution[i][j].__len__()
            xs = 0
            xr = xg / 2  # xr is equal to one-half of the spatial resolution
            xi_mean = 0
            for Xi in pnn_distribution[i][j]:
                if Xi >= xr:
                    xs = xs + math.pow(Xi - xr, 2)
                xi_mean = xi_mean + Xi
            xi_mean = xi_mean / (m * 1.0)
            var_fpp = xs / ((m * 1.0) - 1)
            i_dis = var_fpp / xi_mean
            print("PNN_parameters [xr, xg, dx, dy, k, xs, var_fpp, xi_mean, m]:" + str(
                [xr, xg, dx, dy, k, xs, var_fpp, xi_mean, m]))
            scale_dim[0] = math.sqrt(var_fpp)  # σ_fpp -> Filtered point-particle deviation
            scale_dim[1] = i_dis  # i_dis -> Index of dispersion
            scale_dim[2] = xg  # xg -> Spatial resolution
            scl_segregation_ind[i] = scale_dim
            j = j + 1
        i = i + 1
    return scl_segregation_ind


# endregion
# region Auxiliar functions for Particle tracking calculations
def calculate_mean_spacing(img_ind, trg, img_to_process, store_part_pos):
    mean_spa = 0
    for point in store_part_pos[img_ind][trg]:
        s = math.pow(img_to_process[img_ind].Width, 2) + math.pow(img_to_process[img_ind].Height, 2)
        mean_s = int(math.sqrt(s))
        for point_evl in store_part_pos[img_ind][trg]:
            if point != point_evl:
                s = math.pow(point.X - point_evl.X, 2) + math.pow(point.Y - point_evl.Y, 2)
                dist = int(math.sqrt(s))
                if dist < mean_s:
                    mean_s = dist
        mean_spa = mean_spa + mean_s

    mean_spa = int(mean_spa / store_part_pos[img_ind][trg].__len__())
    return mean_spa * 2


def initiate_max_str_thickness(img_to_process, store_part_pos, store_trg_areas):
    defined_transects = []
    m_part_spacing = []
    max_str_thickness = []
    horizontal = True
    for img_ind in range(img_to_process.__len__()):
        defined_transects.append([])
        max_str_thickness.append([])
        m_part_spacing.append([])
        tgt_ind = 0
        while tgt_ind < store_trg_areas[img_ind].__len__():
            mean_s = calculate_mean_spacing(img_ind, tgt_ind, img_to_process, store_part_pos)
            m_part_spacing[img_ind].append([])
            max_str_thickness[tgt_ind].append([])
            # noinspection PyTypeChecker
            m_part_spacing[img_ind][tgt_ind] = mean_s
            # Define new Rectangle Transect for the assessed target
            defined_transects[img_ind].append([])
            # Evaluate for all the transect positions possible
            x = store_trg_areas[img_ind][tgt_ind].X
            y = store_trg_areas[img_ind][tgt_ind].Y
            if horizontal:
                height = mean_s
                width = store_trg_areas[img_ind][tgt_ind].Width
                ini = y
                limit = y + store_trg_areas[img_ind][tgt_ind].Height - 1 - mean_s
            else:
                height = store_trg_areas[img_ind][tgt_ind].Height
                width = mean_s
                ini = x
                limit = x + store_trg_areas[img_ind][tgt_ind].Width - 1 - mean_s
            mst = mean_s
            j = ini
            while j < limit:
                if horizontal:
                    rect_t = Rectangle(x, j, width, height)
                else:
                    rect_t = Rectangle(j, y, width, height)
                # noinspection PyTypeChecker
                defined_transects[img_ind][tgt_ind] = rect_t
                mst_evl = calculate_max_str_thickness(img_ind, tgt_ind, mean_s, store_part_pos, defined_transects,
                                                      store_trg_areas)
                if mst_evl > mst:
                    mst = mst_evl
                j = j + 1
            max_str_thickness[img_ind][tgt_ind] = mst
            tgt_ind = tgt_ind + 1
    return m_part_spacing, defined_transects, max_str_thickness


def calculate_max_str_thickness(img_ind, trg_ind, m_part_spacing, store_part_pos, defined_transects, store_trg_areas):
    horizontal = True
    # Evaluate if is horizontal or Vertical
    if defined_transects[img_ind][trg_ind].Height == store_trg_areas[img_ind][trg_ind].Height:
        horizontal = False
    array = []
    ind_tgt = 0
    j = 0
    for item in store_part_pos[img_ind][trg_ind]:
        x1 = defined_transects[img_ind][trg_ind].X
        x2 = x1 + defined_transects[img_ind][trg_ind].Width - 1
        y1 = defined_transects[img_ind][trg_ind].Y
        y2 = y1 + defined_transects[img_ind][trg_ind].Height - 1
        if x1 <= item.X <= x2 and y1 <= item.Y <= y2:
            array.append(0)  # Adds one more space into the array
            if horizontal:
                array[j] = item.X
            else:
                array[j] = item.Y
            j = j + 1
        ind_tgt = ind_tgt + 1
    if array.__len__() > 1:
        array.sort()
        mst = 0
        start = array[0]
        ind_tgt = 1
        while ind_tgt < array.__len__():
            striation = array[ind_tgt] - array[ind_tgt - 1]
            if striation > m_part_spacing:
                if array[ind_tgt - 1] - start > mst:
                    mst = array[ind_tgt - 1] - start
                start = array[ind_tgt]

            if ind_tgt == array.__len__() - 1:
                if array[ind_tgt] - start > mst:
                    mst = array[ind_tgt] - start
            ind_tgt = ind_tgt + 1
        if mst < m_part_spacing:
            mst = m_part_spacing
    else:
        mst = m_part_spacing
    return mst


def get_concentration_from_particles(store_target_areas, loaded_image_info, store_part_positions,
                                     max_striation_thickness):
    # Copy Images, Images Info and Stored targets
    store_target_areas2 = []
    f = 0
    for List1 in store_target_areas:
        store_target_areas2.append([[]])
        for item in List1:
            store_target_areas2[f] = item
        f = f + 1
    loaded_image_info2 = []
    for item in loaded_image_info:
        loaded_image_info2.append(item)
    # Compute concentration matrix from particle distribution
    store_con_particle_data = []
    i = 0
    while i < store_target_areas.__len__():
        store_con_particle_data.append([[]])
        j = 0
        for item in store_target_areas[i]:
            mst = max_striation_thickness[i][j]
            width = item.Width
            height = item.Height
            # Define the number of columns and rows in each target
            col = math.floor(width / mst)
            dist_x = (width - col * mst) / 2
            row = math.floor(height / mst)
            dist_y = (height - row * mst) / 2
            concentration = np.zeros(shape=(col, row))
            n = 1
            while n <= row:
                y_cmp = store_target_areas[i][j].Y + dist_y
                y_start = y_cmp + (n - 1) * mst - 1
                y_limit = y_cmp + n * mst - 1
                m = 1
                while m <= col:
                    x_comp = store_target_areas[i][j].X + dist_x
                    x_start = x_comp + (m - 1) * mst - 1
                    x_limit = x_comp + m * mst - 1
                    nn = 0
                    for part in store_part_positions[i][j]:
                        x = part.X
                        y = part.Y
                        if x_start <= x < x_limit and y_start <= y < y_limit:
                            nn = nn + 1
                    area = mst * mst
                    concentration[m - 1][n - 1] = nn / (area * 1.0)
                    m = m + 1
                n = n + 1
            store_con_particle_data[i][j] = concentration
            j = j + 1
        i = i + 1
    return store_con_particle_data


def statistical_measures_particles(data, target_area, num_of_particles):
    """
    COMPUTE STATISTICAL MEASURES 

    StatisticalArray=[μ,σ,x_min,x_max,n]=[Mean, Std. Dev., Min Value, Max Value, Number of Data] = [0,1,2,3,4]
    
    :rtype: float list
    :type data: float list
    :param data: array
    :param target_area: integer target area
    :param num_of_particles: integer number of particles
    :return: stat_measures Statistical measures array
    """
    # Define variables
    st_dev = 0
    x_max = 0
    x_min = data[0][0]
    n = 0
    stat_measures = [0.0, 0.0, 0.0, 0.0, 0.0]
    # Calculate mean value
    mean_v = num_of_particles / float(target_area)
    # Find n, x_max & x_min and Compute Standard deviation
    xc = 0
    while xc < data.shape[0]:
        yc = 0
        while yc < data.shape[1]:
            st_dev = st_dev + (data[xc][yc] - mean_v) ** 2
            if x_max < data[xc][yc]:
                x_max = data[xc][yc]
            if x_min > data[xc][yc]:
                x_min = data[xc][yc]
            n = n + 1
            yc = yc + 1
        xc = xc + 1
    st_dev = (st_dev / n) ** 0.5
    stat_measures[0] = mean_v
    stat_measures[1] = st_dev
    stat_measures[2] = x_min
    stat_measures[3] = x_max
    stat_measures[4] = n
    return stat_measures


def ideal_particle_position(tgt_area, num_of_part):
    """

    :rtype: list
    :param tgt_area: rectangle structure c#
    :param num_of_part: integer number of particles
    :return: ideal_part_pos float list
    """
    k = int(num_of_part ** 0.5)
    # print(k)
    x = tgt_area.X
    y = tgt_area.Y
    width = tgt_area.Width
    height = tgt_area.Height
    dist_x = width / (k * 1.0)
    dist = (width - int(math.ceil((dist_x - 1) / 2.0)) - (k - 1) * dist_x) / 2.0
    ini_x = x + int(math.ceil(dist))
    dist_y = height / (k * 1.0)
    dist = int(math.ceil(((height - dist_y * k) / 2.0)))
    ini_y = y + dist + int(math.ceil(dist_y / 2.0))
    ideal_part_pos = ListPoints(0, 0).list_points(k * k)  # point structure
    # print(ideal_part_pos.__len__())
    i = 0
    n = 0
    while n < k:
        y_part = ini_y + n * dist_y
        m = 0
        while m < k:
            if n % 2 == 0:
                x_part = ini_x + m * dist_x
            else:
                x_part = (ini_x + dist_x / 2) + (m * dist_x)
            ideal_part_pos[i] = Point(x_part, y_part)  # point structure
            i = i + 1
            m = m + 1
        n = n + 1
    return ideal_part_pos


# endregion
# region Mixing quantification measures Concentration data

def mixing_dim_concentration_data(img_to_process, store_target_areas, store_concentration_data, images_with_references,
                                  loaded_img_info, dark_checkbox, intensity_measures, hor_var_diagrams,
                                  ver_var_diagrams):
    # "4. Compute measures" 
    store_concentration_data = concentration_matrix(img_to_process, store_target_areas, store_concentration_data,
                                                    images_with_references, loaded_img_info, dark_checkbox)
    print('Concentration matrix')
    intensity_measures = segregation_intensity_index_factors(intensity_measures, img_to_process,
                                                             store_concentration_data)
    print('segregation')
    hor_var_diagrams = horizontal_var_diagram(hor_var_diagrams, store_concentration_data, img_to_process,
                                              intensity_measures)

    print('h diagram')
    print(hor_var_diagrams)
    ver_var_diagrams = vertical_var_diagram(ver_var_diagrams, img_to_process, store_concentration_data,
                                            intensity_measures)

    print('v diagram')
    print(ver_var_diagrams)
    m_length_scales = mean_length_scales(img_to_process, store_concentration_data, intensity_measures, hor_var_diagrams,
                                         ver_var_diagrams)
    exposure_indexes = calculate_exposure_indexes(img_to_process, store_concentration_data)
    print('exposure completed')
    print(exposure_indexes)
    # ("Calculation completed")
    print('intensity_measures')
    print(intensity_measures)
    print('mean_len_scales')
    print(m_length_scales)
    print('exposure_indexes')
    print(exposure_indexes)
    # Evaluate is there are negative Mixing Index
    need_for_inlets = False
    for List1 in intensity_measures:
        for item in List1:  # type: List[float]
            if item[1] > 1:
                need_for_inlets = True

    if need_for_inlets:
        print(["There are negative Mixing Indexes (M < 0)", "\n", "\n",
               "Please define the unmixed condition by defining the inlets"])


def concentration_matrix(img_to_process, store_trg_areas, store_concentration_data, images_with_references,
                         loaded_image_info, dark_checkbox):
    # Copy Images, Images Info and Stored targets
    store_target_areas2 = []
    f = 0
    for List1 in store_trg_areas:
        store_target_areas2.append([Rectangle(0, 0, 1, 1)])
        for item in List1:
            store_target_areas2[f] = item
        f = f + 1
    loaded_image_info2 = []
    for item in loaded_image_info:
        loaded_image_info2.append(item)
    # Define the  store_concentration_data List
    if store_concentration_data.__len__() > 0:
        store_concentration_data = []
    i = 0
    while i < img_to_process.__len__():
        store_concentration_data.append([[]])
        i = i + 1
    # Determine if Images has to be calibrated
    '''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    ->ALL THE REFERENCE AND ASSESSED IMAGES MUST BE ASSIGNED IN THE images_with_references LIST 
    ->ALSO EACH IMAGE TO BE CALIBRATED HAS TO HAVE AT LEAST TWO REFERENCE IMAGES
    ->IF THERE ARE ONE IMAGE THAT HAS NOT BEING ASSIGNED IN THE images_with_references LIST,
      THE CALIBRATION WILL NOT BE PERFORMED
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/'''
    cal_performed = True
    ims_in_calibration = 0
    for item in images_with_references:
        if item.__len__() == 1:
            cal_performed = False
        if item.__len__() > 1:
            ims_in_calibration = ims_in_calibration + item.__len__() + 1
    if ims_in_calibration < loaded_image_info.__len__():
        cal_performed = False
    # region Performing Calibration: Calculate Concentrations using calibration data
    if cal_performed:
        print('calibration')
        # Determine what type of calibration is going to be performed (COMPLEX or SIMPLE)
        cond1 = True
        i = 0
        for List1 in images_with_references:
            for item in List1:
                width = img_to_process[i].Width
                height = img_to_process[i].Height
                width2 = img_to_process[item.ImageIndex].Width
                height2 = img_to_process[item.ImageIndex].Height
                if width != width2 or height != height2:
                    cond1 = False  # Images with different dimensions
                j = 0
                while j < store_trg_areas[i].__len__():
                    tgt_width = store_trg_areas[i][j].Width
                    tgt_height = store_trg_areas[i][j].Height
                    tgt_width2 = store_trg_areas[item.ImageIndex][j].Width
                    tgt_height2 = store_trg_areas[item.ImageIndex][j].Height
                    if tgt_width != tgt_width2 or tgt_height != tgt_height2:
                        cond1 = False
                    j = j + 1
            i = i + 1
        # region COMPLEX Calibration: Same Image Size and Same Target Sizes (COMPLEX CALIBRATION)
        if cond1:
            img = 0
            while img < img_to_process.__len__():
                if images_with_references[img].__len__() > 0:
                    # Image filtration
                    filtered_image = img_to_process[img].clone(Rectangle(0, 0, img_to_process[img].Width,
                                                                         img_to_process[img].Height))  # bitmap type
                    # Apply Mean Filter (to eliminate local noise)
                    filtered_image = cv2.medianBlur(filtered_image, 5)
                    # Apply Grayscale filter
                    filtered_image = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2GRAY)  # create and app greyscale fil
                    # Define Array of Reference Images for the Image to be calibrated
                    ref_img = BitMap(filtered_image).bitmaps(images_with_references[img].__len__())
                    k = 0
                    while k < images_with_references[img].__len__():
                        img_index = images_with_references[img][k].ImageIndex
                        ref_filtered_image = img_to_process[img_index].clone(
                            Rectangle(0, 0, img_to_process[img_index].Width,
                                      img_to_process[img_index].Height))  # bitmap type
                        # Apply median filter
                        ref_filtered_image = cv2.medianBlur(ref_filtered_image, 5)
                        # Apply Grayscale filter
                        ref_filtered_image = cv2.cvtColor(ref_filtered_image, cv2.COLOR_BGR2GRAY)
                        ref_img[k] = ref_filtered_image
                        k = k + 1
                    num_targets = store_trg_areas[img].__len__()
                    if num_targets > 0:
                        j = 0
                        while j < num_targets:
                            # Array size
                            m = store_trg_areas[img][j].Width
                            n = store_trg_areas[img][j].Height
                            concentration_array = np.zeros(shape=(m, n))  # list of m x n float type
                            # Target area square/rectangle dimension
                            xi = store_trg_areas[img][j].X
                            xf = xi + store_trg_areas[img][j].Width - 1
                            yi = store_trg_areas[img][j].Y
                            yf = yi + store_trg_areas[img][j].Height - 1
                            xc = xi
                            while xc <= xf:
                                yc = yi
                                while yc <= yf:
                                    # Perform a linear regression for each pixel
                                    # [i,0]->Intensity [i,1]->concentration
                                    array = np.zeros(shape=(images_with_references[img].__len__, 2))
                                    # Define array to perform linear regression
                                    k = 0
                                    while k < images_with_references[img].__len__():
                                        array[k][0] = BitMap(ref_img[k]).pixel(xc, yc, layer='R')
                                        array[k][1] = images_with_references[img][k].Concentration / 100.0
                                        k = k + 1
                                    # Linear Regression
                                    # c_mean and Mean Intensity
                                    c_mean = 0.0
                                    i_mean = 0.0
                                    kk = images_with_references[img].__len__()
                                    k = 0
                                    while k < kk:
                                        c_mean = c_mean + array[k][1]
                                        i_mean = i_mean + array[k][0]
                                        k = k + 1
                                    c_mean = c_mean / (kk * 1.0)
                                    i_mean = i_mean / (kk * 1.0)
                                    #  Calculate sc, si, r
                                    sc = 0.0
                                    si = 0.0
                                    r = 0.0
                                    k = 0
                                    while k < kk:
                                        sc = sc + ((array[k][1] - c_mean) ** 2)
                                        si = si + ((array[k][0] - i_mean) ** 2)
                                        r = r + (array[k][1] - c_mean) * (array[k][0] - i_mean)
                                        k = k + 1
                                    if si == 0 or sc == 0:
                                        con_c = c_mean
                                    else:
                                        r = r / ((sc * si) ** 0.5)
                                        sc = ((sc / (kk - 1)) ** 0.5)
                                        si = ((si / (kk - 1)) ** 0.5)
                                        b = r * sc / (si * 1.0)
                                        a = c_mean - b * i_mean * 1.0
                                        intensity = filtered_image.pixel(xc, yc, 'R')
                                        con_c = b * intensity + a
                                    x = (xc - xi)
                                    y = (yc - yi)
                                    concentration_array[x][y] = con_c
                                    yc = yc + 1
                                xc = xc + 1
                            store_concentration_data[img] = concentration_array  # Stores Concentration Array
                            j = j + 1
                img = img + 1
        # endregion
        # region SIMPLE Calibration
        # Different Image Size or Different Target Sizes (SIMPLE CALIBRATION)
        if not cond1:
            img = 0
            while img < img_to_process.__len__():
                if images_with_references[img].__len__() > 0:
                    # Image filtration
                    filtered_image = img_to_process[img].clone(
                        Rectangle(0, 0, img_to_process[img].Width, img_to_process[img].Height))
                    # Apply Mean Filter (to eliminate local noise)
                    filtered_image = cv2.medianBlur(filtered_image, 5)
                    # Apply Grayscale filter
                    filtered_image = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2GRAY)
                    num_targets = store_trg_areas[img].__len__()
                    if num_targets > 0:
                        j = 0
                        while j < num_targets:
                            # Array size
                            m = store_trg_areas[img][j].Width
                            n = store_trg_areas[img][j].Height
                            concentration_array = np.zeros(shape=(m, n))
                            # Target area square/rectangle dimension
                            xi = store_trg_areas[img][j].X
                            xf = xi + store_trg_areas[img][j].Width - 1
                            yi = store_trg_areas[img][j].Y
                            yf = yi + store_trg_areas[img][j].Height - 1
                            # PERFORM LINEAR REGRESSION FOR EACH TARGET
                            # [i,0]->Intensity [i,1]->concentration
                            array = np.zeros(shape=(images_with_references[img].__len__(), 2))  # array count x 2
                            # Define array to perform linear regression
                            k = 0
                            while k < images_with_references[img].__len__():
                                array[k][0] = get_mean_intensity_value(images_with_references[img][k].ImageIndex, j,
                                                                       img_to_process, store_trg_areas)
                                array[k][1] = images_with_references[img][k].Concentration / 100.0
                                k = k + 1
                            # Linear Regression
                            # c_mean and Mean Intensity
                            c_mean = 0.0
                            i_mean = 0.0
                            kk = images_with_references[img].__len__()
                            k = 0
                            while k < kk:
                                c_mean = c_mean + array[k][1]
                                i_mean = i_mean + array[k][0]
                                k = k + 1
                            c_mean = c_mean / (kk * 1.0)
                            i_mean = i_mean / (kk * 1.0)
                            #  Calculate sc, si, r
                            sc = 0.0
                            si = 0.0
                            r = 0.0
                            k = 0
                            while k < kk:
                                sc = sc + ((array[k][1] - c_mean) ** 2)
                                si = si + ((array[k][0] - i_mean) ** 2)
                                r = r + (array[k][1] - c_mean) * (array[k][0] - i_mean)
                                k = k + 1
                            r = r / ((sc * si) ** 0.5)
                            sc = ((sc / (kk - 1)) ** 0.5)
                            si = ((si / (kk - 1)) ** 0.5)
                            b = r * sc / si
                            a = c_mean - b * i_mean
                            xc = xi
                            while xc <= xf:
                                yc = yi
                                while yc <= yf:
                                    intensity = filtered_image.pixel(xc, yc, 'R')
                                    if sc == 0 or si == 0:
                                        con_c = c_mean
                                    else:
                                        con_c = b * intensity + a
                                    x = (xc - xi)
                                    y = (yc - yi)
                                    concentration_array[x][y] = con_c
                                    yc = yc + 1
                                xc = xc + 1
                            store_concentration_data[img][j] = concentration_array  # Stores Concentration Array
                            j = j + 1
                img = img + 1
        # endregion

    # region Without Calibration performed
    #  Calculate Concentrations by performing a normalization of data
    if not cal_performed:
        '''/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        DEFINE CONCENTRATION ARRAYS FOR EACH TARGET DEFINED BY PERFORMING A NORMALIZATION OF THE DATA
        Inputs:
        ∙ target_area and img_to_process
        ∙ Image loaded

        Output:
        ∙ Concentration arrays
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/'''
        print('not calibration')
        i = 0
        while i < img_to_process.__len__():
            # Image filtration
            index = i
            filtered_image = filter_image(img_to_process[index])
            i_max_min = get_intensity_max_min(filtered_image)  # point structure
            i_max = i_max_min.X
            i_min = i_max_min.Y
            num_targets = store_trg_areas[i].__len__()
            if num_targets > 0:
                j = 0
                while j < num_targets:
                    # Array size
                    m = store_trg_areas[index][j].Width
                    n = store_trg_areas[index][j].Height
                    concentration_array = np.zeros(shape=(m, n))
                    # Target area square/rectangle dimension---------------------------------------------------------
                    xi = store_trg_areas[index][j].X
                    xf = xi + store_trg_areas[index][j].Width - 1
                    yi = store_trg_areas[index][j].Y
                    yf = yi + store_trg_areas[index][j].Height - 1
                    xc = xi
                    while xc <= xf:
                        yc = yi
                        while yc <= yf:
                            x = (xc - xi)
                            y = (yc - yi)
                            # Gets Intensity value of the grayscale Image
                            intensity = filtered_image.pixel(xc, yc, 'R')
                            con_c = (intensity - i_min) / ((i_max - i_min) * 1.0)
                            if dark_checkbox:
                                con_c = 1 - con_c  # Dark Areas Higher concentration
                            concentration_array[x][y] = con_c
                            yc = yc + 1
                        xc = xc + 1
                    store_concentration_data[index][j] = concentration_array  # Stores Concentration Array
                    j = j + 1
            i = i + 1
    return store_concentration_data
    # endregion
    # Defines store_concentration_data[image_index][Target number]=Concentration array


'''/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
REDUCTION IN THE SEGREGATION OF CONCENTRATION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/'''


def segregation_intensity_index_factors(intensity_measures, img_to_process, store_con_data):
    """
    CALCULATION OF SEGREGATION INTENSITY INDEX MEASURES
    Inputs: 
    ∙ Concentration matrix (Normalized or Calibrated intensity values)

    Output: 
    ∙ Segregation Intensity Index factors = [σ, cov, m, ...] =
      [St. dev., Cof. of Variance, Mixing Index, ...]
    ∙ Other Target factors = [...,cm, c_max, c_min, n]
      [..., Mean Concentration, Max. Con. Value found, Min. Con. Value found, Number of measured points]

    Hector Betancourt Cervantes, 2017
    """
    # Define the  intensity_measures List
    if intensity_measures.__len__() > 0:
        intensity_measures = []
    i = 0
    while i < img_to_process.__len__():
        intensity_measures.append([[]])
        i = i + 1
    j = 0
    for List1 in store_con_data:
        if List1.__len__() > 0:
            i = 0
            for item in List1:  # type: list
                # Get mean and standard deviation of the previous matrix
                stat_measure = statistical_measures(item)
                cm = stat_measure[0] * 1.0
                st_dev = stat_measure[1] * 1.0
                cov = 0.0
                m = 1.0
                if st_dev > 0:
                    cov = st_dev / cm
                    m = 1 - cov
                c_max = stat_measure[3] * 1.0
                c_min = stat_measure[2] * 1.0
                n = stat_measure[4] * 1.0
                int_measures = [st_dev, cov, m, cm, c_max, c_min, n]
                intensity_measures[j][i] = int_measures
                i = i + 1
        j = j + 1
    return intensity_measures
    # NormalizeCoV()
    # Defines intensity_measures[image_index][Target number]={σ, cov, m, cm, c_max, c_min, n}


'''/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
REDUCTION IN THE SCALE OF CONCENTRATION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/'''


def horizontal_var_diagram(hor_var_diagrams, store_con_data, img_to_process, intensity_measures):
    """
    HORIZONTAL VARIOGRAM CALCULATION
    Inputs:
    ∙ Standarized concentration matrix

    Output:
    ∙ Variogram array: γx(h)=variogram[h]

    Computing method proposed by Alena Kukukova, 2010
    """
    # Define Horizontal_Var_diagrams List
    if hor_var_diagrams.__len__() > 0:
        hor_var_diagrams = []
    k = 0
    while k < img_to_process.__len__():
        hor_var_diagrams.append([[]])
        k = k + 1
    i = 0
    for List1 in store_con_data:
        if List1.__len__() > 0:
            for j in range(List1.__len__()):
                # Variables
                # Get standarized concentration matrix
                standard_data = standarized_array(i, j, store_con_data, intensity_measures)
                print("standard data size")
                print(standard_data.shape)
                #  Maximum separation distance is one half of the target area
                # max_h = total # of separation distances to evaluate
                max_h = int(math.floor(standard_data.shape[0] / 2.0))
                # Define Horizontal Var diagram array
                h_var_diagram = np.zeros(max_h + 1)  # array float
                h_var_diagram[0] = 0
                #  loop through all separation distances  for zero dist, var is 0, so we don't need to calculate
                dist = 1
                while dist <= max_h:
                    sum2 = 0
                    nh = 0
                    # Loop through all rows (y-direction)
                    y = 0
                    while y < standard_data.shape[1]:
                        # for each row, loop through columns (x-direction)
                        x = 0
                        while x < standard_data.shape[0] - dist:
                            sum2 = sum2 + (standard_data[x][y] - standard_data[(x + dist)][y] ** 2)
                            nh = nh + 1
                            x = x + 1
                        y = y + 1
                    h_var_diagram[dist] = sum2 / (2 * nh)  # Var diagram calculation from equation
                    dist = dist + 1
                # noinspection PyTypeChecker
                hor_var_diagrams[i][j] = h_var_diagram
                print("h var diagram size")
                print(h_var_diagram.size)
        i = i + 1
    return hor_var_diagrams
    # Defines Horizontal_Var_diagrams[image_index][Target number] = Horizontal Var diagram


def vertical_var_diagram(ver_var_diagrams, img_to_process, store_con_data, intensity_measures):
    """
    VERTICAL VARIOGRAM CALCULATION
    Inputs:
    ∙ target_area
    ∙ Standarized concentration matrix

    Output:
    ∙ Variogram array: γx(h)=variogram[h]

    Computing method proposed by Alena Kukukova, 2010
    """
    # Define Horizontal_Var_diagrams List
    if ver_var_diagrams.__len__() > 0:
        ver_var_diagrams = []
    k = 0
    while k < img_to_process.__len__():
        ver_var_diagrams.append([[]])
        k = k + 1
    i = 0
    for List1 in store_con_data:
        if List1.__len__() > 0:
            for j in range(List1.__len__()):
                # Get standarized concentration matrix
                std_data = standarized_array(i, j, store_con_data, intensity_measures)
                # Variables
                #  Maximum separation distance is one half of the target area
                # max_h = total # of separation distances to evaluate
                max_h = int(math.floor(std_data.shape[1] / 2.0))
                # Define Horizontal Variogram array
                v_var_diagram = np.zeros(max_h + 1)
                v_var_diagram[0] = 0
                #  loop through all separation distances  for zero dist, var is 0, so we don't need to calculate
                dist = 1
                while dist <= max_h:
                    sum2 = 0
                    nh = 0
                    # Loop through all rows (y-direction)
                    x = 0
                    while x < std_data.shape[0]:
                        # for each row, loop through columns (x-direction)
                        y = 0
                        while y < std_data.shape[1] - dist:
                            sum2 = sum2 + (std_data[x][y] - std_data[x][(y + dist)] ** 2)
                            nh = nh + 1
                            y = y + 1
                        x = x + 1
                    v_var_diagram[dist] = sum2 / (2 * nh)  # Variogram calculation from equation
                    dist = dist + 1
                # noinspection PyTypeChecker
                ver_var_diagrams[i][j] = v_var_diagram
        i = i + 1
    return ver_var_diagrams
    # Defines Vertical_Var_diagrams[image_index][Target number] = Vertical Variogram


def mean_length_scales(img_to_process, store_concentration_data, intensity_measures, hor_var_diagrams,
                       ver_var_diagrams):
    """
    MEAN LENGTH SCALE CALCULATION
    Inputs:
    ∙ target_area
    ∙ Horizontal or vertical variogram vector


    Output:
    ∙ Mean length scale: Lv = p∙[δγx/δh]^(-1)
        Horizontal(1) or Vertical(2) mean length scale

    Computing method proposed by Alena Kukukova, 2010
    """
    # Define mean_len_scales List
    mean_len_scales = []
    k = 0
    while k < img_to_process.__len__():
        mean_len_scales.append([[]])
        k = k + 1
    i = 0
    for List1 in store_concentration_data:
        if List1.__len__() > 0:
            for j in range(List1.__len__()):
                # Read standarized intensity array from the requested target
                lms = Coordinate(0, 0)  # structure coordinate
                p = intensity_measures[i][j][3]  # The proportion of the minor species in the sample region = C_mean
                # Horizontal(1) or Vertical(2) mean length scale calculation
                #  Units:pixels/concentration^2
                lms.X = p * (1 / (hor_var_diagrams[i][j][1] - hor_var_diagrams[i][j][0]))
                #  Units:pixels/concentration^2
                lms.Y = p * (1 / (ver_var_diagrams[i][j][1] - ver_var_diagrams[i][j][0]))
                # noinspection PyTypeChecker
                mean_len_scales[i][j] = lms
        i = i + 1
    return mean_len_scales
    # Defines mean_len_scales[image_index][Target number].X = Hor_mean_length_scale  .Y = Ver_mean_length_scale


'''/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
RATE OF CHANGE IN SEGREGATION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/'''


def calculate_exposure_indexes(img_to_process, store_concentration_data):
    """
    HORIZONTAL VARIOGRAM CALCULATION
    Inputs:
    ∙ Concentration matrix

    Output:
    ∙ Exposure: Ε≅∑∑〖(1/2)⋅K⋅a(i,j)⋅(Ci-Cj) 〗

    Computing method proposed by Alena Kukukova, 2009
    """
    # Define exposure_indexes List
    exposure_indexes = []
    k = 0
    while k < img_to_process.__len__():
        exposure_indexes.append([])
        k = k + 1
    i = 0
    for List1 in store_concentration_data:
        if List1.__len__() > 0:
            for j in range(List1.__len__()):
                # Get Concentration Array
                data = store_concentration_data[i][j]
                # Define Variables
                exp = 0
                xf = np.array(data).shape[0]
                yf = np.array(data).shape[1]
                # Calculate Exposure
                x = 0
                while x < xf:
                    y = 0
                    while y < yf:
                        if x != 0:
                            exp = exp + 0.5 * abs(data[x][y] - data[x - 1][y])
                        if y != 0:
                            exp = exp + 0.5 * abs(data[x][y] - data[x][y - 1])
                        if x != xf - 1:
                            exp = exp + 0.5 * abs(data[x][y] - data[x + 1][y])
                        if y != yf - 1:
                            exp = exp + 0.5 * abs(data[x][y] - data[x][y + 1])
                        y = y + 1
                    x = x + 1
                exposure_indexes[i] = exp
        i = i + 1
    return exposure_indexes
    # Defines exposure_indexes[image_index][Target number] = Exposure


# endregion
# region Auxiliar functions and Intensity Information Arrays


def filter_image(img_ori):
    """
    :rtype: bitmap
    :param img_ori: bitmap image
    """
    filtered_image = img_ori.clone(Rectangle(0, 0, img_ori.Width, img_ori.Height))
    # Apply Mean Filter (to eliminate local noise)
    filtered_image = cv2.medianBlur(filtered_image, 5)
    # Apply Grayscale filter
    filtered_image = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2GRAY)
    # Apply Histogram remapping
    # filtered_image = new HistogramEqualization().Apply(filtered_image)
    return BitMap(filtered_image)


def get_mean_intensity_value(img_index, target, img_to_process, store_target_areas):
    """
    :param store_target_areas: target areas of each image
    :param img_to_process: images to process
    :rtype: float
    :param img_index: 
    :param target:
    """
    tgt_mean = 0.0
    ref_filtered_image = img_to_process[img_index].clone(
        Rectangle(0, 0, img_to_process[img_index].Width, img_to_process[img_index].Height))
    # Apply median filter
    ref_filtered_image = cv2.medianBlur(ref_filtered_image, 5)
    # Apply Grayscale filter
    ref_filtered_image = cv2.cvtColor(ref_filtered_image, cv2.COLOR_BGR2GRAY)
    # Array size
    # ConcentrationArray = np.zeros(shape=(m, n))
    # Target area square/rectangle dimension
    xi = store_target_areas[img_index][target].X
    xf = xi + store_target_areas[img_index][target].Width - 1
    yi = store_target_areas[img_index][target].Y
    yf = yi + store_target_areas[img_index][target].Height - 1
    nn = 0.0
    xc = xi
    while xc <= xf:
        yc = yi
        while yc <= yf:
            tgt_mean = tgt_mean + BitMap(ref_filtered_image).pixel(xc, yc, layer='R')
            nn = nn + 1
            yc = yc + 1
        xc = xc + 1
    tgt_mean = tgt_mean / (nn * 1.0)
    return tgt_mean
    # Get Mean Intensity value in a target of a REFERENCE IMAGE


def get_intensity_max_min(filtered_image):
    """

    :rtype: float point
    :param filtered_image: bitmap file
    """
    intensity_max_and_min = Point(0.0, 0.0)
    intensity_max_and_min.X = 0  # I_max
    intensity_max_and_min.Y = 255  # I_min
    # Target area square/rectangle dimension
    xf = filtered_image.Width
    yf = filtered_image.Height
    # Define intensity array in "IntensityArrayData
    x = 0
    while x < xf:
        y = 0
        while y < yf:
            pix_val = filtered_image.pixel(x, y, 'R')
            if pix_val > intensity_max_and_min.X:
                intensity_max_and_min.X = pix_val
            if pix_val < intensity_max_and_min.Y:
                intensity_max_and_min.Y = pix_val
            y = y + 1
        x = x + 1
    return intensity_max_and_min


def statistical_measures(data):
    # type: (list) -> list
    """
    COMPUTE STATISTICAL MEASURES
    Inputs:
    ∙ Array

    StatisticalArray=[μ,σ,x_min,x_max,n]=[Mean, Std. Dev., Min Value, Max Value, Number of Data] = [0,1,2,3,4]

    Output:
    ∙ Statistical measures array
    :return: stat_measures
    :rtype: list
    :param data: array
    """
    # Define variables
    mean = 0.0
    st_dev = 0.0
    x_max = 0.0
    if data.shape.__len__() == 1:
        data = data.reshape((data.__len__(), 1))
    x_min = data[0][0]
    n = 0.0
    stat_measures = [0.0, 0.0, 0.0, 0.0, 0.0]
    # Find Mean, n, x_max & x_min
    xc = 0
    while xc < np.array(data).shape[0]:
        yc = 0
        while yc < np.array(data).shape[1]:
            if x_max < data[xc][yc]:
                x_max = data[xc][yc]
            if x_min > data[xc][yc]:
                x_min = data[xc][yc]
            mean = mean + data[xc][yc]
            n = n + 1
            yc = yc + 1
        xc = xc + 1
    mean = mean / (n * 1.0)
    # Compute Standard deviation
    xc = 0
    while xc < np.array(data).shape[0]:
        yc = 0
        while yc < np.array(data).shape[1]:
            st_dev = st_dev + ((data[xc][yc] - mean) ** 2)
            yc = yc + 1
        xc = xc + 1
    st_dev = ((st_dev / (n * 1.0)) ** 0.5)
    stat_measures[0] = mean
    stat_measures[1] = st_dev
    stat_measures[2] = x_min
    stat_measures[3] = x_max
    stat_measures[4] = n
    return stat_measures


def standarized_array(image_index, target, store_con_data, intensity_measures):
    """
    DEFINE STANDARIZED ARRAY
    Inputs:
    ∙ Array
    ∙ Statistical measures: Mean (μ) and Standard deviation (σ)

    Xsi=(xi-μ)/σ

    Output:
    ∙ Standarized array [0,1,2,3,4]
    :param intensity_measures:
    :param store_con_data:
    :param image_index:
    :param target:
    """
    # Declare normalized intensity array
    # m = The number of rows in the concentration array -> data.shape[0)
    # n = The number of columns in the concentration array -> data.shape[1)
    m = int(np.array(store_con_data[image_index][target]).shape[0])
    n = int(np.array(store_con_data[image_index][target]).shape[1])
    standarized_data = np.zeros(shape=(m, n))
    # Declare other variables
    # Get Mean and standard deviation to standarize the array
    mean = intensity_measures[image_index][target][3]
    st_dev = intensity_measures[image_index][target][0]
    # Define standarized intensity array
    xc = 0
    while xc < m:
        yc = 0
        while yc < n:
            xi = store_con_data[image_index][target][xc][yc]
            standarized_data[xc][yc] = (xi - mean) / st_dev
            yc = yc + 1
        xc = xc + 1
    return standarized_data
    # Function that returns normalized intensity array of a target area


def get_intensity_array(image_index, target_area, img_to_process2, store_target_areas2):
    """
    get_intensity_array
    DEFINE INTENSITY ARRAY
    Inputs:
    ∙ target_area and img_to_process
    ∙ Image loaded

    Output:
    ∙ Intensity array
    :param store_target_areas2: store areas to process from each image
    :param img_to_process2: images to process
    :param image_index:
    :param target_area:
    """
    index = image_index
    filtered_image = img_to_process2[index]
    filtered_image = filter_image(filtered_image)
    # Target area square/rectangle dimension
    xi = store_target_areas2[index][target_area].X
    xf = xi + store_target_areas2[index][target_area].Width - 1
    yi = store_target_areas2[index][target_area].Y
    yf = yi + store_target_areas2[index][target_area].Height - 1
    # Array dimension
    x = (xf - xi)
    y = (yf - yi)
    # Variables
    intensity_array_data = np.zeros(shape=(x + 1, y + 1))  # Declare array of intensity values
    # Define intensity array in "intensity_array_data[]"
    xc = xi
    while xc <= xf:
        yc = yi
        while yc <= yf:
            x = (xc - xi)
            y = (yc - yi)
            # Gets Intensity value of the grayscale Image
            intensity_array_data[x][y] = BitMap(filtered_image).pixel(xc, yc, layer='R')
            yc = yc + 1
        xc = xc + 1
    return intensity_array_data
    # Function that returns the intensity array of a target area


def full_image_data_array(image_index, img_to_process2):
    """
    DEFINE INTENSITY ARRAY
    Inputs:
    ∙ Image loaded

    Output:
    ∙ Full image intensity array
    :param img_to_process2:
    :param image_index:
    """
    filtered_image = img_to_process2[image_index]
    filtered_image = filter_image(filtered_image)
    # Target area square/rectangle dimension
    xf = filtered_image.Width
    yf = filtered_image.Height
    # Variables
    image_intensity_array = np.zeros(shape=(xf, yf))  # Declare array of intensity values
    # Define intensity array in "IntensityArrayData[]"
    x = 0
    while x < xf:
        y = 0
        while y < yf:
            # Gets Intensity value of the grayscale Image
            image_intensity_array[x][y] = BitMap(filtered_image).pixel(x, y, layer='R')
            y = y + 1
        x = x + 1
    return image_intensity_array
    # Function that returns the intensity array of the loaded image


def blob_detection_image(img_to_process, threshold_value, store_target_areas):
    store_blob_rectangles = []
    store_part_pos = []  # type: List[List[Point]]
    # Multiple object detection----------------------------------------------------------
    # Filter by Area.
    area_blob = [1, 50]
    blob_counter = BlobDetector(threshold=[150, 255], flag_area=True, limit_area=area_blob, flag_circularity=False,
                                min_cir=0.050, flag_convexity=False, convexity=[0.01, 1], flag_inertia=False,
                                ratio_inertia=[0.00, 1], flag_color=False)
    # Filter IMAGE---------------------------------------------------------------------
    index = 0
    for img in img_to_process:
        assert isinstance(img, BitMap)
        trg_ind = 0
        # noinspection SpellCheckingInspection
        for area in store_target_areas[index]:
            # Store Rectangles and Particles positions
            store_blob_rectangles.append([])
            store_part_pos.append([])
            filtered_img = img.clone(area)
            original_img = img.clone(area)
            # cv2.imshow('Image selected area', filtered_img)
            # cv2.waitKey(0)
            plt.imshow(filtered_img)
            plt.show()
            cv2.imwrite('0.jpg', filtered_img)
            # It converts the BGR color space of image to HSV color space
            hsv = cv2.cvtColor(filtered_img, cv2.COLOR_BGR2HSV)
            # Threshold of blue in HSV space
            lower_blue = np.array([85, 100, 100])
            upper_blue = np.array([130, 255, 255])
            lower_red = np.array([0, 100, 100])
            upper_red = np.array([10, 255, 255])
            lower_green = np.array([50, 100, 100])
            upper_green = np.array([65, 255, 255])
            lower_yellow = np.array([18, 100, 100])
            upper_yellow = np.array([38, 255, 255])
            # preparing the mask to overlay
            # mask = cv2.inRange(hsv, lower_blue, upper_blue)
            mask = cv2.inRange(hsv, lower_red, upper_red)
            # cv2.imshow('mask of the image', mask)
            # cv2.waitKey(0)
            cv2.imwrite('1.jpg', mask)
            # The black region in the mask has the value of 0,
            # so when multiplied with original image removes all non-blue regions
            aux = cv2.bitwise_and(filtered_img, filtered_img, mask=mask)
            aux1 = cv2.cvtColor(aux, cv2.COLOR_HSV2RGB)
            # cv2.imshow('Image filtered color', aux)
            # cv2.waitKey(0)
            plt.imshow(aux)
            plt.show()
            cv2.imwrite('2.jpg', aux)
            filtered_img = aux1
            # Grayscale filter
            aux2 = cv2.cvtColor(aux, cv2.COLOR_BGR2GRAY)
            # cv2.imshow('Image filtered gray', aux2)
            # cv2.waitKey(0)
            plt.imshow(aux2)
            plt.show()
            cv2.imwrite('3.jpg', aux2)
            filtered_img = aux2
            # ApplyThreshold
            # Blue
            # kernel = np.ones((3, 3), np.uint8)
            # filtered_img = cv2.dilate(filtered_img, kernel, iterations=2)
            # kernel = np.ones((6, 6), np.uint8)
            # filtered_img = cv2.erode(filtered_img, kernel, iterations=2)
            # green
            kernel = np.ones((2, 2), np.uint8)
            filtered_img = cv2.dilate(filtered_img, kernel, iterations=1)
            kernel = np.ones((2, 2), np.uint8)
            filtered_img = cv2.erode(filtered_img, kernel, iterations=1)
            ret, filtered_img = cv2.threshold(filtered_img, threshold_value, 255, cv2.THRESH_BINARY_INV)
            # cv2.imshow('Image filtered erode', filtered_img)
            # cv2.waitKey(0)
            plt.imshow(filtered_img)
            plt.show()
            cv2.imwrite('4.jpg', filtered_img)
            # Perform Blob detection
            key_points = blob_counter.detect_blobs(filtered_img)
            rectangles = blob_counter.rectangles(key_points)
            store_blob_rectangles[index] = rectangles
            store_part_pos[index] = [[]]
            for i in range(rectangles.__len__()):
                part_coord = Point(int(key_points[i].pt[0]), int(key_points[i].pt[1]))
                store_part_pos[index][trg_ind].append(part_coord)
        index = index + 1
    im_with_keypoints = cv2.drawKeypoints(original_img, key_points, np.array([]), (255, 255, 255),
                                          cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    for point in key_points:
        im_with_keypoints2 = cv2.circle(original_img, (int(point.pt[0]), int(point.pt[1])), int(point.size),
                                        (255, 255, 255), 4)
    cv2.imshow('Image with ' + str(store_part_pos[0][0].__len__()) + ' blobs', im_with_keypoints2)
    cv2.waitKey(0)
    plt.imshow(im_with_keypoints2)
    plt.show()
    cv2.imwrite('5.jpg', im_with_keypoints2)
    return store_part_pos, store_blob_rectangles
# endregion
