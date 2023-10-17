using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AForgeImageProcessing
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        public class inletinfo
        {
            public int ImageCoordinate { get; set; }
            public int TargetCoordinate { get; set; }
        }

        public class AssignInlet
        {
            public int TargetNumber { get; set; }
            public int InletImageCoordinate { get; set; }
            public int InletTargetCoordinate { get; set; }
        }

        public class RefImg
        {
            public int ImageIndex { get; set; }
            public int Concentration { get; set; }
        }

        #region General Variables Assigned Inlets

        //Number of inlet in the List InletTrgts
        //Number of image assigned
        //Number of target assigned
        List<List<List<int>>> AssignedTrgts = new List<List<List<int>>>();
        List<List<int>> InletTargets = new List<List<int>>();
        List<string[]> ImagesInfo2 = new List<string[]>();//Images Info
        List<List<Rectangle>> TargetAreas2 = new List<List<Rectangle>>();
        List<inletinfo> InletListcoordinate = new List<inletinfo>();
        List<inletinfo> ListBox2opt = new List<inletinfo>();
        public static List<List<AssignInlet>> AssignedInletsList = new List<List<AssignInlet>>();

        //Missing target to associate to an inlet
        public static int MisTrgts=1;
        #endregion

        #region General variables Perform Calibration

        public static List<List<RefImg>> ImageswithReferences = new List<List<RefImg>>();
        List<int> ImagestoCalibrate = new List<int>();
        List<int> AvalaibleCalImg = new List<int>();
        List<inletinfo> AssignedRefList= new List<inletinfo>();
        #endregion

        private void Form1_Load(object sender, EventArgs e)
        {
            //Getting Form2 variables
            InletTargets = Form2.inletTrgts;
            ImagesInfo2 = Form2.LoadedImageInfo;
            TargetAreas2 = Form2.storeTargetAreas;

            if (!Form2.calibration)
            {
                if (tabControl1.TabPages.Contains(CalibImages))
                { tabControl1.TabPages.Remove(CalibImages); }
                    
                if (!tabControl1.TabPages.Contains(AssignTargets)) //Evaluates if tab was already shown
                { tabControl1.TabPages.Add(AssignTargets); }
                
                #region Assign Inlets
                //Clear All
                listBox1.Items.Clear();
                ImageCombobox.Items.Clear();
                TargetCombobox.Items.Clear();
                TargetCombobox.Text = "";

                //Initializates the Assigned inlet List
                if (AssignedInletsList.Count < ImagesInfo2.Count)
                {
                    for (int c = AssignedInletsList.Count; c < ImagesInfo2.Count; c++)
                    {
                        AssignedInletsList.Add(new List<AssignInlet>());
                    }
                }

                //Clear inlet list
                InletListcoordinate.Clear();

                //Fills listBox 1 
                int i = 0;
                int j = 0;
                foreach (var list in InletTargets)
                {
                    foreach (var item in list)
                    {
                        listBox1.Items.Add("Inlet " + (i + 1) + "       Image name: " + ImagesInfo2[j][0] +
                            "       # of Target assigned: " + (item + 1));
                        inletinfo inletcoord = new inletinfo();
                        inletcoord.ImageCoordinate = j;
                        inletcoord.TargetCoordinate = item;
                        InletListcoordinate.Add(inletcoord);
                        i = i + 1;
                    }
                    j = j + 1;
                }
                listBox1.SelectedIndex = 0;

                FillComboboxes();
                FillListBox2();
                CheckCompletion();
                #endregion
            }

            if (Form2.calibration)
            {
                if (!tabControl1.TabPages.Contains(CalibImages))
                { tabControl1.TabPages.Add(CalibImages); }

                if (tabControl1.TabPages.Contains(AssignTargets)) //Evaluates if tab was already shown
                { tabControl1.TabPages.Remove(AssignTargets); }

                #region Perform Calibration

                //Clear All
                RefImgCombobox.Items.Clear();
                listBox3.Items.Clear();
                listBox4.Items.Clear();
                ConTextBox.Text = "";

                //Initializates the Images with References List
                if (ImageswithReferences.Count < ImagesInfo2.Count)
                {
                    for (int c = ImageswithReferences.Count; c < ImagesInfo2.Count; c++)
                    {
                        ImageswithReferences.Add(new List<RefImg>());
                    }
                }
                
                //Clear inlet list
                //InletListcoordinate.Clear();

                //Fills listBox 3 
                ImagestoCalibrate.Clear();
                for (int j = 0; j < ImagesInfo2.Count; j++) 
                {
                    bool refimg = false;
                    for (int i = 0; i < Form2.calibimgarray.Length; i++)
                    {
                        int image_index = Form2.calibimgarray[i];
                        if (image_index == j) { refimg = true; break; }
                    }

                    if (!refimg)
                    {
                        listBox3.Items.Add("Image to calibrate: "+ImagesInfo2[j][0] + "      # of targets: "
                            + TargetAreas2[j].Count);
                        ImagestoCalibrate.Add(j);
                    }

                }
                listBox3.SelectedIndex = 0;

                FillRefImageCombobox();
                FillListBox4();
                CheckAssignedRefImgs();

                #endregion

            }


        }

        #region Assign Inlets Functions

        private void listBox1_SelectedIndexChanged(object sender, EventArgs e)
        {
            FillListBox2();
        }

        private void FillListBox2()
        {
            listBox2.Items.Clear();
            ListBox2opt.Clear();

            int imageEval = InletListcoordinate[listBox1.SelectedIndex].ImageCoordinate;
            int inlettargetEval= InletListcoordinate[listBox1.SelectedIndex].TargetCoordinate;

            int j = 0;
            foreach (var list in AssignedInletsList)
            {
                foreach (var item in list)
                {
                    if (item.InletImageCoordinate == imageEval && item.InletTargetCoordinate == inlettargetEval)
                    {
                        listBox2.Items.Add("Image name: " + ImagesInfo2[j][0] +
                        "       Target #: " + (item.TargetNumber+1).ToString());
                        inletinfo AssTrgt = new inletinfo();
                        AssTrgt.ImageCoordinate = j;
                        AssTrgt.TargetCoordinate = item.TargetNumber;
                        ListBox2opt.Add(AssTrgt);
                    } 
                }
                j = j + 1;
            }
        }

        private void FillComboboxes()
        {
            //Fill Image List combobox
            for (int i = 0; i < ImagesInfo2.Count; i++)
            {
                ImageCombobox.Items.Add(ImagesInfo2[i][0]);
            }
            //Fill Target List combobox
            ImageCombobox.SelectedIndex = 0;
            FillTargetCombobox(0);
        }

        private void FillTargetCombobox(int image_index)
        {
            TargetCombobox.Items.Clear();
            for (int i = 0; i < TargetAreas2[image_index].Count; i++)
            {
                bool aux = false;
                foreach (var item in InletTargets[image_index])
                {
                    if (item == i) { aux = true; }
                }
                foreach (var item in AssignedInletsList[image_index])
                {
                    if (item.TargetNumber == i) { aux = true; }
                }
                if (!aux) { TargetCombobox.Items.Add(i + 1); }

                if (TargetCombobox.Items.Count > 0) { TargetCombobox.SelectedIndex = 0; }
                else { TargetCombobox.Text = ""; }
            }
        }

        private void ImageCombobox_SelectedIndexChanged(object sender, EventArgs e)
        {
            FillTargetCombobox(ImageCombobox.SelectedIndex);
        }

        private void AddButton_Click(object sender, EventArgs e)
        {
            if (TargetCombobox.Text != "")
            {
                AssignInlet NewTarget = new AssignInlet();
                NewTarget.TargetNumber = Convert.ToInt32(TargetCombobox.Text)-1;
                NewTarget.InletImageCoordinate = InletListcoordinate[listBox1.SelectedIndex].ImageCoordinate;
                NewTarget.InletTargetCoordinate = InletListcoordinate[listBox1.SelectedIndex].TargetCoordinate;
                AssignedInletsList[ImageCombobox.SelectedIndex].Add(NewTarget);
                FillListBox2();
                FillTargetCombobox(ImageCombobox.SelectedIndex);
                CheckCompletion();
            }


            
        }

        private void RemoveButton_Click(object sender, EventArgs e)
        {
            if (listBox2.SelectedIndex > -1)
            {
                int ImgCoor = ListBox2opt[listBox2.SelectedIndex].ImageCoordinate;
                int TrgtCoor = ListBox2opt[listBox2.SelectedIndex].TargetCoordinate;
                int j = 0;
                for (int i = 0; i < AssignedInletsList[ImgCoor].Count; i++)
                {
                    if (AssignedInletsList[ImgCoor][i].TargetNumber == TrgtCoor) { j = i; break; }

                }
                AssignedInletsList[ImgCoor].RemoveAt(j);
                FillListBox2();
                FillTargetCombobox(ImageCombobox.SelectedIndex);
                Checklabel.Visible = false;
            }
            
        }

        private void CheckCompletion()
        {
            MisTrgts=0;
            for (int image_index = 0; image_index < ImagesInfo2.Count; image_index++)
            {
                for (int i = 0; i < TargetAreas2[image_index].Count; i++)
                {
                    bool aux = false;
                    foreach (var item in InletTargets[image_index])
                    {
                        if (item == i) { aux = true; }
                    }
                    foreach (var item in AssignedInletsList[image_index])
                    {
                        if (item.TargetNumber == i) { aux = true; }
                    }
                    if (!aux) { MisTrgts= MisTrgts+1; }

                }
            }

            if (MisTrgts == 0)
            {
                Checklabel.Visible = true;
            }
            else { Checklabel.Visible = false; }
        }
        #endregion

        #region Perform calibration
        private void FillRefImageCombobox()
        {
            RefImgCombobox.Items.Clear();
            AvalaibleCalImg.Clear();
            for (int i = 0; i < Form2.calibimgarray.Length; i++)
            {
                bool cnd = false;
                int image_index = Form2.calibimgarray[i];

                foreach (var img in ImagestoCalibrate)
                {
                    foreach (var item in ImageswithReferences[img])
                    {
                        if (item.ImageIndex == image_index) { cnd = true; break; }
                    }
                }

                if (!cnd)
                {
                    RefImgCombobox.Items.Add(ImagesInfo2[image_index][0]);
                    AvalaibleCalImg.Add(image_index);
                }
                
            }
            if (RefImgCombobox.Items.Count > 0)
            {
                RefImgCombobox.SelectedIndex = 0;
                targetslabel.Text = "# of targets:" + TargetAreas2[AvalaibleCalImg[0]].Count.ToString();
            }
            else { targetslabel.Text = "# of targets:"; }
            
        }

        private void AddRefButton_Click(object sender, EventArgs e)
        {
            int image_index = ImagestoCalibrate[listBox3.SelectedIndex];
            if (TargetAreas2[image_index].Count > 0)
            {
                #region CodeAdd
                if (RefImgCombobox.Text != "")
                {
                    int calibimg_index = AvalaibleCalImg[RefImgCombobox.SelectedIndex];

                    if (TargetAreas2[image_index].Count == TargetAreas2[calibimg_index].Count)
                    {
                        if (ConTextBox.Text.All(char.IsDigit) && ConTextBox.Text != "")
                        {
                            int conc = Convert.ToInt32(ConTextBox.Text);
                            if (conc >= 0 && conc <= 100)
                            {
                                RefImg Newreference = new RefImg();
                                Newreference.ImageIndex = calibimg_index;
                                Newreference.Concentration = conc;
                                ImageswithReferences[image_index].Add(Newreference);
                                ConTextBox.Text = "";
                                FillListBox4();
                                FillRefImageCombobox();
                                CheckAssignedRefImgs();
                            }
                        }
                        else { MessageBox.Show("Please insert an integer number between 0 and 100"); }
                    }
                    else { MessageBox.Show("The reference image must have the same number of targets"); }
                }
                else { MessageBox.Show("There are no Reference images left to assign"); }
                #endregion
            }
            else {MessageBox.Show("Please define targets in the image to be calibrated"); }
        }

        private void FillListBox4()
        {
            listBox4.Items.Clear();
            AssignedRefList.Clear();
            int image_index = ImagestoCalibrate[listBox3.SelectedIndex];
            if (ImageswithReferences[image_index].Count > 0)
            {
                for (int i = 0; i < ImageswithReferences[image_index].Count; i++)
                {
                    int RefImg = ImageswithReferences[image_index][i].ImageIndex;
                    listBox4.Items.Add("Ref Image: " + ImagesInfo2[RefImg][0] + "      Concentration: " +
                        ImageswithReferences[image_index][i].Concentration + "%");
                    inletinfo ListBox4elem = new inletinfo();
                    ListBox4elem.ImageCoordinate = image_index;
                    ListBox4elem.TargetCoordinate = i; //RemoveAt
                    AssignedRefList.Add(ListBox4elem);
                }
            }
            
        }

        private void RemoveRefButton_Click(object sender, EventArgs e)
        {
            int image_index = AssignedRefList[listBox4.SelectedIndex].ImageCoordinate;
            int pos = AssignedRefList[listBox4.SelectedIndex].TargetCoordinate;
            ImageswithReferences[image_index].RemoveAt(pos);
            FillListBox4();
            FillRefImageCombobox();
        }

        #endregion

        private void RefImgCombobox_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (RefImgCombobox.Items.Count > 0)
            {
                targetslabel.Text = "# of targets:" + TargetAreas2[AvalaibleCalImg[RefImgCombobox.SelectedIndex]].Count.ToString();
            }
            else { targetslabel.Text = "# of targets:"; }
        }

        private void CheckAssignedRefImgs()
        {
            bool RefAssignedOk = true;
            foreach (var item in ImageswithReferences)
            {
                int a = item.Count;
                if (a == 1) { RefAssignedOk = false; }
            }
            if (RefAssignedOk)
            {
                label6.ForeColor = Color.Black;
            }
            else
            {
                label6.ForeColor = Color.Red;
            }
        }

        private void listBox3_SelectedIndexChanged(object sender, EventArgs e)
        {
            FillListBox4();
        }
    }
}
