package com.poc_itesm.miquod2

import android.content.ContentUris
import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.DocumentsContract
import android.provider.MediaStore
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.runtime.*
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.navigation.NavController
import androidx.navigation.Navigation
import org.opencv.android.OpenCVLoader
import org.opencv.imgcodecs.Imgcodecs

var arImages = 0.5
var pathImg: String = " "
var flagPathAcquired: Boolean = false
var selectionCalculation: String = "Concentration"
var r1 = MyClassRectangle(2.0, 144.0, 295.0, 295.0)
var helloViewModel: HelloViewModel = HelloViewModel()
lateinit var parametersResult: MutableMap<String, MutableList<MutableMap<String, String>>>
var targetsRect: MutableMap<String, Float> = mutableMapOf("p0x" to 0f, "p0y" to 0f,
    "p1x" to 0f, "p1y" to 0f, "p2x" to 0f, "p2y" to 0f, "p3x" to 0f, "p3y" to 0f)
val storeTargetAreas: MutableList<MutableList<MyClassRectangle>> =
    arrayListOf(arrayListOf(r1))  //[#of picture][#of target area]=>rectangle dimensions
lateinit var storeParticlePositions: MutableList<MutableList<MutableList<MyClassPoint>>>
lateinit var strParPosColors: MutableMap<String, MutableList<MutableList<MutableList<MyClassPoint>>>>
var mainFlagShow = true
var resultsFlagShow = false
var thresholdValue = 90.0
var thresholdBlobMin = 120.0
var thresholdBlobMax = 255.0
var flagBlobArea = false
var limitAreaMin = 1.0f
var limitAreaMax = 100.0f
var flagBlobCircularity = false
var minCircularity = 0.05f
var maxCircularity = 1.0f
var flagBlobConvexity = false
var limitConvMin = 0.01f
var limitConvMax = 1.0f
var flagBlobInertia = true
var limitRatioInertiaMin = 0.01f
var limitRatioInertiaMax = 1.0f
var flagBlobColor = false
var textErrorMain = "Error"
var limitErodeX = 1.0
var limitErodeY = 1.0
var limitDilateX = 1.0
var limitDilateY = 1.0
var colorsSelected: MutableMap<String, Boolean> = mutableMapOf("Red" to false, "green" to false,
    "Blue" to false, "Yellow" to false)
var colorScaleR: MutableMap<String, Float> = mutableMapOf("Red" to 1f, "Green" to 0f,
    "Blue" to 0f, "Yellow" to 1f)
var colorScaleG: MutableMap<String, Float> = mutableMapOf("Red" to 0f, "Green" to 1f,
    "Blue" to 0f, "Yellow" to 0.918f)
var colorScaleB: MutableMap<String, Float> = mutableMapOf("Red" to 0f, "Green" to 0f,
    "Blue" to 1f, "Yellow" to 0f)
var colorSelectedCount = 0

class MainFragment : Fragment() {
    private var navController: NavController? = null
    private var imageUriState = mutableStateOf<Uri?>(null)

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        // Inflate the layout for this fragment
        parametersResult = mutableMapOf("no" to arrayListOf(mutableMapOf(Pair("Mixing Index", 0.0.toString()))))
        resultsFlagShow = false
        mainFlagShow = true
        return ComposeView(requireContext()).apply {
            setContent {
                navController = Navigation.findNavController(this)
                Main(Title = "Source selection")
            }
        }
    }

    @Composable
    fun Main(Title: String) {
        val openDialog by helloViewModel.errorFlag.observeAsState(initial = false)
//        val openDialog = remember { mutableStateOf(false)  }

        Column {
            Surface(modifier = Modifier.fillMaxWidth()) {
                Row(modifier = Modifier.fillMaxWidth()) {
                    MyTitle(str = Title)
                    MyIconConfiguration()
                }
            }
            Column (
                verticalArrangement = Arrangement.SpaceEvenly,
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight()
            ) {
                MyButtonSelectImg()
                MyImage()
                DisplayRadioGroup()
//            DisplayRectData()
                SelectTargets()
                MyCalculationButton()
                ShowResults()
                if (openDialog){
                    AlertDialog(
                        onDismissRequest = {
                            helloViewModel.onError(false)
                        },
                        title = {
                            Text(text = "Alert Message")
                        },
                        text = {
                            Text(text = textErrorMain)
                        },
                        buttons = {
                            Button(
                                onClick = { helloViewModel.onError(false)
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(text = "Dismiss")
                            }
                        }
                    )
                }

            }
        }

    }

    @Composable
    private fun MyIconConfiguration() {
        IconButton(
            onClick = {
                navController!!.navigate(R.id.action_mainFragment_to_configurationFragment2) }
        ) {
            Icon(Icons.Filled.MoreVert, "Configurations")
        }
    }

    @Composable
    fun MyTitle(str: String){
        Text(
            text = str, fontSize = 30.sp,
            style = MaterialTheme.typography.h6,
            modifier = Modifier
                .fillMaxWidth(0.9f))
    }

    private val selectImageLauncher = registerForActivityResult(ActivityResultContracts.GetContent())
    {uri ->
        imageUriState.value = uri
        val uriPathHelper = URIPathHelper()
        if (imageUriState.value != null){
            val filePath = uriPathHelper.getPath(requireContext(), imageUriState.value!!)
            pathImg= filePath.toString()
            flagPathAcquired = true
            helloViewModel.onImgSelected(true)
        }
    }
    @Composable
    fun MyButtonSelectImg(){
        Button(
            onClick = {
                selectImageLauncher.launch("image/*")
            }
        ) {
            Text(text = "Select Image")
        }
    }

    @Composable
    fun MyImage(){
        if (imageUriState.value != null) {
            println("Image selected")
            println(pathImg)
            val displayMetrics = resources.displayMetrics
            arImages = displayMetrics.widthPixels.toDouble()/displayMetrics.heightPixels.toDouble()
            val bitmap = MediaStore.Images.Media.getBitmap(
                requireContext().contentResolver, imageUriState.value!!)
            Image(bitmap = bitmap.asImageBitmap(),
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(0.3f),
                contentDescription = "Image selected")
        }else{

            Image(
                painterResource(id = R.drawable.ic_launcher_background),
                contentDescription = "Test Image"
            )
        }

    }

    @Composable
    fun DisplayRadioGroup(){
        var selected by remember { mutableStateOf("Concentration Data") }
        Row {
            RadioButton(selected = selected == "Concentration Data",
                onClick = { selected = "Concentration Data" })
            Text(
                text = "Concentration Data",
                modifier = Modifier
                    .clickable(onClick = {
                        selected = "Concentration Data"
                        selectionCalculation = "Concentration"
                        helloViewModel.onResultsFinished(false)
                        println(selectionCalculation)
                    })
                    .padding(start = 4.dp)
            )
            Spacer(modifier = Modifier.size(4.dp))
            RadioButton(selected = selected == "Particle Tracking Data",
                onClick = { selected = "Particle Tracking Data" })
            Text(
                text = "Particle Tracking Data",
                modifier = Modifier
                    .clickable(onClick = {
                        selected = "Particle Tracking Data"
                        selectionCalculation = "Particle"
                        helloViewModel.onResultsFinished(false)
                        println(selectionCalculation)
                    })
                    .padding(start = 4.dp)
            )
        }
    }

    @Composable
    fun SelectTargets(){
        val flagImg by helloViewModel.stateImg.observeAsState(initial = false)
        DisplaySelectTarget(flag = flagImg)

    }
    @Composable
    fun DisplaySelectTarget(flag: Boolean){
        if (flag){
            val bundle = bundleOf(
                "dataPath" to Paths(pathImg),
                "dataUri" to UriImg(imageUriState.value!!))
            Button(onClick = {
                navController!!.navigate(R.id.action_mainFragment_to_targetsFragment,
                    bundle)})
            {
                Text(text = "Select Targets")
            }
        }
    }


    @Composable
    fun MyCalculationButton(){
        Button(onClick = {
            if (flagPathAcquired) {
                try {
                    // some code
                    mixingData()
                    helloViewModel.onResultsFinished(true)
                    resultsFlagShow = true
                } catch (e: Exception) {
                    // handler
                    println("Error at trying to calculate")
                    println(e)
                    textErrorMain = "Error: Review the selected image or targets."
                    helloViewModel.onError(true)
                }
            }else{
                println("Select and Image first")
                textErrorMain = "Select and Image first"
                helloViewModel.onError(true)
            }
        }) {
            Text(text = "Calculate")
        }
    }

    @Composable
    fun ShowResults(){
        val flagResults by helloViewModel.stateRes.observeAsState(initial = false)
        if (!resultsFlagShow){
            helloViewModel.onResultsFinished(false)
        }
        DisplayResultData(
            flag = flagResults)
    }

    @Composable
    fun DisplayResultData( flag: Boolean){
        if (flag){
            val bundle = bundleOf(
                "data" to Results(parametersResult),
                "dataUri" to UriImg(imageUriState.value!!))
            Button(onClick = {
                navController!!.navigate(R.id.action_mainFragment_to_resultsFragment,
                bundle)})
            {
            Text(text = "Show Results")
            }
        }

    }

    @Preview(showBackground = true)
    @Composable
    fun DefaultPreview() {
        Main("welcome to main")
    }
}

class HelloViewModel : ViewModel() {

    // LiveData holds state which is observed by the UI
    // (state flows down from ViewModel)
    private val _results = MutableLiveData(false)
    val stateRes: LiveData<Boolean> = _results
    private val _point = MutableLiveData("P0")
    val statePoint: LiveData<String> = _point
    private val _imgFlag = MutableLiveData(false)
    val stateImg: LiveData<Boolean> = _imgFlag
    private val _targetNumber = MutableLiveData(0)
    val indTarget: LiveData<Int> = _targetNumber
    private val _indFlag = MutableLiveData(false)
    val stateInd: LiveData<Boolean> = _indFlag
    private val _indShow = MutableLiveData(0)
    val indShow: LiveData<Int> = _indShow
    private val _indFlagShow = MutableLiveData(false)
    val stateIndShow: LiveData<Boolean> = _indFlagShow
    private val _errorFlag = MutableLiveData(false)
    val errorFlag: LiveData<Boolean> = _errorFlag
    private val _targetNumberShow = MutableLiveData(0)
    val indTargetShow: LiveData<Int> = _targetNumberShow
    private val _colorShow = MutableLiveData("no")
    val colorShow: LiveData<String> = _colorShow
    private val _indFlagThreshold = MutableLiveData(false)
    val stateThreshold: LiveData<Boolean> = _indFlagThreshold
    private val _valThreshold = MutableLiveData(defaultValues[3])
    val stateThresholdValue: LiveData<String> = _valThreshold
    private val _filterNumberShow = MutableLiveData(0)
    val indFilterShow: LiveData<Int> = _filterNumberShow
    // Threshold blob variables
    private val _indFlagThresholdMin = MutableLiveData(false)
    val stateThresholdMin: LiveData<Boolean> = _indFlagThresholdMin
    private val _valThresholdMin = MutableLiveData(defaultValues[4])
    val stateThresholdMinValue: LiveData<String> = _valThresholdMin
    private val _indFlagThresholdMax = MutableLiveData(false)
    val stateThresholdMax: LiveData<Boolean> = _indFlagThresholdMax
    private val _valThresholdMax = MutableLiveData(defaultValues[5])
    val stateThresholdMaxValue: LiveData<String> = _valThresholdMax
    // Area blob variables
    private val _indFlagAreaBlob = MutableLiveData(false)
    val stateAreaBlob: LiveData<Boolean> = _indFlagAreaBlob
    private val _indFlagAreaBlobMin = MutableLiveData(false)
    val stateAreaBlobMin: LiveData<Boolean> = _indFlagAreaBlobMin
    private val _valAreaBlobMin = MutableLiveData(defaultValues[2])
    val stateAreaBlobMinValue: LiveData<String> = _valAreaBlobMin
    private val _indFlagAreaBlobMax = MutableLiveData(false)
    val stateAreaBlobMax: LiveData<Boolean> = _indFlagAreaBlobMax
    private val _valAreaBlobMax = MutableLiveData(defaultValues[4])
    val stateAreaBlobMaxValue: LiveData<String> = _valAreaBlobMax
    // Circularity blob variables
    private val _indFlagCirBlob = MutableLiveData(false)
    val stateCirBlob: LiveData<Boolean> = _indFlagCirBlob
    private val _indFlagCirBlobMin = MutableLiveData(false)
    val stateCirBlobMin: LiveData<Boolean> = _indFlagCirBlobMin
    private val _valCirBlobMin = MutableLiveData(defaultValues[1])
    val stateCirBlobMinValue: LiveData<String> = _valCirBlobMin
    private val _indFlagCirBlobMax = MutableLiveData(false)
    val stateCirBlobMax: LiveData<Boolean> = _indFlagCirBlobMax
    private val _valCirBlobMax = MutableLiveData(defaultValues[2])
    val stateCirBlobMaxValue: LiveData<String> = _valCirBlobMax
    // Convexity blob variables
    private val _indFlagConBlob = MutableLiveData(false)
    val stateConBlob: LiveData<Boolean> = _indFlagConBlob
    private val _indFlagConBlobMin = MutableLiveData(false)
    val stateConBlobMin: LiveData<Boolean> = _indFlagConBlobMin
    private val _valConBlobMin = MutableLiveData(defaultValues[0])
    val stateConBlobMinValue: LiveData<String> = _valConBlobMin
    private val _indFlagConBlobMax = MutableLiveData(false)
    val stateConBlobMax: LiveData<Boolean> = _indFlagConBlobMax
    private val _valConBlobMax = MutableLiveData(defaultValues[2])
    val stateConBlobMaxValue: LiveData<String> = _valConBlobMax
    // Ratio of inertia blob variables
    private val _indFlagIneBlob = MutableLiveData(false)
    val stateIneBlob: LiveData<Boolean> = _indFlagIneBlob
    private val _indFlagIneBlobMin = MutableLiveData(false)
    val stateIneBlobMin: LiveData<Boolean> = _indFlagIneBlobMin
    private val _valIneBlobMin = MutableLiveData(defaultValues[0])
    val stateIneBlobMinValue: LiveData<String> = _valIneBlobMin
    private val _indFlagIneBlobMax = MutableLiveData(false)
    val stateIneBlobMax: LiveData<Boolean> = _indFlagIneBlobMax
    private val _valIneBlobMax = MutableLiveData(defaultValues[2])
    val stateIneBlobMaxValue: LiveData<String> = _valIneBlobMax
    // Color flag blob variable
    private val _indFlagColorBlob = MutableLiveData(false)
    val stateColorBlob: LiveData<Boolean> = _indFlagColorBlob
    // Erode and Dilate variables
    private val _indFlagErodeX = MutableLiveData(false)
    val stateErodeX: LiveData<Boolean> = _indFlagErodeX
    private val _valErodeX = MutableLiveData(defaultValues[2])
    val stateErodeXValue: LiveData<String> = _valErodeX
    private val _indFlagErodeY = MutableLiveData(false)
    val stateErodeY: LiveData<Boolean> = _indFlagErodeY
    private val _valErodeY = MutableLiveData(defaultValues[2])
    val stateErodeYValue: LiveData<String> = _valErodeY
    private val _indFlagDilateX = MutableLiveData(false)
    val stateDilateX: LiveData<Boolean> = _indFlagDilateX
    private val _valDilateX = MutableLiveData(defaultValues[2])
    val stateDilateXValue: LiveData<String> = _valDilateX
    private val _indFlagDilateY = MutableLiveData(false)
    val stateDilateY: LiveData<Boolean> = _indFlagDilateY
    private val _valDilateY = MutableLiveData(defaultValues[2])
    val stateDilateYValue: LiveData<String> = _valDilateY
    private val _valColorCount = MutableLiveData(0)
    val stateColorCountValue: LiveData<Int> = _valColorCount
    private val _indFlagColorError = MutableLiveData(false)
    val stateColorValueError: LiveData<Boolean> = _indFlagColorError
    // onNameChange is an event we're defining that the UI can invoke
    // (events flow up from UI)
    fun onResultsFinished(newFlagRes: Boolean){
        _results.value = newFlagRes
    }

    fun onSelectedPoint(newPoint: String){
        _point.value = newPoint
    }


    fun onImgSelected(newImgFlag: Boolean){
        _imgFlag.value = newImgFlag
    }

    fun onSelectedTarget(newIndTarget: Int){
        _targetNumber.value = newIndTarget
    }

    fun onSelectedTargetDefined(newFlag: Boolean){
        _indFlag.value = newFlag
    }
    fun onDefiningPoints(newInd: Int, newFlag: Boolean){
        _indShow.value = newInd
        _indFlagShow.value = newFlag
    }

    fun onError(newFlag: Boolean){
        _errorFlag.value = newFlag
    }

    fun onSelectedTargetShow(newTarget: Int){
        _targetNumberShow.value = newTarget
    }

    fun onSelectedColorShow(newColor: String){
        _colorShow.value = newColor
    }

    fun onChangeThreshold(newValue: String){
        _valThreshold.value = newValue
    }

    fun onThresholdError (newFlag: Boolean){
        _indFlagThreshold.value = newFlag
    }

    fun onChangeThresholdMin(newValue: String){
        _valThresholdMin.value = newValue
    }

    fun onThresholdMinError (newFlag: Boolean){
        _indFlagThresholdMin.value = newFlag
    }

    fun onChangeThresholdMax(newValue: String){
        _valThresholdMax.value = newValue
    }

    fun onThresholdMaxError (newFlag: Boolean){
        _indFlagThresholdMax.value = newFlag
    }

    fun onAreaBlobSelected (newFlag: Boolean){
        _indFlagAreaBlob.value = newFlag
    }

    fun onChangeAreaBlobMin(newValue: String){
        _valAreaBlobMin.value = newValue
    }

    fun onAreaBlobMinError (newFlag: Boolean){
        _indFlagAreaBlobMin.value = newFlag
    }

    fun onChangeAreaBlobMax(newValue: String){
        _valAreaBlobMax.value = newValue
    }

    fun onAreaBlobMaxError (newFlag: Boolean){
        _indFlagAreaBlobMax.value = newFlag
    }

    fun onCirBlobSelected (newFlag: Boolean){
        _indFlagCirBlob.value = newFlag
    }

    fun onChangeCirBlobMin(newValue: String){
        _valCirBlobMin.value = newValue
    }

    fun onCirBlobMinError (newFlag: Boolean){
        _indFlagCirBlobMin.value = newFlag
    }

    fun onChangeCirBlobMax(newValue: String){
        _valCirBlobMax.value = newValue
    }

    fun onCirBlobMaxError (newFlag: Boolean){
        _indFlagCirBlobMax.value = newFlag
    }

    fun onConBlobSelected (newFlag: Boolean){
        _indFlagConBlob.value = newFlag
    }

    fun onChangeConBlobMin(newValue: String){
        _valConBlobMin.value = newValue
    }

    fun onConBlobMinError (newFlag: Boolean){
        _indFlagConBlobMin.value = newFlag
    }

    fun onChangeConBlobMax(newValue: String){
        _valConBlobMax.value = newValue
    }

    fun onConBlobMaxError (newFlag: Boolean){
        _indFlagConBlobMax.value = newFlag
    }

    fun onIneBlobSelected (newFlag: Boolean){
        _indFlagIneBlob.value = newFlag
    }

    fun onChangeIneBlobMin(newValue: String){
        _valIneBlobMin.value = newValue
    }

    fun onIneBlobMinError (newFlag: Boolean){
        _indFlagIneBlobMin.value = newFlag
    }

    fun onChangeIneBlobMax(newValue: String){
        _valIneBlobMax.value = newValue
    }

    fun onIneBlobMaxError (newFlag: Boolean){
        _indFlagIneBlobMax.value = newFlag
    }

    fun onColorBlobSelected (newFlag: Boolean){
        _indFlagColorBlob.value = newFlag
    }

    fun onChangeErodeX(newValue: String){
        _valErodeX.value = newValue
    }

    fun onErodeXError (newFlag: Boolean){
        _indFlagErodeX.value = newFlag
    }

    fun onChangeErodeY(newValue: String){
        _valErodeY.value = newValue
    }

    fun onErodeYError (newFlag: Boolean){
        _indFlagErodeY.value = newFlag
    }

    fun onChangeDilateX(newValue: String){
        _valDilateX.value = newValue
    }

    fun onDilateXError (newFlag: Boolean){
        _indFlagDilateX.value = newFlag
    }

    fun onChangeDilateY(newValue: String){
        _valDilateY.value = newValue
    }

    fun onDilateYError (newFlag: Boolean){
        _indFlagDilateY.value = newFlag
    }

    fun onColorCount (newValue: Int){
        _valColorCount.value = newValue
    }

    fun onChangeValueColorError(newValue: Boolean) {
        _indFlagColorError.value = newValue
    }

    fun onChangeValueColorScaleB(newValue: String){
        _valDilateY.value = newValue
    }
}


class URIPathHelper {

    fun getPath(context: Context, uri: Uri): String? {
        val isKitKatorAbove = Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT
        // DocumentProvider
        if (isKitKatorAbove && DocumentsContract.isDocumentUri(context, uri)) {
            // ExternalStorageProvider
            if (isExternalStorageDocument(uri)) {
                val docId = DocumentsContract.getDocumentId(uri)
                val split = docId.split(":".toRegex()).toTypedArray()
                val type = split[0]
                if ("primary".equals(type, ignoreCase = true)) {
                    return Environment.getExternalStorageDirectory().toString() + "/" + split[1]
                }

            } else if (isDownloadsDocument(uri)) {
                val id = DocumentsContract.getDocumentId(uri)
                val contentUri = ContentUris.withAppendedId(Uri.parse("content://downloads/public_downloads"), java.lang.Long.valueOf(id))
                return getDataColumn(context, contentUri, null, null)
            } else if (isMediaDocument(uri)) {
                val docId = DocumentsContract.getDocumentId(uri)
                val split = docId.split(":".toRegex()).toTypedArray()
                val type = split[0]
                var contentUri: Uri? = null
                when (type) {
                    "image" -> {
                        contentUri = MediaStore.Images.Media.EXTERNAL_CONTENT_URI
                    }
                    "video" -> {
                        contentUri = MediaStore.Video.Media.EXTERNAL_CONTENT_URI
                    }
                    "audio" -> {
                        contentUri = MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
                    }
                }
                val selection = "_id=?"
                val selectionArgs = arrayOf(split[1])
                return getDataColumn(context, contentUri, selection, selectionArgs)
            }
        } else if ("content".equals(uri.scheme, ignoreCase = true)) {
            return getDataColumn(context, uri, null, null)
        } else if ("file".equals(uri.scheme, ignoreCase = true)) {
            return uri.path
        }
        return null
    }

    private fun getDataColumn(context: Context, uri: Uri?, selection: String?, selectionArgs: Array<String>?): String? {
        var cursor: Cursor? = null
        val column = "_data"
        val projection = arrayOf(column)
        try {
            cursor = context.contentResolver.query(uri!!, projection, selection, selectionArgs,null)
            if (cursor != null && cursor.moveToFirst()) {
                val columnIndex: Int = cursor.getColumnIndexOrThrow(column)
                return cursor.getString(columnIndex)
            }
        } finally {
            cursor?.close()
        }
        return null
    }

    private fun isExternalStorageDocument(uri: Uri): Boolean {
        return "com.android.externalstorage.documents" == uri.authority
    }

    private fun isDownloadsDocument(uri: Uri): Boolean {
        return "com.android.providers.downloads.documents" == uri.authority
    }

    private fun isMediaDocument(uri: Uri): Boolean {
        return "com.android.providers.media.documents" == uri.authority
    }
}

fun mixingData(){
    val im = Imgcodecs.imread(pathImg)
    if(colorSelectedCount>0){
        for (color in colorsSelected){
            if (color.value){
                parametersResult[color.key] = arrayListOf(mutableMapOf(
                    Pair("Mixing Index", 0.0.toString())))
                for ((imgIndex,img) in storeTargetAreas.withIndex()){
                    for ((tgtIndex, tgt) in storeTargetAreas[imgIndex].withIndex()){
                        if (tgtIndex>0){
                            parametersResult[color.key]!!.add(tgtIndex,
                                mutableMapOf(Pair("Mixing Index", 0.0.toString())))
                        }
                    }
                }
            }
        }
    } else{
        for ((imgIndex,img) in storeTargetAreas.withIndex()){
            for ((tgtIndex, tgt) in storeTargetAreas[imgIndex].withIndex()){
                if (tgtIndex>0){
                    parametersResult["no"]!!.add(tgtIndex,
                        mutableMapOf(Pair("Mixing Index", 0.0.toString())))
                }else{
                    parametersResult["no"]!![tgtIndex] =
                        mutableMapOf(Pair("Mixing Index", 0.0.toString()))
                }
            }
        }
    }

    val numberOfTargets = storeTargetAreas[0].size
    //println("the width is ${data}")
    val imgToProcesses: MutableList<MyBitMap> = arrayListOf(MyBitMap(im, 2))
    val loadedImageInfo: MutableList<String> = arrayListOf("Img1")
    val imagesWithReferences: MutableList<MutableList<RefImg>> = arrayListOf(arrayListOf(RefImg(0, 1.0)))
//    val r1 = MyClassRectangle(2.0, 144.0, 295.0, 295.0)

    /*val storeTargetAreas2: MutableList<MutableList<MyClassRectangle>> = arrayListOf(arrayListOf(r1))
    val inletTargets: MutableList<MutableList<Int>> = arrayListOf(arrayListOf(0))
    val imgToProcess2 = imgToProcesses*/
    val storeConcentrationData: MutableList<MutableList<MutableList<MutableList<Double>>>> = arrayListOf(arrayListOf(arrayListOf(
        arrayListOf(0.0))))
    val darkCheckbox = false  // Dark Areas Higher concentration
//    val loadedImageInfo2 = loadedImageInfo
    val intensityMeasures: MutableList<MutableList<MutableList<Double>>> = arrayListOf(
        arrayListOf(arrayListOf(0.0, 0.0), arrayListOf(0.0, 0.0)))  // type: List[List[float]] # [#picture][#target area]=>{σ,CoV,M,Cm,C_max,C_min, N}
    val horizontalVarDiagrams: MutableList<MutableList<MutableList<Double>>> = arrayListOf(
        arrayListOf(arrayListOf(0.0, 0.0)), arrayListOf(arrayListOf(0.0, 0.0)))  // [#of picture][#of target area]=> Horizontal Variogram
    val verticalVarDiagrams: MutableList<MutableList<MutableList<Double>>> = arrayListOf(
        arrayListOf(arrayListOf(0.0, 0.0)), arrayListOf(arrayListOf(0.0, 0.0)))  // [#of picture][#of target area]=> Vertical Variogram
    if (!OpenCVLoader.initDebug()){
        println("An error occurred  ")
    }
    strParPosColors = mutableMapOf("no" to arrayListOf(arrayListOf(arrayListOf(MyClassPoint(0.0, 0.0)))))
    if (colorSelectedCount>0){
        println("Colors selection for particles")
        for (color in colorsSelected) {
            if (color.value){
                println("Particles of ${color.key}")
                val label = color.key
                val aux: BlobPackColors = blobDetectionImageForColors(
                    imgToProcesses, thresholdValue,storeTargetAreas, color.key)
                strParPosColors[color.key] = aux.storePartPos[color.key]!!
                val storeBlobRectangles = aux.storeBlobRectangles
                // Calculations after particle detection
                for ((i,itemPoints) in strParPosColors[label]!![0].withIndex()){
                    println("particles detected $i: ${itemPoints.size}")
                    parametersResult[label]!![i]["ParticlesDetected"] = itemPoints.size.toString()
                }
                val aux1: StrPack = initiateMaxStrThickness(imgToProcesses, strParPosColors, storeTargetAreas, label)
                val meanSpacingParticles = aux1.meanPartSpacing
                val definedTransects = aux1.definedTransects
                val maxStriationThick = aux1.maxStrThickness
                for ((i,item) in maxStriationThick[0].withIndex()){
                    parametersResult[label]!![i]["Max Striation Thickness"] = "%.4f".format(item)
                }
                println("Max striation calculated")
                println(maxStriationThick)
                println("defined transects calculated")
                println(definedTransects)
                println("mean spacing particles calculated")
                println(meanSpacingParticles)
                val storeConParticleData: MutableList<MutableList<List<List<Double>>>> = arrayListOf(arrayListOf(
                    arrayListOf(arrayListOf(0.0))))  // [#of picture][#of target area]=>Particle concentration array
                val storeMaxStrThickness:MutableList<MutableList<Int>> = arrayListOf(arrayListOf(0, 0))// type: List[List[int]] # [#picture][#targetarea]=>Maximum Striation Thickness
                val pnnDistribution: MutableList<MutableList<MutableList<Double>>> = arrayListOf(arrayListOf(arrayListOf(0.0, 0.0)))  // [#of picture,#of target area]=>PNN Distribution
                val scaleSegregationIndexes: ArrayList<ArrayList<Double>> = arrayListOf(arrayListOf(0.0, 0.0))  // [#of picture,#of target area]=> {σf_pp, I_dis, Xg}
                val dataMixing = FunctionsMixing(imgToProcesses, storeTargetAreas, storeConcentrationData,
                    imagesWithReferences, loadedImageInfo, darkCheckbox, intensityMeasures,
                    horizontalVarDiagrams, verticalVarDiagrams, strParPosColors, maxStriationThick,
                    storeConParticleData, pnnDistribution, meanSpacingParticles, definedTransects, parametersResult, label)
                when (selectionCalculation){
                    "Concentration"-> dataMixing.mixingDimConcentrationData()
                    "Particle"-> dataMixing.mixingDimParticleData()
                }
            }
        }
    }else{
        val aux: BlobPack = blobDetectionImage(imgToProcesses, thresholdValue,storeTargetAreas)
        strParPosColors["no"] = aux.storePartPos
        val storeBlobRectangles = aux.storeBlobRectangles
        // Calculations after particle detection
        for ((i,itemPoints) in strParPosColors["no"]!![0].withIndex()){
            println("particles detected $i: ${itemPoints.size}")
            parametersResult["no"]!![i]["ParticlesDetected"] = itemPoints.size.toString()
        }
        val aux1: StrPack = initiateMaxStrThickness(imgToProcesses, strParPosColors, storeTargetAreas, "no")
        val meanSpacingParticles = aux1.meanPartSpacing
        val definedTransects = aux1.definedTransects
        val maxStriationThick = aux1.maxStrThickness
        for ((i,item) in maxStriationThick[0].withIndex()){
            parametersResult["no"]!![i]["Max Striation Thickness"] = "%.4f".format(item)
        }
        println("Max striation calculated")
        println(maxStriationThick)
        println("defined transects calculated")
        println(definedTransects)
        println("mean spacing particles calculated")
        println(meanSpacingParticles)
        val storeConParticleData: MutableList<MutableList<List<List<Double>>>> = arrayListOf(arrayListOf(
            arrayListOf(arrayListOf(0.0))))  // [#of picture][#of target area]=>Particle concentration array
        val storeMaxStrThickness:MutableList<MutableList<Int>> = arrayListOf(arrayListOf(0, 0))// type: List[List[int]] # [#picture][#targetarea]=>Maximum Striation Thickness
        val pnnDistribution: MutableList<MutableList<MutableList<Double>>> = arrayListOf(arrayListOf(arrayListOf(0.0, 0.0)))  // [#of picture,#of target area]=>PNN Distribution
        val scaleSegregationIndexes: ArrayList<ArrayList<Double>> = arrayListOf(arrayListOf(0.0, 0.0))  // [#of picture,#of target area]=> {σf_pp, I_dis, Xg}
        val dataMixing = FunctionsMixing(imgToProcesses, storeTargetAreas, storeConcentrationData,
            imagesWithReferences, loadedImageInfo, darkCheckbox, intensityMeasures,
            horizontalVarDiagrams, verticalVarDiagrams, strParPosColors, maxStriationThick,
            storeConParticleData, pnnDistribution, meanSpacingParticles, definedTransects, parametersResult, "no")
        when (selectionCalculation){
            "Concentration"-> dataMixing.mixingDimConcentrationData()
            "Particle"-> dataMixing.mixingDimParticleData()
        }
    }


    println("hello world fin")
}