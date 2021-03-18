from Visualization.create_cam import create_cam
import argparse
import json
import os
import sys
import time
import torch
import torch.optim as optim
import random
import numpy as np
from utils import load_params, save_params


def parse_args(args):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="choose the mode",
        epilog="python run.py mode")

    # required input parameters
    parser.add_argument(
        'mode', type=str,
        help='train or visual, cam')
    #TRAIN SECTION
    parser.add_argument(
        '--seed', type=int, default=1,
        help='fix random seed')
    parser.add_argument(
        '--batch_size', type=int, default=128,
        help='set mini-batch size')
    parser.add_argument(
        '--patience', type=int, default=10,
        help='set mini-batch size')
    parser.add_argument(
        '--nn_type', type=str, default='lenet5',
        help='choose NeuralNetwork type')
    parser.add_argument(
        '--device', type=str, default='gpu',
        help='choose NeuralNetwork')
    parser.add_argument(
        '--colab', type=bool, default=False,
        help='if you are in colab use it')
    parser.add_argument(
        '--num_workers', type=int, default=3,
        help='number of process you have')
    parser.add_argument(
        '--log', type=bool, default=True,
        help='generate log')
    #TRAIN OPTION BY NN
    nn_type = parser.parse_known_args(args)[0].nn_type.lower()
    if nn_type == 'lenet5':
        dataset = 'mnist'
        epochs = 60
        lr=1e-1
    elif nn_type == 'vgg16':
        dataset = 'cifar10'
        epochs = 300
        lr=1e-2
    parser.add_argument(
        '--lr', type=float, default=lr,
        help='set learning rate')
    parser.add_argument(
        '--epochs', type=int, default=epochs,
        help='run epochs')
    parser.add_argument(
        '--dataset', type=str, default=dataset,
        help='choose dataset, if nn==lenet5,mnist elif nn==vgg16,cifar10')
    
    # VISUAL and CAM SECTION
    parser.add_argument(
        '--file_name', type=str, default=None,
        help='grad_data/grad_[].log for VISUAL and grad_[].pt file load for CAM')
    parser.add_argument(
        '--visual_type', type=str, default='time_domain',
        help='visualization domain decision [time,node,node_integrated]')
    parser.add_argument(
        '--num_result', type=int, default=1,
        help='grad_data/grad_[].log file load')



    return parser.parse_known_args(args)[0]


def main(args):
    flags = parse_args(args)
    if flags.file_name is None and flags.mode == 'train':
        time_data = time.strftime(
            '%m-%d_%H-%M-%S', time.localtime(time.time()))
    elif flags.file_name is not None and (flags.mode == 'visual' or flags.mode=='cam' or flags.mode=='hist'):  # load
        time_data = flags.file_name
        file_name = flags.file_name
    else:
        file_name = None  # no file name just read from grad.csv, .npy and .pt

    use_cuda = torch.cuda.is_available()
    device = torch.device(
        "cuda" if use_cuda and flags.device == 'gpu' else "cpu")
    print("Using device: {}".format(device))
    # Random Seed 설정
    random_seed = flags.seed
    random.seed(random_seed)
    torch.manual_seed(random_seed)
    torch.random.manual_seed(random_seed)
    torch.cuda.manual_seed_all(random_seed)
    np.random.seed(random_seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    '''
    Basic Setting
    '''
    configs = {'device': str(device),
               'seed': random_seed,
               'epochs': flags.epochs,
               'lr': flags.lr,
               'batch_size': flags.batch_size,
               'dataset': flags.dataset.lower(),
               'nn_type': flags.nn_type.lower(),
               'colab': flags.colab,
               'log_extraction': flags.log,
               'num_workers': flags.num_workers,
               'visual_type':flags.visual_type,
               'mode':flags.mode,
               'patience':flags.patience,
               }
    if flags.mode == 'visual':
        from visualization import visualization
        configs = visualization(configs, file_name)
    
    
    if configs['nn_type'] == 'lenet5':
        from NeuralNet.lenet5 import LeNet5
        model = LeNet5(configs).to(configs['device'])
    if configs['nn_type'][:3] == 'vgg':
        from NeuralNet.vgg import VGG
        model = VGG(configs).to(configs['device'])

    if flags.mode == 'train':
        from train import extract_data
        configs = extract_data(model,configs, time_data)
        if configs['log_extraction'] == True:
            save_params(configs, time_data)
    if flags.mode.lower() =='cam':
        configs['batch_size']=1 # 1장씩 extracting
        file_path=os.path.dirname(os.path.abspath(__file__))
        create_cam(model,file_path,file_name,flags.num_result,configs)
    if flags.mode.lower()=='hist':
        from utils import channel_hist
        configs['batch_size']=1 # 1장씩 extracting
        file_path=os.path.dirname(os.path.abspath(__file__))
        channel_hist(model,file_path,file_name,configs)


    print("End the process")


if __name__ == '__main__':
    main(sys.argv[1:])
