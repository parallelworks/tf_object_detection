import parsl
import os
import time,sys

import pandas as pd

from parsl.app.app import python_app, bash_app
from parsl.data_provider.files import File
from parsl.data_provider.pwfiles import Path

from parslpw import pwconfig,pwargs

# sudo mount -vvv -o sync,nolock,vers=4 {mount_ip}:/ultxvfs2 {mount_dir}
# Mount: gcsfuse demoworkflows /pw/storage/demoworkflows_bucket
# Unmount: fusermount -u /home/shared/local_folder/
# --file-mode
#ubuntu@alvaro-tmp-2:~$ sudo chown ubuntu -R /home/ubuntu/.config/gcloud
#ubuntu@alvaro-tmp-2:~$ gcloud auth activate-service-account --key-file gs-demoworkflows
# gsutil -m rsync -r /mnt/images gs://demoworkflows/tf_object_detection/images
@bash_app
def process_images(mount_cmd, mount_dir, path_to_sing, imgdir, outdir, inputs=[], outputs=[], stdout = 'std.out', stderr = 'std.err'):
    return '''
        # Mount data
        if [ -z "$(ls -A {mount_dir})" ]; then
            echo {mount_cmd}
            sudo mkdir -p {mount_dir}
            sudo chmod 777 {mount_dir} -R
            {mount_cmd}
        fi
        # FIXME: Need to copy singularity file
        # fusemount not supported in singularity 3.5 --> Install 3.6+ and make new singularity container
        # Run TensorFlow
        singularity exec -B `pwd`:`pwd` -B {mount_dir}:{mount_dir} {path_to_sing} /usr/local/bin/python {pyscript} --imgdir {imgdir} --outdir {outdir} --start_time $(date  +"%s")
        chmod 777 {outdir} -R
    '''.format(
        mount_cmd = mount_cmd,
        mount_dir = mount_dir,
        path_to_sing = path_to_sing,
        pyscript = './tf_object_detection/main.py',
        imgdir = imgdir,
        outdir = outdir
    )


# Assumes the file system is already mounted!
@python_app
def merge_dex_results(worker_mount_dir, pw_mount_dir, imgdirs, outputs = [], stdout = 'std.out', stderr = 'std.err'):
    import pandas as pd
    import os

    # Merge results for design explorer:
    print('Creating CSV file for Design Explorer', flush = True)
    dex_df = pd.concat([ pd.read_csv(os.path.join(worker_mount_dir, img + '-out', 'dex.csv')) for img in imgdirs ])
    dex_df['img:original'] = dex_df['img:original'].map(lambda x: x.replace(worker_mount_dir, pw_mount_dir))
    dex_df['img:processed'] = dex_df['img:processed'].map(lambda x: x.replace(worker_mount_dir, pw_mount_dir))
    dex_df.to_csv(outputs[0].local_path, index = False)

    print('Creating HTML file for Design Explorer', flush = True)
    dex_html = open(outputs[1].local_path, 'w')
    dex_html.write(
        '''
        <html style="overflow-y:hidden;background:white"><a
            style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px"
            href="/preview/DesignExplorer/index.html?datafile={csv}&colorby=max_score"
            target="_blank">Open in New Window
        </a><iframe
            width="100%"
            height="100%"
            src="/preview/DesignExplorer/index.html?datafile={csv}&colorby=max_score"
            frameborder="0">
        </iframe></html>
        '''.format(csv = os.path.join(os.getcwd(), outputs[0].local_path))
    )
    dex_html.close()


# Assumes the file system is already mounted!
@python_app
def merge_measurements(worker_mount_dir, imgdirs, outputs = [], stdout = 'std.out', stderr = 'std.err'):
    import pandas as pd
    import os
    measurements_df = pd.concat([ pd.read_csv(os.path.join(worker_mount_dir, img + '-out', 'measurements.csv')) for img in imgdirs ])
    print(measurements_df)
    measurements_df.describe().to_csv(outputs[0].local_path)


if __name__ == '__main__':
    parsl.load(pwconfig)
    os.makedirs('./logs', exist_ok = True)

    if pwargs.data_source == 'gcp_bucket':
        mount_cmd = 'gcsfuse --file-mode 777 --dir-mode 777 --implicit-dirs {bucket_name} {mount_dir}'.format(
            bucket_name = pwargs.bucket_name,
            mount_dir = pwargs.worker_mount_dir
        )
    else:
        mount_cmd = 'sudo mount -vvv -o sync,nolock,vers=4 {mount_ip}:/ultxvfs2 {mount_dir}'.format(
            mount_ip = pwargs.mount_ip,
            mount_dir = pwargs.worker_mount_dir
        )

    print('Mount command:\n' + mount_cmd, flush = True)

    futs = []
    imgdirs = pwargs.imgdirs.split('---')

    for imgdir in imgdirs:
        print('Processing images in directory: ' + imgdir, flush = True)

        fut = process_images(
            mount_cmd,
            pwargs.worker_mount_dir,
            pwargs.path_to_sing,
            os.path.join(pwargs.worker_mount_dir, imgdir),
            os.path.join(pwargs.worker_mount_dir, os.path.dirname(imgdir), os.path.basename(imgdir) + '-out'),
            inputs = [Path('./tf_object_detection')],
            outputs = [
                Path('logs/std-{}.out'.format(os.path.basename(imgdir)), scheme = 'stream'),
                Path('logs/std-{}.out'.format(os.path.basename(imgdir)), scheme = 'stream')
            ],
            stdout = 'logs/std-{}.out'.format(os.path.basename(imgdir)),
            stderr = 'logs/std-{}.out'.format(os.path.basename(imgdir))
        )
        futs.append(fut)

    # Wait for results:
    for fut,imgdir in zip(futs, imgdirs):
        print('Waiting for images in: ' + imgdir, flush = True)
        fut.result()

    # Merge results for design explorer:
    print('Creating Design Explorer files', flush = True)
    dex_fut = merge_dex_results(
        pwargs.worker_mount_dir,
        pwargs.pw_mount_dir,
        imgdirs,
        outputs = [
            Path('./dex.csv'),
            Path('./dex.html'),
            Path('logs/std-merge-dex.out', scheme = 'stream'),
            Path('logs/std-merge-dex.err', scheme = 'stream')
        ],
        stdout = 'logs/std-merge-dex.out',
        stderr = 'logs/std-merge-dex.err'
    )

    # FIXME: The python_apps dont mount the file system
    # If just one image directory is selected stop workflow here until worker is done
    if len(imgdirs) == 1:
        dex_fut.result()
        print('Design Explorer files are ready', flush = True)

    # Merge measurements:
    print('Merging measurements', flush = True)
    measurements_fut = merge_measurements(
        pwargs.worker_mount_dir,
        imgdirs,
        outputs = [
            Path('./measurements.csv'),
            Path('logs/std-merge-measurements.out', scheme = 'stream'),
            Path('logs/std-merge-measurements.err', scheme = 'stream')
        ],
        stdout = 'logs/std-merge-measurements.out',
        stderr = 'logs/std-merge-measurements.err'
    )

    if len(imgdirs) > 1:
        dex_fut.result()
        print('Design Explorer files are ready', flush = True)

    measurements_fut.result()
    print('Measurements are ready', flush = True)
