"""
Сервис для сканирования Wi-Fi сети и обнаружения подключенных устройств
"""

import socket
import time
import subprocess
import platform
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class NetworkScanner:
    """Класс для сканирования Wi-Fi сети"""
    
    # Порты для определения типа устройства
    DEVICE_PORTS = {
        80: 'Web Server / Router',
        443: 'HTTPS Server',
        22: 'SSH / Linux Device',
    
    # Определение типа устройства по MAC адресу (первые 3 байта - OUI)
    VENDOR_DB = {
        'apple': ['00:03:93', '00:05:02', '00:0a:27', '00:0d:93', '00:14:51', '00:16:cb', 
                  '00:17:f2', '00:19:e3', '00:1b:63', '00:1e:52', '00:1f:5b', '00:1f:f3',
                  '00:21:e9', '00:22:41', '00:23:12', '00:23:32', '00:23:6c', '00:23:df',
                  '00:24:36', '00:25:00', '00:25:4b', '00:25:bc', '00:26:08', '00:26:4a',
                  '00:26:b0', '00:26:bb', '3c:ab:8e', '40:6c:8f', '44:2a:60', '48:60:bc',
                  '4c:57:ca', '50:ea:d6', '54:26:96', '54:72:4f', '58:55:ca', '5c:59:48',
                  '5c:95:ae', '5c:f9:38', '60:69:44', '60:c5:47', '60:f8:1d', '64:20:0c',
                  '64:76:ba', '64:a3:cb', '64:b9:e8', '64:e6:82', '68:09:27', '68:5b:35',
                  '68:96:7b', '68:a8:6d', '68:db:ca', '6c:19:c0', '6c:4d:73', '6c:70:9f',
                  '6c:72:e7', '6c:96:cf', '6c:ab:31', '6c:c2:6b', '70:11:24', '70:48:0f',
                  '70:73:cb', '70:cd:60', '70:de:e2', '70:ec:e4', '74:1b:b2', '74:e1:b6',
                  '74:e2:f5', '78:31:c1', '78:6c:1c', '78:7b:8a', '78:a3:e4', '78:ca:39',
                  '78:d7:5f', '78:fd:94', '7c:01:91', '7c:11:be', '7c:50:49', '7c:6d:f8',
                  '7c:c3:a1', '7c:d1:c3', '7c:f0:5f', '80:49:71', '80:92:9f', '80:e6:50',
                  '84:38:35', '84:78:8b', '84:85:06', '84:fc:fe', '88:1f:a1', '88:53:95',
                  '88:63:df', '88:66:5a', '88:c6:63', '88:e8:7f', '8c:00:6d', '8c:2d:aa',
                  '8c:58:77', '8c:7c:92', '8c:85:90', '8c:fa:ba', '90:27:e4', '90:72:40',
                  '90:84:0d', '90:8d:6c', '90:b0:ed', '90:b2:1f', '94:94:26', '94:bf:2d',
                  '94:e9:6a', '94:f6:a3', '98:01:a7', '98:03:d8', '98:5a:eb', '98:b8:e3',
                  '98:ca:33', '98:d6:bb', '98:e0:d9', '98:fe:94', '9c:04:eb', '9c:20:7b',
                  '9c:35:5b', '9c:84:bf', '9c:f4:8e', 'a0:99:9b', 'a4:5e:60', 'a4:67:06',
                  'a4:b1:97', 'a4:c3:61', 'a4:d1:8c', 'a8:20:66', 'a8:60:b6', 'a8:66:7f',
                  'a8:88:08', 'a8:96:8a', 'a8:be:27', 'a8:fa:d8', 'ac:1f:74', 'ac:29:3a',
                  'ac:3c:0b', 'ac:61:ea', 'ac:7f:3e', 'ac:87:a3', 'ac:bc:32', 'ac:cf:5c',
                  'ac:de:48', 'ac:fd:ec', 'b0:34:95', 'b0:65:bd', 'b0:9f:ba', 'b0:ca:68',
                  'b4:18:d1', 'b4:8b:19', 'b4:f0:ab', 'b4:f6:1c', 'b8:09:8a', 'b8:17:c2',
                  'b8:41:a4', 'b8:44:d9', 'b8:53:ac', 'b8:63:4d', 'b8:78:2e', 'b8:8d:12',
                  'b8:c1:11', 'b8:c7:5d', 'b8:e8:56', 'b8:f6:b1', 'bc:3b:af', 'bc:52:b7',
                  'bc:67:1c', 'bc:6c:21', 'bc:92:6b', 'bc:a9:20', 'bc:ec:5d', 'c0:1a:da',
                  'c0:3f:0e', 'c0:6b:9d', 'c0:a5:3e', 'c0:b6:58', 'c0:ce:cd', 'c0:d0:12',
                  'c4:2c:03', 'c8:1e:e7', 'c8:2a:14', 'c8:33:4b', 'c8:69:cd', 'c8:6f:1d',
                  'c8:85:50', 'c8:89:f3', 'c8:b5:b7', 'c8:bc:c8', 'c8:d0:83', 'c8:e0:eb',
                  'cc:08:8d', 'cc:20:e8', 'cc:25:ef', 'cc:29:f5', 'cc:44:63', 'cc:78:5f',
                  'cc:c7:60', 'd0:03:4b', 'd0:23:db', 'd0:25:98', 'd0:33:11', 'd0:4f:7e',
                  'd0:81:7a', 'd0:a6:37', 'd0:c5:f3', 'd0:e1:40', 'd4:90:9c', 'd4:9a:20',
                  'd4:a3:3d', 'd4:f4:6f', 'd8:00:4d', 'd8:1c:79', 'd8:30:62', 'd8:9e:3f',
                  'd8:a2:5e', 'd8:bb:2c', 'd8:cf:9c', 'd8:d1:cb', 'd8:f1:5b', 'dc:0c:5c',
                  'dc:2b:2a', 'dc:2b:61', 'dc:37:18', 'dc:56:e7', 'dc:86:d8', 'dc:9b:9c',
                  'dc:a4:ca', 'dc:a9:04', 'dc:bf:e0', 'dc:d3:a2', 'dc:e5:5b', 'e0:5f:45',
                  'e0:66:78', 'e0:ac:cb', 'e0:b5:2d', 'e0:b9:ba', 'e0:c7:67', 'e0:f5:c6',
                  'e0:f8:47', 'e4:25:e7', 'e4:8b:7f', 'e4:98:d6', 'e4:9a:79', 'e4:c6:3d',
                  'e4:ce:8f', 'e8:04:62', 'e8:06:88', 'e8:80:2e', 'e8:8d:28', 'ec:35:86',
                  'ec:85:2f', 'f0:18:98', 'f0:24:75', 'f0:98:9d', 'f0:b4:79', 'f0:c1:f1',
                  'f0:db:e2', 'f0:dc:e2', 'f0:f6:1c', 'f4:0f:24', 'f4:1b:a1', 'f4:37:b7',
                  'f4:5c:89', 'f4:f1:5a', 'f4:f9:51', 'f8:1e:df', 'f8:27:93', 'f8:4f:57',
                  'fc:25:3f', 'fc:fc:48'],
        'samsung': ['00:00:f0', '00:07:ab', '00:0d:ae', '00:0d:e5', '00:12:47', '00:12:fb',
                   '00:13:77', '00:15:99', '00:15:b9', '00:16:32', '00:16:6b', '00:16:6c',
                   '00:17:c9', '00:17:d5', '00:18:af', '00:1a:8a', '00:1b:98', '00:1c:43',
                   '00:1d:25', '00:1d:f6', '00:1e:7d', '00:1e:e1', '00:1e:e2', '00:1f:cd',
                   '00:21:19', '00:21:4c', '00:23:39', '00:23:99', '00:23:d6', '00:23:d7',
                   '00:24:54', '00:24:90', '00:24:91', '00:24:e9', '00:25:38', '00:26:37',
                   '04:1b:ba', '04:fe:31', '08:08:c2', '08:d4:2b', '08:ee:8b', '0c:14:20',
                   '0c:89:10', '10:30:47', '10:77:b1', '10:92:66', '14:49:e0', '14:7d:c5',
                   '18:3f:47', '18:46:17', '18:67:b0', '1c:62:b8', '1c:66:6d', '1c:af:05',
                   '20:13:e0', '20:64:32', '20:6e:9c', '20:a9:9b', '20:d5:bf', '24:da:9b',
                   '24:f5:aa', '28:39:5e', '28:ba:b5', '28:cd:c4', '28:e3:1f', '2c:44:01',
                   '2c:44:fd', '2c:8a:72', '30:07:4d', '30:19:66', '30:d6:c9', '34:08:04',
                   '34:23:ba', '34:c3:ac', '34:fc:ef', '38:0a:94', '38:16:d1', '38:2d:d1',
                   '38:83:45', '3c:5a:37', '3c:62:00', '3c:8b:fe', '40:0e:85', '40:23:43',
                   '40:4d:8e', '40:5b:d8', '40:b8:9a', '40:d3:ae', '44:4e:1a', '44:87:fc',
                   '44:a7:cf', '44:d6:e8', '48:02:2a', '48:44:f7', '48:5a:3f', '48:db:50',
                   '4c:3c:16', '4c:bc:a5', '4c:e1:75', '50:01:bb', '50:32:75', '50:3d:c5',
                   '50:55:27', '50:56:bf', '50:a4:c8', '50:b7:c3', '50:c8:e5', '50:cc:f8',
                   '50:ea:d6', '54:33:cb', '54:88:0e', '54:92:be', '58:1f:28', '58:67:1a',
                   '58:91:cf', '58:a2:b5', '58:c3:8b', '5c:0a:5b', '5c:0e:8b', '5c:3c:27',
                   '5c:51:88', '5c:f6:dc', '60:21:c0', '60:6b:bd', '60:d0:a9', '60:f4:94',
                   '64:16:f0', '64:77:91', '64:b3:10', '68:14:01', '68:9a:87', '68:c4:4d',
                   '68:eb:ae', '6c:2f:2c', '6c:40:08', '6c:83:36', '6c:f3:73', '70:2a:d5',
                   '70:5a:0f', '70:f3:95', '74:40:bb', '74:45:8a', '74:5c:4b', '78:1f:db',
                   '78:25:ad', '78:40:e4', '78:47:1d', '78:52:1a', '78:59:5e', '78:bd:bc',
                   '78:d6:f0', '78:f7:be', '7c:11:cb', '7c:1c:4e', '7c:61:93', '7c:64:56',
                   '7c:b7:33', '7c:c2:c6', '80:18:a7', '80:19:34', '80:57:19', '80:71:7a',
                   '80:79:72', '80:7a:bf', '84:00:d2', '84:25:db', '84:38:38', '84:51:81',
                   '88:32:9b', '88:36:6c', '88:9b:39', '88:bd:45', '88:e3:ab', '8c:71:f8',
                   '8c:77:12', '8c:79:67', '90:18:7c', '90:4e:91', '94:0c:6d', '94:35:0a',
                   '98:0c:82', '98:52:b1', '9c:02:98', '9c:3a:af', '9c:b2:b2', 'a0:07:98',
                   'a0:0b:ba', 'a0:21:95', 'a0:75:91', 'a0:8e:78', 'a0:b4:a5', 'a0:d0:dc',
                   'a4:9a:58', 'a4:eb:d3', 'a8:7c:01', 'a8:f2:74', 'ac:36:13', 'ac:3f:a4',
                   'ac:5f:3e', 'b0:72:bf', 'b0:c7:45', 'b0:ec:71', 'b4:07:f9', 'b4:62:93',
                   'b4:79:a7', 'b8:5e:7b', 'b8:5f:98', 'b8:c6:8e', 'bc:14:85', 'bc:15:ac',
                   'bc:20:ba', 'bc:44:86', 'bc:72:b1', 'bc:79:ad', 'bc:85:56', 'bc:98:89',
                   'bc:b1:f3', 'c0:97:27', 'c0:bd:d1', 'c4:42:02', 'c4:57:6e', 'c4:62:ea',
                   'c8:19:f7', 'c8:3d:d4', 'c8:a8:23', 'c8:ba:94', 'c8:d1:5e', 'c8:f2:30',
                   'cc:03:fa', 'cc:07:ab', 'cc:fe:3c', 'd0:17:6a', 'd0:22:be', 'd0:59:e4',
                   'd0:66:7b', 'd0:87:e2', 'd0:df:c7', 'd4:87:d8', 'd4:88:90', 'd4:e8:b2',
                   'd8:57:ef', 'd8:90:e8', 'd8:c4:6a', 'dc:71:44', 'dc:74:a8', 'e4:12:1d',
                   'e4:32:cb', 'e4:40:e2', 'e4:7c:f9', 'e4:92:fb', 'e4:b0:21', 'e4:e0:c5',
                   'e8:03:9a', 'e8:11:32', 'e8:50:8b', 'e8:b2:ac', 'e8:e5:d6', 'ec:1d:8b',
                   'ec:9b:f3', 'f0:08:f1', 'f0:25:b7', 'f0:5a:09', 'f0:6b:ca', 'f0:e7:7e',
                   'f4:09:d8', 'f4:7b:5e', 'f4:d9:fb', 'f8:04:2e', 'f8:d0:ac', 'f8:e0:79',
                   'f8:e6:1a', 'fc:03:9f', 'fc:a1:3e', 'fc:c7:34'],
        'xiaomi': ['00:9e:c8', '04:cf:4b', '08:57:00', '0c:1d:af', '0c:61:cf', '10:2a:b3',
                  '10:4f:a8', '14:75:5b', '14:f6:5a', '18:59:36', '1c:1b:0d', '20:34:fb',
                  '28:6c:07', '28:e3:47', '2c:3a:fd', '34:5b:8e', '34:60:f9', '34:ce:00',
                  '38:83:45', '3c:bd:d8', '3c:e7:2a', '40:31:3c', '44:03:2c', '44:23:7c',
                  '50:64:2b', '50:8f:4c', '54:25:ea', '58:13:d0', '58:44:98', '58:cf:79',
                  '5c:c9:d3', '64:09:80', '64:76:ba', '68:3e:34', '68:df:dd', '6c:fa:89',
                  '70:e7:2c', '74:23:44', '74:51:ba', '78:02:b7', '78:02:f8', '78:11:dc',
                  '7c:1d:d9', '7c:49:eb', '7c:da:b6', '80:35:c1', '80:d2:1d', '80:ea:07',
                  '84:a8:e4', '88:c3:97', '8c:be:be', '90:67:1c', '98:fa:e3', '9c:28:ef',
                  '9c:99:a0', 'a0:86:c6', 'a4:da:22', 'a8:7e:ea', 'ac:12:03', 'ac:23:3f',
                  'ac:c1:ee', 'b0:e2:35', 'b4:0b:44', 'b8:f8:53', 'c4:0b:cb', 'c4:6a:b7',
                  'c8:83:14', 'c8:ff:77', 'cc:32:e5', 'd0:6f:cb', 'd0:c6:37', 'd4:61:da',
                  'd4:97:0b', 'd8:32:14', 'd8:96:85', 'e0:19:1d', 'e4:46:da', 'f0:b4:29',
                  'f4:8e:92', 'f4:f5:24', 'f8:28:19', 'f8:59:71', 'fc:64:ba'],
        'huawei': ['00:1e:10', '00:25:68', '00:46:4b', '00:66:4b', '00:9a:cd', '00:e0:fc',
                  '04:02:1f', '04:33:c2', '08:10:77', '08:19:a6', '0c:37:dc', '0c:96:bf',
                  '10:1f:74', '10:47:80', '18:0f:76', '18:31:bf', '18:4f:32', '18:e2:9f',
                  '1c:48:ed', '1c:61:b4', '1c:7e:51', '1c:b7:2c', '20:08:ed', '20:f3:a3',
                  '24:09:95', '24:1f:a0', '24:69:68', '28:31:52', '28:6e:d4', '28:c6:8e',
                  '2c:ab:a4', '2c:f0:a2', '30:2d:2d', '34:00:a3', '34:6a:c2', '34:6b:d3',
                  '34:cd:be', '38:bc:01', '38:c8:5c', '3c:a9:f4', '3c:d5:79', '40:4d:7f',
                  '40:4e:36', '44:11:3e', '44:48:c1', '44:6e:e5', '48:7b:6b', '48:d5:39',
                  '48:db:50', '48:f8:b3', '4c:1f:cc', '4c:54:99', '50:01:bb', '50:d4:f7',
                  '54:25:ea', '54:51:1b', '54:88:0e', '58:2a:f7', '5c:3a:45', '5c:63:bf',
                  '5c:cf:7f', '5c:e3:0e', '60:de:44', '64:3e:8c', '64:a6:51', '68:3e:34',
                  '68:59:7b', '6c:4a:85', '6c:92:bf', '70:72:3c', '74:90:50', '74:a5:28',
                  '78:d7:52', '7c:60:97', '80:38:bc', '80:71:7a', '80:89:17', '84:a8:e4',
                  '84:db:ac', '88:28:b3', '88:53:d4', '88:cf:98', '8c:0f:6f', '8c:34:fd',
                  '90:17:ac', '90:67:1c', '94:d9:b3', '98:52:b1', '98:e1:7e', '9c:28:ef',
                  '9c:52:f8', '9c:a9:f4', 'a0:d8:44', 'a4:50:46', 'a4:c4:94', 'a8:4e:3f',
                  'ac:85:3d', 'ac:e2:15', 'b0:c5:59', 'b4:cd:27', 'b4:e6:2a', 'b8:08:d7',
                  'bc:25:e0', 'bc:46:99', 'c0:18:03', 'c4:0b:cb', 'c4:f0:81', 'c8:14:79',
                  'c8:3a:35', 'cc:a2:23', 'cc:b1:1a', 'cc:c0:79', 'd0:57:85', 'd4:6e:5c',
                  'd4:f9:a1', 'd8:49:0b', 'dc:d9:16', 'e0:19:1d', 'e0:99:71', 'e4:d3:32',
                  'e8:cd:2d', 'ec:23:3d', 'ec:38:8f', 'ec:6c:9f', 'f0:79:59', 'f4:4e:fc',
                  'f4:7b:5e', 'f8:7b:8c', 'f8:a4:5f', 'fc:48:ef'],
        'tp-link': ['00:27:19', '14:cf:92', '18:d6:c7', '1c:3b:f3', '20:dc:e6', '50:c7:bf',
                   '54:a0:50', '64:66:b3', '74:da:88', '88:25:2c', '8c:21:0a', '90:f6:52',
                   'a0:f3:c1', 'a4:2b:8c', 'ac:15:a2', 'ac:84:c6', 'b0:4e:26', 'b0:95:8e',
                   'c0:4a:00', 'c4:6e:1f', 'c4:e9:84', 'cc:32:e5', 'd4:6e:0e', 'd8:07:b6',
                   'e8:48:b8', 'e8:94:f6', 'ec:08:6b', 'f4:6d:04', 'f4:f2:6d', 'f8:1a:67'],
        'router': ['00:0c:29', '00:15:5d', '00:1c:42', '00:50:56', '08:00:27', '52:54:00'],
        'camera': ['00:12:12', '00:40:8c', '44:19:b6', '5c:f9:6a', 'e0:62:67'],
        'smart_tv': ['00:09:d0', '00:11:d9', '00:13:ce', '00:17:ab', '00:1b:98', '00:1d:25',
                    '00:1e:e1', '00:21:19', '00:26:37', '04:fe:31', '08:08:c2', '0c:14:20',
                    '10:30:47', '10:77:b1', '14:7d:c5', '18:3f:47', '1c:af:05', '20:13:e0',
                    '24:da:9b', '28:ba:b5', '2c:44:01', '30:19:66', '34:08:04', '38:0a:94',
                    '3c:62:00', '40:0e:85', '44:4e:1a', '48:44:f7', '4c:bc:a5', '50:32:75',
                    '50:a4:c8', '50:c8:e5', '54:88:0e', '58:1f:28', '58:a2:b5', '5c:0a:5b',
                    '60:21:c0', '60:d0:a9', '64:16:f0', '68:14:01', '68:c4:4d', '6c:40:08',
                    '70:2a:d5', '74:5c:4b', '78:bd:bc', '7c:11:cb', '7c:c2:c6', '80:18:a7',
                    '80:71:7a', '84:25:db', '88:32:9b', '88:e3:ab', '8c:79:67', '90:18:7c',
                    '94:0c:6d', '98:0c:82', '9c:02:98', 'a0:07:98', 'a0:75:91', 'a4:eb:d3',
                    'ac:36:13', 'b0:72:bf', 'b4:07:f9', 'b8:5e:7b', 'bc:14:85', 'bc:72:b1',
                    'c0:97:27', 'c4:57:6e', 'c8:a8:23', 'cc:03:fa', 'd0:22:be', 'd4:87:d8',
                    'd8:57:ef', 'dc:71:44', 'e4:12:1d', 'e4:92:fb', 'e8:03:9a', 'ec:9b:f3',
                    'f0:08:f1', 'f0:5a:09', 'f4:7b:5e', 'f8:04:2e'],
    }       'description': 'Memcached может быть использован для DDoS атак',
            'recommendation': 'Ограничьте доступ только локальной сетью'
        },
        27017: {
            'service': 'MongoDB',
            'severity': 'critical',
            'description': 'MongoDB открыт без аутентификации',
            'recommendation': 'Включите аутентификацию и firewall'
        }
    }
    
    def __init__(self, timeout=1.0, max_workers=50):
        """
        Инициализация сканера
        
        Args:
            timeout: Таймаут для подключения к порту (в секундах)
            max_workers: Максимальное количество потоков
        """
        self.timeout = timeout
        self.max_workers = max_workers
        
    def get_local_network(self):
        """Определяет локальную сеть текущего компьютера"""
        try:
            # Получаем IP адрес компьютера
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Создаём подсеть /24 (255 адресов)
            parts = local_ip.split('.')
            network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            
            return local_ip, network
        except Exception as e:
            logger.error(f"Ошибка определения сети: {e}")
            return None, None
    
    def ping_host(self, ip: str) -> bool:
        """Проверяет доступность хоста через ping"""
        try:
            # Windows использует -n, Linux/Mac используют -c
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            # Проверяем только 1 пакет с таймаутом
            command = ['ping', param, '1', '-w', '1000', ip] if platform.system().lower() == 'windows' else ['ping', param, '1', '-W', '1', ip]
            
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def get_mac_address(self, ip: str) -> Optional[str]:
        """Получает MAC адрес устройства"""
        try:
            # Windows: arp -a | findstr IP
            # Linux/Mac: arp -n IP
            if platform.system().lower() == 'windows':
                result = subprocess.run(
                    ['arp', '-a', ip],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                output = result.stdout
                
                # Ищем MAC в формате xx-xx-xx-xx-xx-xx
                mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', output)
                if mac_match:
                    mac = mac_match.group(0).replace('-', ':').upper()
                    return mac
            else:
                result = subprocess.run(
                    ['arp', '-n', ip],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                output = result.stdout
                
                # Ищем MAC в формате xx:xx:xx:xx:xx:xx
                mac_match = re.search(r'([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})', output)
                if mac_match:
                    return mac_match.group(0).upper()
            
            return None
        except Exception as e:
            logger.debug(f"Ошибка получения MAC для {ip}: {e}")
            return None
    
    def resolve_target(self, target: str) -> Optional[str]:
        """
        Разрешить домен в IP адрес
        
        Args:
            target: Домен или IP
            
        Returns:
            IP адрес или None
        """
        try:
            return socket.gethostbyname(target)
        except socket.gaierror:
            logger.error(f'Failed to resolve {target}')
            return None
    
    def scan_port(self, ip: str, port: int) -> Dict:
        """
        Сканировать один порт
        
        Args:
            ip: IP адрес
            port: Номер порта
            
        Returns:
            Словарь с результатами сканирования
        """
        result = {
            'port': port,
            'state': 'closed',
            'service': self.SERVICE_DB.get(port, 'Unknown'),
            'banner': None
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Пытаемся подключиться
            connection_result = sock.connect_ex((ip, port))
            
            if connection_result == 0:
                result['state'] = 'open'
                
                # Пытаемся получить баннер
                try:
                    sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    if banner:
                        result['banner'] = banner[:200]  # Ограничиваем длину
                except:
                    pass
            
            sock.close()
            
        except socket.timeout:
            result['state'] = 'filtered'
        except Exception as e:
            logger.debug(f'Error scanning port {port}: {e}')
        
        return result
    
    def scan_ports(self, ip: str, ports: List[int]) -> List[Dict]:
        """
        Сканировать список портов
        
        Args:
            ip: IP адрес
            ports: Список портов для сканирования
            
        Returns:
            Список открытых портов с информацией
        """
        open_ports = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаём задачи для всех портов
            future_to_port = {
                executor.submit(self.scan_port, ip, port): port 
                for port in ports
            }
            
            # Собираем результаты
            for future in as_completed(future_to_port):
                try:
                    result = future.result()
                    if result['state'] == 'open':
                        open_ports.append(result)
                except Exception as e:
                    logger.error(f'Port scan future error: {e}')
        
        return sorted(open_ports, key=lambda x: x['port'])
    
    def detect_service_version(self, ip: str, port: int, service: str) -> Optional[str]:
        """
        Определить версию сервиса
        
        Args:
            ip: IP адрес
            port: Порт
            service: Название сервиса
            
        Returns:
            Версия сервиса или None
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((ip, port))
            
            # Специфичные запросы для разных сервисов
            if service in ['HTTP', 'HTTPS']:
                sock.send(b'HEAD / HTTP/1.1\r\nHost: localhost\r\n\r\n')
            elif service == 'SSH':
                pass  # SSH отправляет баннер сразу
            elif service == 'FTP':
                pass  # FTP отправляет баннер сразу
            else:
                sock.send(b'\r\n')
            
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            
            # Извлекаем версию из ответа
            if 'Server:' in response:
                for line in response.split('\n'):
                    if line.startswith('Server:'):
                        return line.split(':', 1)[1].strip()[:100]
            
            # Для SSH/FTP баннер в первой строке
            if service in ['SSH', 'FTP']:
                first_line = response.split('\n')[0].strip()
                if first_line:
                    return first_line[:100]
            
        except Exception as e:
            logger.debug(f'Service version detection error for {service} on port {port}: {e}')
        
        return None
    
    def check_vulnerabilities(self, open_ports: List[Dict]) -> List[Dict]:
        """
        Проверить открытые порты на известные уязвимости
        
        Args:
            open_ports: Список открытых портов
            
        Returns:
            Список найденных уязвимостей
        """
        vulnerabilities = []
        
        for port_info in open_ports:
            port = port_info['port']
            
            if port in self.VULNERABILITY_DB:
                vuln = self.VULNERABILITY_DB[port].copy()
                vuln['port'] = port
                vuln['detected_service'] = port_info['service']
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def run_full_scan(self, target: str, scan_ports: bool = True, 
                     scan_services: bool = True, custom_ports: Optional[List[int]] = None) -> Dict:
        """
        Выполнить полное сканирование
        
        Args:
            target: Цель сканирования (IP или домен)
            scan_ports: Сканировать порты
            scan_services: Определять версии сервисов
            custom_ports: Пользовательский список портов (или None для стандартных)
            
        Returns:
            Словарь с результатами сканирования
        """
        start_time = time.time()
        
        result = {
            'target': target,
            'resolved_ip': None,
            'open_ports': [],
            'services': {},
            'vulnerabilities': [],
            'total_ports_scanned': 0,
            'scan_duration': 0,
            'os_detection': None
        }
        
        # Разрешаем IP
        ip = self.resolve_target(target)
        if not ip:
            raise Exception(f'Не удалось разрешить цель: {target}')
        
        result['resolved_ip'] = ip
        
        # Определяем список портов для сканирования
        if custom_ports:
            ports_to_scan = custom_ports
        else:
            ports_to_scan = self.COMMON_PORTS
        
        result['total_ports_scanned'] = len(ports_to_scan)
        
        # Сканируем порты
        if scan_ports:
            result['open_ports'] = self.scan_ports(ip, ports_to_scan)
        
        # Определяем версии сервисов
        if scan_services and result['open_ports']:
            for port_info in result['open_ports']:
                version = self.detect_service_version(
                    ip, 
                    port_info['port'], 
                    port_info['service']
                )
                if version:
                    result['services'][port_info['port']] = {
                        'name': port_info['service'],
                        'version': version,
                        'banner': port_info.get('banner')
                    }
        
        # Проверяем уязвимости
        result['vulnerabilities'] = self.check_vulnerabilities(result['open_ports'])
        
        # Простое определение ОС по открытым портам
        result['os_detection'] = self._detect_os(result['open_ports'])
        
        # Время сканирования
        result['scan_duration'] = round(time.time() - start_time, 2)
        
        return result
    
    def _detect_os(self, open_ports: List[Dict]) -> Optional[str]:
        """
        Простое определение ОС по открытым портам
        
        Args:
            open_ports: Список открытых портов
            
        Returns:
            Предполагаемая ОС
        """
        ports = [p['port'] for p in open_ports]
        
        # Windows признаки
        if 3389 in ports or 445 in ports:
            return 'Вероятно Windows Server'
        
        # Linux/Unix признаки
        if 22 in ports:
            return 'Вероятно Linux/Unix'
        
        # Web server
        if 80 in ports or 443 in ports:
            if 3306 in ports:
                return 'Вероятно LAMP Stack (Linux)'
            return 'Вероятно Web Server'
        
        return 'Не удалось определить'
