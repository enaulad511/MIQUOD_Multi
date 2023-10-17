package com.poc_itesm.miquod2

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActionScope
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.fragment.app.Fragment
import androidx.navigation.NavController
import androidx.navigation.Navigation


class ConfigurationFragment : Fragment() {
    private var navController: NavController? = null
    private var textError ="Error"
    var typeErr = 2
    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        // Inflate the layout for this fragment
        return ComposeView(requireContext()).apply {
            setContent {
                navController = Navigation.findNavController(this)
                Main("Configuration")
            }
        }
    }
    @Composable
    private fun Main(title: String) {
        val parameters = listOf<String>("Threshold value gray filter", "Threshold blob detector",
        "Area Blob Filters", "Circularity Blob Filters", "Convexity Blob Filters",
        "Inertia Blob Filters", "Color of dyes", "Erode and Dilate Filters")
        Column (
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier
                .fillMaxHeight()
                .fillMaxWidth()
        ) {
            Title(title = title)
            Subtitle(subtitle = "Filter Parameters")
            Filters(parameters)
            Subtitle(subtitle = "Particle Data")
            ColorsParticle()
            //ThresholdInput()
            //ThresholdBlobInput()
            //DisplayAreaBlobFilter()
            //DisplayCirBlobFilter()
            //DisplayConBlobFilter()
            //DisplayInertiaBlobFilter()
            //DisplayColorBlobFilter()
            //DisplayErodeDilateFilters()
        }
    }

    @Composable
    private fun ColorsParticle() {
        ColorsCount()
        Row(
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            ColorsCheckboxList()
            Spacer(Modifier.size(16.dp))

        }
    }

    @Composable
    private fun ColorsCount() {
        val valCount by helloViewModel.stateColorCountValue.observeAsState(initial = 0)
        Row (horizontalArrangement = Arrangement.Start){
            Text(text = "Colors to detect:")
            Spacer(Modifier.size(6.dp))
            colorSelectedCount = if (valCount > 0){
                Text(text = valCount.toString())
                valCount
            }else{
                Text(text = "Default color")
                0
            }
        }
    }

    @Composable
    fun ColorsCheckboxList() {
        val colorsParticles = listOf("Red", "Blue", "Yellow", "Green")
        val localFocusManager = LocalFocusManager.current
        val flagColorError by helloViewModel.stateColorValueError.observeAsState(initial = false)
        val options = colorsParticles.map { it0 ->
            val checked = remember { mutableStateOf(false)}
            val valuedR = remember { mutableStateOf(defaultValuesColors[it0]!!["R"]!!.toString())}
            val valuedG = remember { mutableStateOf(defaultValuesColors[it0]!!["G"]!!.toString())}
            val valuedB = remember { mutableStateOf(defaultValuesColors[it0]!!["B"]!!.toString())}
            Option(
                checked = checked.value,
                onCheckedChange = { it1 ->
                    colorsSelected[it0] = it1
                    helloViewModel.onColorCount(colorsSelected.count{it.value})
                    checked.value = it1 },
                label = it0,
                onValueChangeR = {newValue ->
                    valuedR.value = newValue },
                onValueDoneR = {
                    localFocusManager.clearFocus()
                    val resultValueChecked = validateColorValue(
                        valueRGB = valuedR.value, label= it0, layer = "R" )
                    if (resultValueChecked.errorFlag) {
                        colorScaleR[it0]= defaultValuesColors[it0]!!["R"]!!
                        valuedR.value = defaultValuesColors[it0]!!["R"]!!.toString()
                        helloViewModel.onChangeValueColorError(resultValueChecked.errorFlag)
                    }else{
                        colorScaleR[it0] = valuedR.value.toFloat()
                    }
                },
                valueR = valuedR.value,
                onValueChangeG = {newValue ->
                    valuedG.value = newValue },
                onValueDoneG = {
                    localFocusManager.clearFocus()
                    val resultValueChecked = validateColorValue(
                        valueRGB = valuedG.value, label= it0, layer = "G" )
                    helloViewModel.onChangeValueColorError(resultValueChecked.errorFlag)
                    if (flagColorError) {
                        colorScaleG[it0]= defaultValuesColors[it0]!!["G"]!!
                        valuedG.value = defaultValuesColors[it0]!!["G"]!!.toString()
                    }else{
                        colorScaleG[it0] = valuedG.value.toFloat()
                        helloViewModel.onChangeValueColorError(false)
                    }
                },
                valueG = valuedG.value,
                onValueChangeB = {newValue ->
                    valuedB.value = newValue },
                onValueDoneB = {
                    localFocusManager.clearFocus()
                    val resultValueChecked = validateColorValue(
                        valueRGB = valuedB.value, label= it0, layer = "B" )
                    if (resultValueChecked.errorFlag) {
                        colorScaleB[it0]= defaultValuesColors[it0]!!["B"]!!
                        valuedB.value = defaultValuesColors[it0]!!["B"]!!.toString()
                        helloViewModel.onChangeValueColorError(resultValueChecked.errorFlag)
                    }else{
                        colorScaleB[it0] = valuedB.value.toFloat()
                    }
                },
                valueB = valuedB.value
            )
        }
        CheckboxList(options = options, listTitle = "Colors allowed")
        if (flagColorError){
            PopMessage(text = textError, 255.0, typeErr)
            print("Colors: $colorScaleR ,  $colorScaleG,  $colorScaleB")
        }
    }

    data class Option( // 1
        var checked: Boolean,
        var onCheckedChange: (Boolean) -> Unit = {},
        val label: String,
        val valueR: String,
        val valueG: String,
        val valueB: String,
        val onValueChangeR: (String) -> Unit = {},
        val onValueChangeG: (String) -> Unit = {},
        val onValueChangeB: (String) -> Unit = {},
        val onValueDoneR: KeyboardActionScope.() -> Unit = {},
        val onValueDoneG: KeyboardActionScope.() -> Unit = {},
        val onValueDoneB: KeyboardActionScope.() -> Unit = {},
        var enabled: Boolean = true
    )

    @Composable
    fun CheckboxList(options: List<Option>, listTitle: String) {// 2
        Column {
            Text(listTitle, textAlign = TextAlign.Justify)
            Spacer(Modifier.size(6.dp))
            LazyColumn(
                modifier = Modifier.height(115.dp)
            ){
                items(options){ option ->
                    LabelledCheckbox(
                        checked = option.checked,
                        onCheckedChange = option.onCheckedChange,
                        label = option.label,
                        onValueChangeR = option.onValueChangeR,
                        onValueChangeG = option.onValueChangeG,
                        onValueChangeB = option.onValueChangeB,
                        onValueDoneR = option.onValueDoneR,
                        onValueDoneG = option.onValueDoneG,
                        onValueDoneB = option.onValueDoneB,
                        valueR = option.valueR,
                        valueG = option.valueG,
                        valueB = option.valueB,
                        enabled = option.enabled
                    )
                }
            }
        }
    }

    data class ErrorResultPack (
        var typeError: Int,
        var textError: String,
        var errorFlag: Boolean = false
    )

    private fun validateColorValue(valueRGB: String, label: String, layer: String): ErrorResultPack{
        val result = ErrorResultPack(
            typeError= 16,
            textError ="Invalid value on $label $layer layer," +
                    " it must be between limits, so value set to default",
            errorFlag = false)
        if(valueRGB.isNotEmpty()) {
            try{
                val valueT = valueRGB.toFloat()
                if (!valueT.isNaN()) {
                    if (valueT in 0f..1f) {
                        when (layer){
                            "R"->{
                                colorScaleR[label] = valueT
                            }
                            "G"->{
                                colorScaleG[label] = valueT
                            }
                            "B"->{
                                colorScaleB[label] = valueT
                            }
                        }
                        result.errorFlag = false
                    }else{
                        println("Invalid values ${result.typeError}")
                        result.textError = "Invalid value on $label $layer layer," +
                                " it must be between limits, so value set to default"
                        textError = result.textError
                        typeErr = result.typeError
                        result.errorFlag = true
                    }
                } else {
                    println("Invalid value signs")
                    typeErr = result.typeError
                    result.errorFlag = true
                }
            }catch(e: Exception){
                println("Exception on conversion ${result.typeError} : $e")
                typeErr = result.typeError
                result.textError = "Error on conversion: $e, so value set to default"
                textError = result.textError
                result.errorFlag = true
            }

        }else{
            println("Invalid Value ${result.typeError}")
            typeErr = result.typeError
            result.textError = "Value is empty, so default value assigned"
            result.errorFlag = true
        }
        print("error: ${result.errorFlag}")
        return result
    }


    @Composable
    fun LabelledCheckbox(
        checked: Boolean,
        onCheckedChange: (Boolean) -> Unit,
        label: String,
        modifier: Modifier = Modifier,
        enabled: Boolean = true,
        valueR: String,
        valueG: String,
        valueB: String,
        onValueChangeR: (String) -> Unit,
        onValueChangeG: (String) -> Unit,
        onValueChangeB: (String) -> Unit,
        onValueDoneR: KeyboardActionScope.() -> Unit,
        onValueDoneG: KeyboardActionScope.() -> Unit,
        onValueDoneB: KeyboardActionScope.() -> Unit,
        colors: CheckboxColors = CheckboxDefaults.colors()
    ) {
        val columns = listOf("Checkbox")
        val targetsList = IntArray(columns.size-1) { 1 * (it + 1) }
        var resultValueChecked = ErrorResultPack(16, "no error yet", false)
        LazyRow(
            modifier = modifier
                .height(50.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceEvenly
        ){
            items(columns){
                Checkbox(
                    checked = checked,
                    onCheckedChange = onCheckedChange,
                    enabled = enabled,
                    colors = colors
                )
                Spacer(Modifier.width(4.dp))
                Text(label, modifier= Modifier.width(50.dp))
                Spacer(modifier = Modifier.size(3.dp))
                TextField(
                    modifier = Modifier.width(105.dp),
                    value = valueR,
                    onValueChange = onValueChangeR,
                    label = {
                        Text("R")
                    },
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Number,
                        imeAction = ImeAction.Done
                    ),
                    leadingIcon = {
                        Icon(Icons.Filled.Edit, "Icon r")
                    },
                    keyboardActions = KeyboardActions(
                        onDone = onValueDoneR
                    )
                )
                Spacer(modifier = Modifier.size(2.dp))
                TextField(
                    modifier = Modifier.width(105.dp),
                    value = valueG,
                    onValueChange = onValueChangeG,
                    label = {
                        Text("G")
                    },
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Number,
                        imeAction = ImeAction.Done
                    ),
                    leadingIcon = {
                        Icon(Icons.Filled.Edit, "Icon G")
                    },
                    keyboardActions = KeyboardActions(
                        onDone = onValueDoneG
                    )
                )
                Spacer(modifier = Modifier.size(2.dp))
                TextField(
                    modifier = Modifier.width(105.dp),
                    value = valueB,
                    onValueChange = onValueChangeB,
                    label = {
                        Text("B")
                    },
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Number,
                        imeAction = ImeAction.Done
                    ),
                    leadingIcon = {
                        Icon(Icons.Filled.Edit, "Icon B")
                    },
                    keyboardActions = KeyboardActions(
                        onDone = onValueDoneB
                    )
                )
                Spacer(modifier = Modifier.size(2.dp))
                Canvas(
                    modifier = Modifier
                        .size(size = 30.dp)
                        .border(color = Color.Black, width = 2.dp)
                ) {
                    if(!resultValueChecked.errorFlag){
                        try {
                            drawCircle(
                                color = Color(
                                    red = colorScaleR[label]!!.toFloat(),
                                    green = colorScaleG[label]!!.toFloat(),
                                    blue = colorScaleB[label]!!.toFloat()
                                ),
                                radius = 10.dp.toPx()
                            )
                        }catch(e: Exception){
                            println("Error draw circles:  $e")
                        }
                    }
                }
            }

        }
    }

    @Composable
    fun Filters(parameters: List<String>) {
        val targetIndToShow by helloViewModel.indFilterShow.observeAsState(initial = 0)
        val targetsList = IntArray(parameters.size-1) { 1 * (it + 1) }
        LazyColumn(
            verticalArrangement = Arrangement.SpaceEvenly,
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.height(300.dp)
        ) {
            items(items = targetsList.toList()){
                ShowFilters(Title = parameters[it], index = it )
            }
        }
    }

    @Composable
    fun ShowFilters(Title: String, index: Int){
        Text(text = Title)
        when (index){
            0->{
                ThresholdInput()
            }
            1->{
                ThresholdBlobInput()
            }
            2->{
                DisplayAreaBlobFilter()
            }
            3->{
                DisplayCirBlobFilter()
            }
            4->{
                DisplayConBlobFilter()
            }
            5->{
                DisplayInertiaBlobFilter()
            }
            6->{
                DisplayColorBlobFilter()
            }
            7->{
                DisplayErodeDilateFilters()
            }
        }
    }

    @Composable
    fun DisplayErodeDilateFilters() {
        val openDialogMin by helloViewModel.stateErodeX.observeAsState(initial = false)
        val textMin by helloViewModel.stateErodeXValue.observeAsState(initial = defaultValues[2])
        val openDialogMax by helloViewModel.stateErodeY.observeAsState(initial = false)
        val textMax by helloViewModel.stateErodeYValue.observeAsState(initial = defaultValues[2])
        val openDialogMinD by helloViewModel.stateDilateX.observeAsState(initial = false)
        val textMinD by helloViewModel.stateDilateXValue.observeAsState(initial = defaultValues[2])
        val openDialogMaxD by helloViewModel.stateDilateY.observeAsState(initial = false)
        val textMaxD by helloViewModel.stateDilateYValue.observeAsState(initial = defaultValues[2])
        val localFocusManager = LocalFocusManager.current
        Text(text = "Erode image filter")
        Row {
            TextField(
                modifier = Modifier.width(100.dp),
                value = textMin,
                onValueChange = { newValue ->
                    helloViewModel.onChangeErodeX(newValue)
                },
                label = {
                    Text("X")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon min")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMin.isNotEmpty()) {
                            try{
                                val valueT = textMin.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in 0.0..100.0) {
                                        limitErodeX= valueT
                                        helloViewModel.onErodeXError(false)
                                    }else{
                                        println("Invalid values 12")
                                        typeErr = 12
                                        textError = "Invalid value, it must be between 0 and 100.0," +
                                                " so value set to default. Also take into account " +
                                                "that big values can erase details"
                                        helloViewModel.onErodeXError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 12")
                                    typeErr = 12
                                    helloViewModel.onErodeXError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 12 : $e")
                                typeErr = 12
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onErodeXError(true)
                            }

                        }else{
                            println("Invalid Value 12")
                            typeErr = 12
                            textError = "Value is empty, so default value assigned"
                            helloViewModel.onErodeXError(true)
                            helloViewModel.onChangeErodeX(defaultValues[2])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
            Spacer(modifier = Modifier.size(4.dp))
            TextField(
                modifier = Modifier.width(100.dp),
                value = textMax,
                onValueChange = { newValue ->
                    helloViewModel.onChangeErodeY(newValue)
                },
                label = {
                    Text("Y")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon max")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMax.isNotEmpty()) {
                            try{
                                val valueT = textMax.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in 0.0..100.0) {
                                        limitErodeY = valueT
                                        helloViewModel.onErodeYError(false)
                                    }else{
                                        println("Invalid values 13")
                                        typeErr = 13
                                        textError = "Invalid value, it must be between 0 and 100.0," +
                                                " so value set to default. Also take into account " +
                                                "that big values can erase details"
                                        helloViewModel.onErodeYError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 13")
                                    typeErr = 13
                                    helloViewModel.onErodeYError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 13: $e")
                                typeErr = 13
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onErodeYError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 13")
                            typeErr = 13
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onErodeYError(true)
                            helloViewModel.onChangeErodeY(defaultValues[2])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
        }
        Text(text = "Dilate image filter")
        Row {
            TextField(
                modifier = Modifier.width(100.dp),
                value = textMinD,
                onValueChange = { newValue ->
                    helloViewModel.onChangeDilateX(newValue)
                },
                label = {
                    Text("X")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon min")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMinD.isNotEmpty()) {
                            try{
                                val valueT = textMinD.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in 0.0..100.0) {
                                        limitDilateX= valueT
                                        helloViewModel.onDilateXError(false)
                                    }else{
                                        println("Invalid values 14")
                                        typeErr = 14
                                        textError = "Invalid value, it must be between 0 and 100.0," +
                                                " so value set to default. Also take into account " +
                                                "that big values can erase details"
                                        helloViewModel.onDilateXError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 14")
                                    typeErr = 14
                                    helloViewModel.onDilateXError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 14 : $e")
                                typeErr = 14
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onDilateXError(true)
                            }

                        }else{
                            println("Invalid Value 14")
                            typeErr = 14
                            textError = "Value is empty, so default value assigned"
                            helloViewModel.onDilateXError(true)
                            helloViewModel.onChangeDilateX(defaultValues[2])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
            Spacer(modifier = Modifier.size(4.dp))
            TextField(
                modifier = Modifier.width(100.dp),
                value = textMaxD,
                onValueChange = { newValue ->
                    helloViewModel.onChangeDilateY(newValue)
                },
                label = {
                    Text("Y")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon max")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMaxD.isNotEmpty()) {
                            try{
                                val valueT = textMaxD.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in 0.0..100.0) {
                                        limitDilateY = valueT
                                        helloViewModel.onDilateYError(false)
                                    }else{
                                        println("Invalid values 15")
                                        typeErr = 15
                                        textError = "Invalid value, it must be between 0 and 100.0," +
                                                " so value set to default. Also take into account " +
                                                "that big values can erase details"
                                        helloViewModel.onDilateYError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 15")
                                    typeErr = 15
                                    helloViewModel.onDilateYError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 15: $e")
                                typeErr = 15
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onDilateYError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 15")
                            typeErr = 15
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onDilateYError(true)
                            helloViewModel.onChangeDilateY(defaultValues[2])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
        }
        if (openDialogMin || openDialogMax||openDialogMinD || openDialogMaxD){
            println("textMin: $textMin")
            println(openDialogMin)
            println("textMax: $textMax")
            println(openDialogMax)
            println("textMin: $textMinD")
            println(openDialogMinD)
            println("textMax: $textMaxD")
            println(openDialogMaxD)
            PopMessage(text = textError, 255.0, typeErr)
        }
    }

    @Composable
    fun DisplayColorBlobFilter() {
        val filterFlagColorBlob by helloViewModel.stateColorBlob.observeAsState(initial = false)
        val localFocusManager = LocalFocusManager.current
        //Text(text = "Inertia blob filters")
        Row (
            modifier = Modifier
                .height(30.dp),
            verticalAlignment = Alignment.CenterVertically
        ){
            IconToggleButton(
                checked = filterFlagColorBlob,
                onCheckedChange = {
                    println("Filtered by Con changed to: $it")
                    flagBlobColor = it
                    helloViewModel.onColorBlobSelected(it)
                }) {
                Icon(
                    imageVector = if (filterFlagColorBlob) Icons.Filled.CheckCircle else Icons.Outlined.CheckCircle,
                    contentDescription = //4
                    if (filterFlagColorBlob) "Filtered by Con"
                    else "Not filtered by Con",
                    tint = Color(0xFF26C6DA)
                )
            }
            Spacer(modifier = Modifier.size(14.dp))
            Text(
                text = if (filterFlagColorBlob) "Clear dyes" else "Dark dyes",
                color = if (filterFlagColorBlob) Color.LightGray else Color.DarkGray,
                fontSize = 17.sp,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center
            )
        }
    }

    @Composable
    fun DisplayInertiaBlobFilter() {
        val filterFlagIneBlob by helloViewModel.stateIneBlob.observeAsState(initial = false)
        val openDialogMin by helloViewModel.stateIneBlobMin.observeAsState(initial = false)
        val textMin by helloViewModel.stateIneBlobMinValue.observeAsState(initial = defaultValues[0])
        val openDialogMax by helloViewModel.stateIneBlobMax.observeAsState(initial = false)
        val textMax by helloViewModel.stateIneBlobMaxValue.observeAsState(initial = defaultValues[2])
//        var checked by remember { mutableStateOf(false) } //1
        val localFocusManager = LocalFocusManager.current
        //Text(text = "Inertia blob filters")
        Row {
            IconToggleButton(
                checked = filterFlagIneBlob,
                onCheckedChange = {
                    println("Filtered by Con changed to: $it")
                    flagBlobConvexity = it
                    helloViewModel.onIneBlobSelected(it)
                }) {
                Icon(
                    imageVector = if (filterFlagIneBlob) Icons.Filled.CheckCircle else Icons.Outlined.CheckCircle,
                    contentDescription = //4
                    if (filterFlagIneBlob) "Filtered by Con"
                    else "Not filtered by Con",
                    tint = Color(0xFF26C6DA)
                )
            }
            Spacer(modifier = Modifier.size(14.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMin,
                onValueChange = { newValue ->
                    helloViewModel.onChangeIneBlobMin(newValue)
                },
                label = {
                    Text("Min")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon min")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMin.isNotEmpty()) {
                            try{
                                val valueT = textMin.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in 0.0..1.0) {
                                        limitConvMin= valueT.toFloat()
                                        helloViewModel.onIneBlobMinError(false)
                                    }else{
                                        println("Invalid values 10")
                                        typeErr = 10
                                        textError = "Invalid value, it must be between 0 and 1.0, so value set to default"
                                        helloViewModel.onIneBlobMinError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 10")
                                    typeErr = 10
                                    helloViewModel.onIneBlobMinError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 10 : $e")
                                typeErr = 10
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onIneBlobMinError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 10")
                            typeErr = 10
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onIneBlobMinError(true)
                            helloViewModel.onChangeIneBlobMin(defaultValues[0])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
            Spacer(modifier = Modifier.size(4.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMax,
                onValueChange = { newValue ->
                    helloViewModel.onChangeIneBlobMax(newValue)
                },
                label = {
                    Text("Max")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon max")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMax.isNotEmpty()) {
                            try{
                                val valueT = textMax.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in thresholdBlobMin..1.0) {
                                        limitConvMax = valueT.toFloat()
                                        helloViewModel.onIneBlobMaxError(false)
                                    }else{
                                        println("Invalid values 11")
                                        typeErr = 11
                                        textError = "Invalid value, it must be between Min and 1.0, so value set to default"
                                        helloViewModel.onIneBlobMaxError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 11")
                                    typeErr = 11
                                    helloViewModel.onIneBlobMaxError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 11: $e")
                                typeErr = 11
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onIneBlobMaxError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 11")
                            typeErr = 11
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onIneBlobMaxError(true)
                            helloViewModel.onChangeIneBlobMax(defaultValues[2])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
        }
        if (openDialogMin || openDialogMax){
            println("textMin: $textMin")
            println(openDialogMin)
            println("textMax: $textMax")
            println(openDialogMax)
            PopMessage(text = textError, 255.0, typeErr)
        }
    }

    @Composable
    fun DisplayConBlobFilter() {
        val filterFlagConBlob by helloViewModel.stateConBlob.observeAsState(initial = false)
        val openDialogMin by helloViewModel.stateConBlobMin.observeAsState(initial = false)
        val textMin by helloViewModel.stateConBlobMinValue.observeAsState(initial = defaultValues[0])
        val openDialogMax by helloViewModel.stateConBlobMax.observeAsState(initial = false)
        val textMax by helloViewModel.stateConBlobMaxValue.observeAsState(initial = defaultValues[2])
//        var checked by remember { mutableStateOf(false) } //1
        val localFocusManager = LocalFocusManager.current
        //Text(text = "Convexity blob filters")
        Row {
            IconToggleButton(
                checked = filterFlagConBlob,
                onCheckedChange = {
                    println("Filtered by Con changed to: $it")
                    flagBlobConvexity = it
                    helloViewModel.onConBlobSelected(it)
                }) {
                Icon(
                    imageVector = if (filterFlagConBlob) Icons.Filled.CheckCircle else Icons.Outlined.CheckCircle,
                    contentDescription = //4
                    if (filterFlagConBlob) "Filtered by Con"
                    else "Not filtered by Con",
                    tint = Color(0xFF26C6DA)
                )
            }
            Spacer(modifier = Modifier.size(14.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMin,
                onValueChange = { newValue ->
                    helloViewModel.onChangeConBlobMin(newValue)
                },
                label = {
                    Text("Min")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon min")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMin.isNotEmpty()) {
                            try{
                                val valueT = textMin.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in 0.0..1.0) {
                                        limitConvMin= valueT.toFloat()
                                        helloViewModel.onConBlobMinError(false)
                                    }else{
                                        println("Invalid values 8")
                                        typeErr = 8
                                        textError = "Invalid value, it must be between 0 and 1.0, so value set to default"
                                        helloViewModel.onConBlobMinError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 8")
                                    typeErr = 8
                                    helloViewModel.onConBlobMinError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 8 : $e")
                                typeErr = 8
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onConBlobMinError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 8")
                            typeErr = 8
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onConBlobMinError(true)
                            helloViewModel.onChangeConBlobMin(defaultValues[0])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
            Spacer(modifier = Modifier.size(4.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMax,
                onValueChange = { newValue ->
                    helloViewModel.onChangeConBlobMax(newValue)
                },
                label = {
                    Text("Max")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon max")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMax.isNotEmpty()) {
                            try{
                                val valueT = textMax.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in thresholdBlobMin..1.0) {
                                        limitConvMax = valueT.toFloat()
                                        helloViewModel.onConBlobMaxError(false)
                                    }else{
                                        println("Invalid values 9")
                                        typeErr = 9
                                        textError = "Invalid value, it must be between Min and 1.0, so value set to default"
                                        helloViewModel.onConBlobMaxError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 9")
                                    typeErr = 9
                                    helloViewModel.onConBlobMaxError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 9: $e")
                                typeErr = 9
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onConBlobMaxError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 9")
                            typeErr = 9
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onConBlobMaxError(true)
                            helloViewModel.onChangeConBlobMax(defaultValues[2])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
        }
        if (openDialogMin || openDialogMax){
            println("textMin: $textMin")
            println(openDialogMin)
            println("textMax: $textMax")
            println(openDialogMax)
            PopMessage(text = textError, 255.0, typeErr)
        }
    }

    @Composable
    private fun DisplayCirBlobFilter() {
        val filterFlagCirBlob by helloViewModel.stateCirBlob.observeAsState(initial = false)
        val openDialogMin by helloViewModel.stateCirBlobMin.observeAsState(initial = false)
        val textMin by helloViewModel.stateCirBlobMinValue.observeAsState(initial = defaultValues[1])
        val openDialogMax by helloViewModel.stateCirBlobMax.observeAsState(initial = false)
        val textMax by helloViewModel.stateCirBlobMaxValue.observeAsState(initial = defaultValues[2])
//        var checked by remember { mutableStateOf(false) } //1
        val localFocusManager = LocalFocusManager.current
        //Text(text = "Circularity blob filters")
        Row {
            IconToggleButton(
                checked = filterFlagCirBlob,
                onCheckedChange = {
                    println("Filtered by Cir changed to: $it")
                    flagBlobCircularity = it
                    helloViewModel.onCirBlobSelected(it)
                }) {
                Icon(
                    imageVector = if (filterFlagCirBlob) Icons.Filled.CheckCircle else Icons.Outlined.CheckCircle,
                    contentDescription = //4
                    if (filterFlagCirBlob) "Filtered by Cir"
                    else "Not filtered by Cir",
                    tint = Color(0xFF26C6DA)
                )
            }
            Spacer(modifier = Modifier.size(14.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMin,
                onValueChange = { newValue ->
                    helloViewModel.onChangeCirBlobMin(newValue)
                },
                label = {
                    Text("Min")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon min")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMin.isNotEmpty()) {
                            try{
                                val valueT = textMin.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in 0.0..1.0) {
                                        minCircularity = valueT.toFloat()
                                        helloViewModel.onCirBlobMinError(false)
                                    }else{
                                        println("Invalid values 6")
                                        typeErr = 6
                                        textError = "Invalid value, it must be between 0 and 1.0, so value set to default"
                                        helloViewModel.onCirBlobMinError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 6")
                                    typeErr = 6
                                    helloViewModel.onCirBlobMinError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 6 : $e")
                                typeErr = 6
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onCirBlobMinError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 6")
                            typeErr = 6
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onCirBlobMinError(true)
                            helloViewModel.onChangeCirBlobMin(defaultValues[1])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
            Spacer(modifier = Modifier.size(4.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMax,
                onValueChange = { newValue ->
                    helloViewModel.onChangeCirBlobMax(newValue)
                },
                label = {
                    Text("Max")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon max")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMax.isNotEmpty()) {
                            try{
                                val valueT = textMax.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT in thresholdBlobMin..1.0) {
                                        maxCircularity = valueT.toFloat()
                                        helloViewModel.onCirBlobMaxError(false)
                                    }else{
                                        println("Invalid values 7")
                                        typeErr = 7
                                        textError = "Invalid value, it must be between Min and 1.0, so value set to default"
                                        helloViewModel.onCirBlobMaxError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 7")
                                    typeErr = 7
                                    helloViewModel.onCirBlobMaxError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 7: $e")
                                typeErr = 7
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onCirBlobMaxError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 7")
                            typeErr = 7
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onCirBlobMaxError(true)
                            helloViewModel.onChangeCirBlobMax(defaultValues[2])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
        }
        if (openDialogMin || openDialogMax){
            println("textMin: $textMin")
            println(openDialogMin)
            println("textMax: $textMax")
            println(openDialogMax)
            PopMessage(text = textError, 255.0, typeErr)
        }
    }

    @Composable
    private fun ThresholdInput() {
//        var text by remember { mutableStateOf("80") }
        val openDialog by helloViewModel.stateThreshold.observeAsState(initial = false)
        val text by helloViewModel.stateThresholdValue.observeAsState(defaultValues[3])
        val localFocusManager = LocalFocusManager.current
        TextField(
            value = text,
            onValueChange = { newValue ->
                helloViewModel.onChangeThreshold(newValue)
            },
            label = {
                Text("Threshold value gray filter")
                    },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Number,
                imeAction = ImeAction.Done
            ),
            leadingIcon = {
                Icon(Icons.Filled.Edit, "Icon threshold")
            },
            keyboardActions = KeyboardActions(
                onDone = {
                    if(text.isNotEmpty()) {
                        try{
                            val valueT = text.toDouble()
                            if (!valueT.isNaN()) {
                                if (valueT>0 && valueT<100) {
                                    thresholdValue = valueT
                                    helloViewModel.onThresholdError(false)
                                }else{
                                    println("Invalid values 1")
                                    textError = "Invalid value, it must be between 0 and 100, so value set to default"
                                    helloViewModel.onThresholdError(true)
                                }
                            } else {
                                println("Invalid Threshold Value signs 1")
                                helloViewModel.onThresholdError(true)
                            }
                        }catch(e: Exception){
                            println("Exception on conversion 1: $e")
                            textError = "Error on conversion: $e, so value set to default"
                            helloViewModel.onThresholdError(true)
                        }

                    }else{
                        println("Invalid Threshold Value 1")
                        textError = "Threshold value is empty, so default value assigned"
                        helloViewModel.onThresholdError(true)
                        helloViewModel.onChangeThreshold(defaultValues[3])
                    }
                    localFocusManager.clearFocus()
                }
            )
        )
        if (openDialog){
            println("text: $text")
            PopMessage(text = textError, 80.0, 1)
        }
    }

    @Composable
    private fun ThresholdBlobInput() {
//        var text by remember { mutableStateOf("80") }
        val openDialogMin by helloViewModel.stateThresholdMin.observeAsState(initial = false)
        val textMin by helloViewModel.stateThresholdMinValue.observeAsState(initial = defaultValues[4])
        val openDialogMax by helloViewModel.stateThresholdMax.observeAsState(initial = false)
        val textMax by helloViewModel.stateThresholdMaxValue.observeAsState(initial = defaultValues[5])
        val localFocusManager = LocalFocusManager.current
        //Text(text = "Threshold blob filters")
        Row (
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ){
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMin,
                onValueChange = { newValue ->
                    helloViewModel.onChangeThresholdMin(newValue)
                },
                label = {
                    Text("Min")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon threshold")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMin.isNotEmpty()) {
                            try{
                                val valueT = textMin.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT>0 && valueT<255) {
                                        thresholdBlobMin = valueT
                                        helloViewModel.onThresholdMinError(false)
                                    }else{
                                        println("Invalid values 2")
                                        typeErr = 2
                                        textError = "Invalid value, it must be between 0 and 255, so value set to default"
                                        helloViewModel.onThresholdMinError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 2")
                                    typeErr = 2
                                    helloViewModel.onThresholdMinError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion2 : $e")
                                typeErr = 2
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onThresholdMinError(true)
                            }
    
                        }else{
                            println("Invalid Threshold Value 2")
                            typeErr = 2
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onThresholdMinError(true)
                            helloViewModel.onChangeThresholdMin(defaultValues[4])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
            Spacer(modifier = Modifier.size(4.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMax,
                onValueChange = { newValue ->
                    helloViewModel.onChangeThresholdMax(newValue)
                },
                label = {
                    Text("Max")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon threshold")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMax.isNotEmpty()) {
                            try{
                                val valueT = textMax.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT> thresholdBlobMin && valueT<100) {
                                        thresholdBlobMax = valueT
                                        helloViewModel.onThresholdMaxError(false)
                                    }else{
                                        println("Invalid values 3")
                                        typeErr = 3
                                        textError = "Invalid value, it must be between Min and 255, so value set to default"
                                        helloViewModel.onThresholdMaxError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 3")
                                    typeErr = 3
                                    helloViewModel.onThresholdMaxError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 3: $e")
                                typeErr = 3
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onThresholdMaxError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 3")
                            typeErr = 3
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onThresholdMaxError(true)
                            helloViewModel.onChangeThresholdMax(defaultValues[5])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
        }
        if (openDialogMin || openDialogMax){
            println("textMin: $textMin")
            println(openDialogMin)
            println("textMax: $textMax")
            println(openDialogMax)
            PopMessage(text = textError, 255.0, typeErr)
        }
    }

    @Composable
    private fun DisplayAreaBlobFilter() {
//        var text by remember { mutableStateOf("80") }
        val filterFlagAreaBlob by helloViewModel.stateAreaBlob.observeAsState(initial = false)
        val openDialogMin by helloViewModel.stateAreaBlobMin.observeAsState(initial = false)
        val textMin by helloViewModel.stateAreaBlobMinValue.observeAsState(initial = defaultValues[2])
        val openDialogMax by helloViewModel.stateAreaBlobMax.observeAsState(initial = false)
        val textMax by helloViewModel.stateAreaBlobMaxValue.observeAsState(initial = defaultValues[4])
//        var checked by remember { mutableStateOf(false) } //1
        val localFocusManager = LocalFocusManager.current
        //Text(text = "Area blob filters")
        Row {
            IconToggleButton(
                checked = filterFlagAreaBlob,
                onCheckedChange = {
                    println("Filtered by area changed to: $it")
                    flagBlobArea = it
                    helloViewModel.onAreaBlobSelected(it)
                }) {
                Icon(
                    imageVector = if (filterFlagAreaBlob) Icons.Filled.CheckCircle else Icons.Outlined.CheckCircle,
                    contentDescription = //4
                    if (filterFlagAreaBlob) "Filtered by area"
                    else "Not filtered by area",
                    tint = Color(0xFF26C6DA)
                )
            }
            Spacer(modifier = Modifier.size(14.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMin,
                onValueChange = { newValue ->
                    helloViewModel.onChangeAreaBlobMin(newValue)
                },
                label = {
                    Text("Min")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon min")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMin.isNotEmpty()) {
                            try{
                                val valueT = textMin.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT>0 && valueT<2055) {
                                        limitAreaMin = valueT.toFloat()
                                        helloViewModel.onAreaBlobMinError(false)
                                    }else{
                                        println("Invalid values 4")
                                        typeErr = 4
                                        textError = "Invalid value, it must be between 0 and n, so value set to default"
                                        helloViewModel.onAreaBlobMinError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 4")
                                    typeErr = 4
                                    helloViewModel.onAreaBlobMinError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 4 : $e")
                                typeErr = 4
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onAreaBlobMinError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 4")
                            typeErr = 4
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onAreaBlobMinError(true)
                            helloViewModel.onChangeAreaBlobMin(defaultValues[4])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
            Spacer(modifier = Modifier.size(4.dp))
            TextField(
                modifier = Modifier.width(150.dp),
                value = textMax,
                onValueChange = { newValue ->
                    helloViewModel.onChangeAreaBlobMax(newValue)
                },
                label = {
                    Text("Max")
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                    imeAction = ImeAction.Done
                ),
                leadingIcon = {
                    Icon(Icons.Filled.Edit, "Icon max")
                },
                keyboardActions = KeyboardActions(
                    onDone = {
                        if(textMax.isNotEmpty()) {
                            try{
                                val valueT = textMax.toDouble()
                                if (!valueT.isNaN()) {
                                    if (valueT> limitAreaMin && valueT<10000) {
                                        limitAreaMax = valueT.toFloat()
                                        helloViewModel.onAreaBlobMaxError(false)
                                    }else{
                                        println("Invalid values 5")
                                        typeErr = 5
                                        textError = "Invalid value, it must be between Min and 255, so value set to default"
                                        helloViewModel.onAreaBlobMaxError(true)
                                    }
                                } else {
                                    println("Invalid Threshold Value signs 5")
                                    typeErr = 5
                                    helloViewModel.onAreaBlobMaxError(true)
                                }
                            }catch(e: Exception){
                                println("Exception on conversion 5: $e")
                                typeErr = 5
                                textError = "Error on conversion: $e, so value set to default"
                                helloViewModel.onAreaBlobMaxError(true)
                            }

                        }else{
                            println("Invalid Threshold Value 5")
                            typeErr = 5
                            textError = "Threshold value is empty, so default value assigned"
                            helloViewModel.onAreaBlobMaxError(true)
                            helloViewModel.onChangeAreaBlobMax(defaultValues[4])
                        }
                        localFocusManager.clearFocus()
                    }
                )
            )
        }
        if (openDialogMin || openDialogMax){
            println("textMin: $textMin")
            println(openDialogMin)
            println("textMax: $textMax")
            println(openDialogMax)
            PopMessage(text = textError, 255.0, typeErr)
        }
    }

    @Composable
    fun PopMessage(text: String, argDefault: Double, typeError: Int){
        AlertDialog(
            onDismissRequest = {
                println(text)
            },
            title = {
                Text(text = "Alert Message")
            },
            text = {
                Text(text = text)
            },
            buttons = {
                Button(
                    onClick = {
                        println("error type: $typeError")
                        when (typeError){
                            1->{
                                println("error type: $typeError")
                                thresholdValue = argDefault
                                helloViewModel.onChangeThreshold(defaultValues[3])
                                helloViewModel.onThresholdError(false)
                            }
                            2->{
                                println("error type: $typeError")
                                thresholdBlobMin = argDefault
                                helloViewModel.onChangeThresholdMin(defaultValues[4])
                                helloViewModel.onThresholdMinError(false)
                            }
                            3->{
                                println("error type: $typeError")
                                thresholdBlobMax = argDefault
                                helloViewModel.onChangeThresholdMax(defaultValues[5])
                                helloViewModel.onThresholdMaxError(false)
                            }
                            4->{
                                println("error type: $typeError")
                                limitAreaMin = argDefault.toFloat()
                                helloViewModel.onChangeAreaBlobMin(defaultValues[2])
                                helloViewModel.onAreaBlobMinError(false)
                            }
                            5->{
                                println("error type: $typeError")
                                limitAreaMax = argDefault.toFloat()
                                helloViewModel.onChangeAreaBlobMax(defaultValues[4])
                                helloViewModel.onAreaBlobMaxError(false)
                            }
                            6->{
                                println("error type: $typeError")
                                minCircularity = argDefault.toFloat()
                                helloViewModel.onChangeCirBlobMin(defaultValues[1])
                                helloViewModel.onCirBlobMinError(false)
                            }
                            7->{
                                println("error type: $typeError")
                                maxCircularity = argDefault.toFloat()
                                helloViewModel.onChangeCirBlobMax(defaultValues[2])
                                helloViewModel.onCirBlobMaxError(false)
                            }
                            8->{
                                println("error type: $typeError")
                                limitConvMin = argDefault.toFloat()
                                helloViewModel.onChangeConBlobMin(defaultValues[0])
                                helloViewModel.onConBlobMinError(false)
                            }
                            9->{
                                println("error type: $typeError")
                                limitConvMax = argDefault.toFloat()
                                helloViewModel.onChangeConBlobMax(defaultValues[2])
                                helloViewModel.onConBlobMaxError(false)
                            }
                            10->{
                                println("error type: $typeError")
                                limitRatioInertiaMin = argDefault.toFloat()
                                helloViewModel.onChangeIneBlobMin(defaultValues[0])
                                helloViewModel.onIneBlobMinError(false)
                            }
                            11->{
                                println("error type: $typeError")
                                limitRatioInertiaMax = argDefault.toFloat()
                                helloViewModel.onChangeIneBlobMax(defaultValues[2])
                                helloViewModel.onIneBlobMaxError(false)
                            }
                            12->{
                                println("error type: $typeError")
                                limitErodeX = argDefault
                                helloViewModel.onChangeErodeX(defaultValues[2])
                                helloViewModel.onErodeXError(false)
                            }
                            13->{
                                println("error type: $typeError")
                                limitErodeY = argDefault
                                helloViewModel.onChangeErodeY(defaultValues[2])
                                helloViewModel.onErodeYError(false)
                            }
                            14->{
                                println("error type: $typeError")
                                limitDilateX = argDefault
                                helloViewModel.onChangeDilateX(defaultValues[2])
                                helloViewModel.onDilateXError(false)
                            }
                            15->{
                                println("error type: $typeError")
                                limitDilateY = argDefault
                                helloViewModel.onChangeDilateY(defaultValues[2])
                                helloViewModel.onDilateYError(false)
                            }
                            16->{
                                println("error type: $typeError")
                                helloViewModel.onChangeValueColorError(false)
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(text = "Dismiss")
                }
            }
        )
    }

    @Composable
    private fun Title(title: String) {
        Text(text = title,
            fontSize = 30.sp,
            style = MaterialTheme.typography.h6
        )
    }
    @Composable
    private fun Subtitle(subtitle: String) {
        Text(text = subtitle,
            fontSize = 20.sp,
            style = MaterialTheme.typography.h6
        )
    }
}




