import network
import socket
import uasyncio as asyncio
from machine import I2S
from MIC_async import MIC  # la tua libreria così com’è


# 2) Task di streaming audio via UDP
async def audio_stream_task(
    udp_ip="192.168.1.100",
    udp_port=12345,
    sck_pin=14,
    ws_pin=15,
    sd_pin=32
):
    # 2.1) Assicurati di aver già connesso il Wi-Fi
    addr = (udp_ip, udp_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 2.2) callback che manda ogni chunk su UDP
    def send_chunk(data: bytes):
        try:
            sock.sendto(data, addr)
        except Exception as e:
            print("Errore invio chunk:", e)

    # 2.3) Istanzia MIC con parametri identici al PC
    mic = MIC(
        sck_pin=sck_pin,
        ws_pin=ws_pin,
        sd_pin=sd_pin,
        bits_per_sample=16,
        format=I2S.MONO,
        sample_rate=8000,
        buff_size=1024,
        i2s_id=0
    )

    # 2.4) Avvia la registrazione asincrona; invia chunk via UDP
    try:
        await mic.record(send_chunk, buff_size=1024)
    finally:
        sock.close()