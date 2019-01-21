"""Define inputters reading from TFRecord files."""

import numpy as np
import tensorflow as tf

from opennmt.inputters.inputter import Inputter


class SequenceRecordInputter(Inputter):
  """Inputter that reads variable-length tensors.

  Each record contains a ``tf.train.SequenceExample`` with values indexed by
  "values".
  """

  def __init__(self, input_depth, dtype=tf.float32):
    """Initializes the parameters of the record inputter.

    Args:
      input_depth: The depth dimension of the input vectors.
      dtype: The data type to convert values to.
    """
    super(SequenceRecordInputter, self).__init__(dtype=dtype)
    self.input_depth = input_depth

  def make_dataset(self, data_file):
    return tf.data.TFRecordDataset(data_file)

  def get_dataset_size(self, data_file):
    return sum(1 for _ in tf.io.tf_record_iterator(data_file))

  def _get_receiver_tensors(self):
    return {
        "tensor": tf.placeholder(self.dtype, shape=(None, None, self.input_depth)),
        "length": tf.placeholder(tf.int32, shape=(None,))
    }

  def make_features(self, element=None, features=None):
    if features is None:
      features = {}
    if "tensor" in features:
      return features
    if element is None:
      raise ValueError("Missing element")
    element = tf.io.parse_single_sequence_example(element, sequence_features={
        "values": tf.io.FixedLenSequenceFeature([self.input_depth], dtype=tf.float32),
    })
    tensor = element[1]["values"]
    features["length"] = tf.shape(tensor)[0]
    features["tensor"] = tf.cast(tensor, self.dtype)
    return features

  def make_inputs(self, features, training=True):
    return features["tensor"]


def write_sequence_record(vector, writer):
  """Writes a sequence vector as a TFRecord.

  Args:
    vector: A 2D Numpy array of shape :math:`[T, D]`.
    writer: A ``tf.io.TFRecordWriter``.
  """
  feature_list = tf.train.FeatureList(feature=[
      tf.train.Feature(float_list=tf.train.FloatList(value=values))
      for values in vector.astype(np.float32)])
  feature_lists = tf.train.FeatureLists(feature_list={"values": feature_list})
  example = tf.train.SequenceExample(feature_lists=feature_lists)
  writer.write(example.SerializeToString())
