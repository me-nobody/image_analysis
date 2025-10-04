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
out_mean = newArray(lengthOf(xCoordinatesRed));
for(a=0; a<lengthOf(xCoordinatesRed); a++) {
	run("Specify...","width=4 height=4 x="+xCoordinatesRed[a]+" y="+yCoordinatesRed[a]+" oval centered");
	run("Measure");
	out_sum += getResult("Mean",nResults-1);
	}
out_mean = out_sum/lengthOf(xCoordinatesRed);


setSlice(3);
keep = newArray(lengthOf(xCoordinatesGrn));
coloc_red_sum = 0;
roiManager("Reset");
for(b=0; b<lengthOf(xCoordinatesGrn); b++) { 
	for(a=0; a<lengthOf(xCoordinatesRed); a++) {
	
		
		dist = sqrt(((xCoordinatesRed[a]-xCoordinatesGrn[b])*(xCoordinatesRed[a]-xCoordinatesGrn[b]))+((yCoordinatesRed[a]-yCoordinatesGrn[b])*(yCoordinatesRed[a]-yCoordinatesGrn[b])));
		
		if (dist < pixel_distance && keep[b] != true){
			
			keep[b] = true;
			run("Specify...","width=4 height=4 x="+xCoordinatesGrn[b]+" y="+yCoordinatesGrn[b]+" oval centered");
			roiManager("Add");
			run("Measure");
			coloc_red_sum += getResult("Mean",nResults-1);
			}else{
			keep[b] = false;
				}
		
		}
}
coloc_red_mean = coloc_red_sum/roiManager("Count");
print(title+"\tThe number of red foci \t"+lengthOf(xCoordinatesRed)+"\t The average intensity of the red channel \t"+out_mean+"\ttotal green foci\t"+lengthOf(xCoordinatesGrn)+"\tnumber of colocalising\t"+roiManager("Count")+"\tThe average coloc red intensity\t"+coloc_red_mean);