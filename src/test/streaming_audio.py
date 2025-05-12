# udp_audio_sender.py
import socket
import pyaudio
import argparse

CHUNK    = 1024
FORMAT   = pyaudio.paInt16
CHANNELS = 1
RATE     = 8000

def audio_stream(udp_ip, udp_port):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[AUDIO] Streaming RAW PCM a {udp_ip}:{udp_port}…")

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            # invio raw PCM direttamente
            sock.sendto(data, (udp_ip, udp_port))
    except KeyboardInterrupt:
        print("\nInterrotto dall’utente")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",   default="127.0.0.1", help="IP del server UDP (Node-RED)")
    parser.add_argument("--port", type=int, default=12345, help="Porta UDP")
    args = parser.parse_args()
    audio_stream(args.ip, args.port)