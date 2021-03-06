# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Generic training script that trains a model using a given dataset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from slim.datasets import dataset_factory
from slim.deployment import model_deploy
from slim.nets import nets_factory
from slim.preprocessing import preprocessing_factory

import tensorflow.contrib.slim as slim
#slim = tf.contrib.slim
#设定训练时参数
tf.flags.DEFINE_string(
    'master', '', 'The address of the TensorFlow master to use.')

tf.flags.DEFINE_string(
    'train_dir', 'C:\\project-dl\\cell-fenlei\\train_dir',#生成模型的路径,windows下写绝对路径
    'Directory where checkpoints and event logs are written to.')

tf.flags.DEFINE_integer('num_clones', 1,'Number of model clones to deploy.')#每个单机部署多少个clone（即部署在多少个GPU）

tf.flags.DEFINE_boolean('clone_on_cpu', False, 'Use CPUs to deploy clones.')#如果为True，则单机中的每个clone将被放在CPU中
# 使用多少个单机，通常为1，表示单机部署。此时`worker_device`, `num_ps_tasks`和 `ps_device`这几个参数将被忽略。
tf.flags.DEFINE_integer('worker_replicas', 1, 'Number of worker replicas.')
#分布式作业使用多少个单机，如果为0表示不使用单机
tf.flags.DEFINE_integer(
    'num_ps_tasks', 0,
    'The number of parameter servers. If the value is 0, then the parameters '
    'are handled locally by the worker.')

tf.flags.DEFINE_integer(
    'num_readers', 4,
    'The number of parallel readers that read data from the dataset.')#并行阅读器数量

tf.flags.DEFINE_integer(
    'num_preprocessing_threads', 4,
    'The number of threads used to create the batches.')#线程个数

tf.flags.DEFINE_integer(
    'log_every_n_steps', 10,
    'The frequency with which logs are print.')#间隔10步打印训练信息

tf.flags.DEFINE_integer(
    'save_summaries_secs', 2,
    'The frequency with which summaries are saved, in seconds.')#间隔2s保存日志，tensorboard可查看

tf.flags.DEFINE_integer(
    'save_interval_secs', 300,
    'The frequency with which the model is saved, in seconds.')#间隔300s保存模型

tf.flags.DEFINE_integer(
    'task', 0, 'Task id of the replica running the training.')## 整数，模型所部署的单机的索引，通常是0

######################
# Optimization Flags #
######################

tf.flags.DEFINE_float('weight_decay', 0.00004, 'The weight decay on the model weights.')#正则化参数

tf.flags.DEFINE_string(
    'optimizer', 'rmsprop',
    'The name of the optimizer, one of "adadelta", "adagrad", "adam",'#优化器
    '"ftrl", "momentum", "sgd" or "rmsprop".')#Adam（Adaptive Moment Estimation）算法是将Momentum算法和RMSProp算法

tf.flags.DEFINE_float(
    'adadelta_rho', 0.95,
    'The decay rate for adadelta.')#优化器是adadelta时使用

tf.flags.DEFINE_float(
    'adagrad_initial_accumulator_value', 0.1,
    'Starting value for the AdaGrad accumulators.')#优化器是adagrad时使用

tf.flags.DEFINE_float(
    'adam_beta1', 0.9,
    'The exponential decay rate for the 1st moment estimates.')#优化器是adam时使用

tf.flags.DEFINE_float(
    'adam_beta2', 0.999,
    'The exponential decay rate for the 2nd moment estimates.')#优化器是adam时使用,算法计算了梯度的指数移动均值, beta1 和 beta2 控制了这些移动均值的衰减率。

tf.flags.DEFINE_float('opt_epsilon', 1.0, 'Epsilon term for the optimizer.')#

tf.flags.DEFINE_float('ftrl_learning_rate_power', -0.5,'The learning rate power.')#

tf.flags.DEFINE_float(
    'ftrl_initial_accumulator_value', 0.1,
    'Starting value for the FTRL accumulators.')#

tf.flags.DEFINE_float(
    'ftrl_l1', 0.0, 'The FTRL l1 regularization strength.')#

tf.flags.DEFINE_float(
    'ftrl_l2', 0.0, 'The FTRL l2 regularization strength.')#

tf.flags.DEFINE_float(
    'momentum', 0.9,
    'The momentum for the MomentumOptimizer and RMSPropOptimizer.')#

tf.flags.DEFINE_float('rmsprop_decay', 0.9, 'Decay term for RMSProp.')#

#######################
# Learning Rate Flags #
#######################

tf.flags.DEFINE_string(
    'learning_rate_decay_type',
    'exponential',
    'Specifies how the learning rate is decayed. One of "fixed", "exponential",'
    ' or "polynomial"')#学习率是否下降固定

tf.flags.DEFINE_float('learning_rate', 0.001, 'Initial learning rate.')#学习率
#以下是衰减学习率才设置
tf.flags.DEFINE_float(
    'end_learning_rate', 0.0001,
    'The minimal end learning rate used by a polynomial decay learning rate.')#下降的话，最小的学习率值

tf.flags.DEFINE_float(
    'label_smoothing', 0.0, 'The amount of label smoothing.')#防止过拟合策略

tf.flags.DEFINE_float(
    'learning_rate_decay_factor', 0.94, 'Learning rate decay factor.')#学习率衰减因子

tf.flags.DEFINE_float(
    'num_epochs_per_decay', 2.0,
    'Number of epochs after which learning rate decays.')#多少个epoch后学习率衰减

tf.flags.DEFINE_bool(
    'sync_replicas', False,
    'Whether or not to synchronize the replicas during training.')

tf.flags.DEFINE_integer(
    'replicas_to_aggregate', 1,
    'The Number of gradients to collect before updating params.')

tf.flags.DEFINE_float(
    'moving_average_decay', None,
    'The decay to use for the moving average.'
    'If left as None, then moving averages are not used.')

#######################
# Dataset Flags #
#######################

tf.flags.DEFINE_string(
    'dataset_name', 'cell', 'The name of the dataset to load.')#与datasets中对应

tf.flags.DEFINE_string(
    'dataset_split_name', 'train', 'The name of the train/test split.')#选取训练集

tf.flags.DEFINE_string(
    'dataset_dir', 'C:\\project-dl\\cell-fenlei\\data', 'The directory where the dataset files are stored.')#数据集路径

tf.flags.DEFINE_integer(
    'labels_offset', 0,
    'An offset for the labels in the dataset. This flag is primarily used to '
    'evaluate the VGG and ResNet architectures which do not use a background '
    'class for the ImageNet dataset.')#?

tf.flags.DEFINE_string(
    'model_name', 'mobilenet_v2_140', 'The name of the architecture to train.')#网络模型选择

tf.flags.DEFINE_string(
    'preprocessing_name', None, 'The name of the preprocessing to use. If left '
    'as `None`, then the model_name flag is used.')#使用的预训练模型名称

tf.flags.DEFINE_integer(
    'batch_size',64, 'The number of samples in each batch.')#每步使用的batch大小,32修改

tf.flags.DEFINE_integer(
    'train_image_size', 224, 'Train image size')#训练图像大小，inception_v3.default_image_size = 224

tf.flags.DEFINE_integer('max_number_of_steps', 500000,'The maximum number of training steps.')#最大的执行步数

#####################
# Fine-Tuning Flags #
#####################

tf.flags.DEFINE_string(
    'checkpoint_path', 'C:\\project-dl\\cell-fenlei\\pretrained\\mobilenet_v2_1.4_224.ckpt',#写到ckpt即可
    'The path to a checkpoint from which to fine-tune.')#预训练模型位置

tf.flags.DEFINE_string(
    'checkpoint_exclude_scopes', 'MobilenetV2/Logits,MobilenetV2/AuxLogits',
    'Comma-separated list of scopes of variables to exclude when restoring '
    'from a checkpoint.')#恢复预训练模型时，排除末端层

tf.flags.DEFINE_string(
    'trainable_scopes', 'MobilenetV2/Logits,MobilenetV2/AuxLogits',
    'Comma-separated list of scopes to filter the set of variables to train.'
    'By default, None would train all the variables.')#微调的范围，None的话，对所有层训练！！

tf.flags.DEFINE_boolean(
    'ignore_missing_vars', True,
    'When restoring a checkpoint would ignore missing variables.')

FLAGS = tf.flags.FLAGS#新版


def _configure_learning_rate(num_samples_per_epoch, global_step):
  """Configures the learning rate.

  Args:
    num_samples_per_epoch: The number of samples in each epoch of training.
    global_step: The global_step tensor.

  Returns:
    A `Tensor` representing the learning rate.

  Raises:
    ValueError: if
  """
  decay_steps = int(num_samples_per_epoch / FLAGS.batch_size *
                    FLAGS.num_epochs_per_decay)
  if FLAGS.sync_replicas:
    decay_steps /= FLAGS.replicas_to_aggregate

  if FLAGS.learning_rate_decay_type == 'exponential':
    return tf.train.exponential_decay(FLAGS.learning_rate,
                                      global_step,
                                      decay_steps,
                                      FLAGS.learning_rate_decay_factor,
                                      staircase=True,
                                      name='exponential_decay_learning_rate')
  elif FLAGS.learning_rate_decay_type == 'fixed':
    return tf.constant(FLAGS.learning_rate, name='fixed_learning_rate')
  elif FLAGS.learning_rate_decay_type == 'polynomial':
    return tf.train.polynomial_decay(FLAGS.learning_rate,
                                     global_step,
                                     decay_steps,
                                     FLAGS.end_learning_rate,
                                     power=1.0,
                                     cycle=False,
                                     name='polynomial_decay_learning_rate')
  else:
    raise ValueError('learning_rate_decay_type [%s] was not recognized',
                     FLAGS.learning_rate_decay_type)

#优化器参数配置
def _configure_optimizer(learning_rate):
  """Configures the optimizer used for training.

  Args:
    learning_rate: A scalar or `Tensor` learning rate.

  Returns:
    An instance of an optimizer.

  Raises:
    ValueError: if FLAGS.optimizer is not recognized.
  """
  if FLAGS.optimizer == 'adadelta':
    optimizer = tf.train.AdadeltaOptimizer(
        learning_rate,
        rho=FLAGS.adadelta_rho,
        epsilon=FLAGS.opt_epsilon)
  elif FLAGS.optimizer == 'adagrad':
    optimizer = tf.train.AdagradOptimizer(
        learning_rate,
        initial_accumulator_value=FLAGS.adagrad_initial_accumulator_value)
  elif FLAGS.optimizer == 'adam':
    optimizer = tf.train.AdamOptimizer(
        learning_rate,
        beta1=FLAGS.adam_beta1,
        beta2=FLAGS.adam_beta2,
        epsilon=FLAGS.opt_epsilon)
  elif FLAGS.optimizer == 'ftrl':
    optimizer = tf.train.FtrlOptimizer(
        learning_rate,
        learning_rate_power=FLAGS.ftrl_learning_rate_power,
        initial_accumulator_value=FLAGS.ftrl_initial_accumulator_value,
        l1_regularization_strength=FLAGS.ftrl_l1,
        l2_regularization_strength=FLAGS.ftrl_l2)
  elif FLAGS.optimizer == 'momentum':
    optimizer = tf.train.MomentumOptimizer(
        learning_rate,
        momentum=FLAGS.momentum,
        name='Momentum')
  elif FLAGS.optimizer == 'rmsprop':
    optimizer = tf.train.RMSPropOptimizer(
        learning_rate,
        decay=FLAGS.rmsprop_decay,
        momentum=FLAGS.momentum,
        epsilon=FLAGS.opt_epsilon)
  elif FLAGS.optimizer == 'sgd':
    optimizer = tf.train.GradientDescentOptimizer(learning_rate)
  else:
    raise ValueError('Optimizer [%s] was not recognized', FLAGS.optimizer)
  return optimizer


def _get_init_fn():
  """Returns a function run by the chief worker to warm-start the training.

  Note that the init_fn is only run when initializing the model during the very
  first global step.

  Returns:
    An init function run by the supervisor.
  """
  if FLAGS.checkpoint_path is None:
    return None

  # Warn the user if a checkpoint exists in the train_dir. Then we'll be
  # ignoring the checkpoint anyway.
  if tf.train.latest_checkpoint(FLAGS.train_dir):
    tf.logging.info(
        'Ignoring --checkpoint_path because a checkpoint already exists in %s'
        % FLAGS.train_dir)
    return None

  exclusions = []
  if FLAGS.checkpoint_exclude_scopes:
    exclusions = [scope.strip()
                  for scope in FLAGS.checkpoint_exclude_scopes.split(',')]

  # TODO(sguada) variables.filter_variables()
  variables_to_restore = []
  for var in slim.get_model_variables():
    excluded = False
    for exclusion in exclusions:
      if var.op.name.startswith(exclusion):
        excluded = True
        break
    if not excluded:
      variables_to_restore.append(var)

  if tf.gfile.IsDirectory(FLAGS.checkpoint_path):
    checkpoint_path = tf.train.latest_checkpoint(FLAGS.checkpoint_path)
  else:
    checkpoint_path = FLAGS.checkpoint_path

  tf.logging.info('Fine-tuning from %s' % checkpoint_path)

  return slim.assign_from_checkpoint_fn(
      checkpoint_path,
      variables_to_restore,
      ignore_missing_vars=FLAGS.ignore_missing_vars)


def _get_variables_to_train():
  """Returns a list of variables to train.

  Returns:
    A list of variables to train by the optimizer.
  """
  if FLAGS.trainable_scopes is None:
    return tf.trainable_variables()
  else:
    scopes = [scope.strip() for scope in FLAGS.trainable_scopes.split(',')]

  variables_to_train = []
  for scope in scopes:
    variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope)
    variables_to_train.extend(variables)
  return variables_to_train

#主函数
def main(_):
  if not FLAGS.dataset_dir:
    raise ValueError('You must supply the dataset directory with --dataset_dir')

  tf.logging.set_verbosity(tf.logging.INFO)
  with tf.Graph().as_default():
    #######################
    # Config model_deploy 多CPU或GPU部署使用，一般用不到#
    #######################
    deploy_config = model_deploy.DeploymentConfig(
        num_clones=FLAGS.num_clones,
        clone_on_cpu=FLAGS.clone_on_cpu,
        replica_id=FLAGS.task,
        num_replicas=FLAGS.worker_replicas,
        num_ps_tasks=FLAGS.num_ps_tasks)

    # Create global_step
    with tf.device(deploy_config.variables_device()):#global_step在训练中是计数的作用，每训练一个batch就加1
      global_step = tf.train.create_global_step()#代表全局步数，比如在多少步该进行什么操作，现在神经网络训练到多少轮等等，类似于一个钟表。

    ######################
    # Select the dataset #
    ######################
    dataset = dataset_factory.get_dataset(FLAGS.dataset_name, FLAGS.dataset_split_name, FLAGS.dataset_dir)

    ######################
    # Select the network #
    ######################
    network_fn = nets_factory.get_network_fn(
        FLAGS.model_name,
        num_classes=(dataset.num_classes - FLAGS.labels_offset),
        weight_decay=FLAGS.weight_decay,
        is_training=True)#训练

    #####################################
    # Select the preprocessing function #
    #####################################
    preprocessing_name = FLAGS.preprocessing_name or FLAGS.model_name
    image_preprocessing_fn = preprocessing_factory.get_preprocessing(
        preprocessing_name,
        is_training=True)#用于训练true

    ##############################################################
    # Create a dataset provider that loads data from the dataset #
    ##############################################################
    with tf.device(deploy_config.inputs_device()):#从TFRecords文件读取数据集方法
      provider = slim.dataset_data_provider.DatasetDataProvider(
          dataset,#训练集
          num_readers=FLAGS.num_readers,
          common_queue_capacity=20 * FLAGS.batch_size,#读取数据队列的容量，默认为256
          common_queue_min=10 * FLAGS.batch_size)#读取数据队列的最小容量
      [image, label] = provider.get(['image', 'label'])
      label -= FLAGS.labels_offset

      train_image_size = FLAGS.train_image_size or network_fn.default_image_size#224

      image = image_preprocessing_fn(image, train_image_size, train_image_size)#预处理函数
#喂养数据的函数
      images, labels = tf.train.batch(
          [image, label],#一个列表或字典的tensor用来进行入队
          batch_size=FLAGS.batch_size,#设置每次从队列中获取出队数据的数量
          num_threads=FLAGS.num_preprocessing_threads,#用来控制入队tensors线程的数量，如果num_threads大于1，则batch操作将是非确定性的，输出的batch可能会乱序
          capacity=5 * FLAGS.batch_size)#一个整数，用来设置队列中元素的最大数量
      labels = slim.one_hot_encoding(
          labels, dataset.num_classes - FLAGS.labels_offset)
      batch_queue = slim.prefetch_queue.prefetch_queue(
          [images, labels], capacity=2 * deploy_config.num_clones)#使用预加载队列

    ####################
    # Define the model #
    ####################
    def clone_fn(batch_queue):
      """Allows data parallelism by creating multiple clones of network_fn."""
      with tf.device(deploy_config.inputs_device()):
        images, labels = batch_queue.dequeue()
      logits, end_points = network_fn(images)

      #############################
      # Specify the loss function #
      #############################
      if 'AuxLogits' in end_points:
        tf.losses.softmax_cross_entropy(
            logits=end_points['AuxLogits'], onehot_labels=labels,
            label_smoothing=FLAGS.label_smoothing, weights=0.4, scope='aux_loss')
      tf.losses.softmax_cross_entropy(
          logits=logits, onehot_labels=labels,
          label_smoothing=FLAGS.label_smoothing, weights=1.0)
      return end_points

    # Gather initial summaries.
    summaries = set(tf.get_collection(tf.GraphKeys.SUMMARIES))

    clones = model_deploy.create_clones(deploy_config, clone_fn, [batch_queue])
    first_clone_scope = deploy_config.clone_scope(0)
    # Gather update_ops from the first clone. These contain, for example,
    # the updates for the batch_norm variables created by network_fn.
    update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, first_clone_scope)

    # Add summaries for end_points.
    end_points = clones[0].outputs
    for end_point in end_points:
      x = end_points[end_point]
      summaries.add(tf.summary.histogram('activations/' + end_point, x))
      summaries.add(tf.summary.scalar('sparsity/' + end_point,
                                      tf.nn.zero_fraction(x)))

    # Add summaries for losses.
    for loss in tf.get_collection(tf.GraphKeys.LOSSES, first_clone_scope):
      summaries.add(tf.summary.scalar('losses/%s' % loss.op.name, loss))

    # Add summaries for variables.
    for variable in slim.get_model_variables():
      summaries.add(tf.summary.histogram(variable.op.name, variable))

    #################################
    # Configure the moving averages #
    #################################
    #tf.train.ExponentialMovingAverage用于更新参数，采用滑动平均方法更新参数。需要提供一个衰减速率用于控制模型更新速度。
    if FLAGS.moving_average_decay:
      moving_average_variables = slim.get_model_variables()
      variable_averages = tf.train.ExponentialMovingAverage(
          FLAGS.moving_average_decay, global_step)
    else:
      moving_average_variables, variable_averages = None, None

    #########################################
    # Configure the optimization procedure. #
    #########################################
    with tf.device(deploy_config.optimizer_device()):
      learning_rate = _configure_learning_rate(dataset.num_samples, global_step)
      optimizer = _configure_optimizer(learning_rate)
      summaries.add(tf.summary.scalar('learning_rate', learning_rate))

    if FLAGS.sync_replicas:
      # If sync_replicas is enabled, the averaging will be done in the chief queue runner.
      #分布式可以大大的加快模型训练速度，但是分布式怎么分配和参数设定，都和同步梯度更新SyncReplicasOptimizer这个函数有很大关系。
      optimizer = tf.train.SyncReplicasOptimizer(
          opt=optimizer,#优化器
          replicas_to_aggregate=FLAGS.replicas_to_aggregate,
          variable_averages=variable_averages,
          variables_to_average=moving_average_variables,
          replica_id=tf.constant(FLAGS.task, tf.int32, shape=()),
          total_num_replicas=FLAGS.worker_replicas)
    elif FLAGS.moving_average_decay:
      # Update ops executed locally by trainer.
      update_ops.append(variable_averages.apply(moving_average_variables))

    # Variables to train.
    variables_to_train = _get_variables_to_train()#获取训练那层的参数

    #returns a train_tensor and summary_op
    total_loss, clones_gradients = model_deploy.optimize_clones(
        clones,
        optimizer,
        var_list=variables_to_train)
    # Add total_loss to summary.
    summaries.add(tf.summary.scalar('total_loss', total_loss))

    # Create gradient updates.
    grad_updates = optimizer.apply_gradients(clones_gradients, global_step=global_step)
    update_ops.append(grad_updates)

    update_op = tf.group(*update_ops)
    with tf.control_dependencies([update_op]):
      train_tensor = tf.identity(total_loss, name='train_op')

    # Add the summaries from the first clone. These contain the summaries
    # created by model_fn and either optimize_clones() or _gather_clone_loss().
    summaries |= set(tf.get_collection(tf.GraphKeys.SUMMARIES,
                                       first_clone_scope))

    # Merge all summaries together.
    summary_op = tf.summary.merge(list(summaries), name='summary_op')

    ###########################
    # Kicks off the training. #
    ###########################
    session_config = tf.ConfigProto(allow_soft_placement=True)  # 新增
    slim.learning.train(
        train_tensor,
        logdir=FLAGS.train_dir,
        master=FLAGS.master,
        is_chief=(FLAGS.task == 0),
        init_fn=_get_init_fn(),
        summary_op=summary_op,
        number_of_steps=FLAGS.max_number_of_steps,
        log_every_n_steps=FLAGS.log_every_n_steps,
        save_summaries_secs=FLAGS.save_summaries_secs,
        save_interval_secs=FLAGS.save_interval_secs,
        sync_optimizer=optimizer if FLAGS.sync_replicas else None,
        session_config=session_config)


if __name__ == '__main__':
  tf.app.run()
