import json
import os
import zipfile
import gc

import numpy as np
import pandas as pd
#from deepfacelite import VGGFace
from .deepfacelite import functions
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image, ImageDraw
import keras.backend as K
from keras.layers import Input, Convolution2D, ZeroPadding2D, MaxPooling2D, Flatten, Dense, Dropout, Activation
from keras.models import Model, Sequential, model_from_json
from keras.preprocessing.image import load_img, save_img, img_to_array
import gdown

'''
The below section is for analyzing the celeb dataset,
here we are using images that have been stored into an s3 bucket.

If you decide to download images locally, you will have to modify
some of the code below

'''

# rmodel = VGGFace.baseModel()
# gmodel = VGGFace.baseModel()

def baseModel():
	model = Sequential()
	model.add(ZeroPadding2D((1,1),input_shape=(224,224, 3)))
	model.add(Convolution2D(64, (3, 3), activation='relu'))
	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(64, (3, 3), activation='relu'))
	model.add(MaxPooling2D((2,2), strides=(2,2)))

	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(128, (3, 3), activation='relu'))
	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(128, (3, 3), activation='relu'))
	model.add(MaxPooling2D((2,2), strides=(2,2)))

	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(256, (3, 3), activation='relu'))
	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(256, (3, 3), activation='relu'))
	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(256, (3, 3), activation='relu'))
	model.add(MaxPooling2D((2,2), strides=(2,2)))

	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(512, (3, 3), activation='relu'))
	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(512, (3, 3), activation='relu'))
	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(512, (3, 3), activation='relu'))
	model.add(MaxPooling2D((2,2), strides=(2,2)))

	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(512, (3, 3), activation='relu'))
	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(512, (3, 3), activation='relu'))
	model.add(ZeroPadding2D((1,1)))
	model.add(Convolution2D(512, (3, 3), activation='relu'))
	model.add(MaxPooling2D((2,2), strides=(2,2)))

	model.add(Convolution2D(4096, (7, 7), activation='relu'))
	model.add(Dropout(0.5))
	model.add(Convolution2D(4096, (1, 1), activation='relu'))
	model.add(Dropout(0.5))
	model.add(Convolution2D(2622, (1, 1)))
	model.add(Flatten())
	model.add(Activation('softmax'))

	return model


def raceLoadModel(rmodel, weights_dir):
    # global rmodel
    #--------------------------

    classes = 6
    base_model_output = Sequential()
    base_model_output = Convolution2D(classes, (1, 1), name='predictions')(rmodel.layers[-4].output)
    base_model_output = Flatten()(base_model_output)
    base_model_output = Activation('softmax')(base_model_output)

    #--------------------------

    race_model = Model(inputs=rmodel.input, outputs=base_model_output)

    #--------------------------

    #load weights
    weights_file = os.path.join(weights_dir, 'race_model_single_batch.h5')
    if not os.path.isfile(weights_file):
		# print("race_model_single_batch.h5 will be downloaded...")
		#zip
        url = 'https://drive.google.com/uc?id=1nz-WDhghGQBC4biwShQ9kYjvQMpO6smj'
        output = os.path.join(weights_dir, 'race_model_single_batch.zip')
        gdown.download(url, output, quiet=False)
        #unzip race_model_single_batch.zip
        with zipfile.ZipFile(output, 'r') as zip_ref:
            zip_ref.extractall(weights_dir)

    race_model.load_weights(os.path.join(weights_dir, 'race_model_single_batch.h5'))
#     del model
#     del classes
#     del base_model_output
    gc.collect()
    return race_model



def genderLoadModel(gmodel, weights_dir):

    #--------------------------

    classes = 2
    base_model_output = Sequential()
    base_model_output = Convolution2D(classes, (1, 1), name='predictions')(gmodel.layers[-4].output)
    base_model_output = Flatten()(base_model_output)
    base_model_output = Activation('softmax')(base_model_output)

    #--------------------------

    gender_model = Model(inputs=gmodel.input, outputs=base_model_output)

    #--------------------------

    #load weights
    weights_file = os.path.join(weights_dir,'gender_model_weights.h5')

    if not os.path.isfile(weights_file):
        print("gender_model_weights.h5 will be downloaded...")
        url = 'https://drive.google.com/uc?id=1wUXRVlbsni2FN9-jkS_f4UTUrm1bRLyk'
        gdown.download(url, weights_file, quiet=False)

    # gender_model.load_weights('prediction_lib/weights/gender_model_weights.h5')
    gender_model.load_weights(weights_file)
#     del model
#     del classes
#     del base_model_output
    gc.collect()
    return gender_model



# Extracted & Modified From Deepface Library

def analyze(img_path, gender_model, race_model):
    if os.path.isfile(img_path) != True:
        raise ValueError("Confirm that ",img_path," exists")
    #for action in actions:
    img = functions.detectFace(img_path, (224, 224), False)
    gender_prediction = gender_model.predict(img)[0,:]
    race_predictions = race_model.predict(img)[0,:]
    K.clear_session()
    if np.argmax(gender_prediction) == 0:
        gender = "Woman"
    elif np.argmax(gender_prediction) == 1:
        gender = "Man"

    race_labels = ['asian', 'indian', 'black', 'white', 'middle eastern', 'latino hispanic']
    sum_of_predictions = race_predictions.sum()

    for i in range(0, len(race_labels)):
        race_label = race_labels[i]
        race_prediction = 100 * race_predictions[i] / sum_of_predictions
    #del gender_model
    #del race_model
    #del img
    gc.collect()

    return gender, race_labels[np.argmax(race_predictions)]

def predict_gender_race(output_dir, weights_dir, film_characters):

    rmodel = baseModel()
    gmodel = baseModel()

    gender_model = genderLoadModel(gmodel, weights_dir)
    race_model = raceLoadModel(rmodel, weights_dir)

    # Analyze full list & predict gender/race
    list_demography = []
    with open(os.path.join(output_dir,'character_demography.json'), 'w') as filehandle:
        for film in film_characters:
            for character in film:
                celeb_id = character['celeb_id']
                key = celeb_id+'.jpg'

                img_name = os.path.join(output_dir, 'celeb_images', key)
                try:
                    gender, race = analyze(img_name, gender_model, race_model)
                    list_demography.append({
                        'celeb_id':celeb_id,
                        'race_prediction':race,
                        'gender_prediction':gender
                    })
                except Exception as e:
                    print('Caught exception while predicting race/gender %s' % e)
        json.dump(list_demography, filehandle, indent=4)
