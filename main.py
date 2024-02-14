import json
import traceback, sys

import parsl
print(parsl.__version__, flush = True)

import parsl_utils
from parsl_utils.config import config, form_inputs, executor_dict
from parsl_utils.data_provider import PWFile

from workflow_apps import *

if __name__ == '__main__':
    print('Loading Parsl Config', flush = True)
    parsl.load(config)
    
    pytorch_inputs = {
        "model_path": './vae_model.pth',
        "latent_size": int(form_inputs['pytorch']['latent_size']),
        "num_epochs": int(form_inputs['pytorch']['num_epochs']),
        "learning_rate": float(form_inputs['pytorch']['learning_rate']),
        "num_digits": int(form_inputs['pytorch']['num_digits']),
        "gen_data_dir": './generated_data/'
    }
    
    # Transfer files
    model_file = PWFile(
        url = pytorch_inputs['model_path'],
        local_path = pytorch_inputs['model_path']
    )

    pytorch_dir = PWFile(
        url = './pytorch/',
        local_path = './pytorch/'
    )

    pytorch_inputs_json = PWFile(
        url = "./pytorch_inputs.json",
        local_path = "./pytorch_inputs.json"
    )
    
    with open(pytorch_inputs_json.local_path, 'w') as file:
        json.dump(pytorch_inputs, file, indent=4)

    generated_data = PWFile(
        url = pytorch_inputs['gen_data_dir'],
        local_path = pytorch_inputs['gen_data_dir']
    )

    # Run workflow:
    print('\n\nTraining model', flush = True)
    train_fut = train(
        executor_dict['train']['load_pytorch'],
        inputs = [ pytorch_dir, pytorch_inputs_json ],
        outputs = [ model_file ]
    )
    train_fut.result()
    
    print('\n\nGenerating data', flush = True)
    generate_data_fut = generate_data(
        executor_dict['inference']['load_pytorch'],
        inputs = [ pytorch_dir, pytorch_inputs_json, model_file, train_fut],
        outputs = [ generated_data ]
    )

    generate_data_fut.result()
            
    # Design Explorer:
    prepare_design_explorer()