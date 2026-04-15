import asyncio
import websockets

async def test():
    try:
        ws = await websockets.connect('ws://localhost:8000/voice-agent')
        print('Connected successfully!')
        await ws.close()
        print('Clean close')
    except Exception as e:
        print(f'Connection failed: {e}')

asyncio.run(test())
