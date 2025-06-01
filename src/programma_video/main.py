
# The MIT License (MIT)
#
# Copyright (c) Sharil Tumin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-----------------------------------------------------------------------------

# main.py

from machine import reset
from time import sleep
import usocket as soc
import gc

import camera
from wifi import Sta
from help import Setting as cam_setting
import site

auth = site.auth
pwd = site.pwd

def clean_up(cs):
   cs.close()      # svuota il buffer e chiude il socket
   del cs
   gc.collect()

def route(pm):
   cs, rq = pm
   pth = '*NOP*'
   rqp = rq.split('/')
   rl = len(rqp)

   if rl == 1:          # rq == ""
      pth = '/'
      v = 0
   elif rl == 2:        # rq == "/" oppure "/a"
      pth = f'/{rqp[1]}'
      v = 0
   else:                # rq == "/a/v" o "/a/v/w/..."
      pth = f'/{rqp[1]}'
      if rqp[1] == 'login':
         v = rqp[2]
      else:
         try:
            v = int(rqp[2])
         except:
            v = 0
            pth = '*ERR*'
            print('Not an integer value', rqp[2])

   if pth in site.app:
      site.app[pth](cs, v)
   elif pth == '*NOP*':
      site.NOP(cs)
   else:
      site.ERR(cs)

   clean_up(cs)

def server(pm):
   p = pm[0]
   ss = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
   ss.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
   sa = ('0.0.0.0', p)
   ss.bind(sa)
   ss.listen(1)  # serve un client alla volta
   print("Start server", p)
   if auth.on:
      print(f"Try - http://{site.server}/login/{auth.pwd}")
   else:
      print(f"Try - http://{site.server}")

   while True:
      ms = ''
      rq = []
      try:
         cs, ca = ss.accept()
      except:
         pass
      else:
         r = b''
         e = ''
         try:
            r = cs.recv(1024)
         except Exception as e:
            print(f"EX:{e}")
            clean_up(cs)

         try:
            ms = r.decode()
            rq = ms.split(' ')
         except Exception as e:
            print(f"RQ:{ms} EX:{e}")
            clean_up(cs)
         else:
            if len(rq) >= 2:
               print(ca, rq[:2])
               rv, ph = rq[:2]  # GET /path
               if not auth.on:
                  route((cs, ph))
                  continue
               elif auth.ip == ca[0]:  # client già autenticato
                  route((cs, ph))
                  continue
               elif ph.find('login/') >= 0:  # richiesta di login
                  site.client = ca[0]
                  route((cs, ph))
                  continue
               else:
                  # Non autorizzato
                  site.NO(cs)
                  clean_up(cs)

# ------------------------------------------------------------
# INIZIALIZZAZIONE DELLA CAMERA
# ------------------------------------------------------------
for i in range(5):
   cam = camera.init()
   print("Camera ready?: ", cam)
   if cam:
      break
   else:
      sleep(2)
else:
   print('Timeout')
   reset()

if cam:
   print("Camera ready")
   # ------------------------------------------------------------
   # INIZIALIZZAZIONE DEL WIFI (con IP statico)
   # ------------------------------------------------------------
   w = Sta()

   STATIC_IP   = '192.168.1.50'
   NETMASK     = '255.255.255.0'
   GATEWAY     = '192.168.1.1'
   DNS_SERVER  = '192.168.1.1'

   # Applica la configurazione statica prima di connettere
   w.set_static_ip(STATIC_IP, NETMASK, GATEWAY, DNS_SERVER)

   # Effettua la connessione al router
   w.connect()
   w.wait()

   # Controlla fino a 5 secondi che la WiFi sia effettivamente connessa
   for i in range(5):
      if w.wlan.isconnected():
         break
      else:
         print("WIFI not ready. Wait...")
         sleep(2)
   else:
      print("WIFI not ready. Can't continue!")
      reset()

# ------------------------------------------------------------
# CONFIGURAZIONE AUTENTICAZIONE
# ------------------------------------------------------------
auth.on = False
# auth.on = True

if auth.on:
   auth.pwd = pwd()
   auth.ip  = ''
   print(f'PWD: {auth.pwd}')

camera.framesize(10)    
camera.contrast(2)      
camera.speffect(2)       

cam_setting['framesize'] = 10
cam_setting['contrast']  = 2
cam_setting['speffect']  = 2

site.ip     = w.wlan.ifconfig()[0]
site.camera = camera

# Avvia il server HTTP sulla porta 80 (TCP)
server((80,))

# Se mai esce dal ciclo server, forza un reset della board
reset()


