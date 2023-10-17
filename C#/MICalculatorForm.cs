using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using AForge;
using AForge.Imaging;
using AForge.Imaging.ComplexFilters;
using AForge.Imaging.ColorReduction;
using AForge.Imaging.Filters;
using System.Drawing.Imaging;
using AForge.Video.FFMPEG;
using AForge.Video;
using AForge.Video.DirectShow;
using System.IO;
using AForge.Math.Geometry;
using System.Drawing.Drawing2D;
//Excel library
using Excel = Microsoft.Office.Interop.Excel;
//Chart Libraries
using System.Threading;
using System.Diagnostics;
//Save User Settings
using AForgeImageProcessing.Properties;
//Remove ambiguousness between AForge.Image and System.Drawing.Image
using Point = System.Drawing.Point; //Libraries used
//Plot library
using System.Windows.Forms.DataVisualization.Charting;



namespace AForgeImageProcessing
{
    public partial class Form2 : Form
    {
        public Form2()
        {
            InitializeComponent();
            pictureBox1.Controls.Add(pictureBox2);
            pictureBox2.Dock = DockStyle.Fill;
            pictureBox2.Location = new System.Drawing.Point(0, 0);
            pictureBox2.BackColor = Color.Transparent;

        }

        #region Define type of variables

        public class Coordinate
        {
            public double X { get; set; }
            public double Y { get; set; }
        }

        public class Transect
        {
            public int TargetArea { get; set; }
            public Rectangle Rect { get; set; }
            public int MeanSpacingOfPart { get; set; }
        }

        #endregion

        #region General variables

            #region Defining/Erasing target areas
        //Variables to define target areas
        int selectX;
        int selectY;
        int selectWidth;
        int selectHeight;
        public Pen selectPen;
        //This variable control when you start drawing target area
        bool start = false;
        bool ReadMouseClick = false;
        bool ErasingTrgt = false;
        bool DefineInletProcess = false;
        public static bool calibration = false;
        #endregion

            #region  Loaded image arrays, target areas and information
        Bitmap[] ImagetoProcess = new Bitmap[0];
        public static List<string[]> LoadedImageInfo = new List<string[]>();
        //string[,] LoadedImagesInfo = new string[100, 3]; //[,0]file name; [,1]file type; [,2]loaded file ubication (C:\...)
        public static int[] calibimgarray = new int[0];//Stores the position of the calibration image in the ImagetoProcess array
        public static List<List<Rectangle>> storeTargetAreas = new List<List<Rectangle>>();//[#of picture,#of target area]=>rectangle dimensions
        public static List<List<int>> inletTrgts = new List<List<int>>();//[#of picture]=> Target areas defined as inlets
        #endregion

        #region Calculated Mixing Dimensions (Concentration)

        Bitmap[] ImagetoProcess2;
        List<List<Rectangle>> storeTargetAreas2 = new List<List<Rectangle>>();//[#of picture,#of target area]=>rectangle dimensions
        List<string[]> LoadedImageInfo2 = new List<string[]>();
        List<List<double[,]>> storeConcentrationData = new List<List<double[,]>>();//[#of picture,#of target area]=>normalized concentration array
        List<List<double[]>> IntensityMeasures = new List<List<double[]>>();//[#of picture,#of target area]=> {σ, CoV, M, Cm, Cmax, Cmin, N}
        List<List<double[]>> HorizontalVariograms = new List<List<double[]>>();//[#of picture,#of target area]=> Horizontal Variogram
        List<List<double[]>> VerticalVariograms = new List<List<double[]>>();//[#of picture,#of target area]=> Vertical Variogram
        List<List<Coordinate>> MeanLengthScales = new List<List<Coordinate>>();//[#of picture,#of target area].X=> Horizontal mean length scale; [#of picture,#of target area].Y=> Vertical mean length scale
        List<List<double>> ExposureIndexes = new List<List<double>>();//[#of picture,#of target area]=> Exposure

        #endregion

            #region Particle tracking variables
        Bitmap Image1;
        List<int> ThresValueNum = new List<int>();
        List<List<Rectangle[]>> storeBlobRectangles = new List<List<Rectangle[]>>();
        List<List<Point[]>> storePartPositions = new List<List<Point[]>>();
        bool MaxStrTrgtSel = false;
        bool MaxStrTransSel = false;
        int MeanSpacing; // Mean spacing between particles in a target area
        int TrgtNum; // Target area to define transect
        Rectangle Transrect = new Rectangle();
        List<List<Rectangle>> DefinedTransects = new List<List<Rectangle>>();//List to store predefined transects
        List<List<int>> MeanSpacingParticles = new List<List<int>>();
        List<List<int>> MaximumStriationThickness = new List<List<int>>();
        #endregion

        #region Calculated Mixing dimensions (Particles)

        List<List<double[,]>> storeConcParticleData = new List<List<double[,]>>();//[#of picture,#of target area]=>Particle concentration array
        List<List<int>> storeMaxStrThickness = new List<List<int>>();//[#of picture,#of target area]=>Maximum Striation Thickness
        List<List<double[]>> PNNDistribution = new List<List<double[]>>();//[#of picture,#of target area]=>PNN Distribution
        List<List<double[]>> ScaleSegregationIndexes = new List<List<double[]>>();//[#of picture,#of target area]=> {σfpp, Idisp, Xg}
        #endregion

        //Move target
        int MoveTrgt = -1;
        bool startMove = false;
        int IniX = 0;
        int IniY = 0;

        //Define Form 1
        Form1 frm = new Form1();

        //Zoom image in and out
        bool insidepicturebox = false;

        //pictureBox2 events
        int Xposition; int Yposition;

        #endregion
       
        #region Form Events

        private void Form2_Load(object sender, EventArgs e)
        {
            //Show only the tabs necessary to begin---------------------------------------------------------
            RemoveTabs();
            ConcentImgMenu.AutoScroll = true; //Show scrolls in tabs
            ParticleImgMenu.AutoScroll = true; //Show scrolls in tabs
            TrgtAreaMixDimTab.AutoScroll = true;
            PartMixDimTab.AutoScroll = true;
            MixindDataPlotsTab.AutoScroll = true;
            MixPlotsPartData.AutoScroll = true;

            #region FormUserDefineProperties
            this.Width = Settings.Default.FormWidth;
            this.Height = Settings.Default.FormHeight;
            this.Location = new Point(Settings.Default.FormPositionX, Settings.Default.FormPositionY);
            #endregion

        }

        private void Form2_FormClosing(object sender, FormClosingEventArgs e)
        {
            StopRunningVideoOrCamera();
            Properties.Settings.Default.Save();
        }

        private void Form2_ResizeEnd(object sender, EventArgs e)
        {
            Settings.Default.FormWidth = this.Width;
            Settings.Default.FormHeight = this.Height;
            Settings.Default.FormPositionX = this.Location.X;
            Settings.Default.FormPositionY = this.Location.Y;
        }

        #endregion

        #region Menu Buttons
        
        private void loadImageToolStripMenuItem_Click(object sender, EventArgs e)
        {
            StopRunningVideoOrCamera();
            
            //Open Dialog box to load image.....................................................
            OpenFileDialog fdl = new OpenFileDialog();
            fdl.Filter = "All Graphics Types|*.bmp;*.jpg;*.jpeg;*.png;*.tif;*.tiff|"
                        + "BMP|*.bmp|GIF|*.gif|JPG|*.jpg;*.jpeg|PNG|*.png|TIFF|*.tif;*.tiff";
            //fdl.InitialDirectory = @"C:\";
            fdl.Title = "Please select an image file";
            //..................................................................................

            if (fdl.ShowDialog().Equals(DialogResult.OK))
            {
                int numofimg = ImagetoProcess.Length; // Evaluate the number of images stored 
                //(when ImagetoProcess.Length=0 the first image is going to be stored in position 0)

                //Initializate Lists
                storeTargetAreas.Add(new List<Rectangle>()); //Initializates Rectangle List for the new Image
                inletTrgts.Add(new List<int>()); //Initializates inlet list for the new Image    
                ThresValueNum.Add(300); //Defines a Threshold for each new Image.
                storeBlobRectangles.Add(new List<Rectangle[]>());// Defines Blobrectangle Lists
                storePartPositions.Add(new List<Point[]>()); //Defines particle positions list
                DefinedTransects.Add(new List<Rectangle>());//List to store predefined transects
                MeanSpacingParticles.Add(new List<int>());
                MaximumStriationThickness.Add(new List<int>());

                //Store and Show Loaded Image---------------------------------------------------------------------
                Array.Resize(ref ImagetoProcess, ImagetoProcess.Length + 1);//Adds one more space into the image array
                ImagetoProcess[numofimg] = (Bitmap)System.Drawing.Image.FromFile(fdl.FileName);

                //Store Loaded Image Information------------------------------------------------------------------
                //Image file name, Image file extension (*.jpg), Image file last loaded ubication, Image Pixel Format
                string[] Info = { Path.GetFileName(fdl.FileName), Path.GetExtension(fdl.FileName),
                                    fdl.FileName, ImagetoProcess[numofimg].PixelFormat.ToString()};
                LoadedImageInfo.Add(Info);

                //Shows a new tab with the stored image
                CreateNewImageTab(numofimg);
                //If there is no image loaded creates a new Tab??????????????????????????
                if (numofimg == 0){ WorkingWithTab(); }

                UpdateInformation(numofimg);
                
            }

            
        } //Load an image

        //Load a video:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        private void loadVideoToolStripMenuItem_Click(object sender, EventArgs e)
        {
            OpenFileDialog fdl = new OpenFileDialog();
            fdl.Filter = "Video files |*.wmv; *.3g2; *.3gp; *.3gp2; *.3gpp; *.amv; *.asf;  *.avi; " + 
                "*.bin; *.cue; *.divx; *.dv; *.flv; *.gxf; *.iso; *.m1v; *.m2v; *.m2t; *.m2ts; *.m4v; " +
                " *.mkv; *.mov; *.mp2; *.mp2v; *.mp4; *.mpa; *.mpe; *.mpeg; *.mpeg1; *.mpeg2; " + 
                "*.mpeg4; *.mpg; *.mpv2; *.mts; *.nsv; *.nuv; *.ogg; *.ogm; *.ogv; *.ogx; *.ps; *.rec; " +
                "*.rm; *.rmvb; *.tod; *.ts; *.tts; *.vob; *.vro; *.webm; *.dat; ";
            fdl.Title = "Please select a video file";

            if (fdl.ShowDialog().Equals(DialogResult.OK))
            {
                /*
                VideoFileReader vdofile = new VideoFileReader();
                VideoFile = new FileVideoSource(fdl.FileName);
                VideoFile.NewFrame += VideoFile_NewFrame; ;
                VideoFile.Start();

                //Read the video file properties
                vdofile.Open(fdl.FileName);
                varframerate = vdofile.FrameRate;
                
                totalnumframe = vdofile.FrameCount;
                //Shows the first frame before playing to let the user now the video is loaded
                pictureBox1.Image = vdofile.ReadVideoFrame();
                //Defines an array to store the data analized
                MixIndArray = new double[totalnumframe];

                // check some of its attributes
                //MessageBox.Show("width:  " + vdofile.Width + "height: " + vdofile.Height + "fps:    " + vdofile.FrameRate
                //    + "codec:  " + vdofile.CodecName + "number of frames " + vdofile.FrameCount);
                vdofile.Close();*/

            }
        }

        private void VideoFile_NewFrame(object sender, NewFrameEventArgs eventArgs)
        {
           
        }
        #endregion

        #region Buttons

            #region Concentration data
        //Second Step butttons---------------------------------------------------------------------
        private void ImgButton_Click(object sender, EventArgs e)
        {
            loadImageToolStripMenuItem.PerformClick();  
        }

        private void LoadCalibrationImages_Click(object sender, EventArgs e)
        {
            //Set the Image as a calibration image----------------------------------------------------------
            int i = calibimgarray.Length;
            int index = tabControl3.SelectedIndex;
            bool found = false;
            if (index > -1)
            {
                for (int j = 0; j < i; j++) {
                if (calibimgarray[j] == index) { found = true; }
                }
                if (found) {
                    MessageBox.Show("Image already defined as reference");
                }
                else
                {
                    Array.Resize(ref calibimgarray, calibimgarray.Length + 1);
                    calibimgarray[i] = index;
                    tabControl3.TabPages[index].Text = LoadedImageInfo[index][0] + " (Ref)" + "         "; 
                }
                UpdateInformation(index);
            }
            
        }

        //Third Step buttons----------------------------------------------------------------------
        private void TgtAreaButton_Click(object sender, EventArgs e)
        {
            if (ErasingTrgt) { ErasingTrgt = false; }//Cancels the process of defining new target area
            if (DefineInletProcess) { DefineInletProcess = false; }//Cancels the process of setting inlets
            if (MaxStrTransSel) { MaxStrTransSel = false; } // Cancels Transect deffinition
            if (MaxStrTrgtSel) { MaxStrTrgtSel = false; } //Cancels Transect deffinition

            if (ImagetoProcess.Length>0 && !start) { 
            //Changes the cursor to a Cross
            Cursor = Cursors.Cross;
            ReadMouseClick = true;
            }
        } //Create a new target to evaluate in the loaded image

        private void DefineInletButton_Click(object sender, EventArgs e)
        {

            int index = tabControl3.SelectedIndex;
            if (index > -1)
            {
                if (storeTargetAreas[index].Count > 0)
                {
                    if (ReadMouseClick) { ReadMouseClick = false; }//Cancels the process of defining new target area
                    if (ErasingTrgt) { ErasingTrgt = false; }//Cancels the process of erasing targets
                    if (MaxStrTransSel) { MaxStrTransSel = false; } // Cancels Transect deffinition
                    if (MaxStrTrgtSel) { MaxStrTrgtSel = false; } //Cancels Transect deffinition

                    MessageBox.Show("Select the target to define as inlet");
                    Cursor = Cursors.Hand;
                    DefineInletProcess = true;
                }
            }
        }

        private void ErsButton_Click(object sender, EventArgs e)
        {
            if (ReadMouseClick) { ReadMouseClick = false; }//Cancels the process of defining new target area
            if (DefineInletProcess) { DefineInletProcess = false; }//Cancels the process of setting inlets
            if (MaxStrTransSel) { MaxStrTransSel = false; } // Cancels Transect deffinition
            if (MaxStrTrgtSel) { MaxStrTrgtSel = false; } //Cancels Transect deffinition

            int index = tabControl3.SelectedIndex;
            if (index > -1) { 
                if (storeTargetAreas[index].Count > 0)
                {
                    MessageBox.Show("Select the target to erase");
                    Cursor = Cursors.Hand;
                    ErasingTrgt = true;
                }
            }

        }

        private void CotourColorbutton_Click(object sender, EventArgs e)
        {
            ColorDialog colorDialog1 = new ColorDialog();
            // Keeps the user from selecting a custom color.
            // colorDialog1.AllowFullOpen = false;
            // Allows the user to get help. (The default is false.)
            colorDialog1.ShowHelp = true;
            // Sets the initial color select to the current text color.
            colorDialog1.Color = ContourColorbutton.BackColor;
            if (colorDialog1.ShowDialog() == DialogResult.OK)
            {
                ContourColorbutton.BackColor = colorDialog1.Color;
                ContourColorbutton2.BackColor = colorDialog1.Color;
            }
            if (tabControl3.SelectedIndex >= 0) { pictureBox2.Refresh(); DrawRectangles(tabControl3.SelectedIndex); }
        }

        private void NumColorbutton_Click(object sender, EventArgs e)
        {
            FontDialog fontDialog1 = new FontDialog();
            fontDialog1.Font = TrgtAreaNumlabel.Font;
            fontDialog1.ShowColor = true;
            fontDialog1.MaxSize = 12;
            fontDialog1.ShowHelp = true;
            fontDialog1.Color = NumColorbutton.BackColor;
            if (fontDialog1.ShowDialog() == DialogResult.OK)
            {
                TrgtAreaNumlabel.Font = fontDialog1.Font;
                NumColorbutton.BackColor = fontDialog1.Color;
                Trgtarealabel2.Font = fontDialog1.Font;
                NumColorbutton2.BackColor = fontDialog1.Color;
            }
            if (tabControl3.SelectedIndex >= 0) { pictureBox2.Refresh(); DrawRectangles(tabControl3.SelectedIndex); }
        }

        private void CopyTargetsButton_Click(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            int imgtocopy = ImgTrgtCombobox.SelectedIndex;

            if (storeTargetAreas.Count > 1 && imgtocopy!=index && imgtocopy > -1 &&
                MessageBox.Show("Would you like to copy the targets from image:"+ "\n"+ 
                    LoadedImageInfo[imgtocopy][0].ToString() + "?", "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
            {
                if (ImagetoProcess[imgtocopy].Width <= ImagetoProcess[index].Width &&
                    ImagetoProcess[imgtocopy].Height <= ImagetoProcess[index].Height)
                {
                    for (int i = 0; i < storeTargetAreas[index].Count; i++)
                    {
                        storeTargetAreas[index].RemoveAt(i);
                    }
                    for (int i = 0; i < storeTargetAreas[imgtocopy].Count; i++)
                    {
                        storeTargetAreas[index].Add(storeTargetAreas[imgtocopy][i]);
                    }

                    //Evaluate if there are inlets
                    Form1.MisTrgts = 1;
                    Form1.AssignedInletsList.Clear();
                    EvaluateIfThereAreInletsDefined();
                    
                }
                else { MessageBox.Show("The image to copy from must be of the same or lower in size"); }

                //storeTargetAreas.RemoveAt(index); //Erase
             UpdateInformation(index);
            }
            


        }

        private void AssignInletButton_Click(object sender, EventArgs e)
        {
            //Find if there are inlets defined
            int i = 0;
            foreach (var list in inletTrgts)
            {
                foreach (var item in list)
                {
                    i = i + 1;
                }
            }

            if (i > 0)
            {
                calibration = false;
                frm.ShowDialog();
                //Evaluate if there are inlets
                EvaluateIfThereAreInletsDefined();
            }
            else { MessageBox.Show("There are no inlet targets defined"); }

        }

        private void StartCalibButton_Click(object sender, EventArgs e)
        {
            int test = LoadedImageInfo.Count - calibimgarray.Length;
            if (calibimgarray.Length > 0 && test > 0)
            {
                calibration = true;
                frm.ShowDialog();
                CheckAssignedRefImgs();
            }
            else
            {
                if (test == 0)
                    MessageBox.Show("There are no images to be calibrated");

                if (calibimgarray.Length == 0)
                    MessageBox.Show("There are no reference images");
            }

        }

        private void ComputeButton_Click(object sender, EventArgs e)
        {
            int numImages = ImagetoProcess.Length;
            if (numImages> 0 && numImages>calibimgarray.Length)
            {
                bool cnd = false;
                for (int i = 0; i < numImages; i++)
                {
                    if (storeTargetAreas[i].Count > 0) { cnd = true; }
                }
                if (cnd)
                {
                    //DETERMINE IF CALIBRATION PROCESS WILL BE PERFORMED
                    bool calibperformed = true;
                    bool cond1 = true;
                    bool cond2 = true;

                    int ImgsInCalib = 0;
                    foreach (var item in Form1.ImageswithReferences)
                    {
                        if (item.Count == 1) { calibperformed = false; }
                        if (item.Count > 1) { ImgsInCalib = ImgsInCalib + item.Count + 1; }
                    }
                    if (calibimgarray.Length > 0 && !calibperformed)
                    {
                        if (MessageBox.Show("One of the images to be calibrated have less than 2 reference images" + "\n" +
                            "Calibration will not be performed, Do you want to contiinue?",
                            "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.No) { cond1 = false; }
                    }
                    if (ImgsInCalib < LoadedImageInfo.Count && ImgsInCalib > 0)
                    {
                        calibperformed = false;
                        if (MessageBox.Show("One of the images to perform the calibration have not been assigned" + "\n" +
                            "Calibration will not be performed, Do you want to contiinue?",
                            "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.No) { cond2 = false; }
                    }



                    if (cond1 && cond2)
                    {   
                        //Show "Mixing Measures Tab" and Fills Dimensions------------------------------------------
                        if (!tabControl1.TabPages.Contains(TrgtAreaMixDimTab))
                        { tabControl1.TabPages.Insert(0, TrgtAreaMixDimTab); }

                        //Show "Mixing Dta Plots Tab" -------------------------------------------------------------
                        if (tabControl1.TabPages.Contains(MixindDataPlotsTab) == false) //Evaluates if tab was already shown
                        { tabControl1.TabPages.Insert(1, MixindDataPlotsTab); }

                        //Hide "Particle Mixing Dimensions Tab if showed--------------------------------------------------
                        if (tabControl1.TabPages.Contains(PartMixDimTab)) //Evaluates if tab was already shown
                        { tabControl1.TabPages.Remove(PartMixDimTab); }

                        //Hide "Mixind Plots for Particle Data"-----------------------------------------------------------
                        if (tabControl1.TabPages.Contains(MixPlotsPartData)) //Evaluates if tab was already shown
                        { tabControl1.TabPages.Remove(MixPlotsPartData); }
                        
                        CalculateMixingDimConcentrationdata(); //Calculate Concentration data mixing dimensions
                        FillImgCombobox3();
                        ImgTrgtCombobox3.SelectedIndex = 0;
                        ImgTrgtCombobox4.SelectedIndex = 0;
                        tabControl1.SelectedIndex = 0;
                    }
                    
                }
                else { MessageBox.Show("No targets have been defined"); }

            }
            else { MessageBox.Show("There are no loaded images to be assessed"); }
            
        }

        #endregion

            #region Particle data

        private void ContourColorbutton2_Click(object sender, EventArgs e)
        {
            ContourColorbutton.PerformClick();
        }

        private void NumColorbutton2_Click(object sender, EventArgs e)
        {
            NumColorbutton.PerformClick();
        }

        private void ImgButton2_Click(object sender, EventArgs e)
        {
            ImgButton.PerformClick();
        }

        private void DefineTrgtsButton_Click(object sender, EventArgs e)
        {
            TgtAreaButton.PerformClick();
        }

        private void SetInletsButton_Click(object sender, EventArgs e)
        {
            DefineInletButton.PerformClick();
        }

        private void CopyTrgtsPButton_Click(object sender, EventArgs e)
        {
            CopyTargetsButton.PerformClick();
        }

        private void ErsButton2_Click(object sender, EventArgs e)
        {
            ErsButton.PerformClick();
        }

        private void AssignInletButton2_Click(object sender, EventArgs e)
        {
            AssignInletButton.PerformClick();
        }

        #endregion

        //OTHER STEPS----------------------------------
        
        #endregion

        #region PictureBox2 mouse Events    

        private void pictureBox2_MouseEnter(object sender, EventArgs e)
        {
            insidepicturebox = true;
        }

        private void pictureBox2_MouseLeave(object sender, EventArgs e)
        {
            insidepicturebox = false;
            CoordinateLabel.Text = "Position: (   x   ,   y   )";
        }

        private void pictureBox2_MouseDown(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left && ReadMouseClick && VerifyTrgtAreaSelection(e.X, e.Y))
            {
                //starts coordinates for rectangle
                selectX = Xposition;
                selectY = Yposition;
                selectPen = new Pen(ContourColorbutton.BackColor, 1);
                selectPen.DashStyle = DashStyle.DashDotDot;
                start = true;
            }
            if (MoveTrgt > -1 && !ReadMouseClick && !ErasingTrgt && !DefineInletProcess && !MaxStrTrgtSel && !MaxStrTransSel)
            {
                startMove = true;
                IniX = Xposition;
                IniY = Yposition;
            }


        }

        private void pictureBox2_MouseMove(object sender, MouseEventArgs e)
        {
            #region Show image coordinate
            //Show image coordinate while moving the cursor pver the pictureBox--------------------
            Xposition = e.X;
            Yposition = e.Y;

            if (VerifyTrgtAreaSelection(e.X, e.Y))
            {
                double[] factors = ConversionFactors(tabControl3.SelectedIndex);
                Xposition = (int)((Xposition - factors[0]) * factors[2]);
                Yposition = (int)((Yposition - factors[1]) * factors[2]);
                CoordinateLabel.Text = "Position: ( " + Xposition + " , " + Yposition + " )";
                int R = ImagetoProcess[tabControl3.SelectedIndex].GetPixel(Xposition, Yposition).R;
                int G = ImagetoProcess[tabControl3.SelectedIndex].GetPixel(Xposition, Yposition).G;
                int B = ImagetoProcess[tabControl3.SelectedIndex].GetPixel(Xposition, Yposition).B;

                PixIntenLabel.Text = "Intensity: " + ((int)(0.2125 * R + 0.7154 * G + 0.0721 * B)).ToString(); 
            }
            else { CoordinateLabel.Text = "Position: (   x   ,   y   )"; PixIntenLabel.Text = "Intensity:"; }

            #endregion

            #region Define new target
            //validate if right-click was trigger and if the Define target button was pressed------
            if (ReadMouseClick && start)
            {
                //refresh picture box
                pictureBox2.Refresh();
                //set corner square to mouse coordinates
                selectWidth = Xposition - selectX; //selectX is the Left position of the square
                selectHeight = Yposition - selectY; //selectY is the Top position of the square
                //show Image dimensions
                DimAreaTextBox.Text = (selectWidth.ToString() + "x" + selectHeight.ToString());
                //The rectangles are converted to picturebox2 size
                double[] factors = ConversionFactors(tabControl3.SelectedIndex);
                int X = (int)((selectX / factors[2]) + factors[0]);
                int Y = (int)((selectY / factors[2]) + factors[1]);
                int width = (int)(selectWidth / factors[2]);
                int height = (int)(selectHeight / factors[2]);

                Rectangle modfarea = new Rectangle(X, Y, width, height);

                //draw rectangle
                pictureBox2.CreateGraphics().DrawRectangle(selectPen, modfarea);
            }
            #endregion

            #region Define Transect
            if (MaxStrTransSel && VerifyTrgtAreaSelection(e.X, e.Y))
            {
                int index = tabControl3.SelectedIndex;
                int trgt = TrgtNum;
                Rectangle DrawTrans = new Rectangle();

                //refresh picture box
                RefreshPictureBox2();

                //show Image dimensions
                double[] factors = ConversionFactors(tabControl3.SelectedIndex);

                int width = 0;
                int height = 0;
                int Xtrans = 0;
                int Ytrans = 0;

                #region Horizontal Transect
                if (HorizontalCheckBox.Checked)
                {
                    width = storeTargetAreas[index][trgt].Width;
                    height = MeanSpacing;
                    int Y = Yposition;
                    int Ymin = storeTargetAreas[index][trgt].Y;
                    int Ymax = Ymin + storeTargetAreas[index][trgt].Height - 1;

                    if (Y < (Ymin + MeanSpacing / 2)){ Ytrans = Ymin; }
                    else
                    {
                        if (Y > (Ymax - MeanSpacing / 2)){ Ytrans = Ymax - MeanSpacing; }
                        else { Ytrans = Y - MeanSpacing/2; }
                    }
                    Xtrans = storeTargetAreas[index][trgt].X;
                }
                #endregion

                #region Vertical Transect
                if (VerticalCheckBox.Checked)
                {
                    width = MeanSpacing;
                    height = height = storeTargetAreas[index][trgt].Height;
                    int X = Xposition;
                    int Xmin = storeTargetAreas[index][trgt].X;
                    int Xmax = Xmin + storeTargetAreas[index][trgt].Width- 1;

                    if (X < (Xmin + MeanSpacing / 2)){ Xtrans = Xmin; }
                    else
                    {
                        if (X > (Xmax - MeanSpacing / 2)){ Xtrans = Xmax - MeanSpacing; }
                        else { Xtrans = X - MeanSpacing / 2; }
                    }
                    Ytrans = storeTargetAreas[index][trgt].Y;
                }
                #endregion
                
                //Define the transect rectangle to save
                Transrect = new Rectangle(Xtrans, Ytrans, width, height);

                //Define the transect rectangle to plot
                Ytrans = (int)((Ytrans / factors[2]) + factors[1]);
                Xtrans = (int)((Xtrans / factors[2]) + factors[0]);
                width = (int)(width / factors[2]);
                height = (int)(height / factors[2]);
                DrawTrans = new Rectangle(Xtrans, Ytrans, width, height);

                //Draw Transect within the selected target
                SolidBrush semiTransBrush = new SolidBrush(ContourColorbutton2.BackColor);                
                using (Graphics g = pictureBox2.CreateGraphics())
                {
                    g.FillRectangle(Brushes.Lime, DrawTrans);
                    g.CompositingMode = CompositingMode.SourceCopy;
                    g.FillRectangle(semiTransBrush, DrawTrans); 
                }
                
            }
            #endregion

            #region Move Targets
            
            if (!ReadMouseClick && !ErasingTrgt && !DefineInletProcess && !MaxStrTrgtSel && !MaxStrTransSel)
            {
                int index = tabControl3.SelectedIndex;

                if (VerifyTrgtAreaSelection(e.X, e.Y) && !startMove)
                {
                    int i = FindSelectedTargetArea();
                    if (i > -1) { Cursor = Cursors.Hand; MoveTrgt = i; }
                    else { Cursor = Cursors.Arrow; MoveTrgt = -1; }
                }

                if (startMove)
                {
                    //refresh picture box
                    pictureBox2.Refresh();
                    //set corner square to mouse coordinates
                    //The rectangles are converted to picturebox2 size
                    double[] factors = ConversionFactors(tabControl3.SelectedIndex);
                    int width = (int) (storeTargetAreas[index][MoveTrgt].Width/ factors[2]);
                    int height = (int)(storeTargetAreas[index][MoveTrgt].Height / factors[2]);

                    int TrgtX = storeTargetAreas[index][MoveTrgt].X + (Xposition-IniX);
                    int TrgtY = storeTargetAreas[index][MoveTrgt].Y + (Yposition - IniY);

                    if (TrgtX < 0) { TrgtX = 0; }
                    if (TrgtX + storeTargetAreas[index][MoveTrgt].Width > ImagetoProcess[index].Width)
                    { TrgtX = ImagetoProcess[index].Width - storeTargetAreas[index][MoveTrgt].Width - 1; }
                    if (TrgtY < 0) { TrgtY = 0; }
                    if (TrgtY + storeTargetAreas[index][MoveTrgt].Height > ImagetoProcess[index].Height)
                    { TrgtX = ImagetoProcess[index].Height - storeTargetAreas[index][MoveTrgt].Height - 1; }


                    int X = (int)((TrgtX / factors[2]) + factors[0]);
                    int Y = (int)((TrgtY / factors[2]) + factors[1]);

                    Rectangle modfarea = new Rectangle(X, Y, width, height);

                    //draw rectangle
                    pictureBox2.CreateGraphics().DrawRectangle(selectPen, modfarea);
                }
            }
            #endregion


        }

        private void pictureBox2_MouseUp(object sender, MouseEventArgs e)
        {
            #region Defining target areas
            bool cond=false;
            int index = tabControl3.SelectedIndex; //Define which is the picture being evaluated

            //Evaluated if the target area selected is at least 1x1 pixels
            if ((Xposition - selectX) > 1 && (Yposition - selectY) > 1)
            { cond = true; }

            if (ReadMouseClick && start && VerifyTrgtAreaSelection(e.X, e.Y) && cond)
            {
                pictureBox2.Refresh();
                //Store Target Areas dimensions
                int NumTrgtArea = storeTargetAreas[index].Count();
                int X = selectX;
                int Y = selectY;
                int width = Xposition - X + 1;
                int height = Yposition - Y + 1;
                //Store rectangle in Image coordinates ([#of picture,#of target area]=>rectangle dimensions)
                Rectangle Area = new Rectangle(X, Y, width, height);
                storeTargetAreas[index].Add(Area);
                //storeTargetAreas[0][1]; //Retrieve value at index 1 from sub List at index 0
                
                UpdateInformation(index);//Shows all the necesary info in the form

                //Evaluate if there are inlets
                Form1.MisTrgts = 1;
                EvaluateIfThereAreInletsDefined();
                
                //Delete Assigned reference Image List-----------------------------------------------------
                Form1.ImageswithReferences.Clear();

            }
            else { pictureBox2.Refresh(); }
            if(!ErasingTrgt && !DefineInletProcess)
            {
                //Other functions to perform
                start = false;//Tells the program the selection is finished
                Cursor = Cursors.Arrow;//Restablishes the arrow cursor
                ReadMouseClick = false;
                DrawRectangles(index);//Draw the target areas in picturebox2
            }
            
            #endregion

            #region Erasing Targets
            int i = FindSelectedTargetArea();
            if (VerifyTrgtAreaSelection(e.X, e.Y) && ErasingTrgt && i>-1)
            {
                
                if (MessageBox.Show("Would you like to erase target "+(i+1)+"?", "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes) {
                    //Remove last item in the array
                    storeTargetAreas[index].RemoveAt(i);//The list begins in 0
                    if (chkbox3P.Visible)
                    {
                        storeBlobRectangles[index].RemoveAt(i);
                        storePartPositions[index].RemoveAt(i);
                    }

                    EraseTransectInfo(i);//Delete transect predifined measure for the erased target
                    EraseInletTargets(i);

                    //Evaluate if there are inlets
                    Form1.MisTrgts = 1;
                    Form1.AssignedInletsList.Clear();
                    //Delete Assigned reference image list-----------------------------------------------------
                    Form1.ImageswithReferences.Clear();
                    EvaluateIfThereAreInletsDefined();
                }
                UpdateInformation(index);
                Cursor = Cursors.Arrow;
                ErasingTrgt = false; //Lets the software knows that the user is finished erasing a target
                
            }
            #endregion

            #region Defining Inlet Targets
            i = FindSelectedTargetArea();
            if (VerifyTrgtAreaSelection(e.X, e.Y) && DefineInletProcess && i>-1)
            {
                //Find if the selected target is an inlet
                bool newinlettarget=true;
                foreach (var target in inletTrgts[index])
                {
                    if (target == i) { newinlettarget = false; }
                }

                if (!newinlettarget) { MessageBox.Show("El target " + (i+1) + " ya esta definido como inlet"); }

                if (newinlettarget && MessageBox.Show("Would you like to se target " + (i + 1) + " as inlet?", "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
                {
                    //Add item in the array
                    inletTrgts[index].Add(i);
                    //Evaluate if there are inlets
                    Form1.MisTrgts = 1;
                    EvaluateIfThereAreInletsDefined();
                }
                UpdateInformation(index);
                Cursor = Cursors.Arrow;
                DefineInletProcess = false; //Lets the software knows that the user is finished erasing a target
            }
            #endregion

            #region Store Transects and calculate Max Striation Thickness


            if (VerifyTrgtAreaSelection(e.X, e.Y) && MaxStrTransSel)
            {
                MaxStrTransSel = false;
                Cursor = Cursors.Arrow;
                if (DefinedTransects[index].Count - 1 < TrgtNum)
                {
                    for (i = DefinedTransects[index].Count; i <= TrgtNum; i++)
                    {
                        int a = 0;
                        DefinedTransects[index].Add(new Rectangle());
                        MeanSpacingParticles[index].Add(a);
                        MaximumStriationThickness[index].Add(a);
                    }
                }
                DefinedTransects[index][TrgtNum] = Transrect;
                MeanSpacingParticles[index][TrgtNum] = MeanSpacing;
                MaximumStriationThickness[index][TrgtNum] = CalculateMaxStrThickness(index, TrgtNum, MeanSpacing);
                if (MaximumStriationThickness[index][TrgtNum] == MeanSpacing)
                {
                    MessageBox.Show("No sufficient number of particles were found in the transect");
                }
                UpdateInformation(index);
                PartTrgtComboBox.SelectedIndex = TrgtNum;
            }

            #endregion

            #region CalculatingMeanSpacing

            i = FindSelectedTargetArea();
            if (VerifyTrgtAreaSelection(e.X, e.Y) && MaxStrTrgtSel && i > -1)
            {
                //Evaluate the number of Particles
                if (storePartPositions[index][i].Length > 2)
                {
                    MeanSpacing = CalculateMeanSpacing(index, i);
                    TrgtNum = i;
                    if (MeanSpacing < 3) { MeanSpacing = 3; }
                    MaxStrTransSel = true;
                    Cursor = Cursors.Cross;
                    MessageBox.Show("Define the transect position");
                    MaxStrTrgtSel = false;
                }
                else { MessageBox.Show("The calculation can not be performed (Only one particle detected)"); }
                                
                UpdateInformation(index);                
                MaxStrTrgtSel = false; //Lets the software knows that the user is finished erasing a target
            }
            else { Cursor = Cursors.Arrow; MaxStrTrgtSel = false;}

            #endregion

            #region Move Targets
            if (startMove && !ReadMouseClick && !ErasingTrgt && !DefineInletProcess && !MaxStrTrgtSel && !MaxStrTransSel)
            {
                //refresh picture box
                pictureBox2.Refresh();
                //set corner square to mouse coordinates
                //The rectangles are converted to picturebox2 size
                int width = storeTargetAreas[index][MoveTrgt].Width;
                int height = storeTargetAreas[index][MoveTrgt].Height;

                int TrgtX = storeTargetAreas[index][MoveTrgt].X + (Xposition - IniX);
                int TrgtY = storeTargetAreas[index][MoveTrgt].Y + (Yposition - IniY);

                if (TrgtX < 0) { TrgtX = 0; }
                if (TrgtX + storeTargetAreas[index][MoveTrgt].Width > ImagetoProcess[index].Width)
                { TrgtX = ImagetoProcess[index].Width - storeTargetAreas[index][MoveTrgt].Width - 1; }
                if (TrgtY < 0) { TrgtY = 0; }
                if (TrgtY + storeTargetAreas[index][MoveTrgt].Height > ImagetoProcess[index].Height)
                { TrgtX = ImagetoProcess[index].Height - storeTargetAreas[index][MoveTrgt].Height - 1; }


                Rectangle movearea = new Rectangle(TrgtX, TrgtY, width, height);
                storeTargetAreas[index][MoveTrgt] = movearea;
                DrawRectangles(index);
                startMove = false;
                Cursor = Cursors.Arrow;
                UpdateInformation(index);
            }

            #endregion

            RefreshPictureBox2();

        }

        #endregion

        #region Mixing quantification measures Particle data

        private void CalculateMixingDimpParticledata()
        {
            label32.Text = "6. Compute measures";
            GetConcentrationfromParticles();
            CalculateSegregationIntensityIndexfactorsParticles();
            CalculateMaximumStriationThickness();
            CalculatePNNMethodDistribution();
            CalculateScaleSegregationForParticles();

            label32.Text = "6. Compute measures (Done!)";

            MessageBox.Show("Calculation completed");

            //Fill Dimensions Combobox   
            FillDimensionsCombobox2();

        }

        /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        REDUCTION IN THE SEGREGATION OF CONCENTRATION
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

        private void CalculateSegregationIntensityIndexfactorsParticles()
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            CALCULATION OF SEGREGATION INTENSITY INDEX MEASURES
            Inputs: 
            ∙ Concentration matrix (Particles/Area in a Quadrat)

            Output: 
            ∙ Segregation Intensity Index factors = [σ, CoV, M, ...] = 
              [St. dev., Coeff. of Variance, Mixing Index, ...]
            ∙ Other Target factors = [...,Cm, Cmax, Cmin, N, NumOfParticles] 
              [..., Mean Concentration, Max. Conc. Value found, Min. Conc. Value found, Number of measured points, Number of particles ]

            Hector Betancourt Cervantes, 2017
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Define the  IntensityMeasures List
            if (IntensityMeasures.Count > 0) { IntensityMeasures.Clear(); }
            
            int i = 0;
            foreach (var List in storeConcParticleData)
            {
                IntensityMeasures.Add(new List<double[]>());
                int j = 0;
                foreach (var item in List)
                {
                    //Get number of particles and target area
                    int NumofPart = storePartPositions[i][j].Length;
                    int TrgtArea = storeTargetAreas[i][j].Width * storeTargetAreas[i][j].Height;
                    //Get mean and standard deviation of the previous matrix ----------------------------------------
                    double[] StatMeasure = StatisticalMeasuresParticles(item, TrgtArea, NumofPart);
                    double Cm = StatMeasure[0];
                    double StDev = StatMeasure[1];
                    double CoV = 0;
                    double M = 1;
                    if (StDev > 0)
                    {
                        CoV = StDev / Cm;
                        M = 1 - CoV;
                    }
                    double Cmax = StatMeasure[3];
                    double Cmin = StatMeasure[2];
                    double N = StatMeasure[4];

                    double[] IntMeasures = { StDev, CoV, M, Cm, Cmax, Cmin, N, NumofPart };
                    IntensityMeasures[i].Add(IntMeasures);
                    j++;
                }
                i++;
            }

            NormalizeCoV();
        } //Defines IntensityMeasures[image_index][Target number]={σ, CoV, M, Cm, Cmax, Cmin, N, NumPartciles}

        /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        REDUCTION IN THE SCALE OF CONCENTRATION
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

        private void CalculateMaximumStriationThickness()
        {
            if (storeMaxStrThickness.Count > 0) { storeMaxStrThickness.Clear(); }

            int i = 0;
            foreach (var list in MaximumStriationThickness)
            {
                storeMaxStrThickness.Add(new List<int>());
                foreach (var item in list)
                {
                    storeMaxStrThickness[i].Add(item);
                }
                i++;
            }
        }//Defines storeMaxStrThickness[image_index][Target number]=Max. Striation Thickness

        private void CalculatePNNMethodDistribution()
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            CALCULATION OF THE PNN METHOD
            Inputs: 
            ∙ Hexagonal grid 
            ∙ Particle positions

            Output: 
            ∙ PNN Distribution (Distance Xi distribution from Grid Point to closest particles

            Kukukova, 2011
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            if (PNNDistribution.Count > 0) { PNNDistribution.Clear(); }

            int i = 0;
            foreach (var list in storeTargetAreas)
            {
                PNNDistribution.Add(new List<double[]>());
                int j = 0;
                foreach (var item in list)
                {
                    //Define ideal particle postion points in an Hexagonal grid
                    int NumofPart = storePartPositions[i][j].Length;
                    Point[] HexagonalGrid = IdealParticlePosition(item, NumofPart);

                    double[] Xi = new double[HexagonalGrid.Length];

                    int k = 0;
                    foreach (var point in HexagonalGrid)
                    {
                        double s = Math.Pow(item.Width, 2) + Math.Pow(item.Height, 2);
                        Xi[k]= Math.Sqrt(s);
                        foreach (var pointeval in storePartPositions[i][j])
                        {
                            s = Math.Pow(point.X - pointeval.X, 2) + Math.Pow(point.Y - pointeval.Y, 2);
                            double dist = Math.Sqrt(s);
                            if (dist < Xi[k]) { Xi[k] = dist; }
                        }
                        k++;
                    }
                    PNNDistribution[i].Add(Xi);
                    j++;
                }
                i++;
            }
        }//Defines PNNDistribution[#of picture,#of target area]=>PNN Distribution

        private void CalculateScaleSegregationForParticles()
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            CALCULATION OF SCALE OF SEGREGATION MEASURES
            Inputs: 
            ∙ PNN Distribution
            ∙ Hexagonal grid dimensions


            Output: 
            ∙ Scale of Segregation factors = [σfpp, Idisp, Xg] 
              [Filtered point-particle deviation, Index of dispersion, Spatial resolution]
            Kukukova 2011, 2017
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
            if (ScaleSegregationIndexes.Count > 0) { ScaleSegregationIndexes.Clear(); }

            int i = 0;
            foreach (var list in storeTargetAreas)
            {
                ScaleSegregationIndexes.Add(new List<double[]>());
                int j = 0;
                foreach (var item in list)
                {
                    int K = (int) Math.Sqrt(storePartPositions[i][j].Length);
                    //Hexagonal Grid dimensions
                    int Dx = item.Width / K;
                    int Dy = item.Height / K;
                    
                    //Calculate Spatial Resolution (Xg)
                    double Xg = (double)(Dx + 2 * Math.Sqrt(Dx * Dx + Dy * Dy)) / 3;

                    //Define array of indexes
                    double[] ScaleDim = new double[3];

                    int m = PNNDistribution[i][j].Length;
                    double Xs = 0;
                    double Xr = Xg / 2; //Xr is equal to one-half of the spatial resolution
                    double Xi_mean = 0;
                    foreach (var Xi in PNNDistribution[i][j])
                    {
                        if (Xi >= Xr) { Xs = Xs + Math.Pow(Xi - Xr, 2);}
                        Xi_mean = Xi_mean + Xi;
                    }

                    Xi_mean = Xi_mean / m;
                    double Var_fpp =  Xs / (m - 1);
                    double Idisp = Var_fpp / Xi_mean;

                    ScaleDim[0] = Math.Sqrt(Var_fpp);// σfpp -> Filtered point-particle deviation
                    ScaleDim[1] = Idisp;//Idisp -> Index of dispersion
                    ScaleDim[2] = Xg;// Xg -> Spatial resolution

                    ScaleSegregationIndexes[i].Add(ScaleDim);
                    j++;
                }
                i++;
            }
        }

        #endregion

        #region Auxiliar functions for Particle tracking calculations

        private void GetConcentrationfromParticles()
        {
            //Copy Images, Images Info and Stored targets
            ImagetoProcess2 = ImagetoProcess;

            storeTargetAreas2.Clear();
            int f = 0;
            foreach (var list in storeTargetAreas)
            {
                storeTargetAreas2.Add(new List<Rectangle>());
                foreach (var item in list)
                {
                    storeTargetAreas2[f].Add(item);
                }
                f++;
            }

            LoadedImageInfo2.Clear();
            f = 0;
            foreach (var item in LoadedImageInfo)
            {
                LoadedImageInfo2.Add(item);
            }

            //Compute concetration matrix from particle distribution

            if (storeConcParticleData.Count > 0) { storeConcParticleData.Clear(); }

            for (int i = 0; i < storeTargetAreas.Count; i++)
            {
                storeConcParticleData.Add(new List<double[,]>());

                int j = 0;
                foreach (var item in storeTargetAreas[i])
                {
                    int MST = MaximumStriationThickness[i][j];
                    int width = item.Width;
                    int height = item.Height;

                    //Define the number of columns and rows in each target
                    int col = width / MST;
                    int distX = (width - col * MST)/2;
                    int row = height / MST;
                    int distY = (height-row*MST)/ 2;

                    double[,] Concentration = new double[col, row];

                    for (int n = 1; n <= row; n++)
                    {
                        int ycomp = storeTargetAreas[i][j].Y + distY;
                        int Ystart = ycomp + (n - 1) * MST - 1;
                        int Ylimit = ycomp + n * MST - 1;

                        for (int m = 1; m <= col; m++)
                        {
                            int xcomp = storeTargetAreas[i][j].X + distX;
                            int Xstart = xcomp + (m - 1) * MST - 1;
                            int Xlimit = xcomp + m * MST - 1;

                            int N = 0;
                            foreach (var part in storePartPositions[i][j])
                            {
                                int X = part.X;
                                int Y = part.Y;

                                if (X >= Xstart && X < Xlimit && Y >= Ystart && Y < Ylimit)
                                {
                                    N = N + 1;
                                }
                            }

                            int area = MST * MST;                                                       
                            Concentration[m - 1, n - 1] = (double) N / area;

                        }
                    }

                    storeConcParticleData[i].Add(Concentration);
                    j++;
                }
            }
        }

        public double[] StatisticalMeasuresParticles(double[,] data, int TargetArea, int NumofParticles)
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            COMPUTE STATISTICAL MEASURES
            Inputs: 
            ∙ Array 

            StatisticalArray=[μ,σ,Xmin,Xmax,N]=[Mean, Std. Dev., Min Value, Max Value, Number of Data] = [0,1,2,3,4]

            Output: 
            ∙ Statistical measures array
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Define variables------------------------------------------------------------------------------
            double mean = 0; double StDev = 0; double Xmax = 0; double Xmin = data[0, 0]; double N = 0;
            double[] StatMeasures = new double[5];

            //Calculate mean
            mean = (double) NumofParticles/TargetArea;

            //Find N, Xmax & Xmin and Compute Standard deviation--------------------------------------------------------------------
            for (int xc = 0; xc < data.GetLength(0); xc++)
            {
                for (int yc = 0; yc < data.GetLength(1); yc++)
                {
                    StDev = StDev + Math.Pow((data[xc, yc] - mean), 2);
                    if (Xmax < data[xc, yc]) { Xmax = data[xc, yc]; }
                    if (Xmin > data[xc, yc]) { Xmin = data[xc, yc]; }
                    N = N + 1;
                }
            }
            StDev = Math.Sqrt( StDev / N);
            StatMeasures[0] = mean;
            StatMeasures[1] = StDev;
            StatMeasures[2] = Xmin;
            StatMeasures[3] = Xmax;
            StatMeasures[4] = N;

            return StatMeasures;
        }

        public Point[] IdealParticlePosition(Rectangle TrgtArea, int NumofPart)
        {
            int k = (int)Math.Sqrt(NumofPart);

            int X = TrgtArea.X;
            int Y = TrgtArea.Y;
            int width = TrgtArea.Width;
            int height = TrgtArea.Height;

            int dist = 0;

            int distX = width / k;
            dist = (width - (int)Math.Ceiling((decimal)(distX - 1) / 2) - (k - 1) * distX) / 2;
            int iniX = X + (int)Math.Ceiling((decimal)dist);

            int distY = height /k;
            dist = (int)Math.Ceiling((decimal)((height - distY * k)/2));
            int iniY = Y + dist + (int)Math.Ceiling((decimal)distY/2);

            Point[] IdealPartPos = new Point[k*k];

            int i = 0;
            for (int n = 0; n < k; n++)
            {
                int Ypart = iniY + n * distY;
                for (int m = 0; m < k; m++)
                {
                    int Xpart = 0;
                    if (n % 2 == 0) { Xpart = iniX + m * distX; }
                    else { Xpart = (iniX + distX / 2) + (m * distX); }

                    IdealPartPos[i] = new Point(Xpart,Ypart);
                    i++;
                }
            }

            return IdealPartPos;
        }

        #endregion

        #region Mixing quatification measures Concentration data 

        private void CalculateMixingDimConcentrationdata()
        {
            label13.Text = "4. Compute measures";
            CalculateConcentrationMatrix();
            CalculateSegregationIntensityIndexfactors();
            CalculateHorizontalvariograms();
            CalculateVerticalvariograms();
            CalculateMeanLengthScales();
            CalculateExposureIndexes();
            
            MessageBox.Show("Calculation completed");
            label13.Text = "4. Compute measures (Done!)";

            //Evaluate is there are negative Mixing Index
            bool NeedforInlets = false;
            foreach (var list in IntensityMeasures)
            {
                foreach (var item in list)
                {
                    if (item[1] > 1)
                    {
                        NeedforInlets = true;
                    }
                }
            }
            if (NeedforInlets) { MessageBox.Show("There are negative Mixing Indexs (M < 0)" + "\n" + "\n" +
                "Please define the unmixed condition by defining the inlets"); }

            //Fill Dimensions Combobox   
            FillDimensionsCombobox();

        }

        private void CalculateConcentrationMatrix()
        {
            //Copy Images, Images Info and Stored targets
            ImagetoProcess2 = ImagetoProcess;

            storeTargetAreas2.Clear();
            int f = 0;
            foreach (var list in storeTargetAreas)
            {
                storeTargetAreas2.Add(new List<Rectangle>());
                foreach (var item in list)
                {
                    storeTargetAreas2[f].Add(item);
                }
                f++;
            }

            LoadedImageInfo2.Clear();
            f = 0;
            foreach (var item in LoadedImageInfo)
            {
                LoadedImageInfo2.Add(item);                
            }


            //Define the  storeConcentrationData List
            if (storeConcentrationData.Count > 0) { storeConcentrationData.Clear(); }

            for (int i = 0; i < ImagetoProcess.Length; i++)
            {
                storeConcentrationData.Add(new List<double[,]>());
            }
            

            //Determine if Images has to be calibrated
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            ->ALL THE REFERENCE AND ASSESSED IMAGES MUST BE ASSIGNED IN THE ImageswithReferences LIST 
            ->ALSO EACH IMAGE TO BE CALIBRATED HAS TO HAVE AT LEAST TWO REFERENCE IMAGES
            ->IF THERE ARE ONE IMAGE THAT HAS NOT BEING ASSIGNED IN THE ImageswithReferences LIST,
              THE CALIBRATION WILL NOT BE PERFORMED
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            bool calibperformed = true;
            int ImgsInCalib = 0;
            foreach (var item in Form1.ImageswithReferences)
            {
                if (item.Count == 1) { calibperformed = false; }
                if (item.Count > 1) { ImgsInCalib = ImgsInCalib + item.Count + 1; }
            }

            if (ImgsInCalib < LoadedImageInfo.Count) { calibperformed = false; }

            #region Performing Calibration
            // Calculate Concentrations using calibration data
            if (calibperformed)
            {
                //Determine what type of calibration is going to be performed (COMPLEX or SIMPLE)
                bool cond1 = true;
                int i = 0;
                foreach (var list in Form1.ImageswithReferences)
                {
                    foreach (var item in list)
                    {
                        int width = ImagetoProcess[i].Width;
                        int height = ImagetoProcess[i].Height;
                        int width2 = ImagetoProcess[item.ImageIndex].Width;
                        int height2 = ImagetoProcess[item.ImageIndex].Height;

                        if (width != width2 || height != height2) { cond1 = false; }//Images with different dimensions

                        for (int j = 0; j < storeTargetAreas[i].Count; j++)
                        {
                            int Trgtwidth = storeTargetAreas[i][j].Width;
                            int Trgtheight = storeTargetAreas[i][j].Height;
                            int Trgtwidth2 = storeTargetAreas[item.ImageIndex][j].Width;
                            int Trgtheight2 = storeTargetAreas[item.ImageIndex][j].Height;
                            if (Trgtwidth != Trgtwidth2 || Trgtheight != Trgtheight2) { cond1 = false; }
                        }
                    }
                    i = i + 1;
                }

                #region COMPLEX Calibration
                //Same Image Size and Same Target Sizes (COMPLEX CALIBRATION)
                if (cond1)
                {
                    for (int img = 0; img < ImagetoProcess.Length; img++)
                    {

                        if (Form1.ImageswithReferences[img].Count > 0)
                        {
                            //Image filtration
                            int index = i;
                            Bitmap FilteredImage = ImagetoProcess[img].Clone(new Rectangle(0, 0, ImagetoProcess[img].Width, ImagetoProcess[img].Height), PixelFormat.Format32bppRgb);

                            //Apply Mean Filter (to eliminate local noise)
                            Median medianfilter = new Median();
                            medianfilter.Size = 5;
                            FilteredImage = medianfilter.Apply(FilteredImage);
                            //Apply Grayscale filter
                            FilteredImage = new Grayscale(0.2125, 0.7154, 0.0721).Apply(FilteredImage);

                            //Define Array of Reference Images for the Image to be calibrated
                            Bitmap[] REFImg = new Bitmap[Form1.ImageswithReferences[img].Count];

                            for (int k = 0; k < Form1.ImageswithReferences[img].Count; k++)
                            {
                                int img_index = Form1.ImageswithReferences[img][k].ImageIndex;
                                Bitmap RefFilteredImage = ImagetoProcess[img_index].Clone(new Rectangle(0, 0, ImagetoProcess[img_index].Width, ImagetoProcess[img_index].Height), PixelFormat.Format32bppRgb);
                                //Apply median filter
                                medianfilter.Size = 5;
                                RefFilteredImage = medianfilter.Apply(RefFilteredImage);
                                //Apply Grayscale filter
                                RefFilteredImage = new Grayscale(0.2125, 0.7154, 0.0721).Apply(RefFilteredImage);
                                REFImg[k] = RefFilteredImage;
                            }

                            int numTrgts = storeTargetAreas[img].Count;
                            if (numTrgts > 0)
                            {
                                for (int j = 0; j < numTrgts; j++)
                                {
                                    //Array size
                                    int m = storeTargetAreas[img][j].Width;
                                    int n = storeTargetAreas[img][j].Height;
                                    double[,] ConcentrationArray = new double[m, n];

                                    //Target area square/rectangle dimension---------------------------------------------------------
                                    int xi = storeTargetAreas[img][j].X;
                                    int xf = xi + storeTargetAreas[img][j].Width - 1;
                                    int yi = storeTargetAreas[img][j].Y;
                                    int yf = yi + storeTargetAreas[img][j].Height - 1;

                                    for (int xc = xi; xc <= xf; xc++)
                                    {
                                        for (int yc = yi; yc <= yf; yc++)
                                        {
                                            //Perform a linear regression for each pixel 
                                            double[,] array = new double[Form1.ImageswithReferences[img].Count, 2];//[i,0]->Intensity;[i,1]->concentration

                                            //Define array to perform linear regression
                                            for (int k = 0; k < Form1.ImageswithReferences[img].Count; k++)
                                            {
                                                array[k, 0] = (double)REFImg[k].GetPixel(xc, yc).R;
                                                array[k, 1] = (double)Form1.ImageswithReferences[img][k].Concentration / 100;
                                            }
                                            //Linear Regression--------------------------------------------------

                                            //Cmean and Mean Intensity
                                            double Cmean = 0;
                                            double Imean = 0;
                                            int K = Form1.ImageswithReferences[img].Count;

                                            for (int k = 0; k < K; k++)
                                            {
                                                Cmean = Cmean + array[k, 1];
                                                Imean = Imean + array[k, 0];
                                            }
                                            Cmean = (double)Cmean / K;
                                            Imean = (double)Imean / K;

                                            // Calculate Sc, Si, r
                                            double Sc = 0;
                                            double Si = 0;
                                            double r = 0;
                                            for (int k = 0; k < K; k++)
                                            {
                                                Sc = Sc + Math.Pow((array[k, 1] - Cmean), 2);
                                                Si = Si + Math.Pow((array[k, 0] - Imean), 2);
                                                r = r + (array[k, 1] - Cmean) * (array[k, 0] - Imean);
                                            }
                                            double Conc = 0;
                                            if (Si == 0 || Sc == 0)
                                            {
                                                Conc = Cmean;
                                            }
                                            else
                                            {
                                                r = r / Math.Sqrt(Sc * Si);
                                                Sc = Math.Sqrt(Sc / (K - 1));
                                                Si = Math.Sqrt(Si / (K - 1));

                                                double b = r * Sc / Si;
                                                double a = Cmean - b * Imean;

                                                int intensity = FilteredImage.GetPixel(xc, yc).R;
                                                Conc = (double)b * intensity + a;
                                            }

                                            int x = (xc - xi);
                                            int y = (yc - yi);

                                            

                                                ConcentrationArray[x, y] = Conc;
                                        }
                                    }
                                    storeConcentrationData[img].Add(ConcentrationArray);//Stores Concentration Array
                                }
                            }


                        }
                    }
                }
                #endregion

                #region SIMPLE Calibration
                //Diferent Image Size or Different Target Sizes (SIMPLE CALIBRATION)
                if (!cond1)
                {
                    for (int img = 0; img < ImagetoProcess.Length; img++)
                    {

                        if (Form1.ImageswithReferences[img].Count > 0)
                        {
                            //Image filtration
                            int index = i;
                            Bitmap FilteredImage = ImagetoProcess[img].Clone(new Rectangle(0, 0, ImagetoProcess[img].Width, ImagetoProcess[img].Height), PixelFormat.Format32bppRgb);
                            //Apply Mean Filter (to eliminate local noise)
                            Median medianfilter = new Median();
                            medianfilter.Size = 5;
                            FilteredImage = medianfilter.Apply(FilteredImage);
                            //Apply Grayscale filter
                            FilteredImage = new Grayscale(0.2125, 0.7154, 0.0721).Apply(FilteredImage);

                            int numTrgts = storeTargetAreas[img].Count;
                            if (numTrgts > 0)
                            {
                                for (int j = 0; j < numTrgts; j++)
                                {
                                    //Array size
                                    int m = storeTargetAreas[img][j].Width;
                                    int n = storeTargetAreas[img][j].Height;
                                    double[,] ConcentrationArray = new double[m, n];

                                    //Target area square/rectangle dimension---------------------------------------------------------
                                    int xi = storeTargetAreas[img][j].X;
                                    int xf = xi + storeTargetAreas[img][j].Width - 1;
                                    int yi = storeTargetAreas[img][j].Y;
                                    int yf = yi + storeTargetAreas[img][j].Height - 1;

                                    //PERFORM LINEAR REGRESSION FOR EACH TARGET
                                    double[,] array = new double[Form1.ImageswithReferences[img].Count, 2];//[i,0]->Intensity;[i,1]->concentration

                                    //Define array to perform linear regression
                                    for (int k = 0; k < Form1.ImageswithReferences[img].Count; k++)
                                    {
                                        array[k, 0] = GetMeanIntensityValue(Form1.ImageswithReferences[img][k].ImageIndex, j);
                                        array[k, 1] = (double)Form1.ImageswithReferences[img][k].Concentration / 100;
                                    }
                                    //Linear Regression--------------------------------------------------

                                    //Cmean and Mean Intensity
                                    double Cmean = 0;
                                    double Imean = 0;
                                    int K = Form1.ImageswithReferences[img].Count;
                                    for (int k = 0; k < K; k++)
                                    {
                                        Cmean = Cmean + array[k, 1];
                                        Imean = Imean + array[k, 0];
                                    }
                                    Cmean = Cmean / K;
                                    Imean = Imean / K;
                                   
                                    // Calculate Sc, Si, r
                                    double Sc = 0;
                                    double Si = 0;
                                    double r = 0;
                                    for (int k = 0; k < K; k++)
                                    {
                                        Sc = Sc + Math.Pow((array[k, 1] - Cmean), 2);
                                        Si = Si + Math.Pow((array[k, 0] - Imean), 2);
                                        r = r + (array[k, 1] - Cmean) * (array[k, 0] - Imean);
                                    }

                                    r = r / Math.Sqrt(Sc * Si);
                                    Sc = Math.Sqrt(Sc / (K - 1));
                                    Si = Math.Sqrt(Si / (K - 1));

                                    double b = r * Sc / Si;
                                    double a = Cmean - b * Imean;

                                    for (int xc = xi; xc <= xf; xc++)
                                    {
                                        for (int yc = yi; yc <= yf; yc++)
                                        {
                                            int intensity = FilteredImage.GetPixel(xc, yc).R;

                                            double Conc = 0;
                                            if (Sc == 0 || Si == 0) { Conc = Cmean; }
                                            else { Conc = (double)b * intensity + a; }

                                            int x = (xc - xi);
                                            int y = (yc - yi);
                                            ConcentrationArray[x, y] = Conc;
                                        }
                                    }
                                    storeConcentrationData[img].Add(ConcentrationArray);//Stores Concentration Array
                                }
                            }


                        }
                    }
                }
                #endregion

            }
            #endregion

            #region Without Calibration performed
            // Calculate Concentrations by performing a normalization of data
            if (!calibperformed)
            {
                /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                DEFINE CONCENTRATION ARRAYS FOR EACH TARGET DEFINED BY PERFORMING A NORMALIZATION OF THE DATA
                Inputs: 
                ∙ TargetArea and ImagetoProcess
                ∙ Image loaded

                Output: 
                ∙ Concentration arrays
                %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

                for (int i = 0; i < ImagetoProcess.Length; i++)
                {
                    //Image filtration
                    int index = i;
                    Bitmap FilteredImage = FilterImage(ImagetoProcess[index]);
                    Point ImaxAndImin = GetImaxAndImin(FilteredImage);

                    int Imax = ImaxAndImin.X;
                    int Imin = ImaxAndImin.Y;

                    int numTrgts = storeTargetAreas[i].Count;
                    if (numTrgts > 0)
                    {
                        for (int j = 0; j < numTrgts; j++)
                        {
                            //Array size
                            int m = storeTargetAreas[index][j].Width;
                            int n = storeTargetAreas[index][j].Height;
                            double[,] ConcentrationArray = new double[m, n];

                            //Target area square/rectangle dimension---------------------------------------------------------
                            int xi = storeTargetAreas[index][j].X;
                            int xf = xi + storeTargetAreas[index][j].Width - 1;
                            int yi = storeTargetAreas[index][j].Y;
                            int yf = yi + storeTargetAreas[index][j].Height - 1;

                            for (int xc = xi; xc <= xf; xc++)
                            {
                                for (int yc = yi; yc <= yf; yc++)
                                {
                                    int x = (xc - xi);
                                    int y = (yc - yi);
                                    //Gets Intensity value of the grayscale Image
                                    int intensity = FilteredImage.GetPixel(xc, yc).R;
                                    double Conc = (double)(intensity - Imin) / (Imax - Imin);

                                    if (DarkcheckBox.Checked) { Conc = 1 - Conc; }//Dark Areas Higher concentration

                                    ConcentrationArray[x, y] = Conc;
                                }
                            }
                            storeConcentrationData[index].Add(ConcentrationArray);//Stores Concentration Array
                        }
                    }

                }
            }
            #endregion

        }//Defines storeConcentrationData[image_index][Target number]=Concentration array

        /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        REDUCTION IN THE SEGREGATION OF CONCENTRATION
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

        private void CalculateSegregationIntensityIndexfactors()
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            CALCULATION OF SEGREGATION INTENSITY INDEX MEASURES
            Inputs: 
            ∙ Concentration matrix (Normalized or Calibrated intensity values)

            Output: 
            ∙ Segregation Intensity Index factors = [σ, CoV, M, ...] = 
              [St. dev., Coeff. of Variance, Mixing Index, ...]
            ∙ Other Target factors = [...,Cm, Cmax, Cmin, N] 
              [..., Mean Concentration, Max. Conc. Value found, Min. Conc. Value found, Number of measured points]

            Hector Betancourt Cervantes, 2017
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Define the  IntensityMeasures List
            if (IntensityMeasures.Count > 0) { IntensityMeasures.Clear(); }

            for (int i = 0; i < ImagetoProcess.Length; i++)
            {
                IntensityMeasures.Add(new List<double[]>());
            }

            int j = 0;
            foreach (var List in storeConcentrationData)
            {
                if (List.Count > 0)
                {
                    foreach (var item in List)
                    {
                        //Get mean and standard deviation of the previous matrix ----------------------------------------
                        double[] StatMeasure = statistical_measures(item);
                        double Cm = StatMeasure[0];
                        double StDev = StatMeasure[1];
                        double CoV = 0;
                        double M = 1;
                        if (StDev > 0)
                        {              
                            CoV = StDev / Cm;
                            M = 1 - CoV;
                        }                        
                        double Cmax = StatMeasure[3];
                        double Cmin = StatMeasure[2];
                        double N = StatMeasure[4];

                        double[] IntMeasures={ StDev, CoV, M, Cm, Cmax, Cmin, N };
                        IntensityMeasures[j].Add(IntMeasures);
                    }

                }
                j++;
            }

            NormalizeCoV();
        } //Defines IntensityMeasures[image_index][Target number]={σ, CoV, M, Cm, Cmax, Cmin, N}

        private void NormalizeCoV()
        {
            //Normalize Non-inlet targets
            for (int i = 0; i < Form1.AssignedInletsList.Count; i++)
            {
                if (Form1.AssignedInletsList[i].Count > 0)
                {
                    for (int j = 0; j < Form1.AssignedInletsList[i].Count; j++)
                    {
                        //Target Coordinate
                        int Trgtx = Form1.AssignedInletsList[i][j].TargetNumber;
                        double CoVtrgt = IntensityMeasures[i][Trgtx][1];
                        //Assigned Inlet Coordinate
                        int Inletimg= Form1.AssignedInletsList[i][j].InletImageCoordinate;
                        int InletTrgt= Form1.AssignedInletsList[i][j].InletTargetCoordinate;
                        double CoVinlet = IntensityMeasures[Inletimg][InletTrgt][1];

                        double nCoV = CoVtrgt/ CoVinlet;
                        IntensityMeasures[i][Trgtx][1] = nCoV;
                        IntensityMeasures[i][Trgtx][2] = 1 - nCoV;
                    }
                }
            }

            //Normalize Inlets
            for (int i = 0; i < inletTrgts.Count; i++)
            {
                if (inletTrgts[i].Count > 0)
                {
                    for (int j = 0; j < inletTrgts[i].Count; j++)
                    {
                        IntensityMeasures[i][j][1] = 1; //CoV
                        IntensityMeasures[i][j][2] = 0; //M
                    }
                }
            }
        }

        /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        REDUCTION IN THE SCALE OF CONCENTRATION
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

        private void CalculateHorizontalvariograms()
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            HORIZONTAL VARIOGRAM CALCULATION
            Inputs:
            ∙ Standarized concentration matrix

            Output: 
            ∙ Variogram array: γx(h)=variogram[h]

            Computing method proposed by Alena Kukukova, 2010
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Define HorizontalVariograms List
            if (HorizontalVariograms.Count > 0) { HorizontalVariograms.Clear(); }

            for (int k = 0; k < ImagetoProcess.Length; k++)
            {
                HorizontalVariograms.Add(new List<double[]>());
            }

            int i = 0;
            foreach (var List in storeConcentrationData)
            {
                if (List.Count > 0)
                {
                    int j = 0;
                    foreach (var item in List)
                    {
                        //Variables-----------------------------------------------------------------------------------------
                        double Sum2 = 0;
                        double Nh = 0; //Total number of pairs of data separated by distance h

                        //Get standarized concentration matrix
                        double[,] standdata = standarized_array(i, j);

                        // Maximum separation distance is one half of the target area---------------------------------------
                        //Max_h = total # of seperation distances to evaluate
                        int Max_h = (int)Math.Floor((decimal)standdata.GetLength(0) / 2);

                        //Define Horizontal Variogram array ----------------------------------------------------------------
                        double[] hvariogram = new double[Max_h + 1];
                        hvariogram[0] = 0;

                        // loop through all separation distances; for zero dist, var is 0, so we don't need to calculate
                        for (int dist = 1; dist <= Max_h; dist++)
                        {
                            Sum2 = 0;
                            Nh = 0;

                            //Loop through all rows (y-direction)
                            for (int y = 0; y < standdata.GetLength(1); y++)
                            {
                                //for each row, loop through columns (x-direction)
                                for (int x = 0; x < standdata.GetLength(0) - dist; x++)
                                {
                                    Sum2 = Sum2 + Math.Pow(standdata[x, y] - standdata[(x + dist), y], 2);
                                    Nh = Nh + 1;
                                }

                            }
                            hvariogram[dist] = Sum2 / (2 * Nh); //Variogram calculation from equation
                        }
                        HorizontalVariograms[i].Add(hvariogram);
                        j++;
                    }
                }
                i++;
            }
        }//Defines HorizontalVariograms[image_index][Target number] = Horizontal Variogram

        private void CalculateVerticalvariograms()
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            VERTICAL VARIOGRAM CALCULATION
            Inputs: 
            ∙ TargetArea 
            ∙ Standarized concentration matrix

            Output: 
            ∙ Variogram array: γx(h)=variogram[h]

            Computing method proposed by Alena Kukukova, 2010
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Define HorizontalVariograms List
            if (VerticalVariograms.Count > 0) { VerticalVariograms.Clear(); }

            for (int k = 0; k < ImagetoProcess.Length; k++)
            {
                VerticalVariograms.Add(new List<double[]>());
            }

            int i = 0;
            foreach (var List in storeConcentrationData)
            {
                if (List.Count > 0)
                {
                    int j = 0;
                    foreach (var item in List)
                    {
                        //Get standarized concentration matrix
                        double[,] standdata = standarized_array(i, j);

                        //Variables-----------------------------------------------------------------------------------------
                        double Sum2 = 0;
                        double Nh = 0; //Total number of pairs of data separated by distance h

                        // Maximum separation distance is one half of the target area---------------------------------------
                        //Max_h = total # of seperation distances to evaluate
                        int Max_h = (int)Math.Floor((decimal)standdata.GetLength(1) / 2);

                        //Define Horizontal Variogram array ----------------------------------------------------------------
                        double[] vvariogram = new double[Max_h + 1];
                        vvariogram[0] = 0;

                        // loop through all separation distances; for zero dist, var is 0, so we don't need to calculate
                        for (int dist = 1; dist <= Max_h; dist++)
                        {
                            Sum2 = 0;
                            Nh = 0;

                            //Loop through all rows (y-direction)
                            for (int x = 0; x < standdata.GetLength(0); x++)
                            {
                                //for each row, loop through columns (x-direction)
                                for (int y = 0; y < standdata.GetLength(1) - dist; y++)
                                {
                                    Sum2 = Sum2 + Math.Pow(standdata[x, y] - standdata[x, (y + dist)], 2);
                                    Nh = Nh + 1;
                                }

                            }
                            vvariogram[dist] = Sum2 / (2 * Nh); //Variogram calculation from equation
                        }

                        VerticalVariograms[i].Add(vvariogram);
                        j++;
                    }
                }
                i++;
            }

        }//Defines VerticalVariograms[image_index][Target number] = Vertical Variogram

        private void CalculateMeanLengthScales()
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            MEAN LENGTH SCALE CALCULATION
            Inputs: 
            ∙ TargetArea 
            ∙ Horizontal or vertical variogram vector


            Output: 
            ∙ Mean length scale: Lv = P∙[δγx/δh]^(-1) 
                Horizontal(1) or Vertical(2) mean length scale

            Computing method proposed by Alena Kukukova, 2010
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Define MeanLengthScales List
            if (MeanLengthScales.Count > 0) { MeanLengthScales.Clear(); }

            for (int k = 0; k < ImagetoProcess.Length; k++)
            {
                MeanLengthScales.Add(new List<Coordinate>());
            }

            int i = 0;
            foreach (var List in storeConcentrationData)
            {
                if (List.Count > 0)
                {
                    int j = 0;
                    foreach (var item in List)
                    {
                        //Read standarized intensity array from the requested target----------------------------------------
                        Coordinate Lms = new Coordinate();
                        double P = IntensityMeasures[i][j][3];//The proportion of the minor species in the sample region = Cmean

                        //Horizontal(1) or Vertical(2) mean length scale calculation----------------------------------------
                        Lms.X =  P * (1 / (HorizontalVariograms[i][j][1] - HorizontalVariograms[i][j][0])); // Units:pixels/concentration^2
                        Lms.Y = P * (1 / (VerticalVariograms[i][j][1] - VerticalVariograms[i][j][0])); // Units:pixels/concentration^2
                        MeanLengthScales[i].Add(Lms);
                        j++;
                    }
                }
                    i++;
            }
        }//Defines MeanLengthScales[image_index][Target number].X = Horizontal mean length scale; .Y = Vertical mean length scale

        /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        RATE OF CHANGE IN SEGREGATION
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

        private void CalculateExposureIndexes() {

            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            HORIZONTAL VARIOGRAM CALCULATION
            Inputs: 
            ∙ Concentration matrix

            Output: 
            ∙ EXposure: Ε≅∑∑〖(1/2)⋅K⋅a(i,j)⋅(Ci-Cj) 〗

            Computing method proposed by Alena Kukukova, 2009
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Define ExposureIndexes List
            if (ExposureIndexes.Count > 0) { ExposureIndexes.Clear(); }

            for (int k = 0; k < ImagetoProcess.Length; k++)
            {
                ExposureIndexes.Add(new List<double>());
            }

            int i = 0;
            foreach (var List in storeConcentrationData)
            {
                if (List.Count > 0)
                {
                    int j = 0;
                    foreach (var item in List)
                    {
                        //Get Concentration Array
                        double[,] data = storeConcentrationData[i][j];

                        //Define Variables----------------------------------------------------------------------------------
                        double Exp = 0;
                        int xf = data.GetLength(0);
                        int yf = data.GetLength(1);

                        //Calculate Exposure--------------------------------------------------------------------------------
                        for (int x = 0; x < xf; x++)
                        {
                            for (int y = 0; y < yf; y++)
                            {
                                if (x != 0) { Exp = Exp + 0.5 * Math.Abs(data[x, y] - data[x - 1, y]); }
                                if (y != 0) { Exp = Exp + 0.5 * Math.Abs(data[x, y] - data[x, y - 1]); }
                                if (x != xf - 1) { Exp = Exp + 0.5 * Math.Abs(data[x, y] - data[x + 1, y]); }
                                if (y != yf - 1) { Exp = Exp + 0.5 * Math.Abs(data[x, y] - data[x, y + 1]); }
                            }
                        }

                        ExposureIndexes[i].Add(Exp);
                        j++;
                    }
                }
                i++;
            }

        }//Defines ExposureIndexes[image_index][Target number] = Exposure


        #endregion

        #region Auxiliar functions and Intensity Information Arrays

        private Bitmap FilterImage(Bitmap Img)
        {
            Bitmap FilteredImage = Img.Clone(new Rectangle(0, 0, Img.Width, Img.Height), PixelFormat.Format32bppRgb);

            //Apply Mean Filter (to eliminate local noise)
            Median medianfilter = new Median();
            medianfilter.Size = 5;
            FilteredImage = medianfilter.Apply(FilteredImage);
            //Apply Grayscale filter
            FilteredImage = new Grayscale(0.2125, 0.7154, 0.0721).Apply(FilteredImage);
            //Apply Histogram remapping
            //FilteredImage = new HistogramEqualization().Apply(FilteredImage);

            return FilteredImage;
        }

        private double GetMeanIntensityValue(int img_index, int Target)
        {
            double TrgtImean = 0;
            
            Bitmap RefFilteredImage = ImagetoProcess[img_index].Clone(new Rectangle(0, 0, ImagetoProcess[img_index].Width, ImagetoProcess[img_index].Height), PixelFormat.Format32bppRgb);
            //Apply median filter
            Median medianfilter = new Median();
            medianfilter.Size = 5;
            RefFilteredImage = medianfilter.Apply(RefFilteredImage);
            //Apply Grayscale filter
            RefFilteredImage = new Grayscale(0.2125, 0.7154, 0.0721).Apply(RefFilteredImage);

            //Array size
            int m = storeTargetAreas[img_index][Target].Width;
            int n = storeTargetAreas[img_index][Target].Height;
            double[,] ConcentrationArray = new double[m, n];

            //Target area square/rectangle dimension---------------------------------------------------------
            int xi = storeTargetAreas[img_index][Target].X;
            int xf = xi + storeTargetAreas[img_index][Target].Width - 1;
            int yi = storeTargetAreas[img_index][Target].Y;
            int yf = yi + storeTargetAreas[img_index][Target].Height - 1;

            int N = 0;
            for (int xc = xi; xc <= xf; xc++)
            {
                for (int yc = yi; yc <= yf; yc++)
                {
                    TrgtImean = TrgtImean + RefFilteredImage.GetPixel(xc, yc).R;
                    N = N + 1;                   
                }
            }
            TrgtImean = (double)TrgtImean / N;

            return TrgtImean;
        }//Get Mean Intensity value in a Target of a REFERENCE IMAGE 

        private Point GetImaxAndImin(Bitmap FilteredImage)
        {
            Point ImaxAndImin = new Point();
            ImaxAndImin.X = 0; //Imax
            ImaxAndImin.Y = 255; //Imin
            //Target area square/rectangle dimension---------------------------------------------------------
            int xf = FilteredImage.Width;
            int yf = FilteredImage.Height;

            //Define intensity array in "IntensityArrayData[]"-----------------------------------------------
            for (int x = 0; x < xf; x++)
            {
                for (int y = 0; y < yf; y++)
                {
                    int PixVAL = FilteredImage.GetPixel(x, y).R;
                    if (PixVAL > ImaxAndImin.X) { ImaxAndImin.X = PixVAL; }
                    if (PixVAL < ImaxAndImin.Y) { ImaxAndImin.Y = PixVAL; }
                }
            }
            return ImaxAndImin;
        }

        public double[] statistical_measures(double[,] data)
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            COMPUTE STATISTICAL MEASURES
            Inputs: 
            ∙ Array 

            StatisticalArray=[μ,σ,Xmin,Xmax,N]=[Mean, Std. Dev., Min Value, Max Value, Number of Data] = [0,1,2,3,4]

            Output: 
            ∙ Statistical measures array
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Define variables------------------------------------------------------------------------------
            double mean = 0; double StDev = 0; double Xmax = 0; double Xmin = data[0, 0]; double N = 0;
            double[] StatMeasures = new double[5];

            //Find Mean, N, Xmax & Xmin --------------------------------------------------------------------
            for (int xc = 0; xc < data.GetLength(0); xc++)
            {
                for (int yc = 0; yc < data.GetLength(1); yc++)
                {
                    if (Xmax < data[xc, yc]) { Xmax = data[xc, yc]; }
                    if (Xmin > data[xc, yc]) { Xmin = data[xc, yc]; }
                    mean = mean + data[xc, yc];
                    N = N + 1;
                }
            }
            mean = mean / N;

            //Compute Standard deviation--------------------------------------------------------------------
            for (int xc = 0; xc < data.GetLength(0); xc++)
            {
                for (int yc = 0; yc < data.GetLength(1); yc++)
                {
                    StDev = StDev + Math.Pow((data[xc, yc] - mean), 2);
                }
            }
            StDev = Math.Sqrt(StDev / N);
            StatMeasures[0] = mean;
            StatMeasures[1] = StDev;
            StatMeasures[2] = Xmin;
            StatMeasures[3] = Xmax;
            StatMeasures[4] = N;

            return StatMeasures;
        }//Function that returns statistical measures
                   
        public double[,] standarized_array(int Image_index, int Target)
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            DEFINE STANDARIZED ARRAY
            Inputs: 
            ∙ Array 
            ∙ Statistical measures: Mean (μ) and Standard deviation (σ) 

            Xsi=(Xi-μ)/σ

            Output: 
            ∙ Standarized array [0,1,2,3,4]
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            //Declare normalized intensity array-------------------------------------------------------------
            //m = The number of rows in the concentration array -> data.GetLength(0)
            //n = The number of columns in the concentration array -> data.GetLength(1)

            int m = storeConcentrationData[Image_index][Target].GetLength(0);
            int n = storeConcentrationData[Image_index][Target].GetLength(1);

            double[,] StandarizedData = new double[m, n];
            //Declare other variables------------------------------------------------------------------------
            double Xi = 0;    // Concentration value
            //Get Mean and standard deviation to steandarize the array---------------------------------------
            double mean = IntensityMeasures[Image_index][Target][3];
            double StDev = IntensityMeasures[Image_index][Target][0];
            //Define standarized intensity array--------------------------------------------------------------
            for (int xc = 0; xc < m; xc++)
            {
                for (int yc = 0; yc < n; yc++)
                {
                    Xi = storeConcentrationData[Image_index][Target][xc, yc];
                    StandarizedData[xc, yc] = (Xi - mean) / StDev;
                }
            }
            return StandarizedData;
        }//Function that returns normalized intensity array of a target area
        

        public double[,] GetIntensityArray(int Image_index, int TargetArea)
        {
            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            DEFINE INTENSITY ARRAY
            Inputs: 
            ∙ TargetArea and ImagetoProcess
            ∙ Image loaded

            Output: 
            ∙ Intensity array
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            int index = Image_index;
            Bitmap FilteredImage = ImagetoProcess2[index];
            FilteredImage = FilterImage(FilteredImage);
            

            //Target area square/rectangle dimension---------------------------------------------------------
            int xi = storeTargetAreas2[index][TargetArea].X;
            int xf = xi + storeTargetAreas2[index][TargetArea].Width - 1;
            int yi = storeTargetAreas2[index][TargetArea].Y;
            int yf = yi + storeTargetAreas2[index][TargetArea].Height - 1;
            //Array dimension--------------------------------------------------------------------------------
            int x = (xf - xi);
            int y = (yf - yi);
            //Variables--------------------------------------------------------------------------------------
            double[,] IntensityArrayData = new double[x + 1, y + 1]; //Declare array of intensity values
            //Define intensity array in "IntensityArrayData[]"-----------------------------------------------
            for (int xc = xi; xc <= xf; xc++)
            {
                for (int yc = yi; yc <= yf; yc++)
                {
                    x = (xc - xi);
                    y = (yc - yi);
                    //Gets Intensity value of the grayscale Image
                    IntensityArrayData[x, y] = FilteredImage.GetPixel(xc, yc).R;
                }
            }
            return IntensityArrayData;
        }//Function that returns the intensity array of a target area

        public double[,] FullImageDataArray(int Image_index)
        {

            /*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            DEFINE INTENSITY ARRAY
            Inputs: 
            ∙ Image loaded

            Output: 
            ∙ Full image intensity array
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

            Bitmap FilteredImage = ImagetoProcess2[Image_index];
            FilteredImage = FilterImage(FilteredImage);

            //Target area square/rectangle dimension---------------------------------------------------------
            int xf = FilteredImage.Width;
            int yf = FilteredImage.Height;

            //Variables--------------------------------------------------------------------------------------
            double[,] ImageIntensityArray = new double[xf, yf]; //Declare array of intensity values
            //Define intensity array in "IntensityArrayData[]"-----------------------------------------------
            for (int x = 0; x < xf; x++)
            {
                for (int y = 0; y < yf; y++)
                {
                    //Gets Intensity value of the grayscale Image
                    ImageIntensityArray[x, y] = FilteredImage.GetPixel(x, y).R;
                }
            }
            return ImageIntensityArray;
        }//Function that returns the intensity array of the loaded image

        #endregion

        #region Functions

        public double[] ConversionFactors(int ImageEvaluated)
        {
            int ycorr =0;
            int xcorr = 0;
            int index = ImageEvaluated;
            double resizeFactor = 0;
            double[] FactorsArray = new double[3];

            #region Image conversion (Zoomed) 

            //Determines to wich side (horizontal or vertical) the image was Dock in picturebox1------
            var wfactor = (double)ImagetoProcess[index].Width / pictureBox1.ClientSize.Width;
            var hfactor = (double)ImagetoProcess[index].Height / pictureBox1.ClientSize.Height;
            resizeFactor = Math.Max(wfactor, hfactor);
            var imageSize = new Size((int)(ImagetoProcess[index].Width / resizeFactor),
                (int)(ImagetoProcess[index].Height / resizeFactor));

            if (wfactor > hfactor)
            {
                //The image adjust to the pictureBox width
                ycorr = (int) ((pictureBox1.Height - imageSize.Height) / 2);
                xcorr = 0;
            }
            else
            {
                if (wfactor == hfactor) { ycorr = 0; xcorr = 0; }
                else
                {
                    //The image adjust to the pictureBox height
                    xcorr = Convert.ToInt32((pictureBox1.Width - imageSize.Width) / 2);
                    ycorr = 0;
                }
            }


            #endregion

            FactorsArray[0] = xcorr; FactorsArray[1] = ycorr; FactorsArray[2] = resizeFactor;
            return FactorsArray;
        }//[->xcorr,| ycorr, resizeFactor]  -> pictureBox.Width*resizeFactor=ImagetoProcess.Width
   
        private void DrawRectangles(int Image_index) {
            int i = 1;
            using (Graphics g = pictureBox2.CreateGraphics())
            {
                var pen = new Pen(ContourColorbutton.BackColor, 1);

                foreach (var area in storeTargetAreas[Image_index])
                {
                    //The rectangles are converted to picturebox2 size
                    double[] factors= ConversionFactors(Image_index);
                    int X = (int)((area.X / factors[2]) + factors[0]);
                    int Y = (int)((area.Y / factors[2]) + factors[1]);
                    int width = (int)((area.Width -1)/ factors[2]);
                    int height = (int)((area.Height-1) / factors[2]);
                    Rectangle modfarea = new Rectangle(X, Y, width, height);

                    //Here the rectangle is drawn using the converted coordinates from the previous function
                    g.DrawRectangle(pen, modfarea);

                    //Draw the number of the Target created
                    Rectangle rect2 = new Rectangle(modfarea.X - 15, modfarea.Y - 15,15,15);
                    Brush myBrush = new SolidBrush(NumColorbutton.BackColor);
                    g.DrawString(i.ToString(), TrgtAreaNumlabel.Font, myBrush, rect2);

                    //Show that some targets are inlets
                    if (inletTrgts[Image_index].Count > -1)
                    {
                        for (int j = 0; j < inletTrgts[Image_index].Count; j++)
                        {
                            if (inletTrgts[Image_index][j] == i-1)
                            {
                                //Draw the number of the Target created
                                Rectangle rect3 = new Rectangle(modfarea.X + 2, modfarea.Y + 2, 15, 15);
                                g.DrawString("In", TrgtAreaNumlabel.Font, myBrush, rect3);
                            }
                        }
                    }
                    

                    i = i + 1;
                }

                pen.Dispose();
            }
        }

        private void StopRunningVideoOrCamera()
        {
            /*
            //If a video is being played it needs be stopped before closing
            if (VideoFile.IsRunning == true)
            {
                VideoFile.SignalToStop();

            }
            */
        }   

        private bool VerifyTrgtAreaSelection(int x, int y) {

            int index = tabControl3.SelectedIndex;
            double[] factors=ConversionFactors(index);
            if(x > factors[0] && x < (int)(factors[0] + ImagetoProcess[index].Width / factors[2]) &&
                y > factors[1] && y < (int)(factors[1] + ImagetoProcess[index].Height / factors[2])) { return true; }
            else { return false; }
        }

        private int FindSelectedTargetArea() {
            int index = tabControl3.SelectedIndex;
            int TargetAreaNumber = -1;

            if (storeTargetAreas[index].Count > 0)
            {
                for (int i = storeTargetAreas[index].Count-1; i >=0 ; i--) {
                    int X1 = storeTargetAreas[index][i].X;
                    int X2 = X1 + storeTargetAreas[index][i].Width - 1;
                    int Y1 = storeTargetAreas[index][i].Y;
                    int Y2 = Y1 + storeTargetAreas[index][i].Height - 1;

                    if (X1<= Xposition && X2>= Xposition && Y1 <= Yposition && Y2 >= Yposition)
                    {
                        TargetAreaNumber = i;
                        break;
                    }
                }  

            }
            return TargetAreaNumber;
        }

        private void EraseInletTargets(int Target) {

            int index = tabControl3.SelectedIndex;
            
            //Evaluate if the erased target is an inlet
            if (inletTrgts[index].Count > -1)
            {
                for (int j = 0; j < inletTrgts[index].Count; j++)
                {
                    if (inletTrgts[index][j] == Target)
                    {
                       //Remove the target from the inlet list
                       inletTrgts[index].RemoveAt(j);//The list begins in 0  
                    }
                }

                for (int j = 0; j < inletTrgts[index].Count; j++)
                {
                    if (inletTrgts[index][j] > Target)
                    {
                        inletTrgts[index][j] = inletTrgts[index][j] - 1;
                    }
                }
             }
        }

        private void EvaluateIfThereAreInletsDefined()
        {
            int i = 0;
            foreach (var list in inletTrgts)
            {
                foreach (var item in list)
                {
                    i++;
                }
            }

            if (i > 0 && Form1.MisTrgts > 0)
            {
                AssignInletButton.ForeColor = Color.Red;
                AssignInletButton.Font = new Font(AssignInletButton.Font, FontStyle.Bold);

                AssignInletButton2.ForeColor = Color.Red;
                AssignInletButton2.Font = new Font(AssignInletButton.Font, FontStyle.Bold);
            }
            else
            {
                AssignInletButton.ForeColor = Color.Black;
                AssignInletButton.Font = new Font(AssignInletButton.Font, FontStyle.Regular);

                AssignInletButton2.ForeColor = Color.Black;
                AssignInletButton2.Font = new Font(AssignInletButton.Font, FontStyle.Regular);
            }
           
        }

        private void CheckAssignedRefImgs()
        {
            bool RefAssignedOk = true;
            foreach (var item in Form1.ImageswithReferences)
            {
                int a = item.Count;
                if (a == 1) { RefAssignedOk = false; }
            }
            if (RefAssignedOk)
            {
                StartCalibButton.ForeColor = Color.Black;
                StartCalibButton.Font = new Font(StartCalibButton.Font, FontStyle.Regular);
            }
            else
            {
                StartCalibButton.ForeColor = Color.Red;
                StartCalibButton.Font = new Font(StartCalibButton.Font, FontStyle.Bold);
            }
        }

        private void RefreshPictureBox2()
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                pictureBox2.Refresh();
                DrawRectangles(index);
                DrawBlobs(index);
            }
            
        }

        private void FillDimensionsCombobox()
        {
            DimensionsComboBox.Items.Clear();
            DimensionsComboBox.Items.Add("Standard Deviation (σ)");
            DimensionsComboBox.Items.Add("Coeff. of Variation (CoV)");
            DimensionsComboBox.Items.Add("Mixing Index (M)");
            DimensionsComboBox.Items.Add("Mean Length Scale (Lh)");
            DimensionsComboBox.Items.Add("Mean Length Scale (Lv)");
            DimensionsComboBox.Items.Add("Exposure");
            DimensionsComboBox.Items.Add("Mean Concentration (Cm)");
            DimensionsComboBox.Items.Add("Max Concentration (Cmax)");
            DimensionsComboBox.Items.Add("Min Concentration (Cmin)");
            DimensionsComboBox.Items.Add("Measured Points (N)");

            DimensionsComboBox.SelectedIndex = 0;
        }

        private void FillDimensionsCombobox2()
        {
            DimensionsComboBox2.Items.Clear();
            DimensionsComboBox2.Items.Add("Standard Deviation (σ)");
            DimensionsComboBox2.Items.Add("Coeff. of Variation (CoV)");
            DimensionsComboBox2.Items.Add("Mixing Index (M)");
            DimensionsComboBox2.Items.Add("Maximum Striation Thickness");
            DimensionsComboBox2.Items.Add("Point-particle Deviation (σfpp)");
            DimensionsComboBox2.Items.Add("Index of Dispersion (Idisp)");
            DimensionsComboBox2.Items.Add("Spatial resolution (Xg)");
            DimensionsComboBox2.Items.Add("Mean Concentration (Cm)");
            DimensionsComboBox2.Items.Add("Max Concentration (Cmax)");
            DimensionsComboBox2.Items.Add("Min Concentration (Cmin)");
            DimensionsComboBox2.Items.Add("Measured Points (N)");
            DimensionsComboBox2.Items.Add("Number of particles");

            DimensionsComboBox2.SelectedIndex = 0;
        }

        #endregion

        #region  Form Keyboard events

        private void Form2_KeyUp(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Escape)
            {

                if (ReadMouseClick || ErasingTrgt || DefineInletProcess || MaxStrTrgtSel || MaxStrTransSel)
                {
                    Cursor = Cursors.Arrow;
                    ReadMouseClick = false;
                    ErasingTrgt = false;
                    DefineInletProcess = false;
                    MaxStrTrgtSel = false;
                    MaxStrTransSel = false;
                }
                //this.DialogResult = DialogResult.Cancel;
                e.Handled = true;
            }
        }
        
        #endregion

        #region Form Behaviour

            #region When Loading Form

        private void RemoveTabs()
        {
            tabControl1.TabPages.Remove(FilepropertiesTab);
            tabControl1.TabPages.Remove(TrgtAreaMixDimTab);
            tabControl1.TabPages.Remove(MixindDataPlotsTab);
            tabControl1.TabPages.Remove(ProcessImageTab);
            tabControl1.TabPages.Remove(PartMixDimTab);
            tabControl1.TabPages.Remove(MixPlotsPartData);
            tabControl2.TabPages.Remove(ParticleImgMenu);
            tabControl3.TabPages.Remove(ImageTabpage);
        }
        
        #endregion

            #region Checkboxes events

        private void PartDatacheckbox_CheckedChanged(object sender, EventArgs e)
        {
            if (PartDatacheckbox.Checked == true) { ConDatacheckbox.Checked = false; ShowParticleTrackingMenuOptions(); }
            else { ConDatacheckbox.Checked = true;}
        }

        private void ConDatacheckbox_CheckedChanged(object sender, EventArgs e)
        {
            if (ConDatacheckbox.Checked == true) { PartDatacheckbox.Checked = false; ShowConcentrationMenuOptions(); }
            else { PartDatacheckbox.Checked = true; }
        }

        private void DarkcheckBox_CheckedChanged(object sender, EventArgs e)
        {
            if (DarkcheckBox.Checked == true) { LightcheckBox.Checked = false; }
            else { LightcheckBox.Checked = true; }
        }

        private void LightcheckBox_CheckedChanged(object sender, EventArgs e)
        {
            if (LightcheckBox.Checked == true) { DarkcheckBox.Checked = false; }
            else { DarkcheckBox.Checked = true; }
        }

        #endregion

            #region Combobox events

        private void comboBox1_SelectedIndexChanged(object sender, EventArgs e)
        {
            int index=tabControl3.SelectedIndex;
            int NumTrgtAreas = storeTargetAreas[index].Count();

            if (NumTrgtAreas > 0) // Shows the area of the target selected
            {
                int a = int.Parse(comboBox1.SelectedItem.ToString());
                DimAreaTextBox.Text = storeTargetAreas[index][a-1].Width.ToString() + "x" +
                    storeTargetAreas[index][a - 1].Height.ToString();
                TargetAreaDisplay(index);//Displays the target image in TargetPicBox
            }
            else { DimAreaTextBox.Text = ""; TargetPicBox.Image = null; }
            

        }

        #endregion

            #region Zooming Image in picturebox1
        
        protected override void OnMouseWheel(MouseEventArgs ea)
        {
            int index = tabControl3.SelectedIndex;
            bool condition = false;
            int Xcoord = 0;
            int Ycoord = 0;
            if (index >= 0)
            {
                if (ea.X > tabControl3.TabPages[0].Left + 2 && ea.X < tabControl3.TabPages[0].Right)
                {
                    if (ea.Y > tabControl3.TabPages[0].Top + 26 + 2 && ea.Y < tabControl3.TabPages[0].Bottom + 26)
                    {
                        condition = true;
                        Xcoord = ea.X - (tabControl3.TabPages[0].Left + 2);
                        Ycoord = ea.Y - (tabControl3.TabPages[0].Top + 26);
                    }
                }
            }
            //evaluates if there is an image loaded and if the cursor is inside pictureBox1
            if (index>-1 && insidepicturebox && condition) 
            {
                //Evaluate if pictureBox1 is DockStyle=Fill;
                if (pictureBox1.Dock == DockStyle.Fill)
                {
                    int top = pictureBox1.Top; int left = pictureBox1.Left;
                    int width = pictureBox1.Width; int height = pictureBox1.Height;
                    pictureBox1.Dock = DockStyle.None;
                    //tabControl3.TabPages[index].AutoScroll = true;
                    pictureBox1.Top = top; pictureBox1.Left = left;
                    pictureBox1.Width = width; pictureBox1.Height = height;
                }

                // If the mouse wheel is moved forward (Zoom in)
                if (ea.Delta > 0)
                {
                    // Check if the Imagetoprocess dimensions are in range (15 is the minimum and maximum zoom level)
                    if ((pictureBox1.Width < (15 * tabControl3.Width)) && (pictureBox1.Height < (15 * tabControl3.Height)))
                    {
                        // Change the size of the picturebox, multiply it by the ZOOMFACTOR
                        pictureBox1.Width = (int)(pictureBox1.Width * 1.25);
                        pictureBox1.Height = (int)(pictureBox1.Height * 1.25);

                        //If the user is defining a target while zooming in
                        if (start)
                        {selectX = (int)(selectX * 1.25); selectY = (int)(selectY * 1.25);}

                        // Formula to move the picturebox, to zoom in the point selected by the mouse cursor
                        //Assign top---------------------------------------------------------
                        int top= (int)(Ycoord - 1.25 * (Ycoord - pictureBox1.Top));
                        if (top > 0) { pictureBox1.Top = 0; }
                        else
                        {
                            if (tabControl3.TabPages[0].Height-top> pictureBox1.Height)
                            {
                                pictureBox1.Top = tabControl3.TabPages[0].Height - pictureBox1.Height;
                            }
                            else { pictureBox1.Top = top; }
                               
                        }
                        //Assign Left---------------------------------------------------------
                        int left = (int)(Xcoord - 1.25 * (Xcoord - pictureBox1.Left));
                        if (left > 0) { pictureBox1.Left = 0; }
                        else
                        {
                            if (tabControl3.TabPages[0].Width - left > pictureBox1.Width)
                            {
                                pictureBox1.Left = tabControl3.TabPages[0].Width - pictureBox1.Width;
                            }
                            else { pictureBox1.Left = left; }

                        }
                    }
                }
                else
                {
                    // Check if the pictureBox dimensions are in range (15 is the minimum and maximum zoom level)
                    if ((pictureBox1.Width > (tabControl3.Width)) && (pictureBox1.Height > (tabControl3.Height)))
                    {// Change the size of the picturebox, divide it by the ZOOMFACTOR
                        pictureBox1.Width = (int)(pictureBox1.Width / 1.25);
                        pictureBox1.Height = (int)(pictureBox1.Height / 1.25);

                        //If the user is defining a target while zooming
                        if (start)
                        { selectX = (int)(selectX / 1.25); selectY = (int)(selectY / 1.25); }

                        // Formula to move the picturebox, to zoom in the point selected by the mouse cursor
                        //Assign top---------------------------------------------------------
                        int top = (int)(Ycoord - 0.80 * (Ycoord - pictureBox1.Top));
                        if (top > 0) { pictureBox1.Top = 0; }
                        else
                        {
                            if (tabControl3.TabPages[0].Height - top > pictureBox1.Height)
                            {
                                pictureBox1.Top = tabControl3.TabPages[0].Height - pictureBox1.Height;
                            }
                            else { pictureBox1.Top = top; }

                        }
                        //Assign Left---------------------------------------------------------
                        int left = (int)(Xcoord - 0.80 * (Xcoord - pictureBox1.Left));
                        if (left > 0) { pictureBox1.Left = 0; }
                        else
                        {
                            if (tabControl3.TabPages[0].Width - left > pictureBox1.Width)
                            {
                                pictureBox1.Left = tabControl3.TabPages[0].Width - pictureBox1.Width;
                            }
                            else { pictureBox1.Left = left; }

                        }

                    }
                    else {
                        pictureBox1.Dock = DockStyle.Fill;
                    }
                }
                
                pictureBox2.Refresh();
                DrawRectangles(index);
            }
        }//Override OnMouseWheel event, for zooming in/out with the scroll wheel

        #endregion

            #region Display target area image section

        private void TargetAreaDisplay(int Image_index)
        {
            Rectangle cropArea=storeTargetAreas[Image_index][comboBox1.SelectedIndex];
            Bitmap bmpImage = new Bitmap(ImagetoProcess[Image_index]);
            TargetPicBox.Image = bmpImage.Clone(cropArea, bmpImage.PixelFormat);
        }

        #endregion
             
            #region Closing Tabs
        //Close tab Button events---------------------------------------------------------------------------
        private void tabControl3_DrawItem(object sender, DrawItemEventArgs e)
        {
            try
            {
                //Font drawFontBold = new Font("Arial", 12, FontStyle.Bold);
                e.Graphics.DrawString("X", e.Font, Brushes.Black, e.Bounds.Right - 15, e.Bounds.Top + 4);
                e.Graphics.DrawString(this.tabControl3.TabPages[e.Index].Text, e.Font, Brushes.Black, e.Bounds.Left + 12, e.Bounds.Top + 4);
                e.DrawFocusRectangle();
            }
            catch (Exception) { }
        }

        private void tabControl3_MouseDown(object sender, MouseEventArgs e)
        {
            for (int i = 0; i < this.tabControl3.TabPages.Count; i++)
            {
                Rectangle r = tabControl3.GetTabRect(i);
                //Getting the position of the "x" mark.
                Rectangle closeButton = new Rectangle(r.Right - 15, r.Top + 4, 9, 7);
                if (closeButton.Contains(e.Location))
                {
                    if (MessageBox.Show("Would you like to close this Image?", "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
                    {
                        this.tabControl3.TabPages.RemoveAt(i);
                        CloseImageTab(i);
                        break;
                    }
                }
            }
        }

        private void CloseImageTab(int TabIndextoclose)
        {
            int position = Array.IndexOf(calibimgarray, TabIndextoclose);//Shows the position in the array
            //Modify image positions and size of calibimgarray-------------------------------------------------------
            if (position > -1)
            {
                var newArray = new int[calibimgarray.Length - 1];
                int j = 0;
                for (int i = 0; i < calibimgarray.Length; i++)
                {
                    if (i == position) continue; //Finishes one loop, so the following code is ignored
                    if (i > position) { newArray[j] = calibimgarray[i] - 1; }
                    else { newArray[j] = calibimgarray[i]; }
                    j++;
                }
                calibimgarray = newArray;
            }
            else
            {
                for (int i = 0; i < calibimgarray.Length; i++)
                {
                    if (calibimgarray[i] > TabIndextoclose) { calibimgarray[i] = calibimgarray[i] - 1; }
                }
            }

            //Delete image from the ImagetoProcess Array----------------------------------------------------
            if (TabIndextoclose >= 0 && TabIndextoclose < ImagetoProcess.Length)
            {
                var newArray = new Bitmap[ImagetoProcess.Length - 1];
                int j = 0;
                for (int i = 0; i < ImagetoProcess.Length; i++)
                {
                    if (i == TabIndextoclose) continue; //Finishes one loop, so the following code is ignored
                    newArray[j] = ImagetoProcess[i];
                    j++;
                }
                ImagetoProcess = newArray;
            }
            //Delete Assigned Targets to Inlets------------------------------------------------------------- 
            Form1.AssignedInletsList.Clear();

            //Delete Assigned reference image list-----------------------------------------------------
            Form1.ImageswithReferences.Clear();

            //Delet inlet targets from the image closed--------------------------------------------------------------
            inletTrgts.RemoveAt(TabIndextoclose);

            //Delete Store Target Areas from the image closed----------------------------------------------
            storeTargetAreas.RemoveAt(TabIndextoclose);

            //Delete Loaded Image Info---------------------------------------------------------------------
            LoadedImageInfo.RemoveAt(TabIndextoclose);
            
            //Delete Thresvale Info of each Image----------------------------------------------------------
            ThresValueNum.RemoveAt(TabIndextoclose);


            //Delete BlobsRectangles and Particle Points from that image-------------------------------------------------------- 
            storeBlobRectangles.RemoveAt(TabIndextoclose);
            storePartPositions.RemoveAt(TabIndextoclose);

            //Delete Transect information List--------------------------------------------------------------------------------------
            DefinedTransects.RemoveAt(TabIndextoclose);//List to store predefined transects
            MeanSpacingParticles.RemoveAt(TabIndextoclose);
            MaximumStriationThickness.RemoveAt(TabIndextoclose);

            //Update information
            if (ImagetoProcess.Length > 0)
            {
                UpdateInformation(tabControl3.SelectedIndex);
            }

            if (ImagetoProcess.Length == 0)
            {
                PartTrgtComboBox.Items.Clear();
                ThresValue.Text = "";
                MaxStriationLabel.Text = "Maximum striation thickness: ";
                DimAreaTextBox2.Text = "";
            }
            //When there is only one image left--------------------------------------------------------------
            if (TabIndextoclose == 0 && ImagetoProcess.Length > 0) { WorkingWithTab(); }

            //Hide chkbox1 if there are no Images left-------------------------------------------------------
            if (ImagetoProcess.Length == calibimgarray.Length || ImagetoProcess.Length == 0)
            {
                chkbox1.Visible = false;
                chkbox2.Visible = false;
                ImgTrgtCombobox.Items.Clear();
                ImgTrgtCombobox.Text = "";
                AssignInletButton.ForeColor = Color.Black;
                AssignInletButton.Font = new Font(AssignInletButton.Font, FontStyle.Regular);
                comboBox1.Items.Clear();
                comboBox1.Text = "";
                DimAreaTextBox.Text = "";
                TargetPicBox.Image = null;
                numtrgt.Text = "# Targets:";
            }

            //Reset show filter button---------------------------------------
            ImgBinarization.Text = "Show filtered img";

        }
        //--------------------------------------------------------------------------------------------------
        #endregion

        private void ShowConcentrationMenuOptions()
        {
            tabControl2.TabPages.Insert(0, ConcentImgMenu);
            //tabControl2.TabPages.Add(ConcentImgMenu);
            tabControl2.TabPages.Remove(ParticleImgMenu);
        }

        private void ShowParticleTrackingMenuOptions()
        {
            tabControl2.TabPages.Insert(0, ParticleImgMenu);
            //tabControl2.TabPages.Add(ParticleImgMenu);
            tabControl2.TabPages.Remove(ConcentImgMenu);
        }

        private void CreateNewImageTab(int ImagetoAdd_index)
        {
            TabPage NewTabPage = new TabPage();
            NewTabPage.Text = LoadedImageInfo[ImagetoAdd_index][0] + "         "; 
            tabControl3.TabPages.Add(NewTabPage);
            tabControl3.SelectedIndex = ImagetoAdd_index;
        }

        private void tabControl3_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (tabControl3.SelectedIndex >= 0)
            {
                WorkingWithTab();
            }
        }

        private void WorkingWithTab()
        {
            int index = tabControl3.SelectedIndex;
            tabControl3.TabPages[index].Controls.Add(pictureBox1);
            pictureBox1.Image = ImagetoProcess[index];
            pictureBox1.Dock =DockStyle.Fill;
            pictureBox1.Controls.Add(pictureBox2);
            pictureBox2.Dock = DockStyle.Fill;
            //tabControl3.TabPages[index].AutoScroll = false;
            pictureBox1.Width = tabControl3.TabPages[0].Width;
            pictureBox1.Height = tabControl3.TabPages[0].Height;
            UpdateInformation(index);
            pictureBox2.Refresh();
            DrawRectangles(index);
        }

            #region Update Information
        private void UpdateInformation(int index) {

            RefreshPictureBox2();

            int NumTrgtAreas = storeTargetAreas[index].Count();

            #region Concentration data
            //Evaluates if Second Step is completed----------------------------------------------------
            if (ImagetoProcess.Length > calibimgarray.Length) { chkbox1.Visible = true; } else { chkbox1.Visible = false; }//Concentration data

            //Evaluates if Third Step is completed
            if (NumTrgtAreas > 0) { chkbox2.Visible = true; } else { chkbox2.Visible = false; }

            //Fills tabControl2 information------------------------------------------------------------
            numtrgt.Text = "# Targets: " + NumTrgtAreas.ToString();//Shows number of target created in label numtrgt
            FillTargetCombobox(index);//Updates the numbers of targets in the combobox
            FillImgTrgtCombobox();
            if (NumTrgtAreas > 0) // Shows the area of the target selected
            {
                DimAreaTextBox.Text = storeTargetAreas[index][NumTrgtAreas - 1].Width.ToString() + "x" +
                    storeTargetAreas[index][NumTrgtAreas - 1].Height.ToString();
                TargetAreaDisplay(index);//Displays the target image in TargetPicBox
            }
            else { DimAreaTextBox.Text = ""; TargetPicBox.Image = null; }
            #endregion

            #region Particle tracking data
            //Evaluates if Second Step is completed----------------------------------------------------
            if (ImagetoProcess.Length > calibimgarray.Length) { chkbox1P.Visible = true; } else { chkbox1P.Visible = false; }//Particle data

            //Evaluates if Third Step is completed-----------------------------------------------------
            if (NumTrgtAreas > 0) { chkbox2P.Visible = true; } else { chkbox2P.Visible = false; }

            //Evaluates if Fourth Step is completed-----------------------------------------------------
            int Blobs = storeBlobRectangles[index].Count;
            if (Blobs > 0 && Blobs == storeTargetAreas[index].Count) { chkbox3P.Visible = true; }
            else { chkbox3P.Visible = false; }

            //Evaluat if the Fifth step is completed-----------------------------------------------------
            EvaluateStep5Completion();

            //Shows a predefined Threshold value--------------------------------------------------------
            if (ThresValueNum[index] == 300) { ThresValue.Text = ""; }
            else
            {
                ThresValue.Text = ThresValueNum[index].ToString();
                ThresTrackBar.Value = ThresValueNum[index];
            }            

            //Fill PartTrgtComboBox
            PartTrgtComboBox.Items.Clear();
            for (int i = 0; i < storeTargetAreas[index].Count; i++)
            {
                PartTrgtComboBox.Items.Add(i + 1);
            }
            if (storeTargetAreas[index].Count > 0) { PartTrgtComboBox.SelectedIndex = 0; }

            //Displays calculated Max Striation thickness
            if (PartTrgtComboBox.Text != "")
            {
                int trgt = PartTrgtComboBox.SelectedIndex;

                if (MaximumStriationThickness[index].Count > 0)
                {
                    if (MaximumStriationThickness[index][trgt] > 0)
                    {
                        MaxStriationLabel.Text = "Maximum striation thickness: " + MaximumStriationThickness[index][trgt] + " pixels";
                    }
                    else { MaxStriationLabel.Text = "Maximum striation thickness: "; }

                }
                else { MaxStriationLabel.Text = "Maximum striation thickness: "; }
            }
            else { MaxStriationLabel.Text = "Maximum striation thickness: "; }

            #endregion
            
            //Show "Image processing filters Tab"------------------------------------------------------
            if (tabControl1.TabPages.Contains(ProcessImageTab) == false && ImagetoProcess.Length > 0) //Evaluates if tab was already shown
            { tabControl1.TabPages.Add(ProcessImageTab); }

            //Show "File Properties" Tab and Fill information------------------------------------------
            if (tabControl1.TabPages.Contains(FilepropertiesTab) == false && ImagetoProcess.Length > 0) //Evaluates if tab was already shown
            { tabControl1.TabPages.Add(FilepropertiesTab); } //Show File properties tab
            this.FilePropLabelTipo.Text = "File Type: " + LoadedImageInfo[index][1];
            this.TextBoxUbicacion.Text = LoadedImageInfo[index][2];
            this.labelPixelFormat.Text= "Pixel Format: " + LoadedImageInfo[index][3];
            this.FilePropLabelTam.Text = "Size: " + ImagetoProcess[index].Width + " x " + ImagetoProcess[index].Height + " pixels";

            //Hide Tabs if there is no Image Loaded----------------------------------------------------
            if (ImagetoProcess.Length == 0)
            {
                tabControl1.TabPages.Remove(FilepropertiesTab);
                tabControl1.TabPages.Remove(TrgtAreaMixDimTab);
                tabControl1.TabPages.Remove(MixindDataPlotsTab);
                tabControl1.TabPages.Remove(ProcessImageTab);
            }

        }

        private void FillTargetCombobox(int Image_index)
        {
            int Numtrg = storeTargetAreas[Image_index].Count();

            comboBox1.Items.Clear();
            for (int i = 1; i <= Numtrg; i++)
            {
                comboBox1.Items.Add(i);
            }
            if (Numtrg >0) { comboBox1.Text=(Numtrg).ToString(); } else { comboBox1.SelectedItem = 0; }
        }

        private void FillImgTrgtCombobox()
        {
            int numImgs = tabControl3.TabCount;
            if (numImgs > 0)
            {
                ImgTrgtCombobox.Items.Clear();
                ImgTrgtCombobox2.Items.Clear();

                for (int i = 0; i < numImgs; i++)
                {
                    ImgTrgtCombobox.Items.Add(tabControl3.TabPages[i].Text);
                    ImgTrgtCombobox2.Items.Add(tabControl3.TabPages[i].Text);
                }
            }
        }

        #endregion

        #endregion

        #region Form Behaviour particle tracking

        private void ImgTrgtCombobox2_SelectedIndexChanged(object sender, EventArgs e)
        {
            ImgTrgtCombobox.SelectedIndex = ImgTrgtCombobox2.SelectedIndex;
        }

        private void MaxBlobSize_Leave(object sender, EventArgs e)
        {
            if (MaxBlobSize.Text.All(char.IsDigit) && MaxBlobSize.Text != "")
            {
                int max = Convert.ToInt32(MaxBlobSize.Text);
                int min = Convert.ToInt32(MinBlobSize.Text);
                if (min > max) { MaxBlobSize.Text = (Convert.ToInt32(MinBlobSize.Text) + 5).ToString(); }
            }
            else { MaxBlobSize.Text = (Convert.ToInt32(MinBlobSize.Text) + 20).ToString(); }
        }

        private void MinBlobSize_Leave(object sender, EventArgs e)
        {
            if (MinBlobSize.Text.All(char.IsDigit) && MinBlobSize.Text != "")
            {
                int max = Convert.ToInt32(MaxBlobSize.Text);
                int min = Convert.ToInt32(MinBlobSize.Text);
                if (min > max) { MinBlobSize.Text = (Convert.ToInt32(MaxBlobSize.Text) - 1).ToString(); }
            }
            else { MinBlobSize.Text = (Convert.ToInt32(MaxBlobSize.Text) - 1).ToString(); }

        }

        private void ImgTrgtCombobox3_SelectedIndexChanged(object sender, EventArgs e)
        {
            TrgtCombobox.Items.Clear();
            int numtrgts = storeConcentrationData[ImgTrgtCombobox3.SelectedIndex].Count;

            if (numtrgts > 0)
            {
                for (int i = 0; i < numtrgts; i++)
                {
                    TrgtCombobox.Items.Add(i + 1);
                }
            }
            else
            {
                TrgtCombobox.Text = "";
            }
            if (numtrgts > 0) { TrgtCombobox.SelectedIndex = 0; }
        }

        private void ImgTrgtCombobox4_SelectedIndexChanged(object sender, EventArgs e)
        {
            TrgtCombobox2.Items.Clear();
            int numtrgts = storeConcentrationData[ImgTrgtCombobox4.SelectedIndex].Count;

            if (numtrgts > 0)
            {
                for (int i = 0; i < numtrgts; i++)
                {
                    TrgtCombobox2.Items.Add(i + 1);
                }
            }
            else
            {
                TrgtCombobox2.Text = "";
            }
            if (numtrgts > 0) { TrgtCombobox2.SelectedIndex = 0; }

        }

        private void HorizontalCheckBox_CheckedChanged(object sender, EventArgs e)
        {
            if (HorizontalCheckBox.Checked == true) { VerticalCheckBox.Checked = false; }
            else { VerticalCheckBox.Checked = true; }
        }

        private void VerticalCheckBox_CheckedChanged(object sender, EventArgs e)
        {
            if (VerticalCheckBox.Checked == true) { HorizontalCheckBox.Checked = false; }
            else { HorizontalCheckBox.Checked = true; }
        }

        #endregion

        #region Step 4: Partclie tracking

        private void OtsuThreshold_buttom_Click(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                Image1 = ImagetoProcess[index];
                Bitmap Image2;
                OtsuThreshold filter = new OtsuThreshold();
                if (Image1.PixelFormat == PixelFormat.Format8bppIndexed || Image1.PixelFormat == PixelFormat.Format16bppGrayScale)
                {
                    Image2 = filter.Apply(Image1);
                }
                else
                {
                    Image2 = filter.Apply(new Grayscale(0.2125, 0.7154, 0.0721).Apply(Image1));
                }
                ThresValue.Text = filter.ThresholdValue.ToString();
                pictureBox1.Image = Image2;
                ImgBinarization.Text = "Show unfiltered img";
                ThresValueNum[index] = filter.ThresholdValue;
                ThresTrackBar.Value = filter.ThresholdValue;
                pictureBox2.Refresh();
                DrawRectangles(index);
            }
            
        }

        private void ImgBinarization_Click(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;

            if (index >= 0)
            {

                if (ThresValue.Text == "" && ImgBinarization.Text == "Show filtered img")
                {
                    OtsuThreshold_buttom.PerformClick();
                }
                else
                {
                    if (ImgBinarization.Text == "Show unfiltered img")
                    {
                        pictureBox1.Image = ImagetoProcess[index];
                        ImgBinarization.Text = "Show filtered img";
                    }
                    else
                    {
                        if (ThresValue.Text.All(char.IsDigit) && ThresValue.Text != "")
                        {
                            bool cnd = false;
                            int Thres = Convert.ToInt32(ThresValue.Text);
                            if (Thres >= 0 && Thres <= 255) { cnd = true; }

                            if (ImgBinarization.Text == "Show filtered img" && cnd)
                            {
                                Image1 = ImagetoProcess[index];
                                Bitmap Image2;
                                if (Image1.PixelFormat == PixelFormat.Format8bppIndexed || Image1.PixelFormat == PixelFormat.Format16bppGrayScale)
                                {
                                    Image2 = new Threshold((int)ThresTrackBar.Value).Apply(Image1);
                                }
                                else
                                {
                                    Image2 = new Threshold((int)ThresTrackBar.Value).Apply(new Grayscale(0.2125, 0.7154, 0.0721).Apply(Image1));
                                }
                                pictureBox1.Image = Image2;
                                ImgBinarization.Text = "Show unfiltered img";
                            }
                        }
                        else { MessageBox.Show("Please insert an interger between 0 and 255"); }
                    }

                }
                pictureBox2.Refresh();
                DrawRectangles(index);
            }          

        }

        private void ThresTrackBar_Scroll(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                Image1 = ImagetoProcess[index];
                Bitmap Image2;
                if (Image1.PixelFormat == PixelFormat.Format8bppIndexed || Image1.PixelFormat == PixelFormat.Format16bppGrayScale)
                {
                    Image2 = new Threshold((int)ThresTrackBar.Value).Apply(Image1);
                }
                else
                {
                    Image2 = new Threshold((int)ThresTrackBar.Value).Apply(new Grayscale(0.2125, 0.7154, 0.0721).Apply(Image1));
                }
                pictureBox1.Image = Image2;
                if (ImgBinarization.Text == "Show filtered img") { ImgBinarization.Text = "Show unfiltered img"; }

                ThresValue.Text = ThresTrackBar.Value.ToString();
                ThresValueNum[index] = ThresTrackBar.Value;
                pictureBox2.Refresh();
                DrawRectangles(index);
            }
            

        }

        private void ThresValue_TextChanged(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;

            if (index >= 0 && ThresValue.Text.All(char.IsDigit) && ThresValue.Text != "")
            {
                int Thres = Convert.ToInt32(ThresValue.Text);
                if (Thres >= 0 && Thres <= 255)
                {
                    ThresTrackBar.Value = Thres;
                    Image1 = ImagetoProcess[index];
                    Bitmap Image2;
                    if (Image1.PixelFormat == PixelFormat.Format8bppIndexed || Image1.PixelFormat == PixelFormat.Format16bppGrayScale)
                    {
                        Image2 = new Threshold((int)ThresTrackBar.Value).Apply(Image1);
                    }
                    else
                    {
                        Image2 = new Threshold((int)ThresTrackBar.Value).Apply(new Grayscale(0.2125, 0.7154, 0.0721).Apply(Image1));
                    }
                    pictureBox1.Image = Image2;
                    if (ImgBinarization.Text == "Show filtered img") { ImgBinarization.Text = "Show unfiltered img"; }

                    ThresValueNum[index] = ThresTrackBar.Value;
                }
                else { MessageBox.Show("Please insert an interger between 0 and 255"); }
                pictureBox2.Refresh();
                DrawRectangles(index);
            }
            
        }
        
        private void BlobDetection_Click(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                int count = storeBlobRectangles[index].Count;

                if (count > 0)
                {
                    RefreshPictureBox2();
                }
                else { MessageBox.Show("Please perform the calculation for the blob detection"); }
                
            }
            
        }

        private void ComputeBlobButton_Click(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                if (storeTargetAreas[index].Count > 0)
                {
                    if (ThresValue.Text!="")
                    {
                        Blobdetectionimage();
                        UpdateInformation(index);
                        DrawBlobs(index);
                    }
                    else { MessageBox.Show("Please define a threshold value"); }

                }
                else { MessageBox.Show("No inlets have been defined for this image"); }
            }
        }

        private void Blobdetectionimage()
        {
            int index = tabControl3.SelectedIndex;
            storeBlobRectangles[index].Clear();
            storePartPositions[index].Clear();
            //Multiple object detection----------------------------------------------------------

            BlobCounter blobCounter = new BlobCounter();

            
            //Define minimum and maximum particle size to detect
            blobCounter.MinWidth = Convert.ToInt32(MinBlobSize.Text);
            blobCounter.MinHeight = Convert.ToInt32(MinBlobSize.Text);
            blobCounter.MaxWidth = Convert.ToInt32(MaxBlobSize.Text);
            blobCounter.MaxHeight = Convert.ToInt32(MaxBlobSize.Text);
            blobCounter.FilterBlobs = true;
            //Here we define how to order particles
            blobCounter.ObjectsOrder = ObjectsOrder.Size;


            //Filter IMAGE---------------------------------------------------------------------
            Bitmap FilteredImage = ImagetoProcess[index].Clone(
                new Rectangle(0, 0, ImagetoProcess[index].Width,
                ImagetoProcess[index].Height), PixelFormat.Format32bppRgb);
            
            //Apply Mean Filter (to eliminate local noise)
            //Median medianfilter = new Median();
            //medianfilter.Size = 3;
            //FilteredImage = medianfilter.Apply(FilteredImage);
            //Grayscale filter
            FilteredImage = new Grayscale(0.2125, 0.7154, 0.0721).Apply(FilteredImage);
            //ApplyThreshold
            FilteredImage = new Threshold((int)ThresTrackBar.Value).Apply(FilteredImage);

            

            //Perform Blob detection
            blobCounter.ProcessImage(FilteredImage);
            Rectangle[] rects = blobCounter.GetObjectsRectangles();
            Blob[] blobs = blobCounter.GetObjectsInformation();

            List<List<Rectangle>> AssignBlobToTarget = new List<List<Rectangle>>();
            List<List<Point>> AssignPartCoordToTarget = new List<List<Point>>();

            foreach (var item in storeTargetAreas[index])
            {
                AssignBlobToTarget.Add(new List<Rectangle>());
                AssignPartCoordToTarget.Add(new List<Point>());
            }

            //Store Rectangles and Particles positions
            foreach (var rect in rects)
            {
                Point PartCoord = new Point();
                PartCoord.X = rect.X + ((int)rect.Width / 2);
                PartCoord.Y = rect.Y + ((int)rect.Height / 2);
                int Targt = FindTargetAreaforBlob(PartCoord.X, PartCoord.Y);

                if (Targt >= 0)
                {
                    AssignBlobToTarget[Targt].Add(rect);
                    AssignPartCoordToTarget[Targt].Add(PartCoord);
                }                
            }

            int j = 0;
            foreach (var Trgt in AssignBlobToTarget)
            {
                Rectangle[] rectarray = new Rectangle[Trgt.Count];
                Point[] pointarray = new Point[Trgt.Count]; 
                int i = 0;
                foreach (var rect in Trgt)
                {
                    rectarray[i] = rect;
                    pointarray[i] = AssignPartCoordToTarget[j][i];
                    i++;
                }
                storeBlobRectangles[index].Add(rectarray);
                storePartPositions[index].Add(pointarray);
                j++;
            }

        }

        private int FindTargetAreaforBlob(int X, int Y)
        {
            int index = tabControl3.SelectedIndex;
            int TargetAreaNumber = -1;

            if (storeTargetAreas[index].Count > 0)
            {
                for (int i = 0; i < storeTargetAreas[index].Count; i++)
                {
                    int X1 = storeTargetAreas[index][i].X;
                    int X2 = X1 + storeTargetAreas[index][i].Width - 1;
                    int Y1 = storeTargetAreas[index][i].Y;
                    int Y2 = Y1 + storeTargetAreas[index][i].Height - 1;

                    if (X1 <= X && X2 >= X && Y1 <= Y && Y2 >= Y)
                    {
                        TargetAreaNumber = i;
                        break;
                    }
                }

            }
            return TargetAreaNumber;
        }

        #endregion

        #region Particle Functions

        private int CalculateMeanSpacing(int Image_index, int Trgt)
        {
            int MeanSpa = 0;

            foreach (var point in storePartPositions[Image_index][Trgt])
            {
                double s = Math.Pow(ImagetoProcess[Image_index].Width, 2) + Math.Pow(ImagetoProcess[Image_index].Height, 2);
                int MeanS = (int)Math.Sqrt(s);
                foreach (var pointeval in storePartPositions[Image_index][Trgt])
                {
                    if (point != pointeval)
                    {
                        s = Math.Pow(point.X - pointeval.X, 2) + Math.Pow(point.Y - pointeval.Y, 2);
                        int dist = (int)Math.Sqrt(s);
                        if (dist < MeanS) { MeanS = dist; }
                    }
                }
                MeanSpa = MeanSpa + MeanS;
            }

            MeanSpa = (int)MeanSpa / storePartPositions[Image_index][Trgt].Length;

            return MeanSpa*2;
        }

        private int CalculateMaxStrThickness(int Image_index, int Trgt, int MPartSpacing)
        {
            int MST = 0;
            bool Horizontal = true;
            //Evaluate if is Horizontal or Vertical
            if (DefinedTransects[Image_index][Trgt].Height == storeTargetAreas[Image_index][Trgt].Height)
            {
                Horizontal = false;
            }

            int[] array = new int[0];
            int i = 0;
            int j = 0;
            foreach (var item in storePartPositions[Image_index][Trgt])
            {
                int X1 = DefinedTransects[Image_index][Trgt].X;
                int X2 = X1 + DefinedTransects[Image_index][Trgt].Width - 1;
                int Y1 = DefinedTransects[Image_index][Trgt].Y;
                int Y2 = Y1 + DefinedTransects[Image_index][Trgt].Height - 1;

                if (X1 <= item.X && X2 >= item.X && Y1 <= item.Y && Y2 >= item.Y)
                {
                    Array.Resize(ref array, array.Length + 1);//Adds one more space into the array
                    if (Horizontal) { array[j] = item.X; }
                    if (!Horizontal) { array[j] = item.Y; }
                    j++;
                }
                i++;
            }

            if (array.Length > 1)
            {
                Array.Sort(array);
                MST = 0;
                int start = array[0];
                for (i = 1; i < array.Length; i++)
                {
                    int Striation = array[i] - array[i - 1];

                    if (Striation > MPartSpacing)
                    {
                        if (array[i - 1] - start > MST)
                        {
                            MST = array[i - 1] - start;
                        }
                        start = array[i];
                    }

                    if (i == array.Length - 1)
                    {
                        if (array[i] - start > MST)
                        {
                            MST = array[i] - start;
                        }
                    }

                }
                if (MST < MPartSpacing) { MST = MPartSpacing; }
            }
            else { MST = MPartSpacing; }

            return MST;
        }

        private void DrawBlobs(int Image_index)
        {
            using (Graphics g = pictureBox2.CreateGraphics())
            {
                var pen = new Pen(Color.Red, 1);

                foreach (var RectArray in storeBlobRectangles[Image_index])
                {
                    foreach (var area in RectArray)
                    {
                        //The rectangles are converted to picturebox2 size
                        double[] factors = ConversionFactors(Image_index);
                        int X = (int)((area.X / factors[2]) + factors[0]);
                        int Y = (int)((area.Y / factors[2]) + factors[1]);
                        int width = (int)(area.Width / factors[2]);
                        int height = (int)(area.Height / factors[2]);
                        if (width < 3) { width = 3; }
                        if (height < 3) { height = 3; }

                        Rectangle modfarea = new Rectangle(X, Y, width, height);

                        //Here the rectangle is drawn using the converted coordinates from the previous function
                        g.DrawRectangle(pen, modfarea);
                    }

                }

                pen.Dispose();
            }
        }

        private void DrawTransect()
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                for (int trgt = 0; trgt < DefinedTransects[index].Count; trgt++)
                {
                    int Xtrans = DefinedTransects[index][trgt].X;
                    int Ytrans = DefinedTransects[index][trgt].Y;
                    int width = DefinedTransects[index][trgt].Width;
                    int height = DefinedTransects[index][trgt].Height;

                    //show Image dimensions
                    double[] factors = ConversionFactors(index);

                    //Define the transect rectangle to plot
                    Ytrans = (int)((Ytrans / factors[2]) + factors[1]);
                    Xtrans = (int)((Xtrans / factors[2]) + factors[0]);
                    width = (int)(width / factors[2]);
                    height = (int)(height / factors[2]);

                    Rectangle DrawTrans = new Rectangle(Xtrans, Ytrans, width, height);
                    SolidBrush semiTransBrush = new SolidBrush(ContourColorbutton2.BackColor);
                    //Draw Transect
                    using (Graphics g = pictureBox2.CreateGraphics())
                    {
                        g.FillRectangle(Brushes.Lime, DrawTrans);
                        g.CompositingMode = CompositingMode.SourceCopy;
                        g.FillRectangle(semiTransBrush, DrawTrans);
                    }
                }
            }            
            
        }

        private void EvaluateStep5Completion()
        {
            int index = tabControl3.SelectedIndex;
            bool complet = true;
            if (DefinedTransects[index].Count < storeTargetAreas[index].Count) { complet = false; }
            else
            {
                foreach (var rect in DefinedTransects[index])
                {
                    if (rect.Width == 0) { complet = false; break; }
                }
            }

            if (complet && storeTargetAreas[index].Count > 0) { chkbox4P.Visible = true; }
            else { chkbox4P.Visible = false; }
        }

        private void EraseTransectInfo(int Target)
        {
            int index = tabControl3.SelectedIndex;
            if (DefinedTransects[index].Count > Target)
            {
                DefinedTransects[index].RemoveAt(Target);
                MeanSpacingParticles[index].RemoveAt(Target);
                MaximumStriationThickness[index].RemoveAt(Target);
            }
            
            
        }

        private void ManualTransect_Click(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                if (storeTargetAreas[index].Count > 0)
                {
                    if (chkbox3P.Visible)
                    {
                        if (ReadMouseClick) { ReadMouseClick = false; }//Cancels the process of defining new target area
                        if (DefineInletProcess) { DefineInletProcess = false; }//Cancels the process of setting inlets
                        if (ErasingTrgt) { ErasingTrgt = false; } // Cancels Transect deffinition
                        if (MaxStrTrgtSel) { MaxStrTrgtSel = false; } //Cancels Transect deffinition

                        MaxStrTrgtSel = true;
                        Cursor = Cursors.Hand;
                        //bool MaxStrTransSel = false;
                        MessageBox.Show("Select the inlet to calculate");
                    }
                    else { MessageBox.Show("Please perform the previous step first"); MaxStrTrgtSel = false; Cursor = Cursors.Arrow; }
                }
                else { MessageBox.Show("No inlets have been defined for this image"); MaxStrTrgtSel = false; Cursor = Cursors.Arrow; }
            }
        }

        private void PartTrgtComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                if (PartTrgtComboBox.Text != "")
                {
                    int trgt = PartTrgtComboBox.SelectedIndex;
                    DimAreaTextBox2.Text = storeTargetAreas[index][trgt].Width + "x" +
                        storeTargetAreas[index][trgt].Height;

                    if (MaximumStriationThickness[index].Count > 0)
                    {
                        if (MaximumStriationThickness[index][trgt] > 0)
                        {
                            MaxStriationLabel.Text = "Maximum striation thickness: " + MaximumStriationThickness[index][trgt] + " pixels";
                        }

                    }

                }
            }

        }

        private void ShowTransectButton_Click(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                RefreshPictureBox2();
                DrawTransect();
            }

        }

        private void AutoDefineTransectButton_Click(object sender, EventArgs e)
        {
            int index = tabControl3.SelectedIndex;
            if (index >= 0)
            {
                if (storeTargetAreas[index].Count > 0)
                {
                    if (chkbox3P.Visible)
                    {
                        if (MessageBox.Show("All previously defined transects will be deleted!" + "\n" +
                                "Would you like to continue?", "Confirm", MessageBoxButtons.YesNo, 
                                MessageBoxIcon.Question) == DialogResult.Yes)
                        {
                            DefinedTransects[index].Clear();
                            MeanSpacingParticles[index].Clear();
                            MaximumStriationThickness[index].Clear();

                            for (int i = 0; i < storeTargetAreas[index].Count; i++)
                            {
                                int MST = 0;
                                int MS = CalculateMeanSpacing(index, i);
                                MeanSpacingParticles[index].Add(MS);

                                //Define new Rectangle Transect for the assessed target
                                Rectangle RectT = new Rectangle();
                                DefinedTransects[index].Add(RectT);

                                //Evaluate for all the transect positions posible
                                int X = storeTargetAreas[index][i].X;
                                int Y = storeTargetAreas[index][i].Y;
                                int width = 0;
                                int height = 0;
                                int ini = 0;
                                int limit = 0;
                                if (HorizontalCheckBox.Checked)
                                {                                    
                                    height = MS;
                                    width = storeTargetAreas[index][i].Width;
                                    ini = Y;
                                    limit = Y + storeTargetAreas[index][i].Height - 1 - MS;                           
                                }
                                if (VerticalCheckBox.Checked)
                                {
                                    height = storeTargetAreas[index][i].Height; 
                                    width = MS;
                                    ini = X;
                                    limit = X + storeTargetAreas[index][i].Width - 1 - MS;
                                }

                                MST = MS;
                                for (int j = ini; j < limit; j++)
                                {
                                    if (HorizontalCheckBox.Checked) { DefinedTransects[index][i] = new Rectangle(X, j, width, height); }
                                    if (VerticalCheckBox.Checked) { DefinedTransects[index][i] = new Rectangle(j, Y, width, height); }

                                    int MSTeval = CalculateMaxStrThickness(index, i, MS);
                                    if (MSTeval > MST)
                                    {
                                        MST = MSTeval;
                                        if (HorizontalCheckBox.Checked) { RectT = new Rectangle(X, j, width, height); }
                                        if (VerticalCheckBox.Checked) { RectT = new Rectangle(j, Y, width, height); }
                                    }
                                }
                                DefinedTransects[index][i] = RectT;
                                MaximumStriationThickness[index].Add(MST);
                            }                            
                            UpdateInformation(index);
                            DrawTransect();
                        }
                    }
                    else { MessageBox.Show("Please perform the previous step first"); MaxStrTrgtSel = false; Cursor = Cursors.Arrow; }
                }
                else { MessageBox.Show("No inlets have been defined for this image"); MaxStrTrgtSel = false; Cursor = Cursors.Arrow; }
            }
            
        }

        private void CalculatePartButton_Click(object sender, EventArgs e)
        {
            //Evaluate if all the Targets have Computed their Maximum striation thickness
            #region Evaluate Step 5 completion for all targets
            bool complet = true;

            int i = 0;
            foreach (var list in DefinedTransects)
            {
                if (list.Count < storeTargetAreas[i].Count) { complet = false; break; }
                else
                {
                    foreach (var rect in list)
                    {
                        if (rect.Width == 0) { complet = false; break; }
                    }
                }
                if (!complet) { break; }
                i++;
            }
            #endregion

            if (complet && ImagetoProcess.Length > 0)
            {
                //Show "Mixing Measures Tab" and Fills Dimensions------------------------------------------
                if (!tabControl1.TabPages.Contains(PartMixDimTab))
                { tabControl1.TabPages.Insert(0, PartMixDimTab); }

                //Show "Mixing Dta Plots Tab" -------------------------------------------------------------
                if (!tabControl1.TabPages.Contains(MixPlotsPartData)) //Evaluates if tab was already shown
                { tabControl1.TabPages.Insert(1, MixPlotsPartData); }

                //Hide "Particle Mixing Dimensions Tab if showed--------------------------------------------------
                if (tabControl1.TabPages.Contains(TrgtAreaMixDimTab)) //Evaluates if tab was already shown
                { tabControl1.TabPages.Remove(TrgtAreaMixDimTab); }

                //Hide "Mixind Plots for Particle Data"-----------------------------------------------------------
                if (tabControl1.TabPages.Contains(MixindDataPlotsTab)) //Evaluates if tab was already shown
                { tabControl1.TabPages.Remove(MixindDataPlotsTab); }

                CalculateMixingDimpParticledata(); //Calculate particle data mixing dimensions
                FillImgPartCombobox();
                ImgPartCombobox.SelectedIndex = 0;
                ImgPartCombobox2.SelectedIndex = 0;
                tabControl1.SelectedIndex = 0;
                
            }
            else { MessageBox.Show("Please complete the previous steps"); }
        }

        private void DrawGridPoints() //Se asume que todos las partículas presentes ya fueron detectadas
        {
            int index = tabControl3.SelectedIndex;
            int i = 0;
            foreach (var item in storeTargetAreas[index])
            {
                int NumofPart = storePartPositions[index][i].Length;
                //MessageBox.Show(NumofPart.ToString());
                Point[] PartPos = IdealParticlePosition(item, NumofPart);

                using (Graphics g = pictureBox2.CreateGraphics())
                {
                    var pen = new Pen(Color.Red, 1);

                    foreach (var point in PartPos)
                    {
                        //The rectangles are converted to picturebox2 size
                        double[] factors = ConversionFactors(index);
                        int X = (int)((point.X / factors[2]) + factors[0])-2;
                        int Y = (int)((point.Y / factors[2]) + factors[1])-2;
                        int width = 4;
                        int height = 4;

                        Rectangle modfarea = new Rectangle(X, Y, width, height);

                        //Here the rectangle is drawn using the converted coordinates from the previous function
                        g.DrawRectangle(pen, modfarea);
                    }

                    pen.Dispose();
                }
                i++;
            }
        }

        #endregion

        #region Displaying Results 

        #region Concentration Data

            #region Mixing measures tab

        private void TrgtCombobox_SelectedIndexChanged(object sender, EventArgs e)
        {
            //Show Dimensions
            if (TrgtCombobox.Text != "") // Shows the area and info of the target selected
            {
                int index = ImgTrgtCombobox3.SelectedIndex;
                int Trgt = TrgtCombobox.SelectedIndex;
                TrgtDimensionTextBox.Text = storeConcentrationData[index][Trgt].GetLength(0).ToString() + "x" +
                    storeConcentrationData[index][Trgt].GetLength(1).ToString();
                TargetAreaDisplay2(index);//Displays the target image in TargetPicBox
                ShowMeasures();
            }
            else { TrgtDimensionTextBox.Text = ""; TargetPicBox2.Image = null; }

        }               

        private void TargetAreaDisplay2(int Image_index)
        {
            Rectangle cropArea = storeTargetAreas2[Image_index][TrgtCombobox.SelectedIndex];
            Bitmap bmpImage = new Bitmap(ImagetoProcess2[Image_index]);
            TargetPicBox2.Image = bmpImage.Clone(cropArea, bmpImage.PixelFormat);
        }               

        private void ShowMeasures()
        {

            int index= ImgTrgtCombobox3.SelectedIndex;

            if (TrgtCombobox.Text != "")
            {
                int trgt = TrgtCombobox.SelectedIndex;
                SDtxtbox.Text = Math.Round(IntensityMeasures[index][trgt][0], 4).ToString();
                CoVtxtbox.Text = Math.Round(IntensityMeasures[index][trgt][1], 4).ToString();
                MItxtbox.Text = Math.Round(IntensityMeasures[index][trgt][2], 4).ToString();
                Lhtxtbox.Text = Math.Round(MeanLengthScales[index][trgt].X, 4).ToString();
                Lvtxtbox.Text = Math.Round(MeanLengthScales[index][trgt].Y, 4).ToString();
                Etxtbox.Text = Math.Round(ExposureIndexes[index][trgt], 4).ToString();
                Cmtxtbox.Text = Math.Round(IntensityMeasures[index][trgt][3], 4).ToString();
                Cmaxtxtbox.Text = Math.Round(IntensityMeasures[index][trgt][4], 4).ToString();
                Cmintxtbox.Text = Math.Round(IntensityMeasures[index][trgt][5], 4).ToString();
                Ntxtbox.Text = IntensityMeasures[index][trgt][6].ToString();
            }
            else
            {
                SDtxtbox.Text = "";
                CoVtxtbox.Text = "";
                MItxtbox.Text = "";
                Lhtxtbox.Text = "";
                Lvtxtbox.Text = "";
                Etxtbox.Text = "";
                Cmtxtbox.Text = "";
                Cmaxtxtbox.Text = "";
                Cmintxtbox.Text = "";
                Ntxtbox.Text = "";
            }
            
        }
        
        private void FillImgCombobox3()
        {
            ImgTrgtCombobox3.Items.Clear();
            ImgTrgtCombobox4.Items.Clear();
            for (int i = 0; i < storeConcentrationData.Count; i++)
            {
                ImgTrgtCombobox3.Items.Add(LoadedImageInfo[i][0]);
                ImgTrgtCombobox4.Items.Add(LoadedImageInfo[i][0]);
            }
        }

        #endregion

            #region Plot Mixing Data tab

        private void TrgtCombobox2_SelectedIndexChanged(object sender, EventArgs e)
        {
            //Show Dimensions
            if (TrgtCombobox2.Text != "") // Shows the area and info of the target selected
            {
                int index = ImgTrgtCombobox4.SelectedIndex;
                int Trgt = TrgtCombobox2.SelectedIndex;
                TrgtDimensionTextBox2.Text = storeConcentrationData[index][Trgt].GetLength(0).ToString() + "x" +
                    storeConcentrationData[index][Trgt].GetLength(1).ToString();
                TargetAreaDisplay3(index);//Displays the target image in TargetPicBox
            }
            else { TrgtDimensionTextBox.Text = ""; TargetPicBox2.Image = null; }
        }

        private void TargetAreaDisplay3(int Image_index)
        {
            Rectangle cropArea = storeTargetAreas2[Image_index][TrgtCombobox2.SelectedIndex];
            Bitmap bmpImage = new Bitmap(ImagetoProcess2[Image_index]);
            TargetPicBox3.Image = bmpImage.Clone(cropArea, bmpImage.PixelFormat);
        }

        private void PlotDimensions_Click(object sender, EventArgs e)
        {
            if (DimensionsComboBox.Text != "")
            {
                PlotSelectedDimension(DimensionsComboBox.SelectedIndex);
            }            
        }

        private void PlotHorVariogram_Click(object sender, EventArgs e)
        {
            if (TrgtCombobox2.Text != "")
            {
                PlotVariogram(1);
            }
            else { MessageBox.Show("There are no target areas to plot"); }
        }

        private void PlotVertVariogram_Click(object sender, EventArgs e)
        {
            if (TrgtCombobox2.Text != "")
            {
                PlotVariogram(2);
            }
            else { MessageBox.Show("There are no target areas to plot"); }
        }
        
        private void PlotIntHistogram_Click(object sender, EventArgs e)
        {
            if (TrgtCombobox2.Text != "")
            {
                PlotIntensityHistogram(1);
            }
            else { MessageBox.Show("There are no target areas to plot"); }
        }

        private void button1_Click(object sender, EventArgs e)
        {
            if (TrgtCombobox2.Text != "")
            {
                PlotIntensityHistogram(2);
            }
            else { MessageBox.Show("There are no target areas to plot"); }
        }

        #endregion
        
            #region Plot Data

        private void ClearChartDataPoints()
        {
            for (int a = 0; a < MixingPlotChart.Series.Count; a++)
            {
                //Clears all the Data Points added to the chart Series
                MixingPlotChart.Series[a].Points.Clear();
            }
            for (int a = 0; a < MixingPlotChart.ChartAreas.Count; a++)
            {
                //Clears all the configuration of the Chart Areas
                MixingPlotChart.ChartAreas[a].AxisX.Minimum = Double.NaN;
                MixingPlotChart.ChartAreas[a].AxisX.Maximum = Double.NaN;
                MixingPlotChart.ChartAreas[a].AxisY.StripLines.Clear();
                MixingPlotChart.Titles["Mixing dimension"].Text = "";
                MixingPlotChart.ChartAreas[0].AxisX.TitleFont = new Font("Times New Roman", 10);
                MixingPlotChart.ChartAreas[0].AxisX.Title = "";
                MixingPlotChart.ChartAreas[0].AxisY.TitleFont = new Font("Times New Roman", 10);
                MixingPlotChart.ChartAreas[0].AxisY.Title = "";
            }

        }

        private void PlotSelectedDimension(int sel)
        {
            List<List<double>> PlotInfo = new List<List<double>>();
            PlotInfo.Clear();

            //Intensity measures
            if (sel < 3 || sel >5)
            {
                int k = 0;
                foreach (var list in IntensityMeasures)
                {
                    PlotInfo.Add(new List<double>());
                    foreach (var item in list)
                    {
                        if (sel < 3) { PlotInfo[k].Add(item[sel]); }
                        if (sel > 5) { PlotInfo[k].Add(item[sel-3]); }
                    }
                    k++;
                }
            }

            //Scale measures
            if (sel == 3 || sel == 4)
            {
                int k = 0;
                foreach (var list in MeanLengthScales)
                {
                    PlotInfo.Add(new List<double>());
                    foreach (var item in list)
                    {
                        if (sel == 3) { PlotInfo[k].Add(item.X); }
                        if (sel == 4) { PlotInfo[k].Add(item.Y); }
                    }
                    k++;
                }
            }

            //Exposure
            if (sel == 5)
            {
                int k = 0;
                foreach (var list in ExposureIndexes)
                {
                    PlotInfo.Add(new List<double>());
                    foreach (var item in list)
                    {
                        PlotInfo[k].Add(item);
                    }
                    k++;
                }
            }


            ClearChartDataPoints();
            //MixingPlotChart.ChartAreas[0].AxisX.TitleAlignment = StringAlignment.Near;
            //MixingPlotChart.ChartAreas[0].AxisX.TextOrientation = TextOrientation.Horizontal;
            //Standard Deviation (σ)
            if (sel == 0)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Standard Deviation (σ)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "σ [v/v]";
            }
            //Coeff. of Variation (CoV)
            if (sel == 1)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Coeff. of Variation (CoV)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "CoV";
            }
            //Mixing Index (M)
            if (sel == 2)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Mixing Index (M)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "M";
            }
            //Mean Length Scale (Lh)
            if (sel == 3)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Mean Length Scale (Lh)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Lh [pixels]";
            }
            //Mean Length Scale (Lv)
            if (sel == 4)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Mean Length Scale (Lv)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Lv [pixels]";
            }
            //Exposure
            if (sel == 5)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Exposure (E)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "E [(v/v)*pixels*mm^2/s";
            }
            //Mean Concentration (Cm)
            if (sel == 6)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Mean Concentration (Cm)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Cm [v/v]";
            }
            //Max Concentration (Cmax)
            if (sel == 7)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Max Concentration (Cmax)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Cmax [v/v]";
            }
            //Min Concentration (Cmin)
            if (sel == 8)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Standard Deviation (σ)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Cmin [v/v]";
            }
            //Measured Points (N)
            if (sel == 9)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Measured Points (N)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "N";
            }
            
            //Plot Information
            MixingPlotChart.Series.Clear();
            int i = 0;
            foreach (var list in PlotInfo)
            {
                //Validate if there are no other image with the same name
                string name = LoadedImageInfo2[i][0];
                for (int f = 0; f < MixingPlotChart.Series.Count; f++)
                {
                    if (name == MixingPlotChart.Series[f].Name) { name = name + "_" + (f + 1); }
                }

                MixingPlotChart.Series.Add(name);
                int j = 0;
                foreach (var item in list)
                {
                    MixingPlotChart.Series[i].Points.AddXY("Target " + (j+1), item);
                    j++;             
                }
                i++;
            }
        }//Plots all calculated mixing measures

        private void PlotVariogram(int Horizontal_1_Vertical_2)
        {

            int TargetArea = TrgtCombobox2.SelectedIndex;
            int index = ImgTrgtCombobox4.SelectedIndex;
            if (TargetArea >= 0)
            {
                ClearChartDataPoints();//Clear Chart
               
                //Set minimun in X-axis--------------------------------------------------------------------------
                MixingPlotChart.ChartAreas[0].AxisX.Minimum = 0;

                //Define a strip line in Y axis------------------------------------------------------------------
                MixingPlotChart.ChartAreas[0].AxisY.StripLines.Add(new StripLine());
                //MixingPlotChart.ChartAreas[0].AxisY.StripLines[0].BackColor = Color.FromArgb(80, 252, 180, 65);
                MixingPlotChart.ChartAreas[0].AxisY.StripLines[0].BackColor = Color.Blue;
                MixingPlotChart.ChartAreas[0].AxisY.StripLines[0].StripWidth = 0.01;
                MixingPlotChart.ChartAreas[0].AxisY.StripLines[0].Interval = 1;
                MixingPlotChart.ChartAreas[0].AxisY.StripLines[0].IntervalOffset = 1;

                MixingPlotChart.Series.Clear();
                MixingPlotChart.Series.Add("Variograms");
                MixingPlotChart.Series["Variograms"].ChartType = SeriesChartType.Spline;

                int limit = 0;
                if (Horizontal_1_Vertical_2 == 1)
                {
                    MixingPlotChart.Titles["Mixing dimension"].Text = "Horizontal Variogram";
                    limit = HorizontalVariograms[index][TargetArea].Length;
                }

                if (Horizontal_1_Vertical_2 == 2)
                {
                    MixingPlotChart.Titles["Mixing dimension"].Text = "Vertical Variogram";
                    limit = VerticalVariograms[index][TargetArea].Length;
                }

                MixingPlotChart.ChartAreas[0].AxisX.Title = "Distance h [pixels]";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "γx(h)";
                //Plot Horizontal variogram----------------------------------------------------------------------
                for (int i = 0; i < limit; i++)
                {
                    if (Horizontal_1_Vertical_2 == 1)
                    { MixingPlotChart.Series["Variograms"].Points.AddXY(i, HorizontalVariograms[index][TargetArea][i]); }

                    if (Horizontal_1_Vertical_2 == 2)
                    { MixingPlotChart.Series["Variograms"].Points.AddXY(i, VerticalVariograms[index][TargetArea][i]); }
                }
            }


        }//Plot Horizontal Variogram from a target area
                
        private void PlotIntensityHistogram(int ForTarget_1_ForImage_2) {
            int TargetArea = TrgtCombobox2.SelectedIndex;
            int index = ImgTrgtCombobox4.SelectedIndex;
            if (TargetArea >= 0)
            {
                ClearChartDataPoints();//Clear Chart


                //Read intensity array from the requested target-------------------------------------------------
                double[,] data = GetIntensityArray(index, TargetArea); 
                if (ForTarget_1_ForImage_2 == 2) { data = FullImageDataArray(index); }
                

                //Define "Instensity Level vs Frequency" array---------------------------------------------------
                int[] IntFreq = new int[256];
                
                //Define histogram array-------------------------------------------------------------------------
                for (int I = 0; I <= 255; I++)
                {
                    int n = 0;//Number of pixels with an I intensity value
                    for (int xc = 0; xc < data.GetLength(0); xc++)
                    {
                        for (int yc = 0; yc < data.GetLength(1); yc++)
                        {
                            if (I == data[xc, yc]) { n = n + 1; }
                        }
                    }
                    IntFreq[I] = n;
                }
                //Plot Histogram---------------------------------------------------------------------------------
                
                //Set minimun and máximum  in X-axis--------------------------------------------------------------------------
                MixingPlotChart.ChartAreas[0].AxisX.Minimum = 0;
                MixingPlotChart.ChartAreas[0].AxisX.Maximum = 255;

                MixingPlotChart.Series.Clear();
                MixingPlotChart.Series.Add("Intensity distribution");
                if (ForTarget_1_ForImage_2 == 1)
                { MixingPlotChart.Titles["Mixing dimension"].Text = "Intensity histogram of target " + (TargetArea+1) + "from: " + LoadedImageInfo2[index][0]; }
                if (ForTarget_1_ForImage_2 == 2)
                { MixingPlotChart.Titles["Mixing dimension"].Text = "Intensity histogram of image: " + LoadedImageInfo2[index][0]; }
                MixingPlotChart.ChartAreas[0].AxisX.Title = "Intensity pixel value";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Frequency";


                for (int i = 0; i < IntFreq.Length; i++)
                {
                    MixingPlotChart.Series["Intensity distribution"].Points.AddXY(i, IntFreq[i]);
                    MixingPlotChart.Series["Intensity distribution"].XValueType = ChartValueType.Int32;
                    MixingPlotChart.ChartAreas[0].AxisX.Maximum = 255;
                }
            }

        }//Plot Intensity Vs Frequency Histogram       

                #endregion

        #endregion

        #region Particle Data

        private void FillImgPartCombobox()
        {
            ImgPartCombobox.Items.Clear();
            ImgPartCombobox2.Items.Clear();
            for (int i = 0; i < storeTargetAreas.Count; i++)
            {
                ImgPartCombobox.Items.Add(LoadedImageInfo[i][0]);
                ImgPartCombobox2.Items.Add(LoadedImageInfo[i][0]);
            }
        }

        private void ImgPartCombobox_SelectedIndexChanged(object sender, EventArgs e)
        {
            TrgtPartCombobox.Items.Clear();
            int numtrgts = storeTargetAreas2[ImgPartCombobox.SelectedIndex].Count;

            if (numtrgts > 0)
            {
                for (int i = 0; i < numtrgts; i++)
                {
                    TrgtPartCombobox.Items.Add(i + 1);
                }
            }
            else
            {
                TrgtPartCombobox.Text = "";
            }
            if (numtrgts > 0) { TrgtPartCombobox.SelectedIndex = 0; }
        }

        private void ImgPartCombobox2_SelectedIndexChanged(object sender, EventArgs e)
        {
            TrgtPartCombobox2.Items.Clear();
            int numtrgts = storeTargetAreas2[ImgPartCombobox2.SelectedIndex].Count;

            if (numtrgts > 0)
            {
                for (int i = 0; i < numtrgts; i++)
                {
                    TrgtPartCombobox2.Items.Add(i + 1);
                }
            }
            else
            {
                TrgtPartCombobox2.Text = "";
            }
            if (numtrgts > 0) { TrgtPartCombobox2.SelectedIndex = 0; }
        }

        private void TrgtPartCombobox2_SelectedIndexChanged(object sender, EventArgs e)
        {
            //Show Dimensions
            if (TrgtPartCombobox2.Text != "") // Shows the area and info of the target selected
            {
                int index = ImgPartCombobox2.SelectedIndex;
                int Trgt = TrgtPartCombobox2.SelectedIndex;
                TrgtDimTextBox2.Text = storeTargetAreas[index][Trgt].Width.ToString() + "x" +
                    storeTargetAreas[index][Trgt].Height.ToString();
                TargetAreaDisplay4(index);//Displays the target image in TargetPicBox
            }
            else { TrgtDimTextBox2.Text = ""; TrgtPartPicBox2.Image = null; }
        }

        private void TargetAreaDisplay4(int Image_index)
        {
            Rectangle cropArea = storeTargetAreas2[Image_index][TrgtPartCombobox2.SelectedIndex];
            Bitmap bmpImage = new Bitmap(ImagetoProcess2[Image_index]);
            TrgtPartPicBox2.Image = bmpImage.Clone(cropArea, bmpImage.PixelFormat);
        }

        private void TrgtPartCombobox_SelectedIndexChanged(object sender, EventArgs e)
        {

            //Show Dimensions
            if (TrgtPartCombobox.Text != "") // Shows the area and info of the target selected
            {
                int index = ImgPartCombobox.SelectedIndex;
                int Trgt = TrgtPartCombobox.SelectedIndex;
                TrgtDimTextBox.Text = storeTargetAreas2[index][Trgt].Width.ToString() + "x" +
                    storeTargetAreas2[index][Trgt].Height.ToString();
                TargetAreaDisplay5(index);//Displays the target image in TargetPicBox
                ShowParticleMeasures();
            }
            else { TrgtDimensionTextBox.Text = ""; TargetPicBox2.Image = null; }
        }

        private void TargetAreaDisplay5(int Image_index)
        {
            Rectangle cropArea = storeTargetAreas2[Image_index][TrgtPartCombobox.SelectedIndex];
            Bitmap bmpImage = new Bitmap(ImagetoProcess2[Image_index]);
            TrgtPartPicBox.Image = bmpImage.Clone(cropArea, bmpImage.PixelFormat);
        }

        private void ShowParticleMeasures()
        {


            int index = ImgPartCombobox.SelectedIndex;

            if (TrgtPartCombobox.Text != "")
            {
                int trgt = TrgtPartCombobox.SelectedIndex;
                SDtxtbox2.Text = Math.Round(IntensityMeasures[index][trgt][0], 4).ToString();
                CoVtxtbox2.Text = Math.Round(IntensityMeasures[index][trgt][1], 4).ToString();
                MItxtbox2.Text = Math.Round(IntensityMeasures[index][trgt][2], 4).ToString();
                MaxStrThick.Text = storeMaxStrThickness[index][trgt].ToString();
                PPDeviation.Text = Math.Round(ScaleSegregationIndexes[index][trgt][0], 4).ToString();
                IndexDisp.Text = Math.Round(ScaleSegregationIndexes[index][trgt][1], 4).ToString();
                SpResol.Text = Math.Round(ScaleSegregationIndexes[index][trgt][2], 4).ToString();
                Cmtxtbox2.Text = Math.Round(IntensityMeasures[index][trgt][3], 4).ToString();
                Cmaxtxtbox2.Text = Math.Round(IntensityMeasures[index][trgt][4], 4).ToString();
                Cmintxtbox2.Text = Math.Round(IntensityMeasures[index][trgt][5], 4).ToString();
                Ntxtbox2.Text = IntensityMeasures[index][trgt][6].ToString();
                NumPart.Text = IntensityMeasures[index][trgt][7].ToString();
            }
            else
            {
                SDtxtbox2.Text = "";
                CoVtxtbox2.Text = "";
                MItxtbox2.Text = "";
                MaxStrThick.Text = "";
                PPDeviation.Text = "";
                IndexDisp.Text = "";
                SpResol.Text = "";
                Cmtxtbox2.Text = "";
                Cmaxtxtbox2.Text = "";
                Cmintxtbox2.Text = "";
                Ntxtbox2.Text = "";
                NumPart.Text = "";
            }
        }

        private void PlotPartDim_Click(object sender, EventArgs e)
        {
            if (DimensionsComboBox2.Text != "")
            {
                PlotSelectedDimensionforParticles(DimensionsComboBox2.SelectedIndex);
            }
        }

        #region Plot data

        private void PlotPNNDistribution()
        {

        }

        private void PlotSelectedDimensionforParticles(int sel)
        {
            List<List<double>> PlotInfo = new List<List<double>>();
            PlotInfo.Clear();

            //Intensity measures
            if (sel < 3 || sel > 5)
            {
                int k = 0;
                foreach (var list in IntensityMeasures)
                {
                    PlotInfo.Add(new List<double>());
                    foreach (var item in list)
                    {
                        if (sel < 3) { PlotInfo[k].Add(item[sel]); }
                        if (sel > 5) { PlotInfo[k].Add(item[sel - 4]); }
                    }
                    k++;
                }
            }

            //Maximum Striation Thickness
            if (sel == 3)
            {
                int k = 0;
                foreach (var list in storeMaxStrThickness)
                {
                    PlotInfo.Add(new List<double>());
                    foreach (var item in list)
                    {
                        PlotInfo[k].Add(item);
                    }
                    k++;
                }
            }

            //Scale measures
            if (sel >= 4 && sel <= 6)
            {
                int k = 0;
                foreach (var list in ScaleSegregationIndexes)
                {
                    PlotInfo.Add(new List<double>());
                    foreach (var item in list)
                    {
                        if (sel == 4) { PlotInfo[k].Add(item[0]); }
                        if (sel == 5) { PlotInfo[k].Add(item[1]); }
                        if (sel == 6) { PlotInfo[k].Add(item[2]); }
                    }
                    k++;
                }
            }

            


            ClearChartDataPoints();
            //MixingPlotChart.ChartAreas[0].AxisX.TitleAlignment = StringAlignment.Near;
            //MixingPlotChart.ChartAreas[0].AxisX.TextOrientation = TextOrientation.Horizontal;
            //Standard Deviation (σ)
            if (sel == 0)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Standard Deviation (σ)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "σ";
            }
            //Coeff. of Variation (CoV)
            if (sel == 1)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Coeff. of Variation (CoV)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "CoV";
            }
            //Mixing Index (M)
            if (sel == 2)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Mixing Index (M)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "M";
            }
            //Maximum Striation Thickness
            if (sel == 3)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Maximum Striation Thickness";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "MST [pixels]";
            }
            //Point-particle Deviation (σfpp)
            if (sel == 4)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Point-particle Deviation (σfpp)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "σfpp [pixels]";
            }
            //Index of Dispersion (Idisp)
            if (sel == 5)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Index of Dispersion (Idisp)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Idisp [pixels]";
            }
            //Spatial resolution (Xg)
            if (sel == 6)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Spatial resolution (Xg)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Cm [v/v]";
            }
            //Mean Concentration (Cm)
            if (sel == 7)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Mean Concentration (Cm)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Cm [v/v]";
            }
            //Max Concentration (Cmax)
            if (sel == 8)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Max Concentration (Cmax)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Cmax [v/v]";
            }
            //Min Concentration (Cmin)
            if (sel == 9)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Standard Deviation (σ)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "Cmin [v/v]";
            }
            //Measured Points (N)
            if (sel == 10)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Measured Points (N)";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "N";
            }

            if (sel == 11)
            {
                MixingPlotChart.Titles["Mixing dimension"].Text = "Number of particles";
                MixingPlotChart.ChartAreas[0].AxisY.Title = "";
            }

            //Plot Information
            MixingPlotChart.Series.Clear();
            int i = 0;
            foreach (var list in PlotInfo)
            {
                //Validate if there are no other image with the same name
                string name = LoadedImageInfo2[i][0];
                for (int f = 0; f < MixingPlotChart.Series.Count; f++)
                {
                    if (name == MixingPlotChart.Series[f].Name) { name = name + "_" + (f + 1); }
                }

                MixingPlotChart.Series.Add(name);
                int j = 0;
                foreach (var item in list)
                {
                    MixingPlotChart.Series[i].Points.AddXY("Target " + (j + 1), item);
                    j++;
                }
                i++;
            }
        }//Plots all calculated mixing measures

        #endregion

        #endregion

        #endregion



        private void button15_Click(object sender, EventArgs e)
        {
            
        }
    }



}

