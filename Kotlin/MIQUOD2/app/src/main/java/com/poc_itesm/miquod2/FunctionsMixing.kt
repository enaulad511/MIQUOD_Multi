package com.poc_itesm.miquod2

import org.opencv.core.*
import org.opencv.core.Core.bitwise_and
import org.opencv.core.Core.inRange
import org.opencv.features2d.SimpleBlobDetector
import org.opencv.features2d.SimpleBlobDetector_Params
import org.opencv.imgproc.Imgproc
import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.pow

// var imgs_filtered: MutableList<Mat> = mutableListOf(Mat(10, 10, CvType.CV_8UC3, Scalar(0.0, 0.0, 0.0)))
class FunctionsMixing(
    private var imgToProcesses: MutableList<MyBitMap>,
    private var storeTargetAreas: MutableList<MutableList<MyClassRectangle>>,
    private var storeConcentrationData: MutableList<MutableList<MutableList<MutableList<Double>>>>,
    private var imagesWithReferences: MutableList<MutableList<RefImg>>,
    private var loadedImgInfo: MutableList<String>,
    private var darkCheckbox: Boolean,
    private var intensityMeasures: MutableList<MutableList<MutableList<Double>>>,
    private var horVarDiagrams: MutableList<MutableList<MutableList<Double>>>,
    private var verVarDiagrams: MutableList<MutableList<MutableList<Double>>>,
    private var storePartPositionFun: MutableMap<String, MutableList<MutableList<MutableList<MyClassPoint>>>>,
    private var maxStriationThick: MutableList<MutableList<Double>>,
    private var storeConParticleData: MutableList<MutableList<List<List<Double>>>>,
    private var pnnDistribution: MutableList<MutableList<MutableList<Double>>>,
    var MeanSpacingParticles: MutableList<MutableList<Double>>,
    var definedTransects: MutableList<MutableList<MyClassRectangle>>,
    var parametersResultFun: MutableMap<String, MutableList<MutableMap<String, String>>>,
    private val colorResult: String = "no"
){

    fun mixingDimParticleData() {
        getConcentrationFromParticles()
        println("Concentration from particles")
        println(storeConParticleData)
        segregationIntensityIfp()
        println("Intensity Measures")
        println(intensityMeasures)
        saveDataIntensityParticle()
//        parametersResult["Intensity Measures"]=intensityMeasures.toString()
        val storeMaxStrThick = maximumStriationThickness()
        println("Max str thickness")
        println(storeMaxStrThick)
        for ((i, item) in storeMaxStrThick[0].withIndex()){
            parametersResult[colorResult]!![i]["Max Striation Thickness"] = "%.4f".format(item)
        }
        pnnMethodDistribution()
        println("PNN distribution")
        val sclSegregationInd = scaleSegregationForParticles()
        println("Scale segregation index")
        println(sclSegregationInd)
//        [Filtered point-particle deviation, Index of dispersion, Spatial resolution]
        for ((i, item) in sclSegregationInd.withIndex()){
            parametersResult[colorResult]!![i]["Filtered point-particle deviation"]="%.4f".format(item[0])
            parametersResult[colorResult]!![i]["Index of dispersion"]="%.4f".format(item[1])
            parametersResult[colorResult]!![i]["Spatial resolution"]="%.4f".format(item[2])
        }
    }
    fun mixingDimConcentrationData() {
        println("Mixing Concentration Data")
        // "4. Compute measures"
        concentrationMatrix()
        println("Concentration matrix")
        segregationIntensityIndexFactors()
        println("segregation intensity")
        println("intensity_measures")
        println(intensityMeasures)
        saveDataIntensityConcentration()
//        parametersResult["Intensity Measures"]=intensityMeasures.toString()
        horizontalVarDiagram()
        println("h diagram")
        println(horVarDiagrams)
        verticalVarDiagram()
        println("v diagram")
        println(verVarDiagrams)
        val mLengthScales = meanLengthScales()
        print("mean l scales")
        val exposureIndexes = calculateExposureIndexes()
        println("exposure completed")
        // ("Calculation completed")
        println("mean_len_scales")
        println(mLengthScales)
//        parametersResult["Mean Length Scales"]=mLengthScales.toString()
        println("exposure_indexes")
        println(exposureIndexes)
        for ((i, item) in exposureIndexes.withIndex()){
            parametersResult[colorResult]!![i]["Exposure Indexes"] = "%.4f".format(item)
        }
        // Evaluate is there are negative Mixing Index
        var needForInlets = false
        for (List1 in intensityMeasures) {
            for (item in List1) { // type: List[float]
                if (item[0] > 1) {
                    needForInlets = true
                }
            }
        }
        if (needForInlets) {
            println("There are negative Mixing Indexes (M < 0)")
            println("Please define the unmixed condition by defining the inlets")
        }
    }

    private fun saveDataIntensityConcentration(){
        /*Output:
        ∙ Segregation Intensity Index factors = [σ, cov, m, ...] =
        [St. dev., Cof. of Variance, Mixing Index, ...]
        ∙ Other Target factors = [...,cm, c_max, c_min, n]
        [..., Mean Concentration, Max. Con. Value found, Min. Con. Value found, Number of measured points]*/
        for ((i, item) in intensityMeasures[0].withIndex()){
            parametersResult[colorResult]!![i]["Stn. Dev."]="%.4f".format(item[0])
            parametersResult[colorResult]!![i]["Cof. of Variance"]="%.4f".format(item[1])
            parametersResult[colorResult]!![i]["Mixing Index"]="%.4f".format(item[2])
            parametersResult[colorResult]!![i]["Mean Concentration"]="%.4f".format(item[3])
            parametersResult[colorResult]!![i]["Max Con. Value"]="%.4f".format(item[4])
            parametersResult[colorResult]!![i]["Min Con. Value"]="%.4f".format(item[5])
            parametersResult[colorResult]!![i]["Number of Points"]="%.4f".format(item[6])
        }
    }
    private fun saveDataIntensityParticle(){
        /*Output:
        ∙ Segregation Intensity Index factors = [σ, cov, m, ...] =
          [St. dev., Cof. of Variance, Mixing Index, ...]
        ∙ Other Target factors = [...,cm, c_max, c_min, n, NumOfParticles]
          [..., Mean Concentration, Max. Con. Value found, Min. Con. Value found, Number of measured points,
           Number of particles ]*/
        for ((i, item) in intensityMeasures[0].withIndex()){
            parametersResult[colorResult]!![i]["Stn. Dev."]="%.4f".format(item[0])
            parametersResult[colorResult]!![i]["Cof. of Variance"]="%.4f".format(item[1])
            parametersResult[colorResult]!![i]["Mixing Index"]="%.4f".format(item[2])
            parametersResult[colorResult]!![i]["Mean Concentration"]="%.4f".format(item[3])
            parametersResult[colorResult]!![i]["Max Con. Value"]="%.4f".format(item[4])
            parametersResult[colorResult]!![i]["Min Con. Value"]="%.4f".format(item[5])
            parametersResult[colorResult]!![i]["Number of Points"]="%.4f".format(item[6])
            parametersResult[colorResult]!![i]["Number of Particles"]="%.4f".format(item[7])
        }
    }

// region Mixing quantification measures Particle data

/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    REDUCTION IN THE SEGREGATION OF CONCENTRATION
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/


    private fun segregationIntensityIfp(){
/*            CALCULATION OF SEGREGATION INTENSITY INDEX MEASURES
                Inputs:
                ∙ Concentration matrix (Particles/Area in a Quadrant)

                Output:
                ∙ Segregation Intensity Index factors = [σ, cov, m, ...] =
                  [St. dev., Cof. of Variance, Mixing Index, ...]
                ∙ Other Target factors = [...,cm, c_max, c_min, n, NumOfParticles]
                  [..., Mean Concentration, Max. Con. Value found, Min. Con. Value found, Number of measured points,
                   Number of particles ]
            */

        // define the  intensity_measures List
//        var intensity_measures: MutableList<MutableList<MutableList<Double>>> = arrayListOf((arrayListOf(arrayListOf(0.0))))
        var i = 0
        var cov: Double
        var m: Double
        var numOfParticles: Int
        var tgtArea: Double
        var statMeasure: List<Double>
        var cm: Double
        var stDev: Double
        intensityMeasures = arrayListOf(arrayListOf(arrayListOf(0.0)))
        for (List1 in storeConParticleData) {
//            intensity_measures.add([[]])
            for ((j, item) in List1.withIndex()) {
                // Get number of particles and target area
                numOfParticles = this.storePartPositionFun[colorResult]!![i][j].size
                tgtArea = this.storeTargetAreas[i][j].width * this.storeTargetAreas[i][j].height
                // Get mean and standard deviation of the previous matrix--------------------
                if (item.isNotEmpty()){
                    statMeasure = statisticalMeasuresParticles(item, tgtArea.toInt(), numOfParticles)
                    cm = statMeasure[0]
                    stDev = statMeasure[1]
                    cov = 0.0
                    m = 1.0
                    if (stDev > 0){
                        cov = stDev / cm
                        m = 1 - cov
                    }
                    if(j>0){
                        intensityMeasures[i].add(j, arrayListOf(stDev,
                            cov, m, cm, statMeasure[3], statMeasure[2],
                            statMeasure[4], numOfParticles.toDouble()))
                    }else{
                        intensityMeasures[i][j] = arrayListOf(stDev,
                            cov, m, cm, statMeasure[3], statMeasure[2],
                            statMeasure[4], numOfParticles.toDouble())
                    }
                }else{
                    println("Item is empty and indicates a bad target selected")
                    textErrorMain = "Item is empty and indicates a bad target selected"
                    helloViewModel.onError(true)
                }
            }
            i++
        }
        //return intensity_measures
        // NormalizeCoV()
        // defines intensity_measures [image_index][Target number] =
        // { σ, cov, m, cm, c_max, c_min, n, Num_Particles }
    }



/*'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    REDUCTION IN THE SCALE OF CONCENTRATION
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'''*/



    private fun maximumStriationThickness(): MutableList<MutableList<Double>> {
        /*"""
        :param max_str_thick: max str thickness
        :return: store_max_str_thick
        """*/
        return this.maxStriationThick
        // defines store_max_str_thick [image_index][Target number] = Max.Striation Thickness
    }


    private fun pnnMethodDistribution() {
        /*"""
        CALCULATION OF THE PNN METHOD
        Inputs:
        ∙ Hexagonal grid
        ∙ Particle positions

        Output:
        ∙ PNN Distribution (Distance xi distribution from Grid Point to closest particles

        Kukukova, 2011
        """*/

        /*var pnn_distribution: MutableList<MutableList<MutableList<Double>>> = arrayListOf(arrayListOf(
            arrayListOf(0.0)))*/
        var s: Double
        var numOfPart: Int
        var hexagonalGrid: MutableList<MyClassPoint>
        var xi: Array<Double>
        for ((i, List1) in this.storeTargetAreas.withIndex()) {
//            pnn_distribution[i].add([])
            for((j, item) in List1.withIndex()) {
//            // define ideal particle position points in an Hexagonal grid
                numOfPart = storePartPositionFun[colorResult]!![i][j].size
                hexagonalGrid = idealParticlePosition(item, numOfPart)
                xi = Array(hexagonalGrid.size) { _ -> 0.0 }
                for ((k, point) in hexagonalGrid.withIndex()) {
                    s = item.width.pow(2.0) + item.height.pow(2.0)
                    xi[k] = s.pow(0.5)
                    for (point_eva in this.storePartPositionFun[colorResult]!![i][j]){
                        s = (point.x - point_eva.x).pow(2.0) + (point.y - point_eva.y).pow(2.0)
                        val dist = s.pow(0.5)
                        if (dist < xi[k]) {
                            xi[k] = dist
                        }
                    }
                }
                if(j>0){
                    pnnDistribution[i].add(j, xi.toMutableList())
                }else{
                    pnnDistribution[i][j] = xi.toMutableList()
                }
            }
        }
//        return pnnDistribution
//        // defines pnn_distribution [#of picture, #of target area]=>PNN Distribution
    }


    private fun scaleSegregationForParticles(): MutableList<MutableList<Double>> {
        /*"""
        CALCULATION OF SCALE OF SEGREGATION MEASURES
        Inputs:
        ∙ PNN Distribution
        ∙ Hexagonal grid dimensions


        Output:
        ∙ Scale of Segregation factors = [σ_fpp, i_dis, xg]
          [Filtered point-particle deviation, Index of dispersion, Spatial resolution]
        Kukukova 2011, 2017
        """*/
        val sclSegregationInd: MutableList<MutableList<Double>> = arrayListOf(arrayListOf(0.0))
        var xiMean: Double
        var scaleDim: MutableList<Double>
        for ((i, List1) in this.storeTargetAreas.withIndex()) {
//            scl_segregation_ind.add([])
            for ((j, item) in List1.withIndex()) {
                val k = (storePartPositionFun[colorResult]!![i][j].size.toDouble().pow(0.5)).toInt()
                // Hexagonal Grid dimensions
                val dx = item.width / (k * 1.0)
                val dy = item.height / (k * 1.0)
                // Calculate Spatial Resolution(xg)
                val xg = ((dx + 2 * (dx * dx + dy * dy).pow(0.5)) / (3 * 1.0))
                // Define array of indexes
                scaleDim = arrayListOf(0.0, 0.0, 0.0)
                val m = pnnDistribution[i][j].size
                var xs = 0.0
                val xr = xg / 2  // xr is equal to one-half of the spatial resolution
                xiMean = 0.0
                for (Xi in this.pnnDistribution[i][j]) {
                    if (Xi >= xr) {
                        xs += (Xi - xr).pow(2.0)
                    }
                    xiMean += Xi
                }
                xiMean /= (m * 1.0)

                val varFpp = xs / ((m * 1.0) )
                val iDis = varFpp / xiMean
                scaleDim[0] = varFpp.pow(0.5)  //// σ_fpp -> Filtered point-particle deviation
                scaleDim[1] = iDis  //// i_dis -> Index of dispersion
                scaleDim[2] = xg  //// xg -> Spatial resolution
                if (j>0){
                    sclSegregationInd.add(j, scaleDim)
                }else{
                    sclSegregationInd[j] = scaleDim
                }
            }
        }
        return sclSegregationInd
    }
// endregion

// region Mixing quantification measures Concentration data

    private fun concentrationMatrix() {
        // Copy Images, Images Info and Stored targets
//        var storeTargetAreas2 = this.storeTargetAreas
        //var f: Int = 0
        /*for(List1 in store_trg_areas) {
            store_target_areas2.add([MyClassRectangle(0, 0, 1, 1)])
            for (item in List1) {
                store_target_areas2[f] = item
            }
            f++
        }*/
//        var loadedImageInfo2 = this.loadedImgInfo
        /*for (item in loaded_image_info) {
            loaded_image_info2.add(item)
        }*/
        // define the  store_concentration_data List
        /*if(store_concentration_data.size > 0) {
            store_concentration_data = []
        }
        var i = 0
        while(i < img_to_process.size) {
            store_concentration_data.add([[]])
            i += 1
        }*/
        storeConcentrationData = arrayListOf(arrayListOf(arrayListOf(arrayListOf(0.0))))
        // Determine if Images has to be calibrated
        var i: Int
        var j: Int
        var index: Int
        var img: Int         // index
        var k: Int          // index
        var imgIndex: Int        //image index
        var refFilteredImage: Mat   //image to filter
        var numTargets: Int          // number of targets
        var m: Double       // array columns
        var n: Double       // array columns
        var concentrationArray: MutableList<MutableList<Double>>
        var xc: Double  // index Target area
        var yc: Double  // index Target area
        var array: Array<Array<Double>>       // auxiliar array
        var cMean: Double   // c_mean intensity
        var iMean: Double   // i_mean intensity
        var sc: Double
        var si: Double
        var r: Double
        var conC: Double
        var filteredImage: MyBitMap
        var filteredImageMat: Mat
        var refImg: MutableList<Mat>
/*'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        ->ALL THE REFERENCE AND ASSESSED IMAGES MUST BE ASSIGNED IN THE images_with_references LIST
        ->ALSO EACH IMAGE TO BE CALIBRATED HAS TO HAVE AT LEAST TWO REFERENCE IMAGES
        ->IF THERE ARE ONE IMAGE THAT HAS NOT BEING ASSIGNED IN THE images_with_references LIST,
        THE CALIBRATION WILL NOT BE PERFORMED
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'''*/

        var calPerformed = true
        var imsInCalibration = 0
        for (item in imagesWithReferences) {
            if (item.size == 1) {
                calPerformed = false
            }
            if (item.size > 1){
                imsInCalibration += item.size
            }
        }
        if (imsInCalibration < this.loadedImgInfo.size-1) {
            calPerformed = false
        }
        // region Performing Calibration: Calculate Concentrations using calibration data
        var cond1: Boolean

        if (calPerformed) {
            print("calibration")
            // Determine what type of calibration is going to be performed (COMPLEX or SIMPLE)
            cond1 = true
            i = 0
            for (List1 in this.imagesWithReferences) {
                for (item in List1) {
                    val width = this.imgToProcesses[i].width
                    val height = this.imgToProcesses[i].height
                    val width2 = this.imgToProcesses[item.imageIndex].width
                    val height2 = this.imgToProcesses[item.imageIndex].height
                    if (width != width2 || height != height2) {
                        cond1 = false  // Images with different dimensions
                    }
                    j = 0
                    while (j < this.storeTargetAreas[i].size) {
                        val tgtWidth = this.storeTargetAreas[i][j].width
                        val tgtHeight = this.storeTargetAreas[i][j].height
                        val tgtWidth2 = this.storeTargetAreas[item.imageIndex][j].width
                        val tgtHeight2 = this.storeTargetAreas[item.imageIndex][j].height
                        if (tgtWidth != tgtWidth2 || tgtHeight != tgtHeight2) {
                            cond1 = false
                        }
                        j++
                    }
                }
                i++
            }
            // region COMPLEX Calibration: Same Image Size and Same Target Sizes (COMPLEX CALIBRATION)
            if (cond1){
                img = 0
                while (img < this.imgToProcesses.size) {
                    if (imagesWithReferences[img].size > 0) {
                        // Image filtration
                        filteredImageMat = this.imgToProcesses[img].clone(
                            MyClassRectangle(0.0, 0.0, this.imgToProcesses[img].width.toDouble(),
                                this.imgToProcesses[img].height.toDouble()))

                        // bitmap type
                        // Apply Mean Filter (to eliminate local noise)
                        Imgproc.medianBlur(filteredImageMat, filteredImageMat, 5)
                        // Apply Grayscale filter
                        Imgproc.cvtColor(filteredImageMat,filteredImageMat,Imgproc.COLOR_BGR2GRAY)
                        // define Array of Reference Images for the Image to be calibrated
                        refImg = MyBitMap(filteredImageMat).bitmaps(imagesWithReferences[img].size)
                        k = 0
                        while (k < imagesWithReferences[img].size) {
                            imgIndex = imagesWithReferences[img][k].imageIndex
                            refFilteredImage = this.imgToProcesses[imgIndex].clone(
                                MyClassRectangle(0.0, 0.0, this.imgToProcesses[imgIndex].width.toDouble(),
                                    this.imgToProcesses[imgIndex].height.toDouble()))  // bitmap type
                            // Apply median filter
                            Imgproc.medianBlur(refFilteredImage, refFilteredImage, 5)
                            // Apply Grayscale filter
                            Imgproc.cvtColor(refFilteredImage,refFilteredImage, Imgproc.COLOR_BGR2GRAY)
                            refImg[k] = refFilteredImage
                            k++
                        }
                        numTargets = storeTargetAreas[img].size
                        if (numTargets > 0) {
                            j = 0
                            while (j < numTargets) {
                                // Array size
                                m = this.storeTargetAreas[img][j].width
                                n = this.storeTargetAreas[img][j].height
                                concentrationArray = MutableList(m.toInt()) { ii -> MutableList(n.toInt()) { jj -> 0.0 } }
                                // Target area square/rectangle dimension
                                val xi = this.storeTargetAreas[img][j].x
                                val xf = xi + this.storeTargetAreas[img][j].width - 1
                                val yi = this.storeTargetAreas[img][j].y
                                val yf = yi + this.storeTargetAreas[img][j].height - 1
                                xc = xi
                                while (xc <= xf) {
                                    yc = yi
                                    while (yc <= yf) {
                                        // Perform a linear regression for each pixel
                                        // [i,0]->Intensity [i,1]->concentration
                                        array = Array(this.imagesWithReferences[img].size)
                                        { ii -> Array(2) { jj -> 0.0 }}
                                        // define array to perform linear regression
                                        k = 0
                                        while (k < imagesWithReferences[img].size) {
                                            array[k][0] = MyBitMap(refImg[k], 3).pixel(xc.toInt(),
                                                yc.toInt(), layer = "R")
                                            array[k][1] = imagesWithReferences[img][k].concentration / 100.0
                                            k += 1
                                        }
                                        // Linear Regression
                                        // c_mean and Mean Intensity
                                        cMean = 0.0
                                        iMean = 0.0
                                        val kk = imagesWithReferences[img].size
                                        k = 0
                                        while (k < kk) {
                                            cMean += array[k][1]
                                            iMean += array[k][0]
                                            k += 1
                                        }
                                        cMean /= (kk * 1.0)
                                        iMean /= (kk * 1.0)
                                        //  Calculate sc, si, r
                                        sc = 0.0
                                        si = 0.0
                                        r = 0.0
                                        k = 0
                                        while (k < kk) {
                                            sc += (array[k][1] - cMean).pow(2.0)
                                            si += (array[k][0] - iMean).pow(2.0)
                                            r += (array[k][1] - cMean) * (array[k][0] - iMean)
                                            k += 1
                                        }
                                        if (si == 0.0 || sc == 0.0){
                                            conC = cMean
                                        }
                                        else {
                                            r /= (sc * si).pow(0.5)
                                            sc = (sc / (kk - 1)).pow(0.5)
                                            si = (si / (kk - 1)).pow(0.5)
                                            val b = r * sc / (si * 1.0)
                                            val a = cMean - b * iMean * 1.0
                                            val bitImgFiltered = MyBitMap(filteredImageMat,3)
                                            val intensity = bitImgFiltered.pixel(xc.toInt(), yc.toInt(), "R")
                                            conC = intensity * b + a
                                        }
                                        val x = (xc - xi)
                                        val y = (yc - yi)
                                        concentrationArray[x.toInt()][y.toInt()] = conC
                                        yc++
                                    }
                                    xc++
                                }
                                storeConcentrationData[img][j] = concentrationArray  // Stores Concentration Array
                                j++
                            }
                        }
                    }
                    img++
                }
            }
            //  endregion
            //  region SIMPLE Calibration
            // Different Image Size or Different Target Sizes (SIMPLE CALIBRATION)

            if (!cond1) {
                img = 0
                while (img < this.imgToProcesses.size) {
                    if (imagesWithReferences[img].size > 0) {
                        // Image filtration
                        filteredImageMat = this.imgToProcesses[img].clone(
                            MyClassRectangle(0.0, 0.0, this.imgToProcesses[img].width.toDouble(),
                                this.imgToProcesses[img].height.toDouble()))
                        // Apply Mean Filter (to eliminate local noise)
                        Imgproc.medianBlur(filteredImageMat, filteredImageMat, 5)
                        // Apply Grayscale filter
                        Imgproc.cvtColor(filteredImageMat, filteredImageMat, Imgproc.COLOR_BGR2GRAY)
                        numTargets = this.storeTargetAreas[img].size
                        if (numTargets > 0) {
                            j = 0
                            while (j < numTargets) {
                                // Array size
                                m = this.storeTargetAreas[img][j].width
                                n = this.storeTargetAreas[img][j].height
                                concentrationArray = MutableList(m.toInt()) { ii -> MutableList(n.toInt()) { jj -> 0.0 } }
                                // Target area square/rectangle dimension
                                val xi = this.storeTargetAreas[img][j].x
                                val xf = xi + this.storeTargetAreas[img][j].width - 1
                                val yi = this.storeTargetAreas[img][j].y
                                val yf = yi + this.storeTargetAreas[img][j].height - 1
                                // PERFORM LINEAR REGRESSION FOR EACH TARGET
                                // [i,0]->Intensity [i,1]->concentration
                                array = Array(this.imagesWithReferences[img].size)
                                { ii -> Array(2) { jj -> 0.0 }}  // array count x 2
                                // define array to perform linear regression
                                k = 0
                                while (k < imagesWithReferences[img].size) {
                                    array[k][0] = getMeanIntensityValue(this.imagesWithReferences[img][k].imageIndex, j)
                                    array[k][1] = imagesWithReferences[img][k].concentration / 100.0
                                    k += 1
                                }
                                // Linear Regression
                                // c_mean and Mean Intensity
                                cMean = 0.0
                                iMean = 0.0
                                val kk = imagesWithReferences[img].size
                                k = 0
                                while (k < kk) {
                                    cMean += array[k][1]
                                    iMean += array[k][0]
                                    k += 1
                                }
                                cMean /= (kk * 1.0)
                                iMean /= (kk * 1.0)
                                //  Calculate sc, si, r
                                sc = 0.0
                                si = 0.0
                                r = 0.0
                                k = 0
                                while (k < kk) {
                                    sc += (array[k][1] - cMean).pow(2.0)
                                    si += (array[k][0] - iMean).pow(2.0)
                                    r += (array[k][1] - cMean) * (array[k][0] - iMean)
                                    k += 1
                                }
                                r /= (sc * si).pow(0.5)
                                sc = (sc / (kk - 1)).pow(0.5)
                                si = (si / (kk - 1)).pow(0.5)
                                val b = r * sc / si
                                val a = cMean - b * iMean
                                xc = xi
                                while (xc <= xf) {
                                    yc = yi
                                    while (yc <= yf) {
                                        val bitImgFiltered = MyBitMap(filteredImageMat,3)
                                        val intensity = bitImgFiltered.pixel(xc.toInt(), yc.toInt(), "R")

                                        conC = if (sc == 0.0 || si == 0.0) {
                                            cMean
                                        } else {
                                            b * intensity + a
                                        }
                                        val x = (xc - xi)
                                        val y = (yc - yi)
                                        concentrationArray[x.toInt()][y.toInt()] = conC
                                        yc++
                                    }
                                    xc++
                                }
                                storeConcentrationData[img][j] = concentrationArray  // Stores Concentration Array
                                j++
                            }
                        }
                    }
                    img++
                }
            }
// endregion
        }
//  region Without Calibration performed
//  Calculate Concentrations by performing a normalization of data
        if (!calPerformed) {
/*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            funINE CONCENTRATION ARRAYS FOR EACH TARGET DEFINED BY PERFORMING A NORMALIZATION OF THE DATA
                    Inputs:
            ∙ target_area and img_to_process
            ∙ Image loaded

                    Output:
            ∙ Concentration arrays
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            print("not calibration")
            i = 0
            while (i < imgToProcesses.size) {
                // Image filtration
                index = i
                filteredImage = filterImage(imgToProcesses[index])
                val iMaxMin = getIntensityMaxMin(filteredImage)  // point structure
                val iMax = iMaxMin.x
                val iMin = iMaxMin.y
                numTargets = storeTargetAreas[i].size
                if (numTargets > 0){
                    j = 0
                    while (j < numTargets) {
                        // Array size
                        m = this.storeTargetAreas[index][j].width
                        n = this.storeTargetAreas[index][j].height
                        concentrationArray = MutableList(m.toInt()) { ii -> MutableList(n.toInt()) { jj -> 0.0 } }
                        // Target area square/rectangle dimension------------
                        val xi = storeTargetAreas[index][j].x
                        val xf = xi + storeTargetAreas[index][j].width - 1
                        val yi = storeTargetAreas[index][j].y
                        val yf = yi + storeTargetAreas[index][j].height - 1
                        xc = xi
                        while (xc <= xf) {
                            yc = yi
                            while (yc <= yf) {
                                val x = (xc - xi)
                                val y = (yc - yi)
                                // Gets Intensity value of the grayscale Image
                                val intensity = filteredImage.pixel(xc.toInt(), yc.toInt(), "R")
                                conC = (intensity - iMin) / ((iMax - iMin) * 1.0)
                                if (darkCheckbox) {
                                    conC = 1 - conC  // Dark Areas Higher concentration
                                }
                                concentrationArray[x.toInt()][y.toInt()] = conC
                                yc++
                            }
                            xc++
                        }
                        if (j>0) {
                            storeConcentrationData[index].add(index = j, concentrationArray) // Stores Concentration Array
                        }else{
                            storeConcentrationData[index][j]= concentrationArray // Stores Concentration Array
                        }
                        j++
                    }
                }
                i++
            }
        }
    } // defines store_concentration_data[image_index][Target number]=Concentration array
// endregion

// region Auxiliary functions for Particle tracking calculations

    private fun getConcentrationFromParticles(){
        // Copy Images, Images Info and Stored targets
        // Compute concentration matrix from particle distribution
        /*var store_con_particle_data: MutableList<MutableList<MutableList<MutableList<Double>>>> = arrayListOf(arrayListOf(
            arrayListOf(arrayListOf(0.0))))*/
        var i = 0
        var n: Int
        var m: Int
        var xStart: Double
        var xLimit: Double
        var area: Double
        var concentration: List<List<Double>>
        var nn: Int
        var x: Double
        var y: Double
        while (i < storeTargetAreas.size) {
            var j = 0
            println("num targets concentration: ${storeTargetAreas[i].size}")
            for (item in storeTargetAreas[i]){
                val mst = maxStriationThick[i][j]
                val width = item.height-1  //review
                val height = item.width-1   //review
                // define the number of columns and rows in each target
                val col = floor(width / mst)
                val distX = (width - col * mst) / 2
                val row =  floor(height / mst)
                val distY = (height - row * mst) / 2
                println("Limits $row, $col")
                println("values $width, $height, $mst")
                if (row>0 && col>0){
                    concentration= MutableList(row.toInt()) { MutableList(col.toInt()) {0.0} }
                    n = 1
                    println(concentration)
                    println("Limits con array ${concentration.size}, ${concentration[0].size}")
                    while (n <= row) {
                        val yCmp = storeTargetAreas[i][j].y + distY
                        val yStart = yCmp + (n - 1) * mst - 1
                        val yLimit = yCmp + n * mst - 1
                        m = 1
                        while (m <= col) {
                            val xComp = storeTargetAreas[i][j].x + distX
                            xStart = xComp + (m - 1) * mst - 1
                            xLimit = xComp + m * mst - 1
                            nn = 0
                            for (part in this.storePartPositionFun[colorResult]!![i][j]) {
                                x = part.x
                                y = part.y
                                if (x in xStart..xLimit - 1 && y in yStart..yLimit - 1) {
                                    nn += 1
                                }
                            }
                            area = mst * mst
                            concentration[n - 1][m - 1] = nn / (area * 1.0)
                            m += 1
                        }
                        n += 1
                    }
                    if (j>0){
                        storeConParticleData[i].add(j, concentration)
                    }else{
                        storeConParticleData[i][j] = concentration
                    }
                    j += 1
                    println("stored concentration: $j")
                }else{
                    println("No concentration data can be calculated")
                }

            }
            i += 1
        }
/*        this.store_con_particle_data = store_con_particle_data*/
    }

    private fun statisticalMeasuresParticles(data: List<List<Double>>, targetArea: Int,
                                             numOfParticles: Int): List<Double> {
        /*"""
            COMPUTE STATISTICAL MEASURES

            StatisticalArray=[μ,σ,x_min,x_max,n]=[Mean, Std. Dev., Min Value, Max Value, Number of Data] = [0,1,2,3,4]
            :type data: float list
            :param data: array
            :param target_area: integer target area
            :param num_of_particles: integer number of particles
            :return: stat_measures Statistical measures array
            """*/

        //    // define variables
        var stDev = 0.0
        var xMax = 0.0
        var xMin = data[0][0]
        var n = 0
        val statMeasures = arrayListOf(0.0, 0.0, 0.0, 0.0, 0.0)
        //    // Calculate mean value
        val meanV = numOfParticles / (targetArea).toDouble()
        //    // Find n, x_max & x_min and Compute Standard deviation
        var xc = 0
        var yc: Int
        while (xc < data.size){
            yc = 0
            while (yc < data[0].size) {
                stDev += (data[xc][yc] - meanV).pow(2.0)
                if (xMax < data[xc][yc]){
                    xMax = data[xc][yc]
                }
                if (xMin > data[xc][yc]){
                    xMin = data[xc][yc]
                }
                n += 1
                yc += 1
            }
            xc += 1
        }
        stDev = (stDev / n).pow(0.5)
        statMeasures[0] = meanV
        statMeasures[1] = stDev
        statMeasures[2] = xMin
        statMeasures[3] = xMax
        statMeasures[4] = n.toDouble()
        return statMeasures
    }


    private fun idealParticlePosition(tgtArea: MyClassRectangle, numOfPart: Int): MutableList<MyClassPoint> {
        /*"""
        :param tgt_area: rectangle structure c#
        :param num_of_part: integer number of particles
        :return: ideal_part_pos float list
        """*/
        var dist: Double
        val k = numOfPart.toDouble().pow(0.5).toInt()
        val x = tgtArea.x
        val y = tgtArea.y
        val width = tgtArea.width
        val height = tgtArea.height
        val distX = width / (k * 1.0)
        dist = ((width - (ceil((distX - 1) / 2.0)).toInt() - (k - 1) * distX) / 2.0)
        val iniX = x + (ceil(dist)).toInt()
        val distY = height / (k * 1.0)
        dist = (ceil(((height - distY * k) / 2.0)))
        val iniY = y + dist + (ceil(distY / 2.0)).toInt()
        val idealPartPos = ListPoints(0.0, 0.0).listPoints(k * k)  // point structure
        var i = 0
        var n = 0
        var m: Int
        var xPart: Double
        var yPart: Double
        while (k > n) {
            yPart = iniY + n * distY
            m = 0
            while(m < k) {
                xPart = if (n % 2 == 0){
                    iniX + m * distX
                } else {
                    (iniX + distX / 2) + m * distX
                }
                idealPartPos[i] = MyClassPoint(xPart, yPart)  // point structure
                i += 1
                m += 1
            }
            n += 1
        }
        return idealPartPos
    }

    /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    REDUCTION IN THE SEGREGATION OF CONCENTRATION
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

    private fun segregationIntensityIndexFactors(){
        /*"""
            CALCULATION OF SEGREGATION INTENSITY INDEX MEASURES
            Inputs:
            ∙ Concentration matrix (Normalized or Calibrated intensity values)

            Output:
            ∙ Segregation Intensity Index factors = [σ, cov, m, ...] =
              [St. dev., Cof. of Variance, Mixing Index, ...]
            ∙ Other Target factors = [...,cm, c_max, c_min, n]
              [..., Mean Concentration, Max. Con. Value found, Min. Con. Value found, Number of measured points]

            Hector Betancourt Cervantes, 2017
            """*/

        // define the  intensity_measures List
        /*if (intensity_measures.size > 0){
            intensity_measures = []
        }*/
        intensityMeasures = arrayListOf(arrayListOf(arrayListOf(0.0)))
        var i = 1
        while (i < this.imgToProcesses.size) {
            intensityMeasures.add(arrayListOf(arrayListOf(0.0)))
            i += 1
        }
        var cov = 0.0
        var m = 1.0
        for ((j, List1) in storeConcentrationData.withIndex()) {
            if (List1.size > 0) {
                i = 0
                for (item in List1) {  // type: list
                    // Get mean and standard deviation of the previous matrix
                    val statMeasure = statisticalMeasures(item)
                    val cm = statMeasure[0] * 1.0
                    val stDev = statMeasure[1] * 1.0
                    if (stDev > 0) {
                        cov = stDev / cm
                        m = 1 - cov
                    }
                    if (i>0){
                        intensityMeasures[j].add(i, arrayListOf(stDev, cov, m, cm, statMeasure[3] * 1.0,
                            statMeasure[2] * 1.0, statMeasure[4] * 1.0))
                    }else{
                        intensityMeasures[j][i] = arrayListOf(stDev, cov, m, cm, statMeasure[3] * 1.0,
                            statMeasure[2] * 1.0, statMeasure[4] * 1.0)
                    }
                    i++
                }
            }
        }
        // NormalizeCoV()
        // defines intensity_measures[image_index][Target number]={σ, cov, m, cm, c_max, c_min, n}
    }

    /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    REDUCTION IN THE SCALE OF CONCENTRATION
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
    private fun horizontalVarDiagram() {
        /*"""
            HORIZONTAL VARIOGRAM CALCULATION
            Inputs:
            ∙ Standarized concentration matrix

            Output:
            ∙ Variogram array: γx(h)=variogram[h]

            Computing method proposed by Alena Kukukova, 2010
            """*/

        // define Horizontal_Var_diagrams List
        horVarDiagrams = arrayListOf(arrayListOf(arrayListOf(0.0)))
        var k = 0
        while (k < this.imgToProcesses.size){
            horVarDiagrams.add(arrayListOf(arrayListOf(0.0)))
            k++
        }
        var i = 0
        var x: Int
        var y: Int
        var hVarDiagram: MutableList<Double>
        var dist: Int
        var sum2: Double
        var nh: Double
        for (List1 in storeConcentrationData) {
            if (List1.size > 0) {
                for (j in 0 until List1.size) {
                    // Variables
                    // Get standarized concentration matrix
                    val standardData = standarizedArray(i, j)
                    //  Maximum separation distance is one half of the target area
                    // max_h = total // of separation distances to evaluate
                    val maxH = (floor(standardData.size / 2.0)).toInt()
                    // define Horizontal Var diagram array
                    hVarDiagram = MutableList(maxH + 1) { it * 0.0 }
//                    h_var_diagram[0] = 0.0
                    //  loop through all separation distances  for zero dist, var is 0, so we don't need to calculate
                    dist = 1
                    while (dist <= maxH) {
                        sum2 = 0.0
                        nh = 0.0
                        // Loop through all rows (y-direction)
                        y = 0
                        while (y < standardData[0].size) {
                            // for each row, loop through columns (x-direction)
                            x = 0
                            while (x < standardData.size - dist) {
                                sum2 += (standardData[x][y] - (standardData[(x + dist)][y]).pow(2.0))
                                nh++
                                x++
                            }
                            y++
                        }
                        hVarDiagram[dist] = sum2 / (2 * nh)  // Var diagram calculation from equation
                        dist++
                    }
                    if (j>0){
                        horVarDiagrams[i].add(j, hVarDiagram)
                    }else{
                        horVarDiagrams[i][j] = hVarDiagram
                    }


                }
            }
            i += 1
        }
        // defines Horizontal_Var_diagrams[image_index][Target number] = Horizontal Var diagram
    }

    private fun verticalVarDiagram() {
        /*"""
            VERTICAL VARIOGRAM CALCULATION
            Inputs:
            ∙ target_area
            ∙ Standarized concentration matrix

            Output:
            ∙ Variogram array: γx(h)=variogram[h]

            Computing method proposed by Alena Kukukova, 2010
            """*/

        // define Horizontal_Var_diagrams List
        verVarDiagrams = arrayListOf(arrayListOf(arrayListOf(0.0)))
        var k = 0
        while (k < this.imgToProcesses.size) {
            verVarDiagrams.add(arrayListOf(arrayListOf(0.0)))
            k++
        }
        var i = 0
//        var j = 0
        var x: Int
        var y: Int
        var stdData: MutableList<MutableList<Double>>
        var vVarDiagram: MutableList<Double>
        var maxH: Int
        var dist: Int
        var sum2: Double
        var nh: Double
        for (List1 in this.storeConcentrationData) {
            if (List1.size > 0) {
                for (j in 0 until List1.size) {
                    // Get standarized concentration matrix
                    stdData = standarizedArray(i, j)
                    // Variables
                    //  Maximum separation distance is one half of the target area
                    // max_h = total // of separation distances to evaluate
                    maxH = (floor(stdData[0].size / 2.0)).toInt()
                    // define Horizontal Variogram array
                    vVarDiagram = MutableList(maxH + 1) { it * 0.0 }
                    // v_var_diagram[0] = 0
                    //  loop through all separation distances  for zero dist, var is 0, so we don't need to calculate
                    dist = 1
                    while (dist <= maxH) {
                        sum2 = 0.0
                        nh = 0.0
                        // Loop through all rows (y-direction)
                        x = 0
                        while (x < stdData.size) {
                            // for each row, loop through columns (x-direction)
                            y = 0
                            while (y < stdData[0].size - dist) {
                                sum2 += (stdData[x][y] - (stdData[x][(y + dist)]).pow(2.0))
                                nh += 1
                                y += 1
                            }
                            x += 1
                        }
                        vVarDiagram[dist] = sum2 / (2 * nh)  // Variogram calculation from equation
                        dist += 1
                    }
                    if (j>0){
                        verVarDiagrams[i].add(j, vVarDiagram)
                    }else{
                        verVarDiagrams[i][j] = vVarDiagram
                    }
                }
            }
            i += 1
        }
        // defines Vertical_Var_diagrams[image_index][Target number] = Vertical Variogram
    }

    private fun meanLengthScales(): MutableList<MutableList<Coordinate>> {
        /*"""
            MEAN LENGTH SCALE CALCULATION
            Inputs:
            ∙ target_area
            ∙ Horizontal or vertical variogram vector


            Output:
            ∙ Mean length scale: Lv = p∙[δγx/δh]^(-1)
                Horizontal(1) or Vertical(2) mean length scale

            Computing method proposed by Alena Kukukova, 2010
            """*/

        // define mean_len_scales List
        val meanLenScales: MutableList<MutableList<Coordinate>> = arrayListOf(
            arrayListOf(Coordinate(0.0,0.0)))
        var k = 0
        while (k < this.imgToProcesses.size) {
            meanLenScales.add(arrayListOf(Coordinate(0.0,0.0)))
            k++
        }
        var i = 0
        for (List1 in storeConcentrationData) {
            if (List1.size > 0) {
                for (j in 0 until List1.size-1) {
                    // Read standarized intensity array from the requested target
                    val lms = Coordinate(0.0, 0.0)  // structure coordinate
                    val p = intensityMeasures[i][j][3]  // The proportion of the minor species in the sample region = C_mean
                    // Horizontal(1) or Vertical(2) mean length scale calculation
                    //  Units:pixels/concentration^2
                    lms.xin = p * (1 / (horVarDiagrams[i][j][1] - horVarDiagrams[i][j][0]))
                    //  Units:pixels/concentration^2
                    lms.yin = p * (1 / (verVarDiagrams[i][j][1] - verVarDiagrams[i][j][0]))
                    // noinspection PyTypeChecker
                    if (j>0){
                        meanLenScales[i].add(j, lms)
                    }else{
                        meanLenScales[i][j]= lms
                    }
                }
            }
            i += 1
        }
        return meanLenScales
        // defines mean_len_scales[image_index][Target number].X = Hor_mean_length_scale  .Y = Ver_mean_length_scale
    }

    /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    RATE OF CHANGE IN SEGREGATION
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/


    private fun calculateExposureIndexes(): MutableList<Double> {
        /*"""
            HORIZONTAL VARIOGRAM CALCULATION
            Inputs:
            ∙ Concentration matrix

            Output:
            ∙ Exposure: Ε≅∑∑〖(1/2)⋅K⋅a(i,j)⋅(Ci-Cj) 〗

            Computing method proposed by Alena Kukukova, 2009
            """*/

        // define exposure_indexes List
        val exposureIndexes: MutableList<Double> = arrayListOf(0.0)
        var k = 1
        while (k < this.imgToProcesses.size){
            exposureIndexes.add(0.0)
            k++
        }
        var exp: Double
        var xf: Int
        var yf: Int
        var data : MutableList<MutableList<Double>>
        var x: Int
        var y: Int
        for ((i, List1) in storeConcentrationData.withIndex()) {
            if (List1.size > 0) {
                for (j in 0 until List1.size) {
                    // Get Concentration Array
                    data = storeConcentrationData[i][j]
                    // define Variables
                    exp = 0.0
                    xf = data.size
                    yf = data[0].size
                    // Calculate Exposure
                    x = 0
                    while (x < xf) {
                        y = 0
                        while (y < yf) {
                            if (x != 0) {
                                exp += 0.5 * abs(data[x][y] - data[x - 1][y])
                            }
                            if (y != 0) {
                                exp += 0.5 * abs(data[x][y] - data[x][y - 1])
                            }
                            if (x != xf - 1) {
                                exp += 0.5 * abs(data[x][y] - data[x + 1][y])
                            }
                            if (y != yf - 1) {
                                exp += 0.5 * abs(data[x][y] - data[x][y + 1])
                            }
                            y++
                        }
                        x++
                    }
                    if (j>0){
                        exposureIndexes.add(j, exp)
                    }else{
                        exposureIndexes[j] = exp
                    }
                }
            }
        }
        return exposureIndexes
        // defines exposure_indexes[image_index][Target number] = Exposure
    }

    // endregion

// region Auxiliar functions and Intensity Information Arrays

    private fun filterImage(img_ori: MyBitMap): MyBitMap {
        /*"""
        :param img_ori: bitmap image
        """*/
        var filteredImage = img_ori.clone(MyClassRectangle(0.0, 0.0,
            img_ori.height.toDouble(), img_ori.width.toDouble()))
        // Apply Mean Filter (to eliminate local noise)
        Imgproc.medianBlur(filteredImage, filteredImage, 5)
        // Apply Grayscale filter
        Imgproc.cvtColor(filteredImage, filteredImage, Imgproc.COLOR_BGR2GRAY)
        // Apply Histogram remapping
        // filtered_image = new HistogramEqualization().Apply(filtered_image)
        return MyBitMap(filteredImage)
    }

    private fun getMeanIntensityValue(imgIndex: Int, target: Int): Double {
        /*"""
            :param img_index:
            :param target:
            """*/

        var tgtMean = 0.0
        var refFilteredImage = this.imgToProcesses[imgIndex].clone(MyClassRectangle(
            0.0, 0.0, this.imgToProcesses[imgIndex].width.toDouble(),
            this.imgToProcesses[imgIndex].height.toDouble()))
        // Apply median filter
        Imgproc.medianBlur(refFilteredImage, refFilteredImage, 5)
        // Apply Grayscale filter
        Imgproc.cvtColor(refFilteredImage, refFilteredImage, Imgproc.COLOR_BGR2GRAY)
        // Array size
        // ConcentrationArray = np.zeros(shape=(m, n))
        // Target area square/rectangle dimension
        val xi = storeTargetAreas[imgIndex][target].x
        val xf = xi + storeTargetAreas[imgIndex][target].width - 1
        val yi = storeTargetAreas[imgIndex][target].y
        val yf = yi + storeTargetAreas[imgIndex][target].height - 1
        var nn = 0.0
        var xc = xi
        var yc: Double
        while (xc <= xf) {
            yc = yi
            while (yc <= yf) {
                tgtMean += MyBitMap(refFilteredImage).pixel(xc.toInt(), yc.toInt(), layer = "R")
                nn += 1
                yc++
            }
            xc++
        }
        tgtMean /= (nn * 1.0)
        return tgtMean
        // Get Mean Intensity value in a target of a REFERENCE IMAGE
    }

    private fun getIntensityMaxMin(filteredImage: MyBitMap) : MyClassPoint {
        /*"""
        :param filtered_image: bitmap file
        """*/

        val intensityMaxAndMin = MyClassPoint(0.0, 0.0)
        intensityMaxAndMin.x = 0.0  // I_max
        intensityMaxAndMin.y = 255.0  // I_min
        // Target area square/rectangle dimension
        val xf = filteredImage.height-1
        val yf = filteredImage.width-1
        // define intensity array in "IntensityArrayData
        var x = 0
        var y: Int
        var pixVal: Double
        while (x < xf) {
            y = 0
            while (y < yf) {
                pixVal = filteredImage.pixel(x, y, "R")
                if (pixVal > intensityMaxAndMin.x) {
                    intensityMaxAndMin.x = pixVal
                }
                if (pixVal < intensityMaxAndMin.y) {
                    intensityMaxAndMin.y = pixVal
                }
                y += 1
            }
            x += 1
        }
        return intensityMaxAndMin
    }

    private fun statisticalMeasures(data: MutableList<MutableList<Double>>) :MutableList<Double> {
        /*"""
        COMPUTE STATISTICAL MEASURES
        Inputs:
        ∙ Array

        StatisticalArray=[μ,σ,x_min,x_max,n]=[Mean, Std. Dev., Min Value, Max Value, Number of Data] = [0,1,2,3,4]

        Output:
        ∙ Statistical measures array
        :return: stat_measures
        :param data: array
        """*/
        // define variables
        var mean = 0.0
        var stDev = 0.0
        var xMax = 0.0
        /*if (data.shape.size == 1){
            data = data.reshape((data.size, 1))
        }*/
        var xMin = data[0][0]
        var n = 0.0
        val statMeasures: MutableList<Double> = arrayListOf(0.0, 0.0, 0.0, 0.0, 0.0)
        // Find Mean, n, x_max & x_min
        var xc = 0
        var yc: Int
        while (xc < data.size) {
            yc = 0
            while (yc < data[0].size) {
                if (xMax < data[xc][yc]) {
                    xMax = data[xc][yc]
                }
                if (xMin > data[xc][yc]) {
                    xMin = data[xc][yc]
                }
                mean += data[xc][yc]
                n++
                yc++
            }

            xc++
        }
        mean /= (n * 1.0)
        // Compute Standard deviation
        xc = 0
        while (xc < data.size) {
            yc = 0
            while (yc < data[0].size) {
                stDev += (data[xc][yc] - mean).pow(2.0)
                yc++
            }
            xc++
        }
        stDev = (stDev / (n * 1.0)).pow(0.5)
        statMeasures[0] = mean
        statMeasures[1] = stDev
        statMeasures[2] = xMin
        statMeasures[3] = xMax
        statMeasures[4] = n
        return statMeasures
    }

    private fun standarizedArray(imageIndex: Int, target: Int): MutableList<MutableList<Double>> {
        /*"""
            funINE STANDARIZED ARRAY
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
            """*/

        // Declare normalized intensity array
        // m = The number of rows in the concentration array -> data.shape[0)
        // n = The number of columns in the concentration array -> data.shape[1)
        val m = storeConcentrationData[imageIndex][target].size
        val n = storeConcentrationData[imageIndex][target][0].size
        val standarizedData = MutableList(m) { _ -> MutableList(n) { _ -> 0.0 } }
        // Declare other variables
        // Get Mean and standard deviation to standarize the array
        val mean = intensityMeasures[imageIndex][target][3]
        val stDev = intensityMeasures[imageIndex][target][0]
        // define standarized intensity array
        var xc = 0
        var yc: Int
        while (xc < m) {
            yc = 0
            while (yc < n) {
                val xi = storeConcentrationData[imageIndex][target][xc][yc]
                standarizedData[xc][yc] = (xi - mean) / stDev
                yc++
            }
            xc++
        }
        return standarizedData
        // Function that returns normalized intensity array of a target area
    }

    fun getIntensityArray(imageIndex: Int, targetArea: Int): Array<Array<Double>> {
        /*"""
            get_intensity_array
            funINE INTENSITY ARRAY
            Inputs:
            ∙ target_area and img_to_process
            ∙ Image loaded

            Output:
            ∙ Intensity array
            :param store_target_areas2: store areas to process from each image
            :param img_to_process2: images to process
            :param image_index:
            :param target_area:
            """*/
        val imgToProcess2 = this.imgToProcesses
        val storeTargetAreas2 = this.storeTargetAreas
        var filteredImage = imgToProcess2[imageIndex]
        filteredImage = filterImage(filteredImage)
        // Target area square/rectangle dimension
        val xi = storeTargetAreas2[imageIndex][targetArea].x
        val xf = xi + storeTargetAreas2[imageIndex][targetArea].width - 1
        val yi = storeTargetAreas2[imageIndex][targetArea].y
        val yf = yi + storeTargetAreas2[imageIndex][targetArea].height - 1
        // Array dimension
        var x = (xf - xi)
        var y = (yf - yi)
        // Variables
        val intensityArrayData = Array((x+1).toInt())
        { _ -> Array((y+1).toInt()) { _ -> 0.0 }}  // Declare array of intensity values
        // define intensity array in "intensity_array_data[]"
        var xc = xi
        var yc: Double
        while (xc <= xf) {
            yc = yi
            while (yc <= yf) {
                x = (xc - xi)
                y = (yc - yi)
                // Gets Intensity value of the grayscale Image
                intensityArrayData[x.toInt()][y.toInt()] = MyBitMap(filteredImage.img).pixel(xc.toInt(),
                    yc.toInt(), layer = "R")
                yc += 1
            }
            xc += 1
        }
        return intensityArrayData
        // Function that returns the intensity array of a target area
    }

    fun fullImageDataArray(image_index: Int) : Array<Array<Double>> {
        /*"""
            funINE INTENSITY ARRAY
            Inputs:
            ∙ Image loaded

            Output:
            ∙ Full image intensity array
            :param img_to_process2:
            :param image_index:
            """*/
        val imgToProcess2 = this.imgToProcesses
        var filteredImage = imgToProcess2[image_index]
        filteredImage = filterImage(filteredImage)
        // Target area square/rectangle dimension
        val xf = filteredImage.width
        val yf = filteredImage.height
        // Variables
        val imageIntensityArray = Array((xf))
        { _ -> Array((yf)) { _ -> 0.0 }}  // Declare array of intensity values
        // define intensity array in "IntensityArrayData[]"
        var x = 0
        var y: Int
        while (x < xf) {
            y = 0
            while (y < yf) {
                // Gets Intensity value of the grayscale Image
                imageIntensityArray[x][y] = MyBitMap(filteredImage.img).pixel(x, y, layer = "R")
                y += 1
            }
            x += 1
        }
        return imageIntensityArray
        // Function that returns the intensity array of the loaded image
    }
    //endregion

}
// region Auxiliar initialize functions
fun  calculateMeanSpacing(
    imgInd: Int, trgInd: Int, imgToProcesses: MutableList<MyBitMap>,
    storePartPos: MutableMap<String, MutableList<MutableList<MutableList<MyClassPoint>>>>,
    colorLabel: String
) : Double{
    var meanSpa = 0.0
    var dist: Int
    for (point in storePartPos[colorLabel]!![imgInd][trgInd]){
        var s = imgToProcesses[imgInd].width.toDouble().pow(2.0) +
                imgToProcesses[imgInd].height.toDouble().pow(2.0)
        var meanS = (s.pow(0.5)).toInt()
        for (point_evl in storePartPos[colorLabel]!![imgInd][trgInd]) {
            if (point != point_evl) {
                s = (point.x - point_evl.x).pow(2.0) + (point.y - point_evl.y).pow(2.0)
                dist = (s.pow(0.5)).toInt()
                if (dist < meanS) {
                    meanS = dist
                }
            }
        }
        meanSpa += meanS

    }
    meanSpa = (meanSpa / storePartPos[colorLabel]!![imgInd][trgInd].size)
    return meanSpa * 2
}



fun calculateMaxStrThickness(
    img_ind: Int, trg_ind: Int, mSpacingParticles: Double,
    store_part_pos: MutableMap<String, MutableList<MutableList<MutableList<MyClassPoint>>>>,
    definedTransects: MutableList<MutableList<MyClassRectangle>>,
    store_target_areas: MutableList<MutableList<MyClassRectangle>>,
    colorLabel: String
): Double {
    var horizontal = true
    //    // Evaluate if is horizontal or Vertical
    if (definedTransects[img_ind][trg_ind].height == store_target_areas[img_ind][trg_ind].height) {
        horizontal = false
    }
    val array: MutableList<Double> = arrayListOf(0.0)
    var indTgt = 0
    var j = 0
    var mst = 0.0
    for (item in store_part_pos[colorLabel]!![img_ind][trg_ind]){
        val x1 = definedTransects[img_ind][trg_ind].x   // corrected x in exchange of y same for height and width
        val x2 = x1 + definedTransects[img_ind][trg_ind].width - 1
        val y1 = definedTransects[img_ind][trg_ind].y
        val y2 = y1 + definedTransects[img_ind][trg_ind].height - 1
        if ((item.x in x1..x2) && (item.y in y1..y2)) {
            array.add(0.0)  // Adds one more space into the array
            if (horizontal) array[j] = item.x
            else array[j] = item.y
            j++
        }
        indTgt += 1
    }
    if (array.size > 1) {
        array.sorted()
        var start = array[0]
        for (indTgt1 in 1 until array.size) {
            val striation = array[indTgt1] - array[indTgt1 - 1]
            if (striation > mSpacingParticles) {
                if (array[indTgt1 - 1] - start > mst) {
                    mst = array[indTgt1] - start
                }
                start = array[indTgt1]
            }
            if (indTgt1 == array.size){
                if (array[indTgt1] - start > mst) {
                    mst = array[indTgt1] - start
                }
            }
        }
        if (mSpacingParticles > mst) {
            mst = mSpacingParticles
        }
    }
    else {
        mst = mSpacingParticles
    }
    return mst
}

fun initiateMaxStrThickness(
    imgToProcesses: MutableList<MyBitMap>,
    storePartPos: MutableMap<String, MutableList<MutableList<MutableList<MyClassPoint>>>>,
    storeTrgAreas: MutableList<MutableList<MyClassRectangle>>,
    colorLabel: String
) : StrPack {
    val definedTransects: MutableList<MutableList<MyClassRectangle>> =
        arrayListOf(arrayListOf(MyClassRectangle(0.0, 0.0,1.0, 1.0)))
    val meanPartSpacing: MutableList<MutableList<Double>> = arrayListOf(arrayListOf(0.0))
    val maxStrThickness: MutableList<MutableList<Double>> = arrayListOf(arrayListOf(0.0))
    val horizontal = true
    var tgtInd: Int
    var meanS: Double
    var height: Double
    var width: Double
    var ini: Double
    var limit: Double
    var rectT: MyClassRectangle
    var mstEvl: Double
    var j: Double
    var mst: Double
    for (imgInd in 0 until imgToProcesses.size) {
        tgtInd = 0
        while (tgtInd < storeTrgAreas[imgInd].size) {
            meanS = calculateMeanSpacing(imgInd, tgtInd, imgToProcesses, storePartPos, colorLabel)
            if (tgtInd>0){
                meanPartSpacing[imgInd].add(tgtInd, meanS)
            }else{
                meanPartSpacing[imgInd][tgtInd] = meanS
            }
            // define new Rectangle Transect for the assessed target
            // Evaluate for all the transect positions possible
            val x = storeTrgAreas[imgInd][tgtInd].x
            val y = storeTrgAreas[imgInd][tgtInd].y
            if (horizontal) {
                height = meanS
                width = storeTrgAreas[imgInd][tgtInd].width
                ini = y
                limit = y + storeTrgAreas[imgInd][tgtInd].height - 1 - meanS
            }
            else {
                height = storeTrgAreas[imgInd][tgtInd].height
                width = meanS
                ini = x
                limit = x + storeTrgAreas[imgInd][tgtInd].width - 1 - meanS
            }
            mst = meanS
            j = ini
            while (j < limit) {
                rectT = if (horizontal) {
                    MyClassRectangle(x, j, width, height)
                } else {
                    MyClassRectangle(j, y, width, height)
                }
                if (tgtInd>0){
                    definedTransects[imgInd].add(tgtInd, rectT)
                }else{
                    definedTransects[imgInd][tgtInd] = rectT
                }
                mstEvl = calculateMaxStrThickness(imgInd, tgtInd, meanS, storePartPos,
                    definedTransects, storeTrgAreas, colorLabel )

                if ( mstEvl > mst) {
                    mst = mstEvl
                }
                j++
            }
            if (tgtInd>0){
                maxStrThickness[imgInd].add(tgtInd, mst)
            }else{
                maxStrThickness[imgInd][tgtInd] = mst
            }
            tgtInd++
        }
    }
    return StrPack(meanPartSpacing, definedTransects, maxStrThickness)
}


fun calculateHSVThreshold(R: Float, G: Float, B: Float): List<Scalar> {
    val bgr = Mat(1, 1, CvType.CV_8UC3, Scalar(B.toDouble(), G.toDouble(), R.toDouble()))
    var hsv = Mat(1, 1, CvType.CV_8UC3, Scalar(B.toDouble(), G.toDouble(), R.toDouble()))
    var limDown = 0.0
    var limUp = 255.0
    println("calculo hsv ${bgr.get(0,0)[0]},${bgr.get(0,0)[1]},${bgr.get(0,0)[2]}")
    Imgproc.cvtColor(bgr, hsv, Imgproc.COLOR_BGR2HSV)
    println("of ${hsv.get(0,0)[0]}, ${hsv.get(0,0)[1]}, ${hsv.get(0,0)[2]}....R$R G$G B$B")
    when (hsv.get(0,0)[0]){
        0.0 -> {
            val limDown = hsv.get(0,0)[0]
            val limUp = hsv.get(0,0)[0]+10.0
        }
        255.0 -> {
            val limDown = hsv.get(0,0)[0]-10.0
            val limUp = hsv.get(0,0)[0]
        }
        else -> {
            val limDown = hsv.get(0,0)[0]-10.0
            val limUp = hsv.get(0,0)[0]+10.0
        }
    }
    if(hsv.get(0,0)[0]<=0.0){
        limDown = hsv.get(0,0)[0]
        limUp = hsv.get(0,0)[0]+10.0
    }else if(hsv.get(0,0)[0]>=255.0){
        limDown = hsv.get(0,0)[0]-10.0
        limUp = hsv.get(0,0)[0]
    }else {
        limDown = hsv.get(0,0)[0]-10.0
        limUp = hsv.get(0,0)[0]+10.0
    }
    return listOf(Scalar(limDown, 100.0, 100.0), Scalar(limUp, 255.0, 255.0))
}


fun blobDetectionImageForColors(
    imgToProcesses: MutableList<MyBitMap>,
    thresholdValue: Double,
    storeTargetAreas: MutableList<MutableList<MyClassRectangle>>,
    colorLabel: String
): BlobPackColors
{
    val storeBlobRectangles: Map<String, MutableList<MutableList<MyClassRectangle>>> = mapOf(
        colorLabel to arrayListOf(arrayListOf(MyClassRectangle(0.0, 0.0, 1.0, 1.0))))
    val storePartPos: Map<String, MutableList<MutableList<MutableList<MyClassPoint>>>> = mapOf(
        colorLabel to arrayListOf(arrayListOf(arrayListOf(MyClassPoint(0.0, 0.0))))) // type: List[List[Point]]
    // Multiple object detection----------------------------------------------------------
    // Filter by Area.
    val areaBlob = arrayOf(limitAreaMin, limitAreaMax)
    val blobCounter = BlobDetector(
        threshold = arrayOf(thresholdBlobMin.toFloat(), thresholdBlobMax.toFloat()),
        flagArea = flagBlobArea, limitArea = areaBlob, flagCircularity = flagBlobCircularity,
        minCir = minCircularity, flagConvexity = flagBlobConvexity,
        convexity = arrayOf(limitConvMin, limitConvMax), flagInertia = flagBlobInertia,
        ratioInertia = arrayOf(limitRatioInertiaMin, limitRatioInertiaMax), flagColor = flagBlobColor
    )
    // Filter IMAGE---------------------------------------------------------------------
    var imgIndex = 0  //Image index
    var filteredImg: Mat
    var hsv: Mat
    var mask: Mat
    for (img in imgToProcesses) {
        while(storePartPos[colorLabel]!![imgIndex].size<storeTargetAreas[imgIndex].size){
            storePartPos[colorLabel]!![imgIndex].add(arrayListOf(MyClassPoint(0.0, 0.0)))
        }
        for ((trgIndBlob, area) in storeTargetAreas[imgIndex].withIndex()) {
            filteredImg = img.clone(area)
            hsv =  Mat(area.width.toInt(), area.height.toInt(), CvType.CV_8UC3, Scalar(0.0, 0.0, 0.0))
            //hsv = img.clone(area)
            //mask = img.clone(area)
            mask =  Mat(area.width.toInt(), area.height.toInt(), CvType.CV_8UC3, Scalar(255.0, 255.0, 255.0))
            // It converts the BGR color space of image to HSV color space
            Imgproc.cvtColor(filteredImg, hsv, Imgproc.COLOR_BGR2HSV)
            // imgs_filtered.add(hsv)
            // Threshold of blue in HSV space
            val limits = calculateHSVThreshold(colorScaleR[colorLabel]!!, colorScaleG[colorLabel]!!,
                colorScaleB[colorLabel]!!
            )
            println("limits of $colorLabel: $limits" )
            val lowerRGBtoHSV = Scalar(limits[0].`val`[0],limits[0].`val`[1],limits[0].`val`[2])
            val upperRGBtoHSV = Scalar(limits[1].`val`[0],limits[1].`val`[1],limits[1].`val`[2])
            // preparing the mask to overlay
            inRange(hsv,lowerRGBtoHSV, upperRGBtoHSV, mask )
            //imgs_filtered.add(mask)
            //println(" massss ${mask.size().width} x ${mask.size().height}")
            //var count = 0
            //for (i in 0 until mask.size().width.toInt()){
            //    for (j in 0 until mask.size().height.toInt()){
            //        for (k in 0 until mask[j,i].size){
            //            if (mask[j,i][k]==0.0){
            //                count += 1
            //            }
            //        }
            //    }
            //}
            //println("Xontador = $count")
            //mask = Imgproc.inRange(hsv, lower_blue, upper_blue)
            // The black region in the mask has the value of 0,
            // so when multiplied with original image removes all non-blue regions
            //filtered_img = Imgproc.bitwise_and(filteredImg, filteredImg, mask=mask)
            var aux = Mat(area.width.toInt(), area.height.toInt(), CvType.CV_8UC3, Scalar(0.0, 0.0, 0.0))
            var aux2 = Mat(area.width.toInt(), area.height.toInt(), CvType.CV_8UC3, Scalar(255.0, 255.0, 255.0))
            bitwise_and(filteredImg,aux2,aux,mask)
            filteredImg = aux.clone()
            //imgs_filtered.add(filteredImg)
            Imgproc.cvtColor(filteredImg, filteredImg, Imgproc.COLOR_HSV2RGB)
            //imgs_filtered.add(filteredImg)
            //cv2.imshow('Image filtered color', filtered_img)
            //cv2.waitKey(0)
            // Grayscale filter
            Imgproc.cvtColor(filteredImg, filteredImg, Imgproc.COLOR_BGR2GRAY)
            // ApplyThreshold
            var tam = Size(limitErodeX, limitErodeY)
            Imgproc.erode(
                filteredImg,
                filteredImg,
                Imgproc.getStructuringElement(Imgproc.MORPH_RECT, tam)
            )
            tam = Size(limitDilateX, limitDilateY)
            Imgproc.dilate(
                filteredImg,
                filteredImg,
                Imgproc.getStructuringElement(Imgproc.MORPH_RECT, tam)
            )
            Imgproc.threshold(
                filteredImg,
                filteredImg,
                thresholdValue,
                255.0,
                Imgproc.THRESH_BINARY_INV
            )
            val keyPoints = blobCounter.detectBlobs(filteredImg)
            val rectangles = blobCounter.blobRectangles(keyPoints)
            storeBlobRectangles[colorLabel]!![imgIndex] = rectangles
            for (i in 0 until rectangles.size) {
                val particleCoordinate = MyClassPoint((keyPoints[i].pt.x), (keyPoints[i].pt.y))
//                storePartPos[imgIndex][trgInd].add(particleCoordinate)
                storePartPos[colorLabel]!![imgIndex][trgIndBlob].add(particleCoordinate)
            }
        }
        imgIndex += 1
    }
    return BlobPackColors(storePartPos, storeBlobRectangles)
}


fun blobDetectionImage(imgToProcesses: MutableList<MyBitMap>, thresholdValue: Double,
                       storeTargetAreas: MutableList<MutableList<MyClassRectangle>>): BlobPack {
    val storeBlobRectangles: MutableList<MutableList<MyClassRectangle>> =
        arrayListOf(arrayListOf(MyClassRectangle(0.0, 0.0, 1.0, 1.0)))
    val storePartPos: MutableList<MutableList<MutableList<MyClassPoint>>> =
        arrayListOf(arrayListOf(arrayListOf(MyClassPoint(0.0, 0.0)))) // type: List[List[Point]]
    // Multiple object detection----------------------------------------------------------
    // Filter by Area.
    val areaBlob = arrayOf(limitAreaMin, limitAreaMax)
    val blobCounter = BlobDetector(
        threshold = arrayOf(thresholdBlobMin.toFloat(), thresholdBlobMax.toFloat()),
        flagArea = flagBlobArea, limitArea = areaBlob, flagCircularity = flagBlobCircularity,
        minCir = minCircularity, flagConvexity = flagBlobConvexity,
        convexity = arrayOf(limitConvMin, limitConvMax), flagInertia = flagBlobInertia,
        ratioInertia = arrayOf(limitRatioInertiaMin, limitRatioInertiaMax), flagColor = flagBlobColor
    )
    // Filter IMAGE---------------------------------------------------------------------
    var imgIndex = 0  //Image index
    var filteredImg: Mat
    for (img in imgToProcesses) {
        while(storePartPos[imgIndex].size<storeTargetAreas[imgIndex].size){
            storePartPos[imgIndex].add(arrayListOf(MyClassPoint(0.0, 0.0)))
        }
        for ((trgIndBlob, area) in storeTargetAreas[imgIndex].withIndex()) {
            // Store Rectangles and Particles positions
            //            store_blob_rectangles.add([])
            //            store_part_pos.add([])
            filteredImg = img.clone(area)
            //            img
            // Grayscale filter
            println("hsv for all colors")
            calculateHSVThreshold(1f, 1f, 1f)
            Imgproc.cvtColor(filteredImg, filteredImg, Imgproc.COLOR_BGR2GRAY)
            // ApplyThreshold
            var tam = Size(limitErodeX, limitErodeY)
            Imgproc.erode(
                filteredImg,
                filteredImg,
                Imgproc.getStructuringElement(Imgproc.MORPH_RECT, tam)
            )
            tam = Size(limitDilateX, limitDilateY)
            Imgproc.dilate(
                filteredImg,
                filteredImg,
                Imgproc.getStructuringElement(Imgproc.MORPH_RECT, tam)
            )
            Imgproc.threshold(
                filteredImg,
                filteredImg,
                thresholdValue,
                255.0,
                Imgproc.THRESH_BINARY_INV
            )
            val keyPoints = blobCounter.detectBlobs(filteredImg)
            val rectangles = blobCounter.blobRectangles(keyPoints)
            storeBlobRectangles[imgIndex] = rectangles
            for (i in 0 until rectangles.size) {
                val particleCoordinate = MyClassPoint((keyPoints[i].pt.x), (keyPoints[i].pt.y))
//                storePartPos[imgIndex][trgInd].add(particleCoordinate)
                storePartPos[imgIndex][trgIndBlob].add(particleCoordinate)
            }
        }
        imgIndex += 1
    }
    return BlobPack(storePartPos, storeBlobRectangles)

}
// endregion
// region C-like Structures
class MyClassPoint(posX: Double, posY: Double){
    var x = posX
    var y = posY
}

class MyClassRectangle(posX: Double, posY: Double, w: Double, h: Double){
    var x = posX
    var y = posY
    var width = w
    var height = h
}

class ListPoints(posX: Double, posY: Double) {
    private val defPoint = MyClassPoint(posX, posY)

    fun listPoints(num: Int): MutableList<MyClassPoint>{
        val arr = arrayListOf(defPoint)
        for (i in 1 until num) {
            arr.add(defPoint)
        }
        return arr
    }
}

class Coordinate(var xin: Double, var yin:Double){
    fun printCoordinate(){
        println("Coordinate x: $xin ; Coordinate y: $yin")
    }
}


class RefImg(var imageIndex: Int, var concentration: Double){
}

class MyBitMap(var img: Mat, private var dimension: Int = 2) {
    val width = img.width()
    val height = img.height()

    fun clone( rect: MyClassRectangle) : Mat{
        return this.img.submat(rect.x.toInt(), (rect.x+rect.width).toInt(),
            rect.y.toInt(), (rect.y+rect.height).toInt()
        )
    }

    fun pixel(xin: Int, yin: Int, layer: String = "R"): Double {
        var pix = 0.0
        if(dimension == 3){
            when (layer){
                "R"-> pix = this.img.get(xin,yin)[2]
                "G"-> pix = this.img.get(xin,yin)[1]
                "B"-> pix = this.img.get(xin,yin)[0]
            }
        }else{
            try {
                // some code
                pix = this.img.get(xin,yin)[0]
            } catch (e: NullPointerException) {
                // handler
                println("Error at : x$xin  and y$yin")
            }

        }
        return pix
    }

    fun bitmaps(num: Int): MutableList<Mat> {
        val arr: MutableList<Mat> = arrayListOf(this.img)
        for (i in 1 until num-1) {
            arr.add(this.img)
        }
        return arr
    }
}

class StrPack(val meanPartSpacing: MutableList<MutableList<Double>>,
              val definedTransects: MutableList<MutableList<MyClassRectangle>>,
              val maxStrThickness: MutableList<MutableList<Double>>){
}

class BlobPack(val storePartPos: MutableList<MutableList<MutableList<MyClassPoint>>>,
               val storeBlobRectangles: MutableList<MutableList<MyClassRectangle>>){
}
class BlobPackColors(val storePartPos: Map<String, MutableList<MutableList<MutableList<MyClassPoint>>>>,
               val storeBlobRectangles: Map<String, MutableList<MutableList<MyClassRectangle>>>){
}

class BlobDetector (var threshold: Array<Float> = arrayOf(120.0f, 255.0f),
                    var flagArea: Boolean = false,
                    var limitArea: Array<Float> = arrayOf(25.0f, 25.0f * 35.0f),
                    var flagCircularity: Boolean = false,
                    var minCir: Float = 0.1f,
                    var flagConvexity: Boolean = false,
                    var convexity: Array<Float> = arrayOf(0.0f, 10.0f),
                    var flagInertia: Boolean = true,
                    var ratioInertia: Array<Float> = arrayOf(0.0f, 0.5f),
                    var flagColor: Boolean = false) {
    /*"""
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

    """*/
    //Setup SimpleBlobDetector parameters.
    private var params = SimpleBlobDetector_Params()
    private var detector = initialize()
    private var keyPoints: MatOfKeyPoint = MatOfKeyPoint()

    private fun initialize(): SimpleBlobDetector {
        // Change thresholds
        params._minThreshold = threshold[0]
        params._maxThreshold = threshold[1]
        // Filter by Area. [4, 1000]
        params._filterByArea = flagArea
        params._minArea = limitArea[0]
        params._maxArea = limitArea[1]
        // Filter by Circularity
        params._filterByCircularity = flagCircularity
        params._minCircularity = minCir

        // Filter by Convexity
        params._filterByConvexity = flagConvexity
        params._minConvexity = convexity[0]
        params._maxConvexity = convexity[1]
        // Filter by Inertia (ratio of widest to thinnest point)
        params._filterByInertia = flagInertia
        params._minInertiaRatio = ratioInertia[0]
        params._maxInertiaRatio = ratioInertia[1]
        params._filterByColor = flagColor
        // Create a detector with the parameters
        return SimpleBlobDetector.create(params)
    }
    fun  detectBlobs(img: Mat): MutableList<KeyPoint> {
        detector.detect(img,keyPoints)
        return keyPoints.toList()

    }

    fun blobRectangles(points: MutableList<KeyPoint>): MutableList<MyClassRectangle>{
        val aux = mutableListOf<MyClassRectangle>()
        for (item in points){
            aux.add(MyClassRectangle((item.pt.x - item.size / 2),
                (item.pt.y - item.size / 2), item.size.toDouble(), item.size.toDouble()))
        }
        return aux
    }
}
// endregion

// region Multiple inlet functions
fun FilterColorImage(color: String): Int{
    var i = 0
    when(color){
        "Red"-> {
            i = 1
        }
        "Blue"-> {
            i = 2
        }
        "Black"-> {
            i = 3
        }
        "Yellow"-> {
            i = 4
        }
    }
    return i
}

// endregion