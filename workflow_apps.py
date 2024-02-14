import os
from parsl.app.app import bash_app

@bash_app
def transfer_input_data(data_directory):
    
    return '''
    mkdir -p {data_directory}
    
    if [ -d "{data_directory}/selected-images" ]; then
        echo "Directory {data_directory}/selected-images already exists. Data will not be transferred."
    else
        gcloud storage cp -r gs://pw-public-4w3i9l8o7n6g5e4r3b2u1c0k/tf_object_detection/selected-images {data_directory}/selected-images
    fi

    if [ -d "{data_directory}/opt" ]; then
        echo "Directory {data_directory}/opt already exists. Data will not be transferred."
    else
        gcloud storage cp -r gs://pw-public-4w3i9l8o7n6g5e4r3b2u1c0k/tf_object_detection/opt {data_directory}/opt
    fi

'''
