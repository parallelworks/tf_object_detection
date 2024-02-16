import os
from typing import Optional, List
from parsl.app.app import bash_app, python_app


@bash_app
def transfer_input_data(data_directory: str, inputs: Optional[List[str]] = None,  stdout:str = 'transfer_input_data.out', 
                        stderr: str = 'transfer_input_data.err') -> None:
    import os

    return '''
    base64 -d {bucket_credentials} > {cwd}/bucket-credentials.json

    export CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE={cwd}/bucket-credentials.json

    mkdir -p {data_directory}
    
    if [ -d "{data_directory}/selected-images" ]; then
        echo "Directory {data_directory}/selected-images already exists. Data will not be transferred."
    else
        mkdir {data_directory}/selected-images
        gcloud storage cp -r gs://pw-public-4w3i9l8o7n6g5e4r3b2u1c0k/tf_object_detection/selected-images/* {data_directory}/selected-images/
    fi

    if [ -d "{data_directory}/opt" ]; then
        echo "Directory {data_directory}/opt already exists. Data will not be transferred."
    else
        mkdir {data_directory}/opt
        gcloud storage cp -r gs://pw-public-4w3i9l8o7n6g5e4r3b2u1c0k/opt/tensorflow/tensorflow_latest-gpu-jupyter-extra.sif {data_directory}/opt/
    fi

    rm {cwd}/bucket-credentials.json
    '''.format(
        data_directory = data_directory,
        bucket_credentials = inputs[0].local_path,
        cwd = os.getcwd()
    )

@bash_app
def process_images(data_directory: str, dir_number: int, inputs: Optional[List[str]] = None,
                   stdout: str = 'std.out', stderr: str = 'std.err') -> None:
    import os
    return '''
        # FIXME: Need to copy singularity file
        # fusemount not supported in singularity 3.5 --> Install 3.6+ and make new singularity container
        # Run TensorFlow
        singularity exec -B `pwd`:`pwd` -B {data_directory}:{data_directory} {path_to_sing} /usr/local/bin/python {pyscript} --imgdir {imgdir} --outdir {outdir} --start_time $(date  +"%s")
        chmod 777 {outdir} -R
    '''.format(
        data_directory = data_directory,
        path_to_sing = os.path.join(data_directory, 'opt/tensorflow_latest-gpu-jupyter-extra.sif'),
        pyscript = os.path.join(inputs[0].local_path, 'main.py'),
        imgdir = os.path.join(data_directory, 'selected-images/JPEG-1M-5M', str(dir_number)),
        outdir = os.path.join(data_directory, 'selected-images/JPEG-1M-5M', str(dir_number) + '-out')
    )

# Assumes the file system is already mounted!
@python_app
def merge_dex_results(data_directory: str, directories_to_process: int, resource_name: str,
                      inputs: Optional[List[str]] = None, outputs: Optional[List[str]] = None) -> None:
    
    import pandas as pd
    import os

    if data_directory.endswith('/'):
        data_directory = data_directory[:-1]

    data_directory_link = os.path.join(os.getcwd(), 'data')
    images_root_dir = os.path.join(data_directory, 'selected-images/JPEG-1M-5M')
    # Path to the directory link that is mounted in /pw/clusters
    pw_mounted_dir = data_directory_link.replace(os.getenv('HOME'), os.path.join('/pw/clusters', resource_name))
        
    os.symlink(data_directory, data_directory_link)
    print(f"Symbolic link created successfully from {data_directory} to {data_directory_link}")
    
    # Merge results for design explorer:
    print('Creating CSV file for Design Explorer', flush = True)
    dex_df = pd.concat([ pd.read_csv(os.path.join(images_root_dir, f'{i}-out', 'dex.csv')) for i in range(directories_to_process) ])
    dex_df['img:original'] = dex_df['img:original'].map(lambda x: x.replace(data_directory, pw_mounted_dir))
    dex_df['img:processed'] = dex_df['img:processed'].map(lambda x: x.replace(data_directory, pw_mounted_dir))
    dex_df.to_csv(outputs[0].local_path, index = False)

    print('Creating HTML file for Design Explorer', flush = True)
    dex_html = open(outputs[1].local_path, 'w')
    dex_html.write(
        '''
        <html style="overflow-y:hidden;background:white"><a
            style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px"
            href="/DesignExplorer/index.html?datafile={csv}&colorby=max_score"
            target="_blank">Open in New Window
        </a><iframe
            width="100%"
            height="100%"
            src="/DesignExplorer/index.html?datafile={csv}&colorby=max_score"
            frameborder="0">
        </iframe></html>
        '''.format(csv = outputs[0].path)
    )
    dex_html.close()