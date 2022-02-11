# TensorFlow Object Detection

The official TensorFlow [object detection tutorial](https://www.tensorflow.org/hub/tutorials/object_detection) is adapted in this workflow to run inferrence (object detection and classification) in a data set of images sorted by directories. The [model](https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1) is pretrained and downloaded from TensorFlow hub.


### Image processing
Every worker processes the JPEG images under a given directory of the list specified in the input form, where each member is separated by three dashes (`---`). The images are edited to highlight the identified objects with frames and labels and then saved back to an output directory. The path of the output directory is the same as the path to the input directory with an appended `-out` string. For example:
1. Input directory: `/path/to/images/12345`
2. Output directory: `/path/to/images/12345-out`

### Time measurements:
The workflow performs the following time measurements:
1. **load-libs:** Time to load all the required libraries. These are loaded from a singularity file
2. **load-data:** Time to load all the images into memory. These are loded one by one.
3. **processing:** Time to process all the images. Images are processed one by one using multiple cores.
4. **write-data:** Time to write the processed images to the output directory. Multiple images are saved in parallel using all the physical cores (vCPUs/2) available.

These measurements are taken by each worker and saved to the output directory `/path/to/images/12345-out/mesurements.csv`. When all the workers have completed their tasks the measurements are merged to compute statistics (min, max, average, std, ...). These statistics are saved in the job directory: `/pw/jobs/job-dir/measurements.csv`.


### Design explorer:
Two metrics are extraced for each processed images:
1. Number of identified objects per image (with more than a 10% score)
2. Maximum score of the identified objects


These scores and the corresponding paths to the input and output images are saved for each image in the output directory  `/path/to/images/12345-out/dex.csv`. When all the workers have completed their tasks these files are merged and saved in the job directory: `/pw/jobs/job-dir/dex.csv`. The corresponding HTML file is also created under this directory: `/pw/jobs/job-dir/dex.html`. Click on this file to open the design explorer parallel coordinate plot.



### Data sources:

Three data sources are supported:
1. **Vcinity NFS:** NFS mount from AWS west
2. **Direct NFS:** NFS mount from Azure east
3. **GCP bucket:** gcsfuse from a multiregional bucket


### Workflow defaults
5GB of image were selected from the 400GB of in the [ImageNet dataset](https://www.kaggle.com/c/imagenet-object-localization-challenge/data). The full dataset is downloaded to the persistent disk imagenet-object-localization in GCP. The selected data is distributed along 37 directories with 1300 images each (48100 images in total). The average size of each directory and image is 0.14GB and 0.1M, respectively.

The data was copied to the following locations:
1. Vcinity NFS: `54.241.247.242/ultxvfs2/images`
2. Direct NFS: `40.71.67.138/ultxvfs2/images`
3. GCP bucket: `gs://demoworkflows/tf_object_detection/images`

The singularity files was copied to the following locations:
1. Vcinity NFS: `54.241.247.242/ultxvfs2/opt/tensorflow`
2. Direct NFS: `40.71.67.138/ultxvfs2/opt/tensorflow`
3. GCP bucket: `gs://demoworkflows/tf_object_detection/opt/tensorflow`

 To mount all the data sources in the user PW account run:
`bash /pw/workflows/tf_object_detection/mount_defaults.sh`

### Requirements:

#### Software
- [Singularity 3.6+](https://sylabs.io/guides/3.0/user-guide/installation.html)
- Singularity definition file (singularity.txt in workflow directory). Run the command: `singularity build tensorflow_latest-gpu-jupyter-extra.sif singularity.txt`
- `apt-get install nfs-common -y`
- `apt-get install gcsfuse`

The software is installed in GCP image `ubuntu1804-singularity363-nfs-gcsfuse-worker`


#### Network:
To use NFS the worker needs access to the internet through an IP address with access to the Vcinity server. This was implemented using a NAT-Gateway in the GCP region `us-west2` in pool gcpvcinity of the demoworkflows account in PW.


#### PW account:
The user needs to mount the data sources (NFS or GCSFUSE) in their account before running the workflow. Run:

`bash /pw/workflows/tf_object_detection/mount_defaults.sh`

