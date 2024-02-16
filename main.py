import json
import logging
import traceback
import sys

import parsl
import parsl_utils
from parsl_utils.config import config, form_inputs, executor_dict
from parsl_utils.data_provider import PWFile
from workflow_apps import *

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

if __name__ == '__main__':
    logger.info('Parsl Version: %s', parsl.__version__)
    
    logger.info('Loading Parsl Config')
    parsl.load(config)
    
    if form_inputs['inputs']['transfer_input_data']:
        logger.info('Launching tak to transfer input data from GCP bucket to %s', form_inputs['train']['data_directory'])

        # File with the credentials to read input data from a GCP bucket
        bucket_credentials = PWFile(
            url = "./bucket-credentials",
            local_path = "./bucket-credentials"
        )

        transfer_input_data_fut = transfer_input_data(
            form_inputs['train']['data_directory'],
            inputs = [bucket_credentials]
        )
    else:
        transfer_input_data_fut = None
    
    process_images_futs = [] 
    for i in range(int(form_inputs['train']['directories_to_process'])):
        logger.info(
            'Launching task to process images in directory %s', 
            os.path.join(form_inputs['train']['data_directory'], 'selected-images/JPEG-1M-5M', str(i))
        )

        tf_code = PWFile(
            url = "./tf_object_detection/",
            local_path = "./tf_object_detection/"
        )

        process_images_fut = process_images(
            form_inputs['train']['data_directory'],
            i,
            stdout = f'process_images_{i}.out', 
            stderr = f'process_images_{i}.err',
            inputs = [tf_code, transfer_input_data_fut]
        )

        process_images_futs.append(process_images_fut)

    logger.info('Launching task to generate design explorer files')

    dex_fut = merge_dex_results(
        form_inputs['train']['data_directory'],
        int(form_inputs['train']['directories_to_process']),
        form_inputs['train']['resource']['name'],
        inputs = process_images_futs,
        outputs = [
            PWFile(
                url = "./dex.csv",
                local_path = "./dex.csv"
            ),
            PWFile(
                url = "./dex.html",
                local_path = "./dex.html"
            )
        ]
    )

    dex_fut.result()
