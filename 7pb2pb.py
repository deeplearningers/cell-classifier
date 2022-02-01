import tensorflow as tf
from tensorflow.tools.graph_transforms import TransformGraph
 
with tf.gfile.FastGFile('C:\\project-dl\\cell-fenlei\\export\\mobilenetv2_frozen_graph_cell.pb', 'rb') as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())
    graph_def = TransformGraph(graph_def, ['input'], ['MobilenetV2/Predictions/Reshape_1'], ['remove_nodes(op=Identity)'])
    with tf.gfile.FastGFile('C:\\project-dl\\cell-fenlei\\export\\mobilenetv2_frozen_graph_cell_1.pb', 'wb') as f:
        f.write(graph_def.SerializeToString())#保存新的模型
