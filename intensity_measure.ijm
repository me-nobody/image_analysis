//ImageJ macro written by Dominic Waithe for Ronan Broderick. (c) 2015.
//To be used on three channel .lsm files with in the first channel (dapi nucleus),
//second channel (cytoplasmic channel), third channel (condition of interest).

//Find unique id of an image
title = getTitle()
imid = getImageID()
//Make sure there are no selections and the colours are correct.
run("Select None");
run("Colors...", "foreground=black background=white selection=green");
run("Set Measurements...", "area mean standard modal min bounding integrated median redirect=None decimal=3");
//Goto the first slice, the dapi channel
setSlice(1);
//Duplicate that image
run("Duplicate...", "  channels=1");
//Set the auto threshold
setAutoThreshold("Huang dark");
//set the background to be black
setOption("BlackBackground", false);
//commit to the threshold
run("Convert to Mask");
//Clear the roiManager before we add any entries.
roiManager("Reset");
//Analyse the dapi signal to count all the cells.
run("Analyze Particles...", "size=200-Infinity pixel add");
//Select the original image
selectImage(imid);
//Set the channel to the 2nd channel, the cytoplasmic stain
setSlice(2);
//Duplicate so we can modify
run("Duplicate...", "  channels=2");
//Apply a median filter to the image to denoise partially
//run("Median...","radius=1");
run("Gaussian Blur...", "sigma=2");
//Apply auto threshold.
setAutoThreshold("Huang dark");
//With a black background
setOption("BlackBackground",false);
//Commit threshold
run("Convert to Mask");
//Make a selection from the mask for making measurements


rcount= roiManager("Count");
for(i=0;i<rcount;i++){
	roiManager("Select",i);
	run("Invert");
	
	
	}
run("Create Selection");
roiManager("Add");
//Return to the original image
//Select the second channel.
selectImage(imid);
setSlice(2);
//Overlay the selection
run("Restore Selection");
//Make the measurement.
run("Measure");

//Measure within the second channel.
CH2 = getResult("Mean",nResults-1);
CH2raw = getResult("RawIntDen",nResults-1);

//Select the third channel.
setSlice(3);
//Re-overlay with the selection
run("Restore Selection");
//Make the measurement on one of these channels.
run("Measure");
//Measure with the 3rd channel.
CH3 = getResult("Mean",nResults-1);
CH3raw = getResult("RawIntDen",nResults-1);

//Select None so we don't duplicate just the region (we want the whole image).
run("Select None");
run("Duplicate...", "duplicate channels=3");
//Blur to improve the foci detection.
run("Gaussian Blur...", "sigma=1");
//Now we restore the selection
run("Restore Selection");
//We find the maxima and add them to the ROI manager
run("Find Maxima...", "noise=30 output=[Point Selection]");
roiManager("Add");
//We then restore the region and repeat the foci detection just so we get the counts out directly
run("Restore Selection");
run("Find Maxima...","noise=30 output=Count");
CH3foci = getResult("Count",nResults-1);


//Print the output.
print(title,"\tnum of cells\t",roiManager("count"),"\tave intensity per pixel CH3\t",CH3,"\ttotal intensity CH3\t",CH3raw,"\tnum of foci CH3\t",CH3foci);
selectImage(imid);
close("\\Others");