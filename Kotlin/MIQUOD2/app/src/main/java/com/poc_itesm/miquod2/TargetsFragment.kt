package com.poc_itesm.miquod2

import android.graphics.Bitmap
import android.os.Bundle
import android.provider.MediaStore
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.runtime.*
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.layout.boundsInWindow
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.fragment.app.Fragment
import androidx.navigation.NavController
import androidx.navigation.Navigation
import kotlin.math.abs

@ExperimentalComposeUiApi
class TargetsFragment : Fragment() {
    private var navController: NavController? = null
    private var selectionPoint: String = "P0"
    private var selectionTarget: Int = 0
    private lateinit var imgPaths: Paths
    private lateinit var path: String
    private lateinit var imgUri: UriImg

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        imgPaths = requireArguments().getParcelable("dataPath")!!
        imgUri = requireArguments().getParcelable("dataUri")!!
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        // Inflate the layout for this fragment
        resultsFlagShow = true
        mainFlagShow = false
        path = imgPaths.dataPath
        return ComposeView(requireContext()).apply {
            setContent {
                navController = Navigation.findNavController(this)
                Main(Title = "Creation of targets")
            }
        }
    }

    private fun limits(value: Float, maxValue: Int): Float {
        var output = value
        if (value.toInt()>maxValue){
            output = maxValue.toFloat()
        }
        if (value.toInt()<0){
            output = 0f
        }
        return output
    }

    @Composable
    fun Main(Title: String) {
        Column (
            verticalArrangement = Arrangement.SpaceEvenly,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            MyTitle(Title)
            MyImage()
            Row {
                DisplayRadioGroup()
                Spacer(modifier = Modifier.padding(10.dp))
                DisplayListRectangles()
            }
            Row(
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                MyDefineTargetButton()
                Spacer(modifier = Modifier.padding(10.dp))
                MyAddButton()
                Spacer(modifier = Modifier.padding(5.dp))
                MyRemoveButton()
            }

        }
    }

    @Composable
    fun MyAddButton(){
        FloatingActionButton(onClick = {
            val numberOfTargets = storeTargetAreas[0].size
            storeTargetAreas[0].add(numberOfTargets,
                MyClassRectangle(0.0, 0.0, 50.0 , 50.0)
            )
            println(storeTargetAreas[0])
            helloViewModel.onDefiningPoints(numberOfTargets,true)
            helloViewModel.onSelectedTargetDefined(true)

        }) {
            Icon(Icons.Filled.Add, "add target")
        }
    }

    @Composable
    fun MyRemoveButton(){
        FloatingActionButton(onClick = {
            val numberOfTargets = storeTargetAreas[0].size
            if (numberOfTargets>0) {
                storeTargetAreas[0].removeAt(numberOfTargets-1)
                println(storeTargetAreas[0])
                helloViewModel.onDefiningPoints(numberOfTargets-1,false)
            }else{
                println(storeTargetAreas[0])
                helloViewModel.onDefiningPoints(0,false)
            }
        }) {
            Icon(Icons.Filled.Delete, "delete target")
        }
    }

    @Composable
    fun MyTitle(str: String){
        Text(text = str, fontSize = 20.sp)
    }

    @Composable
    fun MyImage(){
        var centerX by remember { mutableStateOf(0f) }
        var centerY by remember { mutableStateOf(0f) }
        var touchX by remember { mutableStateOf(0f) }
        var touchY by remember { mutableStateOf(0f) }
        var bitmap = MediaStore.Images.Media.getBitmap(requireContext().contentResolver, imgUri.dataUri)
        val widthImg = bitmap.width
        val heightImg = bitmap.height
        val heightFactor = 3.8f
        val arOriginal = widthImg.toFloat()/heightImg.toFloat()
        val screenWidthVerticalPosition = resources.displayMetrics.widthPixels
        var vHeight = screenWidthVerticalPosition.toFloat()/ arOriginal
        var vWidth = screenWidthVerticalPosition.toFloat()
        var arPointsW = widthImg.toFloat()/screenWidthVerticalPosition.toFloat()
        var arPointsH = heightImg.toFloat()/vHeight
        val arCanva = screenWidthVerticalPosition.toFloat()/500f
        var scaleFlag = false
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

        /*Image(bitmap = bitmap.asImageBitmap(),
            contentDescription = "Image selected",
            modifier = Modifier
                .onGloballyPositioned {
                    centerY = it.boundsInWindow().size.height / 2f
                    centerX = it.boundsInWindow().size.width / 2f
                    println("Center: $centerX and $centerY")
                    println("width: $widthImg and height: $heightImg")
                }
                .pointerInteropFilter { motionEvent ->
                    touchX = motionEvent.x
                    touchY = motionEvent.y
                    when (motionEvent.action) {
                        MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                            helloViewModel.onDefiningPoints(selectionTarget, false)
                            when (selectionPoint) {
                                "P0" -> {
                                    targetsRect["p0x"] = touchY
                                    targetsRect["p0y"] = touchX
                                }
                                "P1" -> {
                                    targetsRect["p1x"] = touchY
                                    targetsRect["p1y"] = touchX
                                }
                                "P2" -> {
                                    targetsRect["p2x"] = touchY
                                    targetsRect["p2y"] = touchX
                                }
                                "P3" -> {
                                    targetsRect["p3x"] = touchY
                                    targetsRect["p3y"] = touchX
                                }

                            }
                            println(targetsRect)
                            true
                        }
                        else -> false
                    }
                }
        )*/
        Canvas(
            modifier = Modifier
                .aspectRatio(arCanva)
                .onGloballyPositioned {
                    centerY = it.boundsInWindow().size.height / 2f
                    centerX = it.boundsInWindow().size.width / 2f
                    println("Center: $centerX and $centerY")
                    println("width: $widthImg and height: $heightImg")
                    println("Aspect ratio: $arOriginal")
                }
                .pointerInteropFilter { motionEvent ->
                    touchX = motionEvent.x
                    touchY = motionEvent.y
                    when (motionEvent.action) {
                        MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                            helloViewModel.onDefiningPoints(selectionTarget, false)

                            if (scaleFlag) {
                                arx = arPointsW
                                ary = arPointsH
                            }
                            when (selectionPoint) {
                                "P0" -> {
                                    targetsRect["p0x"] = limits(touchY * ary, heightImg)
                                    targetsRect["p0y"] = limits(touchX * arx, widthImg)
                                    helloViewModel.onSelectedPoint("P0")
                                }
                                "P1" -> {
                                    targetsRect["p1x"] = limits(touchY * ary, heightImg)
                                    targetsRect["p1y"] = limits(touchX * arx, widthImg)
                                    helloViewModel.onSelectedPoint("P1")
                                }
                                "P2" -> {
                                    targetsRect["p2x"] = limits(touchY * ary, heightImg)
                                    targetsRect["p2y"] = limits(touchX * arx, widthImg)
                                    helloViewModel.onSelectedPoint("P2")
                                }
                                "P3" -> {
                                    targetsRect["p3x"] = limits(touchY * ary, heightImg)
                                    targetsRect["p3y"] = limits(touchX * arx, widthImg)
                                    helloViewModel.onSelectedPoint("P3")
                                }

                            }
                            println(targetsRect)
                            true
                        }
                        else -> false
                    }
                }
        ){
            if (scaleFlag) {
                arx = arPointsW
                ary = arPointsH
            }
            drawImage(
                image = bitmap.asImageBitmap()
                )
            drawCircle(
                color = Color(0xFFFFFF9C),
                radius = 15f,
                center = Offset(touchX, touchY)
            )
            drawRect(
                color = Color(0xFFFFFF9C),
                topLeft = Offset(targetsRect["p0y"]!!/arx, targetsRect["p0x"]!!/ary),
                size = Size(width = targetsRect["p3y"]!!/arx-targetsRect["p0y"]!!/arx,
                    height = targetsRect["p3x"]!!/ary-targetsRect["p0x"]!!/ary),
                style = Stroke(
                    width = 3.dp.toPx(),
                    miter = 5.dp.toPx(),
                    cap = StrokeCap.Square,
                    pathEffect = PathEffect.cornerPathEffect(2.dp.toPx())
                )
            )
        }

    }

    @Composable
    fun MyDefineTargetButton(){
        Button(onClick = {
            helloViewModel.onSelectedTargetDefined(false)
            storeTargetAreas[0][selectionTarget]= MyClassRectangle(targetsRect["p0x"]!!.toDouble(),
                targetsRect["p0y"]!!.toDouble(),
                abs(targetsRect["p3x"]!!-targetsRect["p0x"]!!).toDouble(),
                abs(targetsRect["p3y"]!!-targetsRect["p0y"]!!).toDouble())
            helloViewModel.onSelectedTargetDefined(true)
            helloViewModel.onDefiningPoints(selectionTarget, true)
            println("Do target")
        })
        {
            Text(text = "Define target", fontSize = 16.sp)
        }
    }

    @Composable
    fun DisplayRadioGroup(){
        var selected by remember { mutableStateOf("P0") }
        val selectPoint by helloViewModel.statePoint.observeAsState(initial = "P0")
        Row {
            RadioButton(selected = selected == "P0",
                onClick = {
                    selected = "P0"
                    selectionPoint = "P0"
                    helloViewModel.onSelectedPoint(selected)})
            Text(
                text = "Upper Left",
                modifier = Modifier
                    .clickable(onClick = {
                        selected = "P0"
                        selectionPoint = "P0"
                        helloViewModel.onSelectedPoint(selected)
                    })
                    .padding(start = 4.dp)
            )
            /*Spacer(modifier = Modifier.size(4.dp))
            RadioButton(selected = selected == "P1",
                onClick = { selected = "P1"
                    helloViewModel.onSelectedPoint(selected)})
            Text(
                text = "P1",
                modifier = Modifier
                    .clickable(onClick = {
                        selected = "P1"
                        selectionPoint = "P1"
                        helloViewModel.onSelectedPoint(selected)
                    })
                    .padding(start = 4.dp)
            )
            Spacer(modifier = Modifier.size(4.dp))
            RadioButton(selected = selected == "P2",
                onClick = { selected = "P2"
                    helloViewModel.onSelectedPoint(selected)})
            Text(
                text = "P2",
                modifier = Modifier
                    .clickable(onClick = {
                        selected = "P2"
                        selectionPoint = "P2"
                        helloViewModel.onSelectedPoint(selected)
                    })
                    .padding(start = 4.dp)
            )*/
            Spacer(modifier = Modifier.size(4.dp))
            RadioButton(selected = selected == "P3",
                onClick = {
                    selected = "P3"
                    selectionPoint = "P3"
                    helloViewModel.onSelectedPoint(selected)})
            Text(
                text = "Bottom Right",
                modifier = Modifier
                    .clickable(onClick = {
                        selected = "P3"
                        selectionPoint = "P3"
                        helloViewModel.onSelectedPoint(selected)
                    })
                    .padding(start = 4.dp)
            )
        }
    }

    @Composable
    fun DisplayListRectangles(){
        val flagInd by helloViewModel.stateInd.observeAsState(initial = false)
        val flagIndShow by helloViewModel.stateIndShow.observeAsState(initial = false)
        val targetIndShow by helloViewModel.indShow.observeAsState(initial = 0)
        var targetsList = IntArray(storeTargetAreas[0].size) { 1 * (it + 1) }
        if (targetIndShow>0 && flagIndShow) {
            targetsList = IntArray(storeTargetAreas[0].size) { 1 * (it + 1) }
        }
        LazyColumn(modifier = Modifier.height(90.dp)){
            items(items = targetsList.toList()){
                RectangleData(recNumber = it, flagInd, targetIndShow, flagIndShow)
            }
        }
    }

    @Composable
    fun RectangleData(recNumber: Int, flagInd: Boolean, recShow: Int, flagIndShow: Boolean){
        if (flagInd) {
            val indRec = recNumber - 1
            Text(
                text = "Target: $recNumber", style = MaterialTheme.typography.h6,
                modifier = Modifier.clickable(onClick = {
                    helloViewModel.onSelectedTarget(indRec)
//                    helloViewModel.onSelectedTargetDefined(false)
                    selectionTarget = indRec
                    println("Selected target: $indRec")
                })
            )
            Text(
                text = "x:${storeTargetAreas[0][indRec].x.toInt()} y:${storeTargetAreas[0][indRec].y.toInt()} Width:${storeTargetAreas[0][indRec].width.toInt()} Height:${storeTargetAreas[0][indRec].height.toInt()}",
                style = MaterialTheme.typography.body2,
                color = Color.Black.copy(.5f),
                modifier = Modifier.clickable(onClick = {
                    helloViewModel.onSelectedTarget(indRec)
//                    helloViewModel.onSelectedTargetDefined(false)
                    selectionTarget = indRec
                    println("Selected target: $indRec")
                })
            )
        }
    }

    @Preview(showBackground = true)
    @Composable
    fun DefaultPreview() {
        Main("Targets")
    }

}