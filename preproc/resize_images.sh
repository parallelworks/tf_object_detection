#!/bin/tcsh
#-----------------------
# Batch process a data set
# to resize images.
#-----------------------

# It may be easier to just copy everything
# over and then work on it here and incrementally
# push resized images back to bucket. Code
# immendiately below is just a possible template.

# Loop over directories
#foreach dir (`gsutil ls gs://demoworkflows/tf_object_detection/images`)
    #echo Working on $dir

    # If *-out, ignore it.
    
    # Copy from bucket to local for processing
    # gsutil cp $dir ./

    # Get basename
    

    # Create new directory
    #mkdir -p ${small}${dir}

    # Process images 
#end

#====================================================
# Starting with n01440764 = 152MB
# Range of sizes: 1.8K - 7.2M => 4000x range
#====================================================
# Small = ~100k or more per image => 200,000 area.
# Takes <1 min, 121MB output -> 0.093MB avg image size.
# Range of sizes: 10K to 350K (35x range).
#====================================================
# Medium = ~1M or more per image => 2,000,000 area.
# Takes ~2 min, 568MB output -> 0.44MB avg image size.
# Range of sizes: 48K to 1.7MB = (35x range)
#====================================================
# Medium2 = 4,000,000 area.
# Takes ~4 min, 921MB output -> 0.71MB avg image size.
# Range of sizes: 77K to 3.0MB = (78x range)
#====================================================
# Large = ~10M or more per image => 20,000,000 area.
# Takes 17min, 2.9GB output -> 2.2MB avg image size.
# Range of sizes: 248K to 10MB -> 43x range
#====================================================
# Experiment with uncompressed .bmp format:
# tiny_bmp:
#   area: 2000
#   output: 11MB -> 8K avg
#   min: 5.8K
#   max: 6.2K
#   runtime: <30 s
#====================================================
# small_bmp:
#   area: 33000
#   output: 127MB -> 98K avg
#   min: 98K
#   max: 99K
#   runtime: 28 s
#====================================================
# medium_bmp:
#   area: 330000
#   output: 1.3GB -> 1MB avg
#   min: 981K
#   max: 991K
#   runtime: 41s
# Core of loop:
#====================================================
set dir = n01440764
set ext_in = .JPEG
set ext_out = .bmp
foreach file (`ls -1 ${dir}`)
    echo Working on $file
    set bn = `basename $file $ext_in`
    convert -resize '33000@' ${dir}/${bn}${ext_in} small_bmp/${dir}/${bn}${ext_out}
end
