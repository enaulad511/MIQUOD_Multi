package com.poc_itesm.miquod2

import android.graphics.Bitmap
import android.os.Bundle
import android.provider.MediaStore
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.Button
import androidx.compose.material.MaterialTheme
import androidx.compose.material.OutlinedTextField
import androidx.compose.material.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.fragment.app.Fragment
import androidx.navigation.NavController
import androidx.navigation.Navigation
import java.io.File
import java.text.DateFormat.getDateInstance
import java.text.DateFormat.getTimeInstance
import java.util.*


@ExperimentalComposeUiApi
class ResultsFragment : Fragment() {
    private var navController: NavController? = null
    private lateinit var dataParameter: Results
    private lateinit var dataShow: Map<String, List<Map<String, String>>>
    private lateinit var targetsToShow: MutableMap<String, MutableList<String>>
    private lateinit var imgUri: UriImg


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        dataParameter = requireArguments().getParcelable("data")!!
        imgUri = requireArguments().getParcelable("dataUri")!!
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,
                              savedInstanceState: Bundle?
    ): View {
        // Inflate the layout for this fragment
        dataShow = dataParameter.data
        targetsToShow = mutableMapOf("no" to arrayListOf("Target 1"))
        val targetSize = storeTargetAreas[0].size
        if (colorSelectedCount>0){
            for (color in colorsSelected){
                if (color.value){
                    for ((i, item) in dataShow[color.key]!!.withIndex()){
                        when (i){
                            0-> {
                                targetsToShow[color.key] = arrayListOf("Target ${i+1}")
                            }
                            in 1 until targetSize -> {
                                targetsToShow[color.key]!!.add(i, "Target ${i+1}")
                            }

                        }
                    }
                }

            }
        }else{
            for ((i, item) in dataShow["no"]!!.withIndex()){
                when (i){
                    0-> targetsToShow["no"]!![i] = "Target ${i+1}"
                    in 1 until targetSize -> targetsToShow["no"]!!.add(i, "Target ${i+1}")
                }
            }
        }
        return ComposeView(requireContext()).apply {
            setContent {
                navController = Navigation.findNavController(this)
                Main("Results Display")
            }
        }
    }

    @Composable
    fun Main(title: String) {
        Column (
            verticalArrangement = Arrangement.SpaceEvenly,
            horizontalAlignment = Alignment.CenterHorizontally,
/*            modifier = Modifier
                .fillMaxHeight()
                .fillMaxWidth()*/
        ) {
            Title(title = title)
            DisplayResultData(parameters = dataShow, flag = true)
        }
    }

    @Composable
    fun SaveDataButton() {
        Button(
            onClick = {
                saveDataText()
            }
        ){
            Text(text = "Save Data")
        }
    }

    private fun saveDataText() {
        val path = requireContext().getExternalFilesDir(null)
        val letDirectory = File(path, "/MIQUOD")
        letDirectory.mkdirs()
        val sdf = getDateInstance()
        val currentDate = sdf.format(Calendar.getInstance().time)
        val sdf1 = getTimeInstance()
        val currentTime = sdf1.format(Calendar.getInstance().time)
        println("saved at $letDirectory")
        val file = File(letDirectory, "Data_${currentDate}_out.txt")
        var text = "Data for $selectionCalculation calculations in $currentDate at $currentTime \n"
        file.appendText(text)
        text = "Color;\tKey;\tValue \n"
        file.appendText(text)
        var value = ""
        if (colorSelectedCount>0){
            for (color in colorsSelected){
                if (color.value){
                    for (item in parametersResult[color.key]!![0]) {
                        text = "${color.key};\t${item.key};\t${item.value}"
                        for (j in 1 until parametersResult[color.key]!!.size) {
                            value = if (!parametersResult[color.key]!![j][item.key].isNullOrBlank()){
                                parametersResult[color.key]!![j][item.key]!!
                            }else{
                                "0.0000"
                            }
                            text += ";\t$value"
                        }
                        text += "\n"
                        file.appendText(text)
                    }
                }
            }
        }else{
            for (item in parametersResult["no"]!![0]) {
                text = "no;\t${item.key};\t${item.value}"
                for (j in 1 until parametersResult["no"]!!.size) {
                    value = if (!parametersResult["no"]!![j][item.key].isNullOrBlank()){
                        parametersResult["no"]!![j][item.key]!!
                    }else{
                        "0.0000"
                    }
                    text += ";\t$value"
                }
                text += " \n"
                file.appendText(text)
            }
        }

    }
    @Composable
    fun Title(title: String){
        Text(text = title, fontSize = 30.sp)
    }

    @Composable
    fun DisplayResultData(parameters: Map<String, List<Map<String, String>>>, flag: Boolean){
        val targetIndToShow by helloViewModel.indTargetShow.observeAsState(initial = 0)
        val colorToShow by helloViewModel.colorShow.observeAsState(initial = "no")
        if (flag){
            Column(
                verticalArrangement = Arrangement.SpaceEvenly,
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Row (
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.Top
                ) {
                    Column(
                        modifier = Modifier.width(200.dp)
                    ) {
                        Text("Result Data: ",
                            modifier = Modifier.padding(4.dp)
                        )
                        LazyColumn(
                            verticalArrangement = Arrangement.SpaceEvenly,
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.height(260.dp)
                        ) {
                            items(items = parameters[colorToShow]!![targetIndToShow].keys.toList()){
                                ResultText(key = it, parameters[colorToShow]!![targetIndToShow])
                            }
                        }
                    }
                    Spacer(modifier = Modifier.padding(15.dp))
                    Column(
                        modifier = Modifier.width(80.dp)
                    ) {
                        Text(text = "Color selected:")
                        Spacer(modifier = Modifier.padding(4.dp))
                        LazyColumn(
                            verticalArrangement = Arrangement.SpaceEvenly,
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            var dummyList = parameters.keys.toList()
                            if (dummyList.count()>1){
                                dummyList = mutableListOf<String>()
                                var i = 0
                                for (color in parameters.keys){
                                    if (color != "no"){
                                        dummyList.add(color)
                                        i=+1
                                    }
                                }
                            }else{
                                dummyList = listOf("no")
                            }
                            items(items = dummyList){
                                ColorToShow(key = it, elements = colorsSelected)
                            }
                        }
                        Spacer(modifier = Modifier.padding(15.dp))
                        LazyColumn(
                            verticalArrangement = Arrangement.SpaceEvenly,
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            items(items = targetsToShow[colorToShow]!!){
                                TargetToShow(key = it, elements = targetsToShow[colorToShow]!!)
                            }
                        }
                    }
                }
                DisplayImageTarget(targetIndToShow)
                SaveDataButton()
            }

        }else{
            Column {
                Text("Result data:",
                    modifier = Modifier.padding(4.dp)
                )
                Text(text = "Data not available")
            }
        }

    }

    @Composable
    fun DisplayImageTarget(targetInd: Int) {
        val colorToShow by helloViewModel.colorShow.observeAsState(initial = "no")
        var bitmap = MediaStore.Images.Media.getBitmap(requireContext().contentResolver, imgUri.dataUri)
        var centerX = 0f
        var centerY = 0f
        val rectangle = storeTargetAreas[0][targetInd]
        bitmap = Bitmap.createBitmap(bitmap, rectangle.y.toInt(), rectangle.x.toInt(),
            rectangle.height.toInt(), rectangle.width.toInt())
        // Utils.matToBitmap(imgs_filtered[10], bitmap);
        val widthImg = bitmap.width
        val heightImg = bitmap.height
        val arOriginal = widthImg.toFloat()/heightImg.toFloat()
        val screenWidthVerticalPosition = resources.displayMetrics.widthPixels
        var vHeight = screenWidthVerticalPosition.toFloat()/ arOriginal
        var vWidth = screenWidthVerticalPosition.toFloat()
        var arPointsW = widthImg.toFloat()/screenWidthVerticalPosition.toFloat()
        var arPointsH = heightImg.toFloat()/vHeight
        var scaleFlag = false
        val heightFactor = 5.9f
        val arCanva = screenWidthVerticalPosition.toFloat()/(resources.displayMetrics.heightPixels/heightFactor)
        if (heightImg>resources.displayMetrics.heightPixels/heightFactor){
            scaleFlag = true
            vHeight = resources.displayMetrics.heightPixels/heightFactor
            vWidth = vHeight*arOriginal
            arPointsW =widthImg.toFloat()/vWidth
            arPointsH = heightImg.toFloat()/vHeight
            bitmap = Bitmap.createScaledBitmap(bitmap,
                vWidth.toInt(), vHeight.toInt(), false)
        }else{
            if (widthImg>screenWidthVerticalPosition){
                scaleFlag = true
                bitmap = Bitmap.createScaledBitmap(bitmap,
                    vWidth.toInt(), vHeight.toInt(), false)
            }
        }
        var arx = 1f
        var ary = 1f
        var ar = 1f
        if (scaleFlag){
            ar = arCanva
            arx = arPointsW
            ary = arPointsH
            println("Scaled factor: $ar ; $arx; $ary")
        }
        Canvas(
            modifier = Modifier
                .aspectRatio(ar)
                .fillMaxWidth()
        ){
            drawImage(
                image = bitmap.asImageBitmap()
            )
            when (selectionCalculation){
                "Concentration"-> {
                    println("Not particles to show")
                }
                "Particle"-> {
                    for (item in strParPosColors[colorToShow]!![0][targetInd]){
                        drawCircle(
                            color = Color(0xFFFF0000),
                            radius = 3f,
                            center = Offset(item.x.toFloat()/arx, item.y.toFloat()/ary)
                        )
                    }

                }
            }

        }
    }

    @Composable
    fun TargetToShow(key: String, elements: List<String>){
        Text(text = key,
            style = MaterialTheme.typography.h6,
            modifier = Modifier.clickable(onClick = {
                for ((i,item) in  elements.withIndex()){
                    if (item == key){
                        helloViewModel.onSelectedTargetShow(i)
                        println("index to show: $i")
                    }
                }
            })
        )
    }

    @Composable
    fun ColorToShow(key: String, elements: Map<String, Boolean>){
        if (key == "no"){
            println("no colors last $elements key $key")
            Text(text = key,
                style = MaterialTheme.typography.h6,
                modifier = Modifier.clickable(
                    onClick = {
                        helloViewModel.onSelectedColorShow(key)
                        println("index to show: $key")
                    }
                )
            )
        }else{
            println("colors last")
            if (elements[key]!!){
                Text(text = key,
                    style = MaterialTheme.typography.h6,
                    modifier = Modifier.clickable(
                        onClick = {
                            helloViewModel.onSelectedColorShow(key)
                            println("index to show: $key")
                        }
                    )
                )
            }
        }
    }
    @Composable
    fun ResultText(key: String, values: Map<String, String>){
        var text = ""
        Column {
            OutlinedTextField(value = values[key].toString(),
                onValueChange = {text = it},
                label = { Text("$key: ") }
            )
        }
    }

    @Preview(showBackground = true)
    @Composable
    fun DefaultPreview() {
        Main("Results")
    }
}

