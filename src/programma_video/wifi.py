
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

#Basic WiFi configuration:
from time import sleep
import network
import site

class Sta:

   AP = "" 
   PWD = ""

   def __init__(my, ap='', pwd=''):
      # Disabilita l’Access Point interno
      network.WLAN(network.AP_IF).active(False)
      # Attiva la modalità Station (STA)
      my.wlan = network.WLAN(network.STA_IF)
      my.wlan.active(True)

      if ap == '':
         my.ap = Sta.AP
         my.pwd = Sta.PWD 
      else:
         my.ap = ap
         my.pwd = pwd

      # Storage per la configurazione IP statica (se impostata)
      my.static_ip = None

   def set_static_ip(my, ip, subnet, gateway, dns):
      """
      Imposta manualmente un IP statico (IP, netmask, gateway, DNS).
      Deve essere chiamato PRIMA di .connect().
      """
      my.static_ip = (ip, subnet, gateway, dns)
      # Applica subito la configurazione sulla scheda di rete
      my.wlan.ifconfig(my.static_ip)

   def connect(my, ap='', pwd=''):
      """
      Connessione alla rete WiFi. 
      Se è stata già fatta una configurazione statica, 
      richiama ifconfig() prima di eseguire wlan.connect().
      """
      if ap != '':
         my.ap = ap
         my.pwd = pwd

      # Se è stato configurato un IP statico, ripassa la tupla a ifconfig
      if my.static_ip:
         my.wlan.ifconfig(my.static_ip)

      if not my.wlan.isconnected(): 
         my.wlan.connect(my.ap, my.pwd)

   def status(my):
      """
      Restituisce la tupla ifconfig() se connesso, altrimenti ritorna ()
      """
      if my.wlan.isconnected():
         return my.wlan.ifconfig()
      else:
         return ()

   def wait(my):
      """
      Attende fino a 30 secondi che la connessione vada a buon fine.
      Alla connessione, imposta site.server = IP_locale.
      """
      cnt = 30
      while cnt > 0:
         print("Waiting ...")
         if my.wlan.isconnected():
           print("Connected to %s" % my.ap)
           print('network config:', my.wlan.ifconfig())
           site.server = my.wlan.ifconfig()[0]
           cnt = 0
         else:
           sleep(5)
           cnt -= 5
      return

   def scan(my):
      """
      Ritorna la lista delle reti WiFi disponibili.
      """
      return my.wlan.scan()

