# SlopeRatioTool
Uses DEM and USFS Publish Trail Data to calculate trail sustainability.

GIS Physical Trail Assessment: Slope Ratio Tool Guide

Background

Purpose
The purpose of the Slope Tool is to provide a physical sustainability assessment for a trail network.  This assessment is based on research by Dr. Jeff Marion and other Recreation Ecologists. The specific rating system is according to: Marion, J.L., Arredondo, J., and Meadema, F. 2022. Assessing the Condition and Sustainability of the Trail System at Tallgrass Prairie National Preserve. Final Report to the Nature Conservancy, Kansas Flint Hills Office, and DOI National Park Service, Tallgrass Prairie National Preserve, Strong City, KS. Results should be verified by knowledge field employees.

About
The Slope Tool is a toolbox and python script designed in ArcPro 2.9.2 for users with an advanced license. The original script was developed by Fletcher Meadema as a PhD student at Virginia Tech.  USFS staff modified the script to work as an ArcPro toolbox and added additional functionality, optimization, and error trapping.
The toolbox can be downloaded as a zip file here[WA-F1]:
If you have interest in contributing to the project, the public git repository for the tool resides at https://github.com/WOtrailAsstPm/SlopeRatioTool .

Suggested Use
Use the tool to get a rapid, office-based, assessment of a current or proposed trail network.  Look at the outputs and compare them with your knowledge of the ground.  Symbolize segments or trails on the various characteristics included in the assessment.

What is the tool doing?
The tool breaks the input trail layer into user specified segments.
It gets various slope and elevation characteristics for each segment.
It buffers both sides of the trail segments at the user input distance.
It uses that buffer to extract surface characteristics of the area around the trail.
It divides the average slope of the trail segment by the average landform grade of the surrounding area.
It gives a trail segment score and an overall trail score based on the aforementioned research paper classifications.


Installing and Running the Tool
1. Download the SRTool zip file and extract it to your computer.
2. Follow ESRI’s “Add an existing toolbox to a project” instructions below:
https://pro.arcgis.com/en/pro-app/latest/help/projects/connect-to-a-toolbox.htm
3. When you add the toolbox you should see the following items:
4. Right-click the Trail Slope Ratio Script and select “open”
5. The tool should open and display the parameters:

6. Input the correct parameters (additional info below) and click “run”



Tool Parameters
 Overview 
You will need the following features/rasters.  You can save them to your local machine for improved performance:
A. Digital Elevation Model (DEM), integer raster
B. Percent Rise Slope Raster, raster
C. Trails Layer, vector
D. Trail Name or Trail Number, Field
o Derived drop down of fields derived from Trails Layer
E. Trail Segment Distance, integer
E2. Includes unit of measure drop down 
F. Trail Buffer Distance, integer
F2. Includes unit of measure drop down
G. Unit Name, text


Parameter Descriptions
Required Features/Rasters
Digital Elevation Model (DEM) Raster
Used to create slope raster (if not provided) and calculate trail grade
* Integer type (tool will fail otherwise). Tested with 10m DEM.
* This can be any resolution/cellsize, but the process does get slower the higher the resolution. 
* Clip the DEM to the Admin Boundary of your Forest for faster processing.  Too large of a DEM (say the entire state or country) and the script will take forever to derive a slope raster.
Trails Layer with a Trail Name or Trail Number field
* Tested with TrailNFS_Publish clipped to AdministrativeForest or other forest boundary.  
Optional Raster
Percent Rise Slope Raster: used to calculate landform grade
* Derived from input DEM and in same projection.
* This will speed up the process as the script doesn’t need to derive slope from DEM.
* If you don’t have a slope raster, the tool will create one for you. Leave this parameter blank.
Other Required Inputs
Trail Name or Number Field  
Dropdown list derived from the input Trail Layer.  Select the field that you want to use to summarize the results.  Trail Name generally works best unless you know trail numbers by heart.
Trail Segment Distance with units 
Breaks the trail feature into X length segments. Used to assign individual slope ratio and other calculations.
* Tested with 100-meter segments.
* The smaller the segment, the more time it will take to process.
* The larger the segment, the quicker it will process but the less exact the results will be.
* Any segmentation below the cell size of the raster (i.e. 5m on a 10m DEM) will not yield accurate results.
Trail Buffer Distance with units 
The distance to buffer the trail segment on both sides. Used to calculate the prevailing landform grade.
* Tested with 60 meter buffers.
* Should be at least two times the cell size for the raster for best results. If you use less than that it may not pick up enough slope data to assign a value for your segment. (explained here: https://pro.arcgis.com/en/pro-app/2.8/tool-reference/spatial-analyst/how-zonal-statistics-works.htm)
* The idea is to get enough of the prevailing slope to give a decent average without including extraneous data that will throw off the average.
Unit Name 
A text field that will append the unit name to the output files.
Example: with WMNF as input unit the output would be WMNFInDepthTrail and WMNFSummaryTrail.


Tool Outputs:
Example outputs can be found here: https://arcg.is/0P0W4

All outputs will be saved in default project workspace as of 08/17/2022
The tool produces 4 final outputs:
* {unit name}InDepthTrail Feature Class
* {unit name}SummaryTrail Feature Class
* {unit name}InDepth Excel File
* {unit name}Summary Excel File

In Depth Feature Class
{unit name}InDepthTrail
This feature class gives a segment-by-segment view and rating of trail characteristics.  Each segment has the following fields added to whatever fields exist in the trail feature parameter input:

Summarized Feature Class
{unit name}SummaryTrail
This feature class gives a summarized trail view and rating of trail characteristics.  Each trail has the following fields added to whatever fields exist in the trail feature parameter input:

In Depth Excel Spreadsheet
{unit name}SummaryTrail
This feature class gives the in-depth trail view and rating of trail characteristics in an excel file.  

Summarized Excel Spreadsheet
{unit name}SummaryTrail
This feature class gives a summarized trail view and rating of trail characteristics in an excel file.



