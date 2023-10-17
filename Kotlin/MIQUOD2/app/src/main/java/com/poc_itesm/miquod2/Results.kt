package com.poc_itesm.miquod2

import android.net.Uri
import android.os.Parcelable
import kotlinx.parcelize.Parcelize


@Parcelize
data class Results(val data: MutableMap<String, MutableList<MutableMap<String, String>>>) : Parcelable {

}

@Parcelize
data class Paths (val dataPath: String) : Parcelable {

}

@Parcelize
data class UriImg (val dataUri: Uri) : Parcelable {

}
