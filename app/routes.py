from app import app

from flask import jsonify
import requests
import json

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

tele_url = 'https://vats-bw-001.sberbank-tele.com/vr_callrec/api'
tele_credentials = ('9953454763', 'Forever$4')

@app.route('/todo/api/v1.0/records', methods=['GET'])
def get_tasks():
    r = requests.get(tele_url + '/v1/records', auth=tele_credentials)
    records = json.loads(r.text)
    return jsonify({'tasks': records})

import io 
import os
from pydub import AudioSegment

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from google.oauth2 import service_account

@app.route('/todo/api/v1.0/recognize/<string:recordId>', methods=['GET'])
def recognize_record(recordId):
    #скачиваем файл с указанным Id
    r = requests.get(tele_url + '/v1/records/' + recordId + '/download', auth=tele_credentials)
    
    if r.status_code != requests.codes.ok:
        return(r.text)
    
    records_dir = os.path.join(
        os.path.dirname(os.path.realpath('__file__')),
        'recordings')
    mp3fname = os.path.join(records_dir, recordId + '.mp3')

    with open(mp3fname, 'wb') as file:
    	file.write(r.content)
    
    #конвертируем файл в wav
    sound = AudioSegment.from_mp3(mp3fname)
    wavfname = os.path.join(records_dir, recordId + '.wav')
    sound.export(wavfname, format='wav')

    #отправляем файл в гугл на распознавание
    credentials = service_account.Credentials.from_service_account_file('SpeechRecognitionTest-fd8a534ee8f0.json')

    client = speech.SpeechClient(credentials=credentials)

    with io.open(wavfname, 'rb') as audio_file:
    #mp3 cause error: google.api_core.exceptions.InvalidArgument: 400 Invalid recognition 'config': bad encoding..
    #with io.open(mp3fname, 'rb') as audio_file:
         content = audio_file.read()
         audio = types.RecognitionAudio(content=content)

    config = types.RecognitionConfig(
    #    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    #    sample_rate_hertz=8000,
    #    use_enhanced=True,
    #    diarizationSpeakerCount=2,
         model='default',
         language_code='ru-RU')

    response = client.recognize(config, audio)

    #if r.status_code != response.codes.ok:
    #    return(r.text)
    
    transcript = ''
    for result in response.results:
        transcript += '{}'.format(result.alternatives[0].transcript)
        print('Transcript: {}'.format(result.alternatives[0].transcript))
    
    #return jsonify(Transcript = '{}'.format(result.alternatives[0].transcript))
    #return('Transcript: {}'.format(result.alternatives[0].transcript))
    return transcript
