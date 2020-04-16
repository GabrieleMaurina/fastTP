#!/usr/bin/env python

from tensorflow import keras

def create_model():
	inputs = keras.Input(shape=3)
	l1 = keras.layers.Dense(3, activation='relu')(inputs)
	l2 = keras.layers.Dense(3, activation='relu')(l1)
	outputs = keras.layers.Dense(1)(l2)
	model = keras.Model(inputs=inputs, outputs=outputs, name='fasttp_model')
	model.compile(
		loss=keras.losses.BinaryCrossentropy(),
		optimizer=keras.optimizers.Adam(),
		metrics=['accuracy'])
	return model

def save_model(model):
	model.save('model')

def load_model():
	return keras.models.load_model('model')

def fit_model(model, x, y):
	model.fit(x, y, batch_size=64, epochs=3, validation_split=0.2)

if __name__ == '__main__':
	model = create_model()
	save_model(model)
