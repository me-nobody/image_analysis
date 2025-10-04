//This macro requires the SlideBook plugin for the BioFormats macro extensions, which is found through the ImageJ/Help/Update... menu
 //select  Langauage as IJ1 Macro to run

//CLEAR LOG
print("\\Clear");

// CLOSE ALL OPEN IMAGES
while (nImages>0) { 
	selectImage(nImages); 
    close(); 
}


//START MESSAGE
print("**** STARTING THE MACRO SAVE SLIDE BOOK FILES ****");


//Defining directories for saving and analysis
dir = getDirectory("Select a directory containing one or several .sld files");
files = getFileList(dir);
saveDir = dir + "/Extracted/";
File.makeDirectory(saveDir);

//Batch process .tif extraction
setBatchMode(true);
k=0;
n=0;
run("Bio-Formats Macro Extensions");
for(f=0; f<files.length; f++) {
	if(endsWith(files[f], ".sld")) {
		k++;
		id = dir + files[f];
		Ext.setId(id);
		Ext.getSeriesCount(seriesCount);
		n+=seriesCount;
		for (i=0; i<seriesCount; i++) {
			run("Bio-Formats Importer", "open=["+id+"] color_mode=Default view=Hyperstack stack_order=XYCZT use_virtual_stack series_"+(i+1));			
			getDimensions(width, height, channels, slices, frames);
			if (channels >1) run("Split Channels");
			ch_nbr = nImages ; 
		for ( c = 1 ; c <= ch_nbr ; c++){
			selectImage(c);
			currentImage_name = getTitle();
			saveAs("tiff", saveDir + currentImage_name+".tif");
		}
			// make sure to close every images befores opening the next one
      		run("Close All");
     		}	
		}
	}
setBatchMode(false);

print("All images analysed");
print("***** Macro done *****");
exit();