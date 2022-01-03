import logo from './logo.svg';
import './App.css';
import Siriwave from 'react-siriwave';
import React, {useState, useRef, useEffect} from 'react';
import RecordRTC, { StereoAudioRecorder } from 'recordrtc';

function App() {
  const url = 'http://localhost:8000';
  const [isRecording, setRecording] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [output, setOutput] = useState('');
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
      if (message.state === 1 || message.state === 2) {
        setTranscription(message.value);
        console.log(message.value);
      }

      else if (message.state === 3) {
        setTranscription(message.value);
        stopRecording()
        const requestOptions = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: message.value })
        };
        fetch(url + '/transcribe', requestOptions)
            .then(response => response.json())
            .then(data => setOutput(data.text));
      }
      
    };
    ws.current.onclose = () => console.log('ws closed');

    stream.current = navigator.mediaDevices.getUserMedia({video: false, audio: true}).then( stream => {
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
        stopRecording()
        ws.current.send('stop');
      };
      if (isRecording && ws.current.readyState === 1) {
        startRecording()
      };

  }, [isRecording]);

  function startRecording() {
    recorder.current.startRecording();
    setRecording(true);
    ws.current.send('start');
    console.log('starting recording')
  };

  function stopRecording() {
    recorder.current.pauseRecording();
    setRecording(false);
    updateAmplitude();
    console.log('stopping recording')
  };

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
        <p>{output}</p>
      </div>
    </div>
    )
  }

export default App;
