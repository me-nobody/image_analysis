run("Select None");
//Macro written by Dominic Waithe for Ronan Broderick (c) 2015.
//Counts foci in red channel, measures their intensity.
//Counts number of foci in the green channel which colocalise with the red channel.

sensitivity_in_red = 40;
sensitivity_in_grn = 40;
pixel_distance = 5;
title = getTitle();
setSlice(3);
roiManager("Reset");
run("Find Maxima...", "noise="+sensitivity_in_red+" output=[Point Selection]");
getSelectionCoordinates(xCoordinatesRed, yCoordinatesRed); 

setSlice(2);
run("Find Maxima...", "noise="+sensitivity_in_grn+" output=[Point Selection]");
getSelectionCoordinates(xCoordinatesGrn, yCoordinatesGrn); 
setSlice(3);
red_value = newArray(lengthOf(xCoordinatesRed));
for(a=0; a<lengthOf(xCoordinatesRed); a++) {
	run("Specify...","width=4 height=4 x="+xCoordinatesRed[a]+" y="+yCoordinatesRed[a]+" oval centered");
	run("Measure");
	red_value[a] =  getResult("Mean",nResults-1);
	print(title+"\tmean_red\t"+red_value[a]+"\t");
	}



setSlice(3);
keep = newArray(lengthOf(xCoordinatesGrn));

roiManager("Reset");
for(b=0; b<lengthOf(xCoordinatesGrn); b++) { 
	for(a=0; a<lengthOf(xCoordinatesRed); a++) {
	
		
		dist = sqrt(((xCoordinatesRed[a]-xCoordinatesGrn[b])*(xCoordinatesRed[a]-xCoordinatesGrn[b]))+((yCoordinatesRed[a]-yCoordinatesGrn[b])*(yCoordinatesRed[a]-yCoordinatesGrn[b])));
		
		if (dist < pixel_distance && keep[b] != true){
			
			keep[b] = true;
			run("Specify...","width=4 height=4 x="+xCoordinatesGrn[b]+" y="+yCoordinatesGrn[b]+" oval centered");
			roiManager("Add");
			run("Measure");
			value_true = getResult("Mean",nResults-1);
			print(title+"\t\t\tmean_red_of_coloc\t"+red_value[a]+"\t");
			a = lengthOf(xCoordinatesRed);
			}else{
			keep[b] = false;
			
				}
		
		}
		
		
}

