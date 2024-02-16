# TensorFlow Object Detection
This workflow adapts the official [TensorFlow object detection tutorial](https://www.tensorflow.org/hub/tutorials/object_detection) to perform inference (object detection and classification) on a dataset of images organized in directories. The pretrained [model](https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1) is obtained from TensorFlow Hub.

The primary objective of this workflow is to measure and benchmark data transfer from a storage resource or local disk. The user specifies a data directory, from which the workflow reads the images, processes them, and writes them back to a different location within the same directory. The workflow records the time taken to read and write the images. Users can specify the path to the data directory to align with the mount directory of a storage resource attached to the cluster, such as Lustre, NFS, or cloud storage.

### Image Preprocessing
Images ranging from 1MB to 5MB in size are selected from the [ImageNet Object Localization Challenge dataset](https://www.kaggle.com/c/imagenet-object-localization-challenge/data) and stored across 36 directories, each containing approximately 150MB of data. This amounts to a total of 5GB of data. These images are stored in the GCP bucket `gs://pw-public-4w3i9l8o7n6g5e4r3b2u1c0k/tf_object_detection/selected-images/JPEG-1M-5M/<i>`, where i is an integer ranging from 0 to 35.

### Image Processing
The user specifies the number of directories to process. Each worker then processes the JPEG images from the corresponding directories, starting from 0 up to the selected number. The images are enhanced to highlight identified objects using frames and labels, and then saved to an output directory. The output directory path mirrors the input directory path, with a -out suffix appended. For example:
1. Input directory: `/path/to/images/12345`
2. Output directory: `/path/to/images/12345-out`

### Data Transfer Time Masurements
The workflow tracks the following time measurements:
- **load-libs**: Time taken to load all required libraries from a Singularity file.
- **load-data**: Time required to load all images into memory, processed individually.
processing: Time spent processing all images. Images are processed individually using multiple cores.
- **write-data**: Time taken to save processed images to the output directory. Multiple images are saved concurrently using all available physical cores (vCPUs/2).

Each worker records these measurements and saves them to the output directory `/path/to/images/12345-out/mesurements.csv`. Once all workers finish their tasks, the measurements are merged to calculate statistics (minimum, maximum, average, standard deviation, etc.). These statistics are stored in the job directory: `/pw/jobs/<workflow-name>/<job-number>/data-transfer-time-measurements.csv`.


### Design Explorer
Two metrics are extraced for each processed image:
1. Number of identified objects per image (with more than a 10% score)
2. Maximum score of the identified objects

These scores, along with the paths to the input and output images, are saved for each image in the output directory `/path/to/images/12345-out/dex.csv`. Once all workers complete their tasks, these files are merged and stored in the job directory: `/pw/jobs/<workflow-name>/<job-number>/dex.csv`. Additionally, an HTML file is generated in this directory: `/pw/jobs/<workflow-name>/<job-number>/dex.html`. **Click on this file to open the Design Explorer parallel coordinate plot.**

