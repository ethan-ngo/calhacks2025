import React, { useEffect, useState } from 'react';
import { Room } from 'livekit-client';

const serverUrl = 'wss://triageagent-2aap4wyl.livekit.cloud';
const token = 'YOUR_ACCESS_TOKEN_HERE'; // Replace with your JWT token

function App() {
  const [room, setRoom] = useState(null);

  useEffect(() => {
    const newRoom = new Room();
    newRoom
      .connect(serverUrl, token)
      .then(() => {
        setRoom(newRoom);
        console.log('Connected to room:', newRoom.name);
      })
      .catch((err) => {
        console.error('Failed to connect:', err);
      });

    return () => {
      if (room) {
        room.disconnect();
      }
    };
  }, [room]);

  return (
    <div>
      <h1>LiveKit Room</h1>
      {room ? <p>Connected to room: {room.name}</p> : <p>Connecting...</p>}
    </div>
  );
}

export default App;
