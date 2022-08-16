import arcpy


#Original script from Fletcher Meadema, PhD student at Virginia Tech <trailresearch@vt.edu>
#Modified by Andy Welsh andrew.welsh@usda.gov

#Script generates a slope ratio (average trail grade/ average landform grade) for XXX length segments along a trail
#Developed for ArcPro
#Requires Advanced License.

#set variables from params
#Toolbox side to add a drop down for units for the point dist and buffer dist
dem = arcpy.GetParameterAsText(0)
sr = arcpy.Describe(dem).spatialReference
slopeParam = arcpy.GetParameterAsText(1)
trail = arcpy.GetParameterAsText(2)

#Toolbox side to add a drop down for units for the point dist and buffer dist
pointDist = arcpy.GetParameterAsText(3)
buffDist = arcpy.GetParameterAsText(4)  #buffer size needs to be at least twice as large as cell size to pick up elevation data in zonal stats calc
unitName = arcpy.GetParameterAsText(5) 


#variables with hardcoded names
slopeRaster = unitName +'Slope_dem'
trailProj = "trailProjected"
joiner = "Joiner"
trailName = "TRAIL_NAME"
hiSus = "1-High Sustainability"
modSus = "2-Moderate Sustainability"
lowSus ="3-Low Sustainability"
unSus = "4-Unsustainable"
unSusMod ="5-Moderately Unsustainable"
unSusHi = "6-Highly Unsustainable"

#AT paper variables


#final features
inDepthFinalFeature = unitName + 'InDepthTrail'
finalOutputTable = "SlopeRatio.xlsx"
sumFinalFeature = unitName + "SummaryTrail"
sumExcel = unitName + "SummarySlopeRatio.xlsx"
depthExcel = unitName + "InDepthSlopeRatio.xlsx"

#in memory variables
inMemPts = "in_memory/pts"
inMemSplitTrail = "in_memory/splitTrail"
inMemBuffTrail = "in_memory/buffTrail"
inMemLandTable = "in_memory/landformGrade"
inMemSumTable = "in_memory/summaryTable"


#function for determining the sus score per Marion avg grade/landform grade matrix in National Prairie paper
#TODO:there has got to be a better python way to do this.  Dictionary maybe?
def susScore(inTrailGrade, inLandformGrade):
    trailGrade = inTrailGrade
    lfGrade = inLandformGrade
    outSusScore = "Unknown" #initializing the ourgoing score to unknown
    
    if trailGrade >= lfGrade: #the trail grade is higher than the landform grade due to a sampling issue
        outSusScore = unSus #really not possible, but the zonal sample might say it is.  treating as 100% slope ratio or fall line trail
    
    elif trailGrade <= 2:
        if lfGrade <= 2:
            outSusScore = unSusMod
        elif lfGrade <=5:
            outSusScore = unSus
        elif lfGrade <=10:
            outSusScore = unSus
        elif lfGrade <=15:
            outSusScore = unSus
        elif lfGrade >15:
            outSusScore = unSus
        else:
            outSusScore = "0-Unknown"
            
    elif trailGrade <=5:
        if lfGrade <=5:
            outSusScore = unSus
        elif lfGrade <=10:
            outSusScore = lowSus
        elif lfGrade <=15:
            outSusScore = modSus
        elif lfGrade >15:
            outSusScore = hiSus
        else:
            outSusScore = "0-Unknown"
    
    elif trailGrade <=10:
        if lfGrade <=10:
            outSusScore = unSusMod
        elif lfGrade <=15:
            outSusScore = lowSus
        elif lfGrade >15:
            outSusScore = modSus
        else:
            outSusScore = "Unknown"
    
    elif trailGrade <=15:
        if lfGrade <=15:
            outSusScore = unSusMod
        elif lfGrade >15:
            outSusScore = unSusMod
        else:
            outSusScore = "0-Unknown"
    
    elif trailGrade >15:
        if lfGrade >15:
            outSusScore = unSusHi
        else:
            outSusScore = "0-Unknown"
    
    else:
        outSusScore = "0-Unknown"
    return outSusScore

#function to classify final summary table according to STAT breakouts
def statScore(inSusPct):
    #trapping a nonetpye error with a conditional
    if inSusPct is not None:
        susPct = inSusPct
    else:
        susPct = 101 #setting susPct to 101 triggers the 'Else' statement below when the input is a noneType or <Null> value
    
    outStatScore = "Unknown" #initializing the ourgoing score to unknown
    
    if susPct <= 50:
        outStatScore = "Low"
    elif susPct <= 75:
        outStatScore = "Moderate"
    elif susPct <=100 :
        outStatScore = "High"
    else:
        outStatScore = "Unknown"
    return outStatScore

#Force a projection match to ensure they are the same for the RASTER and input feature
#If we don't do this it will cause bad data in the split and slope ratio calcs
#TODO: logic test.  DEM needss to be projected?  DEM and trail already match projections?
arcpy.AddMessage ("Projecting input trail layer to DEM projection")  
demProj = arcpy.Describe(dem).spatialReference
arcpy.management.Project(trail, trailProj, demProj.exportToString())
arcpy.AddMessage("Done")  
    
    
#create points at XX intervals along the line
arcpy.AddMessage("Generating points at " + pointDist + " intervals on " + trail + "...")
arcpy.management.GeneratePointsAlongLines(trailProj, inMemPts, 'DISTANCE',pointDist,"", 'END_POINTS')
arcpy.AddMessage("Done")
    #Alter this code block to set the "scale" of analysis.  
    #This places points every XX meters on the trail to measure the trail in XX segments.  
    #30m may be an appropriate scale for a 10m dem i think?
    #3m for 1m dem might be good
    #adjust this parameter to suit your DEM and analysis needs

# #Splits the trail layer at XX meter interval points
#This is where it hangs on large inputs
arcpy.AddMessage("Splitting " + trail + " into " + pointDist + " segments")
arcpy.management.SplitLineAtPoint(trailProj,inMemPts,inMemSplitTrail,2)
arcpy.AddMessage("Done")

#unique ID for trail segments
#don't want to use objectid or FID for joining/zonal stats if we can avoid it
arcpy.AddMessage("Adding a unique ID to each trail segment...")
arcpy.management.AddField(inMemSplitTrail,joiner, 'STRING')
with arcpy.da.UpdateCursor (inMemSplitTrail, joiner) as cursor:

    interval = 0
    
    for row in cursor:
        row[0] = interval #set the id to current interval
        interval += 1  #move interval along by 1
        cursor.updateRow(row)
del cursor
arcpy.AddMessage("Done")

#Is it potentially less expesnive to buffer the line segment and use that as the zonal statistic?  Avoids another generate points and split process.
arcpy.analysis.Buffer(inMemSplitTrail, inMemBuffTrail, buffDist, 'FULL', 'FLAT', 'NONE')


# #Generate points halfway on those previously split lines in half
# arcpy.AddMessage("Generating points halfway between the now split lines")
# arcpy.management.GeneratePointsAlongLines(splitTrail,centerPtsSplit, 'PERCENTAGE',"",50, 'NO_END_POINTS')

# arcpy.AddMessage("Done")

# # buffers those points by buffDist meters
# arcpy.AddMessage("Buffering the points " + buffDist + " along the trail")
# arcpy.analysis.Buffer(centerPtsSplit,buffPts, buffDist, 'FULL', 'ROUND', 'NONE')

# arcpy.AddMessage("Done")

#creates a slope DEM off of the input DEM if it doesn't already exist.  Logic test is there because it was slowing down the run time on multiple re-runs.
if arcpy.Exists(slopeRaster): #slope raster already exists in workspace
    arcpy.AddMessage("Slope Raster exists, skipping to next step.")
elif slopeParam: #easy way to check if the optional slope raster has been inputted, if so, make it the slope Raster
    slopeRaster =slopeParam #user input is not the slope raster
    arcpy.AddMessage("Using your optional input " + slopeParam + " as the sloep raster. No need for the tool to generate a new slope raster.")
else:
    arcpy.AddMessage("Creating slope layer from input DEM...this may take a bit")
    arcpy.ddd.SurfaceParameters(dem,slopeRaster, 'SLOPE', 'QUADRATIC','5 METERS', 'FIXED_NEIGHBORHOOD', '', 'PERCENT_RISE')
    arcpy.AddMessage("Done")
    

#LANDFORM GRADE
arcpy.AddMessage("Adding Land Form Grade to the buffered trail segments...")
arcpy.sa.ZonalStatisticsAsTable(inMemBuffTrail,joiner,slopeRaster,inMemLandTable, 'NODATA', 'ALL')
arcpy.AddMessage("Done")

#create a dictionary from landform grade values in order to avoid a join down the line
#avoids calcuate fields, improving overall performance particularly with many records
#watch for hardcoded field names "Joiner" and "MEAN"
meanDict = dict([(row.Joiner, (row.MEAN)) for row in arcpy.SearchCursor(inMemLandTable)]) #the meanest!


#TRAIL GRADE
arcpy.AddMessage("Adding Trail Grade along the " + pointDist + " split trail segments")
Prop = 'Z_MIN;Z_MAX;Z_MEAN;MIN_SLOPE;MAX_SLOPE;AVG_SLOPE'
    #adding surface information to the split trail feature by segment
arcpy.ddd.AddSurfaceInformation(inMemSplitTrail, dem,Prop,'BILINEAR')
    #adding a slope ratio, land form mean, sustainability score, and segment Miles field to the split trail feature
arcpy.management.AddField(inMemSplitTrail,"SLOPERATIO", 'DOUBLE')
arcpy.management.AddField(inMemSplitTrail,"lfMEAN", 'DOUBLE')
arcpy.management.AddField(inMemSplitTrail,"susScore", 'STRING')
arcpy.management.AddField(inMemSplitTrail, "splitMiles", 'DOUBLE')
arcpy.management.AddField(inMemSplitTrail, "hiSusMi", 'DOUBLE')
arcpy.management.AddField(inMemSplitTrail, "modSusMi", 'DOUBLE')
arcpy.management.AddField(inMemSplitTrail, "lowSusMi", 'DOUBLE')
arcpy.management.AddField(inMemSplitTrail, "unSusMi", 'DOUBLE')
arcpy.management.AddField(inMemSplitTrail, "unSusModMi", 'DOUBLE')
arcpy.management.AddField(inMemSplitTrail, "unSusHiMi", 'DOUBLE') 
#TODO: add a remarks or comments field
    #calculate miles for each split length
arcpy.management.CalculateGeometryAttributes(inMemSplitTrail, [["splitMiles", "LENGTH"]], "MILES_US")
arcpy.AddMessage("Done")

#Uses an update cursor with a dictionary to assign a value to slope ratio  and landform grade fields
arcpy.AddMessage("Calculating Slope Ratio for " + trail + " by divding average trail slope by avg landform grade...")
with arcpy.da.UpdateCursor (inMemSplitTrail, ['SLOPERATIO', 'Joiner', 'Avg_Slope', 'lfMEAN', 'susScore', 'splitMiles',
                                             'hiSusMi', 'modSusMi', 'lowSusMi', 'unSusMi', 'unSusModMi', 'unSusHiMi'  ] ) as cursor:
    for row in cursor:
        trailKeyValue = row[1]  #use the value of the Joiner field in the current row
        if trailKeyValue in meanDict: #if that value matches a value in meanDict
            currVal = row[2]/meanDict[trailKeyValue] #divide avg_slope by the value from meanDict at that key
            #check if currVal is showing as > 100% and likely due to a averaging issue with zonal statistics
            if currVal > 1 : #slope ration is more than 100%
                row[0] = 1 #a zonal sampling issue has the slope ratio as > 100%
            else: #slope ratio is 100% or less
                row[0] =  currVal 
                
            row[3] = meanDict[trailKeyValue]
            row[4] = susScore(row[2],meanDict[trailKeyValue])
            
            #put miles into each column head for those mile types
            #Forcing something that coul probably be done by pandas or easiyl in a pivot table in excel.
            #Trying to keep it reeeeeallly easy for whoever runs this. 
            #Eventual ideal output would have feature class with:
                #trails by trail name, miles in each category, percent in each category, and total miles percent sustainable, total miles percent unsustainable
            if row[4] == hiSus:
                row[6] = row[5]
                row[7] = 0 #setting other mileage rows to zero for the segment to avoid <null>
                row[8] = 0
                row[9] = 0
                row[10] = 0
                row[11] = 0
            elif row[4] == modSus:
                row[7] = row[5]
                row[6] = 0
                row[8] = 0
                row[9] = 0
                row[10] = 0
                row[11] = 0
            elif row[4] == lowSus:
                row[8] = row[5]
                row[7] = 0
                row[6] = 0
                row[9] = 0
                row[10] = 0
                row[11] = 0
            elif row[4] == unSus:
                row[9] = row[5]
                row[7] = 0
                row[8] = 0
                row[6] = 0
                row[10] = 0
                row[11] = 0
            elif row[4] == unSusMod:
                row[10] = row[5]
                row[7] = 0
                row[8] = 0
                row[9] = 0
                row[6] = 0
                row[11] = 0
            elif row[4] == unSusHi:
                row[11] = row[5]
                row[7] = 0
                row[8] = 0
                row[9] = 0
                row[10] = 0
                row[6] = 0
            
            cursor.updateRow(row)
del cursor
arcpy.AddMessage("Done")

# This portion will fail if your input does not have a trail_name field
#it will also merge two different trails if they have the same name
#TODO: Add trail field name selection in input parameters
summaryFields = [["splitMiles", "SUM"], ["hiSusMi", "SUM"],["modSusMi", "SUM"],["lowSusMi", "SUM"],["unSusMi", "SUM"],["unSusModMi", "SUM"],["unSusHiMi","SUM"]]
#take the output layer and get some sumamry stats on it, do pct calcs
arcpy.analysis.Statistics(inMemSplitTrail, inMemSumTable, summaryFields, trailName)
arcpy.management.AddField(inMemSumTable, "pctTotUnSus", 'DOUBLE')
arcpy.management.AddField(inMemSumTable, "pctTotSus", 'DOUBLE') 
arcpy.management.AddField(inMemSumTable, "envSTAT", 'STRING')
#consider using an update cursor
arcpy.management.CalculateField(inMemSumTable, 'pctTotSus',"(!SUM_hiSusMi! + !SUM_modSusMi! + !SUM_lowSusMi!)/ !SUM_splitMiles! * 100" , "PYTHON3" )
arcpy.management.CalculateField(inMemSumTable, 'pctTotUnSus', "(!SUM_unSusMi! + !SUM_unSusModMi! + !SUM_unSusHiMi!)/ !SUM_splitMiles! * 100" , "PYTHON3")
with arcpy.da.UpdateCursor (inMemSumTable, ['pctTotSus', 'envSTAT'] ) as cursor:
    for row in cursor:
        #use the total sustainble percent score in the statScore function to write a STAT score in the envSTAT cell
        row[1] = statScore(row[0])
        cursor.updateRow(row)
del cursor

#permanently join summary field to a copy of the original trail layer
arcpy.management.CopyFeatures(trail, sumFinalFeature)
arcpy.management.JoinField(sumFinalFeature, trailName, inMemSumTable, trailName)

#spit split trail out of memory
arcpy.management.CopyFeatures(inMemSplitTrail, inDepthFinalFeature)

#add to map
arcpy.AddMessage("Final feature with summary output is " + sumFinalFeature )
arcpy.AddMessage("Final feature with in-depth output is " + inDepthFinalFeature)

#export to table
arcpy.AddMessage("Exporting Summary and inDepth results to excel tables...")
arcpy.conversion.TableToExcel(sumFinalFeature, sumExcel)
arcpy.conversion.TableToExcel(inDepthFinalFeature, depthExcel)
arcpy.AddMessage("Done")
arcpy.Delete_management("in_memory")


