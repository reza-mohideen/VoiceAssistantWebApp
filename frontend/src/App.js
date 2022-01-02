import logo from './logo.svg';
import './App.css';
import React, {useState, useRef, useEffect} from 'react';
import RecordRTC, { StereoAudioRecorder } from 'recordrtc';

function App() {
  const [isRecording, setRecording] = useState(false);
  const [transcription, setTranscription] = useState('');
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
        mimeType: 'audio/webm;codecs=pcm',
        sampleRate: 44100,
        desiredSampRate: 16000,
        recorderType: StereoAudioRecorder,
        numberOfAudioChannels: 1,
        timeSlice: 300,
        bufferSize: 256,
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
      if (!isRecording && ws.current.readyState === 1) {
        recorder.current.stopRecording();
        recorder.current.reset();
        ws.current.send('stop');
        console.log('stopping recording')
        return

      };
      if (isRecording && ws.current.readyState === 1) {
        recorder.current.startRecording();
        ws.current.send('start');
        console.log('starting recording')
      };


  }, [isRecording]);

  return (
    <div className='container'>
      <div className='box'>
        <h2>Input</h2>
        <button onClick={() => setRecording(!isRecording)}>
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
