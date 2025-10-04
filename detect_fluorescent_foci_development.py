import os,re
from java.io import File
from os import path
from ij import IJ, ImagePlus, ImageStack, VirtualStack, WindowManager
from ij.io import DirectoryChooser, FileSaver, FileOpener, Opener
from ij.gui import GenericDialog,Roi,Overlay
from ij.process import ImageProcessor, ImageConverter
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from ij.plugin import Duplicator, ChannelSplitter, ImageCalculator, ZProjector,MeasurementsWriter
from fiji.util.gui import GenericDialogPlus
from ij.io import OpenDialog  
# parse metadata
from loci.formats import ImageReader
from loci.formats import MetadataTools
# analyze particles  
from ij.plugin.frame import RoiManager
from ij.plugin.filter import ParticleAnalyzer
from ij.measure import ResultsTable,Measurements
import csv
import gc
import glob
import shutil

gc.enable() # collect garbage
gc.DEBUG_SAVEALL # program closes completely else files cannot be accessed
  
def get_image():
	# --- Clear log and close all images ---	
	IJ.log("\\Clear")
	IJ.run("Close All")
	gui = GenericDialogPlus("Open an image")
	gui.addFileField("CZI file path", "enter text here")
#	gui.addDirectoryOrFileField("Some_Path", "DefaultPath")
	gui.showDialog()

	if gui.wasOKed():
		image_path = gui.getNextString()
		IJ.log("image path is "+image_path)
		# jython recognizes single backslash as \\ and double backslash as \\\\
		# this module splits the file with \\\\ and rest of path elements with \\
		dir_path,file_name = image_path.split("\\\\")
		IJ.log(dir_path)
		IJ.log(file_name)
		image_path = dir_path  + "\\"+file_name # file path rectified
		IJ.log("revised image path is "+image_path)
		imps = BF.openImagePlus(image_path)
		imps_type = type(imps)
		IJ.log("imps type in get_image: "+str(imps_type))
		props_imps = len(imps)
		props_imps = str(props_imps)
		IJ.log("length of imps "+props_imps)
		for index,imp in enumerate(imps):
			IJ.log("the index is "+str(index))
			imp.show()

	else:
		gui_m = GenericDialogPlus("Message")
		gui_m.addMessage("File not chosen")
		gui_m.showDialog()
	return imps,image_path,file_name



def parse_metadata(image_path):
	reader = ImageReader()
	omeMeta = MetadataTools.createOMEXMLMetadata()
	reader.setMetadataStore(omeMeta)	
	reader.setId(image_path)
	seriesCount = reader.getSeriesCount()
	reader.close()
	imageCount = omeMeta.getImageCount()
	IJ.log("Total # of image series (from BF reader): " + str(seriesCount))
	IJ.log("Total # of image series (from OME metadata): " + str(imageCount))
	


def extractChannel(imps,image_path):	
	srcDir =  DirectoryChooser("Choose output folder").getDirectory()
	IJ.log("output folder is: "+srcDir)
	if srcDir is None:
		gui_m = GenericDialogPlus("Message")
		gui_m.addMessage("Folder not chosen")
		gui_m.showDialog()		
	# czi_image is a imageplus object but can be extracted only as the 0th index object from the array object created earlier
	imps = imps[0]
	split_channels = ChannelSplitter.split(imps) 
	image_dict = {}
	for image_ in split_channels:
		image_title = image_.getTitle()[:-4] # this is a .czi file
		IJ.log("image title: "+image_title)
		image_id = image_.getID()
		IJ.log("image id: "+str(image_id))
		image_.show()
		
		# this is a dangerous assignment based on Ronan's VIBGYOR sequence BGR
		# need to upgrade it based on channel intensity, independent of text search
		if "C1" in image_title:
			image_dict["dapi"] = image_
			file_name = image_title+"_dapi.tiff"
			save_path = os.path.join(srcDir,file_name)
			FileSaver(image_).saveAsTiff(save_path)
		elif "C2" in image_title:
			image_dict["green"] = image_
			file_name = image_title+"_green.tiff"
			save_path = os.path.join(srcDir,file_name)
			FileSaver(image_).saveAsTiff(save_path)
	 	elif "C3" in image_title:
	 		image_dict["red"] = image_
	 		file_name = image_title+"_red.tiff"
			save_path = os.path.join(srcDir,file_name)
			FileSaver(image_).saveAsTiff(save_path)
	for img_key in image_dict:
		key_value = image_dict.get(img_key).getTitle()
		img_key = str(img_key)
		IJ.log("channel "+img_key+" image title "+key_value)
	return image_dict,srcDir

def open_project_files(title="select the Ilastik project files"):
	gd = GenericDialog(title)
	nucleus_project = gd.addFileField("Nucleus project file","path",14)
	green_project = gd.addFileField("Green channel project file","path",14)
	red_project = gd.addFileField("Red channel project file","path",14)
	gd.showDialog()
	if gd.wasOKed():
		project_path = gd.getStringFields()
		nucleus_project_path = project_path[0].text
		green_project_path = project_path[1].text
		red_project_path = project_path[2].text
	return nucleus_project_path,green_project_path,red_project_path


def run_ilastik(project_file,input_imp=None):
	ilastik_project_file = project_file
	input_image = input_imp
	 # Run Ilastik Pixel Classification
	IJ.run("Run Pixel Classification Prediction", "projectfilename=["+ilastik_project_file+"] inputimage=["+input_image+"] pixelclassificationtype=Probabilities")
	# Find the output probability image  
	for id in WindowManager.getIDList():
		imp = WindowManager.getImage(id)
		title = imp.getTitle()
	if re.match(r'^[A-Z]:.+predictions\.h5/exported_data', title):
		IJ.log(title+ " desired output image found")
		title_2_list = title.split("/")
		windows_title = "\\".join(title_2_list)
		IJ.log("windows title "+windows_title)
		WindowManager.getCurrentImage().setTitle(windows_title) # select the probabilities hd5 image file
		IJ.run(imp, "Stack to Images", "") # split the prediction classes
		mirror_object_image = WindowManager.getImage("2")
		mirror_object_image.close()
		fluorescent_object_image = WindowManager.getImage("1") # get the image with objects labelled 255 and background labelled 0
		IJ.run(fluorescent_object_image, "Grays", "")
		fluorescent_object_image.getProcessor().setAutoThreshold("Default dark")
		IJ.run(fluorescent_object_image, "Convert to Mask", "")
		IJ.run(fluorescent_object_image, "Fill Holes", "")
		return fluorescent_object_image
	else:
		IJ.log("desired image not found")
		return None


#czi_image,image_path = get_image()
#parse_metadata(image_path)
#image_dict = extractChannel(czi_image,image_path)
#nucleus_project_path,green_project_path,red_project_path = open_project_files(title="select the Ilastik project files")
# run ilastik on nuclei
#fluorescent_object_mask = run_ilastik(nucleus_project_path)


def extract_masks():
	czi_image,image_path,file_name = get_image()
	base_file_name = file_name[:-4]
	image_dict = extractChannel(czi_image,image_path)
	nucleus_project_path,green_project_path,red_project_path = open_project_files(title="select the Ilastik project files")
	dapi_image = image_dict.get("dapi")
	dapi_image_id = dapi_image.getID()
	dapi_image_id = str(dapi_image_id)
	dapi_mask = run_ilastik(nucleus_project_path,input_imp=dapi_image_id)	
	dapi_mask.setTitle(base_file_name+"_dapi_mask")
	green_image = image_dict.get("green")
	green_image_id = green_image.getID()
	green_image_id = str(green_image_id)
	green_mask = run_ilastik(green_project_path,input_imp=green_image_id)
	green_mask.setTitle(base_file_name+"_green_mask")
	red_image = image_dict.get("red")
	red_image_id = red_image.getID()
	red_image_id = str(red_image_id)
	red_mask = run_ilastik(red_project_path,input_imp=red_image_id)
	red_mask.setTitle(base_file_name+"_red_mask")
	# close unnecessary windows
	main_image = WindowManager.getImage(file_name)
	main_image.close()
	c1_image_str = "C1-"+file_name
	c1_image = WindowManager.getImage(c1_image_str)
	c1_image.close()
	c2_image_str = "C2-"+file_name
	c2_image = WindowManager.getImage(c2_image_str)
	c2_image.close()
	c3_image_str = "C3-"+file_name
	c3_image = WindowManager.getImage(c3_image_str)
	c3_image.close()
	
	return file_name,dapi_mask,green_mask,red_mask
	
#file_name,dapi_mask,telg_mask,pml_mask = extract_masks()

# helper function to save nuclei csv files.
def save_nuclei_measurements(nuclei_table, output_dir, base_filename):
    """
    Save nuclei measurements to CSV
    """
    csv_filename = base_filename + "_nuclei_measurements.csv"
    file_path = os.path.join(output_dir, csv_filename)
    try:
    	nuclei_table.save(file_path)
    except error as e:
    	IJ.log(e+" file write error")

# create ROI from the nuclei mask and use it to extract foci per nuclei from telg and pml
def create_dapi_ROI(dapi_mask=None,file_name=None,srcDir=None):
	dapi_mask_path = IJ.getFilePath("open dapi mask image")
	dapi_mask = IJ.openImage(dapi_mask_path)
	dapi_mask.show()
	dapi_mask_ID = dapi_mask.getID()
	IJ.log("dapi_mask_id "+str(dapi_mask_ID))
	srcDir =  DirectoryChooser("Choose output folder").getDirectory()
	file_name= "demo"
#	images = WindowManager.getImageTitles()
	nuclei_mask = WindowManager.getImage(dapi_mask_ID)
#	nuclei_mask.show()
	IJ.run("Gaussian Blur...", "sigma=2")
	IJ.run("Convert to Mask")	
	IJ.run("Dilate")
	IJ.run("Fill Holes")
	dapi_mask_processor = dapi_mask.getProcessor().duplicate()
	dapi_mask.setProcessor("Nuclei mask", dapi_mask_processor)
	dapi_mask_processor.setThreshold(147, 147, ImageProcessor.NO_LUT_UPDATE)
	# Call the Thresholder to convert the image to a mask
	IJ.run(dapi_mask, "Convert to Mask", "")
	thresholded_nuclei = WindowManager.getCurrentImage()
	thresholded_nuclei.show()
	nuclei_table = ResultsTable()
	nuclei_roi_manager = RoiManager()
	nuclei_pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER|ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES|ParticleAnalyzer.SHOW_RESULTS, Measurements.ALL_STATS, nuclei_table,100,10000000,0.0,1.0)
	nuclei_pa.setRoiManager(nuclei_roi_manager)
	nuclei_pa.setResultsTable(nuclei_table)
	if thresholded_nuclei is not None:
		nuclei_pa.analyze(thresholded_nuclei,dapi_mask_processor)
		print("All nuclei ok")
		nuclei_table.show("Nuclei measurements")
		save_nuclei_measurements(nuclei_table, srcDir, file_name)
	file_name = file_name+"_dapi_mask.tiff"
	save_path = os.path.join(srcDir,file_name)
	FileSaver(thresholded_nuclei).saveAsTiff(save_path)
	dapi_mask.close()
	return thresholded_nuclei,nuclei_roi_manager,srcDir


# helper function to save foci counts for all nuclei
def save_foci_counts(foci_count_dict,output_dir, base_filename):
	"""
	Save foci counts per nuclei to csv
	"""
	nucleus = foci_count_dict["nucleus"]
	green = foci_count_dict["green_foci"]
	red = foci_count_dict["red_foci"]
	csv_filename = base_filename +  "_foci_counts.csv"
	csv_file_path = os.path.join(output_dir, csv_filename)
	fh = open(csv_file_path, mode='w')
	with open(csv_file_path,mode = 'w') as fh:
		writer = csv.DictWriter(fh, fieldnames=foci_count_dict.keys(),lineterminator='\r') # lineterminator to avoid spaces between lines
		writer.writeheader()  # Write header row
		for nucleus_obj,green_obj,red_obj in zip(nucleus,green,red):
			temp_dict = {"nucleus":nucleus_obj,"green_foci":green_obj,"red_foci":red_obj}
			writer.writerow(temp_dict)  # Write data 
		

# helper function to save foci csv files
def save_foci_measurements(foci_table=None, output_dir=None, base_filename=None, mask=None,roi_name = None):
    """
    Save measurements of foci for each nuclei for each channel to CSV
    """
    csv_filename = base_filename + "_" + mask + "_"+ roi_name+ "_foci_per_nuclei_measurements.csv"
    file_path = os.path.join(output_dir, csv_filename)
    try:
    	foci_table.save(file_path)
    except error as e:
    	IJ.log(e+" file write error")

def join_csv_files(output_dir=None, file_pattern=None, mask=None):
	"""
	join csv files for each channel to CSV
    https://stackoverflow.com/questions/74875493/concatenate-large-csv-files-without-pandas
    
    """
#	srcDir =  DirectoryChooser("Choose output folder").getDirectory()
#	image_file = IJ.openImage()
#	image_name = image_file.getTitle()[:-4]
	image_name = "demo"
	f_path_green = srcDir+"\\"+image_name+ "_green_output.csv"
	f_green = open(f_path_green, 'w')
	f_green.write("ID,Area,Mean,StdDev,Mode,Min,Max,X,Y,XM,YM,Perimeter,BX,BY,Width,Height,Major,Minor,Angle,Circularity,Feret,IntDen,Median,Skew,Kurt,%Area,RawIntDen,FeretX,FeretY,FeretAngle,MinFeret,AR,Round,Solidity\n")
	path_green = srcDir + "*green*foci_per_nuclei*.csv"
	files = glob.glob(path_green)
	for file_ in files:
		with open(file_, 'r') as open_csv:
			first_row = True
			for line in open_csv:
            # Ignore the header row
				if first_row:
					first_row = False
					continue
				f_green.write(line)
				IJ.log("green channel file was read")
	f_green.close()
	
	f_path_red = srcDir+"\\"+image_name +"_red_output.csv"		
	f_red = open(f_path_red, 'w')
	f_red.write("ID,Area,Mean,StdDev,Mode,Min,Max,X,Y,XM,YM,Perimeter,BX,BY,Width,Height,Major,Minor,Angle,Circularity,Feret,IntDen,Median,Skew,Kurt,%Area,RawIntDen,FeretX,FeretY,FeretAngle,MinFeret,AR,Round,Solidity\n")
	path_red = srcDir + "*red*foci_per_nuclei*.csv"	
	files = glob.glob(path_red)
	for file_ in files:
		with open(file_, 'r') as open_csv:
			first_row = True
			for line in open_csv:
            # Ignore the header row
				if first_row:
					first_row = False
					continue
				f_red.write(line)
				IJ.log("red channel file was read")
	f_red.close()


# helper function to measure values in a ROI
def measure_values(subselected_mask=None,srcDir=None,file_name=None,mask=None,roi_name=None):
	"""
    calculate measurements of foci for each nuclei to CSV
    """
#	subselected_mask_path = IJ.getFilePath("open subselected mask image")
#	subselected_mask = BF.openImagePlus(subselected_mask_path)[0]
	# Create a table to store the results
	foci_table = ResultsTable()
	# IMPORTANT
	# Create a hidden ROI manager, to store a ROI for each blob or cell	
	# there can't be 2 ROI windows. Hence, this ROI manager window is set to False
	subselected_mask_roi_manager = RoiManager(False)	
	# properties of particle analyzer are added using bitwise OR
	pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER|ParticleAnalyzer.SHOW_RESULTS, Measurements.ALL_STATS, foci_table,0.0,200.0,0.0,1.0)
	pa.setRoiManager(subselected_mask_roi_manager)
	pa.setResultsTable(foci_table)	
	if subselected_mask is not None:
		pa.analyze(subselected_mask)
		sub_mask_counts = subselected_mask_roi_manager.getCount()		
		print("All foci ok")		
#		foci_table.show("Foci measurements") # the foci_table can be passed to be shown in the main function
		# saving individual nuclei
#		save_foci_measurements(foci_table = foci_table, output_dir = srcDir, base_filename = file_name, mask = mask)
		pa.setHideOutputImage(True)
		subselected_mask_roi_manager.reset() # IMPORTANT this needs to be reset for each nuclei
	else:
		print("There was a problem in analyzing",subselected_mask) 
	return sub_mask_counts,foci_table	

# helper function to move images to subfolder
def move_images(output_folder=None):
	"""
	 move images to sub-folder
	
	"""
	srcDir =  DirectoryChooser("Choose output folder").getDirectory()
	sub_path = srcDir+"\\"+"images"
	if not os.path.exists(sub_path):
		os.mkdir(srcDir+"images") # create images folder and exist_ok checks for a previous folder	
	image_path = srcDir +"*.jpg" # file pattern for images to move
	
	files = glob.glob(image_path)	
	for file_path in files:				
		file_name = file_path.split("\\")[-1]
		new_path= sub_path+"\\"+file_name		
		shutil.move(file_path,new_path)
	print("done")	

def get_foci_per_nuclei(roi_manager=None,srcDir=None,green_mask=None,red_mask=None,file_name=None):
	file_name = "demo" # temp- for standalone execution
	roi_manager = roi_manager
	green_mask_path = IJ.getFilePath("open green mask image")
	green_mask = BF.openImagePlus(green_mask_path)[0]
	red_mask_path = IJ.getFilePath("open red mask image")
	red_mask = BF.openImagePlus(red_mask_path)[0]
	# begin iterating over the ROI manager
	nuclei_count = 0
	num_roi = roi_manager.getCount()
	mask_dict = {"green_mask":green_mask,"red_mask":red_mask}
	green_foci = []
	red_foci = []
	nucleus = []
	foci_count_dict = {"nucleus":nucleus,"green_foci":green_foci,"red_foci":red_foci}
	for i in range(num_roi):
		roi = roi_manager.getRoi(i)
		roi_name = roi.getName()
		nucleus.append(roi_name) # get each nucleus name
		IJ.log("roi name "+roi_name)
		# iterate over the color channel masks
		for mask in mask_dict:			
			try:
				duplicate_mask = mask_dict.get(mask).duplicate()
				duplicate_mask.show() # the window manager can't work if the image is not shown				
				sub_image = WindowManager.getCurrentImage()	# a separate sub_image is needed to save the nuclei 
				roi_manager.select(i) # order of these following commands are very important
				sub_image.show()
			except Exception as e:
				IJ.log("duplicate image couldn't be opened due to " + str(e))
			try:
				IJ.run("Clear Outside")
				# here the FUNCTION TO MEASURE INDIVIDUAL FOCI PER NUCLEI is called
				sub_mask_counts,foci_table = measure_values(subselected_mask = sub_image,srcDir = srcDir,file_name = file_name,mask = mask,roi_name = roi_name)
				# here the FUNCTION TO SAVE THE FOCI TABLE PER NUCLEI 
				save_foci_measurements(foci_table = foci_table, output_dir = srcDir, base_filename = file_name, mask = mask,roi_name = roi_name)
				IJ.log("subselected mask counts "+str(sub_mask_counts))
				foci_table.show("Foci measurements") 
				if mask == "green_mask":
					green_foci.append(sub_mask_counts)					
				elif mask == "red_mask":
					red_foci.append(sub_mask_counts)					
				else:
					IJ.log("masks could not be counted")
				IJ.run("Grays")
				ovly = Overlay() # overlay the nuclei ROI on the images
				ovly.add(roi)
				sub_image.setOverlay(ovly)
			except Exception as e:
				IJ.log("overlay was unsuccessful due to " + str(e))
			try:				
				image_name = file_name+"_" + mask+"_"+roi_name+".jpg"
				image_path = os.path.join(srcDir,image_name)
				FileSaver(sub_image).saveAsJpeg(image_path)
				sub_image.close()
			except Exception as e:
				IJ.log(str(i)+" mask image could not be saved due to " + str(e))
				continue
				
			sub_image.close()
			duplicate_mask.close()
	save_foci_counts(foci_count_dict,srcDir, file_name)
	roi_manager.close()
#	WindowManager.closeAllWindows()
	gc.collect()
#nuclei_mask,roi_manager,srcDir = create_dapi_ROI()
#get_foci_per_nuclei(roi_manager,srcDir)
#join_csv_files()
move_images()