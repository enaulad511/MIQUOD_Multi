package com.poc_itesm.miquod2


import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.material.Button
import androidx.compose.material.ButtonDefaults
import androidx.compose.material.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.sp
import androidx.fragment.app.Fragment
import androidx.navigation.NavController
import androidx.navigation.Navigation
val defaultValues = listOf( "0.01", "0.05", "1.0", "80.0", "120.0", "255.0")
val defaultValuesColors = mapOf(
    "Red" to mapOf("R" to 1f, "G" to 0f, "B" to 0f),
    "Green" to mapOf("R" to 0f, "G" to 1f, "B" to 0f),
    "Blue" to mapOf("R" to 0f, "G" to 0f, "B" to 1f),
    "Yellow" to mapOf("R" to 1f, "G" to 0.918f, "B" to 0f))

class StartFragment : Fragment() {
    private var navController: NavController? = null
    private val scaleApp = 3f
    private val scalePreview = 1f
    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
        ): View {
        // Inflate the layout for this fragment
        return ComposeView(requireContext()).apply {
            setContent {
                navController = Navigation.findNavController(this)
                Main(Title = "Welcome To MIQUOD APP", scaleApp)
            }
        }
    }
    @Composable
    fun Main(Title: String, scaleImage: Float) {
        Column (
            verticalArrangement = Arrangement.SpaceEvenly,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            MyTitle(Title)
            MyImage(scaleImage)
            MyStartButton()
        }
    }

    @Composable
    fun MyTitle(str: String){
        Text(text = str, fontSize = 30.sp)
    }

    @Composable
    fun MyImage(sclImg: Float){
        Image(
            painterResource(id = R.drawable.logo),
            contentDescription = "Test Image", modifier = Modifier.scale(sclImg)
        )
    }

    @Composable
    fun MyStartButton(){
        Button(onClick = {
            flagPathAcquired = false
            helloViewModel.onImgSelected(false)
            navController!!.navigate(R.id.action_startFragment_to_mainFragment)
        }, colors = ButtonDefaults.buttonColors(backgroundColor = Color.Transparent))
        {
            Text(text = "Start", fontSize = 16.sp)
        }
    }

    /*@Preview(showBackground = true)
    @Composable
    fun DefaultPreview() {
        Main("MIQUOD APP Android", scalePreview)
    }*/
}
