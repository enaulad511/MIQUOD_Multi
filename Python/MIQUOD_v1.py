# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 26/3/2020  at 18:00 $'

import cv2
import Mixing_QMPD as Mf
from typing import List

if __name__ == '__main__':
    im = cv2.imread('3colors_unmixed.png')
    # r = cv2.selectROI('Image select', im)
    # print(r)
    img_to_process = [Mf.BitMap(im)]
    LoadedImageInfo = ['Img1']
    images_with_references = [[Mf.RefImg(0, 1)]]
    # r = [144, 2, 295, 295]
    # im2 = im[r[1]:r[1] + r[3], r[0]: r[0] + r[2]]
    # r1 = Mf.Rectangle(2, 10, 556, 617)
    # r1 = Mf.Rectangle(10, 17, 2700, 2180)  # inlet_3d
    r1 = Mf.Rectangle(24, 82, 2700, 2180)  # inlet_3d
    # r1 = Mf.Rectangle(50, 50, 2700, 2180)  # inlet_3d
    store_target_areas = [[r1]]  # [#of picture][#of target area]=>rectangle dimensions
    store_target_areas2 = [r1]
    inlet_targets = [[0]]
    img_to_process2 = img_to_process
    storeConcentrationData = [[0.0]]
    dark_checkbox = False  # Dark Areas Higher concentration
    LoadedImageInfo2 = LoadedImageInfo
    IntensityMeasures = [[0.0, 0.0],
                         [0.0, 0.0]]  # type: List[List[float]] # [#picture][#target area]=>{σ,CoV,M,Cm,Cmax,Cmin, N}
    Horizontal_Var_diagrams = [[0.0, 0.0], [0.0, 0.0]]  # [#of picture][#of target area]=> Horizontal Variogram
    Vertical_Var_diagrams = [[0.0, 0.0], [0.0, 0.0]]  # [#of picture][#of target area]=> Vertical Variogram
    MeanLengthScales = [[Mf.Coordinate(0, 0)],
                        [Mf.Coordinate(0, 0)]]  # [#of picture,#of target area].X=> Horizontal mean length scale; Y vert
    ExposureIndexes = [[0.0, 0.0], [0.0, 0.0]]  # [#of picture][#of target area]=> Exposure
    threshold_value = 50
    storePartPositions, store_blob_rectangles = Mf.blob_detection_image(img_to_process, threshold_value,
                                                                        store_target_areas)
    print('particles detected: ' + str(storePartPositions[0][0].__len__()))
    MaxStrTargetSel = False
    MaxStrTransSel = False
    MeanSpacing = 0  # Mean spacing between particles in a target area
    TargetNum = 0  # Target area to define transect
    Trans_rect = Mf.Rectangle(0, 0, 1, 1)
    MeanSpacingParticles, DefinedTransects, max_striation_thick = Mf.initiate_max_str_thickness(img_to_process,
                                                                                                storePartPositions,
                                                                                                store_target_areas)
    print('mean space calculated: ' + str(MeanSpacingParticles))
    print('defined transects calculated:  ' + str(DefinedTransects))
    print('Max striation calculated:   ' + str(max_striation_thick))
    # MaximumStriationThickness = [[0, 0], [0, 0]]
    # endregion
    # region Calculated Mixing dimensions (Particles)
    storeConParticleData = [[0.0, 0.0], [0.0, 0.0]]  # [#of picture][#of target area]=>Particle concentration array
    storeMaxStrThickness = [[0, 0],
                            [0, 0]]  # type: List[List[int]] # [#picture][#targetarea]=>Maximum Striation Thickness
    PNNDistribution = [[0.0, 0.0], [0.0, 0.0]]  # [#of picture,#of target area]=>PNN Distribution
    ScaleSegregationIndexes = [[0.0, 0.0], [0.0, 0.0]]  # [#of picture,#of target area]=> {σfpp, Idisp, Xg}
    #Mf.mixing_dim_concentration_data(img_to_process, store_target_areas, storeConcentrationData,
    #                                 images_with_references, LoadedImageInfo, dark_checkbox, IntensityMeasures,
    #                                 Horizontal_Var_diagrams, Vertical_Var_diagrams)
    Mf.mixing_dim_particle_data(store_target_areas, LoadedImageInfo, storePartPositions, max_striation_thick)
