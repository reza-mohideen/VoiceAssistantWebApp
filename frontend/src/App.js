import logo from './logo.svg';
import './App.css';
import React, {useState, useRef, useEffect} from 'react';

function App() {
  const [isRecording, setRecording] = useState(false);
  const ws = useRef(null);
  const audioContext = useRef(new AudioContext());
  const source = useRef(null);
  let chunks = useRef([]);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({video: false, audio: true}).then( stream => {
      source.current = audioContext.current.createMediaStreamSource(stream)
      console.log(source.current.context)
    })
    setInterval(hello => {
      console.log(source.current)
    }, 1000);
    
    ws.current = new WebSocket('ws://localhost:8000/ws');
    ws.current.onopen = () => {
      console.log('ws opened')
    };
    ws.current.onmessage = e => {
      const message = JSON.parse(e.data);
      console.log('e', message.value);
    };
    ws.current.onclose = () => console.log('ws closed');

    return () => {
        ws.current.close();
    };
  }, []);

  useEffect(() => {
      if (!isRecording) {
        return

      };
      if (isRecording && ws.current.readyState === 1) {
        source.current.resume();
        
        console.log('starting recording')
      };


  }, [isRecording]);

  return (
    <div className='container'>
      <div className='box'>
        <h2>Max</h2>
        <button onClick={() => setRecording(!isRecording)}>
                {isRecording ? "Stop" : "Start"}
        </button>
      </div>
      <div className='box'>
        <h2>Output</h2>
      </div>
    </div>
    )
  }

export default App;
