import numpy as np
import argparse
import csv
import os
import glob
import datetime
import time
import logging
import h5py
import librosa

from utilities import (get_labels_metadata, create_folder, get_filename, create_logging, 
    float32_to_int16, pad_or_truncate, read_metadata)


def pack_waveforms_to_hdf5(args):
    """Pack waveform and target of several audio clips to a single hdf5 file. 
    This can speed up loading and training.
    """

    # Arguments & parameters
    audios_dir = args.audios_dir
    csv_path = args.csv_path
    waveforms_hdf5_path = args.waveforms_hdf5_path
    mini_data = args.mini_data
    sample_rate = args.sample_rate
    classes_num = args.classes_num
    clip_samples = sample_rate*10

    _,_,_,_,id_to_ix,_ = get_labels_metadata()

    # Paths
    if mini_data:
        prefix = 'mini_'
        waveforms_hdf5_path += '.mini'
    else:
        prefix = ''

    create_folder(os.path.dirname(waveforms_hdf5_path))

    logs_dir = '_logs/pack_waveforms_to_hdf5/{}{}'.format(prefix, get_filename(csv_path))
    create_folder(logs_dir)
    create_logging(logs_dir, filemode='w')
    logging.info('Write logs to {}'.format(logs_dir))
    
    # Read csv file
    meta_dict = read_metadata(csv_path, classes_num, id_to_ix)

    if mini_data:
        mini_num = 10
        for key in meta_dict.keys():
            meta_dict[key] = meta_dict[key][0 : mini_num]

    audios_num = len(meta_dict['audio_name'])

    # Pack waveform to hdf5
    total_time = time.time()

    with h5py.File(waveforms_hdf5_path, 'w') as hf:
        hf.create_dataset('audio_name', shape=((audios_num,)), dtype='S20')
        hf.create_dataset('waveform', shape=((audios_num, clip_samples)), dtype=np.int16)
        hf.create_dataset('target', shape=((audios_num, classes_num)), dtype=np.bool)
        hf.attrs.create('sample_rate', data=sample_rate, dtype=np.int32)

        # Pack waveform & target of several audio clips to a single hdf5 file
        for n in range(audios_num):
            audio_path = os.path.join(audios_dir, meta_dict['audio_name'][n])

            if os.path.isfile(audio_path):
                logging.info('{} {}'.format(n, audio_path))
                (audio, _) = librosa.core.load(audio_path, sr=sample_rate, mono=True)
                audio = pad_or_truncate(audio, clip_samples)

                hf['audio_name'][n] = meta_dict['audio_name'][n].encode()
                hf['waveform'][n] = float32_to_int16(audio)
                hf['target'][n] = meta_dict['target'][n]
            else:
                logging.info('{} File does not exist! {}'.format(n, audio_path))

    logging.info('Write to {}'.format(waveforms_hdf5_path))
    logging.info('Pack hdf5 time: {:.3f}'.format(time.time() - total_time))
          

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--csv_path', type=str, required=True, help='Path of csv file containing audio info.')
    parser.add_argument('--audios_dir', type=str, required=True, help='Directory to save out downloaded audio.')
    parser.add_argument('--waveforms_hdf5_path', type=str, required=True, help='Path to save out packed hdf5.')
    parser.add_argument('--mini_data', action='store_true', default=False, help='Set true to only download 10 audios for debugging.')
    parser.add_argument('--sample_rate', type=int, default=44100, help='Sample rate of the used audios')
    parser.add_argument('--classes_num', type=int, default=110, help='The amount of classes used in the dataset')

    args = parser.parse_args()
    pack_waveforms_to_hdf5(args)
