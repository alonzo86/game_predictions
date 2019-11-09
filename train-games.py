from __future__ import absolute_import, division, print_function, unicode_literals

import warnings

import tensorflow as tf

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

base_folder = os.path.dirname(__file__)


def get_labels(df, label, mapping):
    result_data_labels = df.pop(label)
    result_data = np.zeros((len(result_data_labels)))
    for i, raw_label in enumerate(result_data_labels):
        result_data[i] = mapping[raw_label]
    return result_data


def get_labels1(df, label):
    labels = get_labels(df, label, mapping_to_numbers)
    num_classes = 3
    result_data = tf.one_hot(labels, num_classes)
    return result_data


warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
tf.compat.v1.enable_eager_execution()

print(tf.__version__)

mapping_to_numbers = {'win': 0, 'draw': 1, 'lose': 2}

game_stats_filename = os.path.join(base_folder, 'resources', 'game_stats.csv')
data_frame = pd.read_csv(game_stats_filename)
data_frame.head()

train, test = train_test_split(data_frame, test_size=0.2)
train, val = train_test_split(train, test_size=0.2)
print(len(train), 'train examples')
print(len(val), 'validation examples')
print(len(test), 'test examples')

train_labels = np.array(get_labels(train, label='result', mapping=mapping_to_numbers))
val_labels = np.array(get_labels(val, label='result', mapping=mapping_to_numbers))
test_labels = np.array(get_labels(test, label='result', mapping=mapping_to_numbers))

train_features = np.array(train)
val_features = np.array(val)
test_features = np.array(test)

model = tf.keras.Sequential([
    tf.keras.layers.Flatten(input_shape=(train_features.shape[-1],)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(3, activation='softmax'),
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy'],
    run_eagerly=True)

epochs = 20
batch_size = 160
history = model.fit(
    train_features,
    train_labels,
    epochs=epochs,
    validation_data=(val_features, val_labels))

results = model.evaluate(test_features, test_labels)
print("Results", results)

keras_file = os.path.join(base_folder, 'resources', 'game_prediction_model.h5')
tf.keras.models.save_model(model, keras_file)

print("Saved model to disk")
