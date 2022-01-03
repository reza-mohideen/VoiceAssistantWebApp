import logo from './logo.svg';
import './App.css';
import Siriwave from 'react-siriwave';
import React, {useState, useRef, useEffect} from 'react';
import RecordRTC, { StereoAudioRecorder } from 'recordrtc';

function App() {
  const [isRecording, setRecording] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [amp, setAmplitude] = useState(0);
  const ws = useRef(null);
  const recorder = useRef(null);
  const stream = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws');
    ws.current.onopen = () => {
      console.log('ws opened')
    };
    ws.current.onmessage = e => {
      const message = JSON.parse(e.data);
      setTranscription(message.value);
      console.log(message.value);
    };
    ws.current.onclose = () => console.log('ws closed');

    stream.current =navigator.mediaDevices.getUserMedia({video: false, audio: true}).then( stream => {
      recorder.current = RecordRTC(stream, {
        type: 'audio',
        mimeType: 'audio/webm',
        sampleRate: 44100,
        desiredSampRate: 16000,
        recorderType: StereoAudioRecorder,
        numberOfAudioChannels: 1,
        timeSlice: 500,
        bufferSize: 16384,
        ondataavailable: function(blob) {
          console.log('voice data available')
          ws.current.send(blob);
        }
      });
    })

    return () => {
        ws.current.close();
    };
  }, []);

  useEffect(() => {
      if (!isRecording) {
        try {
          recorder.current.stopRecording();
          recorder.current.reset();
          ws.current.send('stop');
          console.log('stopping recording')
          return
        } catch (error) {
          console.log(error)
        }

      };
      if (isRecording) {
        try {
          recorder.current.startRecording();
          ws.current.send('start');
          console.log('starting recording')
        } catch (error) {
          console.log(error)
        }
        
      };

  }, [isRecording]);

  function updateAmplitude() {
    if (amp === 0) setAmplitude(2);
    else setAmplitude(0);
  };

  return (
    <div className='container'>
      <div className='siriwave'>
        <Siriwave style='ios9' amplitude={amp}/>
      </div>
      <div className='box'>
        <h2>Input</h2>
        <button onClick={() => {setRecording(!isRecording); updateAmplitude()}}>
                {isRecording ? "Stop" : "Start"}
        </button>
        <p>{transcription}</p>
      </div>
      <div className='box'>
        <h2>Output</h2>
      </div>
    </div>
    )
  }

export default App;