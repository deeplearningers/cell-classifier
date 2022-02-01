# coding:utf-8
from __future__ import absolute_import
import argparse
import os
import logging
from src.tfrecord import main#生成tf格式的主函数

def parse_args():
    parser = argparse.ArgumentParser()#解析命令行参数和选项的标准模块
    parser.add_argument('-t', '--tensorflow_data_dir', default='data/')#待转换图像路径,tensorflow-data-dir这样写也行？
    parser.add_argument('--train_shards', default=32, type=int)#训练集分成2块
    parser.add_argument('--validation_shards', default=32, type=int)#验证集分成2块
    parser.add_argument('--num_threads', default=32, type=int)#2个线程产生数据,能整除train_shards
    parser.add_argument('--dataset_name', default='cell', type=str)#生成数据集名字，自定义
    return parser.parse_args()#parse_args()是将之前add_argument()定义的参数进行赋值，并返回相关的namespace

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename='./log/log.txt',filemode='w')    #设置日志等级，日志目录
    args = parse_args()
    args.tensorflow_dir = args.tensorflow_data_dir
    args.train_directory = os.path.join(args.tensorflow_dir, 'train')
    args.validation_directory = os.path.join(args.tensorflow_dir, 'validation')
    args.output_directory = args.tensorflow_dir
    args.labels_file = os.path.join(args.tensorflow_dir, 'label.txt')
    #生成label.txt
    if os.path.exists(args.labels_file) is False:
        logging.warning('Can\'t find label.txt. Now create it.')
        all_entries = os.listdir(args.train_directory)#os.listdir()返回指定的文件夹包含的文件或文件夹的名字的列表
        dirnames = []
        for entry in all_entries:
            if os.path.isdir(os.path.join(args.train_directory, entry)):
                dirnames.append(entry)
        with open(args.labels_file, 'w') as f:
            for dirname in dirnames:
                f.write(dirname + '\n')
    main(args)
