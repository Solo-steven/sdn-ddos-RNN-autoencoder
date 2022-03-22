import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, losses
from tensorflow.keras import Model
from tensorflow.keras.layers.experimental import RandomFourierFeatures
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

class RNNAutoEncoderDetector():
  def __init__(
    self,
    ## For Data Structure
    window_size = 15,
    feature_size = 5,
    ## For Model Cell
    embedding_size= 100,
    hidden_size=20,
    ## Training Hyter
    epochs=100,
    batch_size=10,
  ):
      self.__window_size = window_size
      self.__feature_size = feature_size
      self.__embedding_size = embedding_size
      self.__hidden_size = 20
      self.__batch_size = batch_size
      self.__epochs = epochs
      self.__autoencoder = keras.Sequential([
        layers.GRU(self.__embedding_size, dropout=0.3, input_shape=(window_size, feature_size), return_sequences=True),
        layers.GRU(self.__hidden_size,  dropout=0.3, return_sequences=False),
        layers.RepeatVector(window_size),
        layers.GRU(self.__hidden_size, dropout=0.3, return_sequences=True),
        layers.GRU(self.__embedding_size, dropout=0.3,return_sequences=True),
        layers.TimeDistributed(layers.Dense(feature_size))
      ])
      self.__threshold = 0
      self.__loss_fun = losses.MeanSquaredError()
  """
    @data: pd.DatFrame with Shape(n, feature_size)
    @return: np.array with Shape (n, window_size, feature_size)
  """
  def __windowlized_data(self, data):
    numpy_data = data.to_numpy().astype('float32')
    # numpy_data = StandardScaler().fit_transform(numpy_data)
    training_data = []
    for i in range( numpy_data.shape[0] - self.__window_size +1 ):
      training_data.append(numpy_data[i : i + self.__window_size])
    training_data = np.array(training_data)
    return training_data
  """
    @data: pd.DataFrame with Shape (n, feature size)
    @return: None
  """
  def train(self, data):
    training_data = self.__windowlized_data(data)
    self.__autoencoder.compile(optimizer="adam", loss=self.__loss_fun)
    self.__autoencoder.fit(
        training_data ,
        training_data ,
        epochs=self.__epochs,
        batch_size= self.__batch_size
    )
    rector_error = self.rector(data)
    rector_error_std = ( rector_error - rector_error.mean() ) / rector_error.std()
    self.__threshold = rector_error_std.mean() + 2* rector_error_std.std() 
    self.__threshold = self.__threshold * rector_error.std() + rector_error.mean()
    print("Threshold is {}".format(self.__threshold))
  """
    @data: pd.DataFrame with Shape (n, feature size)
    @return: numpy array with length n.
  """
  def rector(self, data):
    training_data = self.__windowlized_data(data)
    rector_data = self.__autoencoder(training_data)
    rector_error = []
    for [rector_vector, training_vector] in zip(rector_data, training_data):
      rector_error.append(self.__loss_fun(rector_vector, training_vector).numpy())
    return np.array(rector_error)
  """
    @normal_df: pd.DataFrame with Shape(n, feature), Storage Normal Data
    @anomal_df: pd.DataFrame with Shape(n, feature), Storage Anomal Data
    @return: None
  """
  def envalute(self, normal_df, anomal_df):
    print("Number of Normal Sample: {}, construct {} window.".format(normal_df.shape[0], normal_df.shape[0] - 15))
    print("Number of Anomal Smaple: {}, constrcut {} window.".format(anomal_df.shape[0], anomal_df.shape[0] - 15))

    error_normal = self.rector(normal_df)
    error_anomal = self.rector(anomal_df)

    real_result = []
    predict_result = []
    for error in error_normal:
      real_result.append(0)
      predict_result.append( 0 if error < self.__threshold else 1 )
    for error in error_anomal:
      real_result.append(1)
      predict_result.append( 0 if error < self.__threshold else 1 )

    print("=================================")
    matrix = confusion_matrix(real_result, predict_result, labels=[0,1] )
    precision = matrix[0][0]/(matrix[0][0] + matrix[1][0])
    recall = matrix[0][0]/(matrix[0][0] + matrix[0][1])
    print("Precision: {}".format( precision ))
    print("Recall : {}".format(recall))
    print("F1 Score: {}".format(2 * precision * recall / (precision + recall)))
  """
    @data:  np array or list with Shape (window_size, feature_size)
    return  List of True or False
  """
  def predict(self, data):
    if len(data.shape) < 3:
      data = np.expand_dims(data, axis=0)
    rector = self.__autoencoder(data)
    result = []
    for [rector_vector, data_vector] in zip(rector, data):
        error = self.__loss_fun(rector_vector, data_vector)
        result.append( 0 if error < self.__threshold else 1)
    return result