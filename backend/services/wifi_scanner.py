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


class WiFiScanner:
    """Класс для сканирования Wi-Fi сети"""
    
    # Порты для определения типа устройства
    DEVICE_PORTS = [22, 80, 443, 445, 554, 3389, 5000, 5900, 7000, 8000, 8080, 9000, 62078]
    
    # Определение производителя по MAC адресу (первые 3 байта - OUI)
    VENDOR_DB = {
        'Apple': ['00:03:93', '00:05:02', '00:0a:27', '3c:ab:8e', '40:6c:8f', '44:2a:60', 
                  '50:ea:d6', '54:26:96', '58:55:ca', '5c:59:48', '60:69:44', '60:c5:47',
                  '64:20:0c', '64:76:ba', '68:09:27', '6c:19:c0', '70:11:24', '74:1b:b2',
                  '78:31:c1', '7c:01:91', '80:49:71', '84:38:35', '88:1f:a1', '8c:00:6d',
                  '90:27:e4', '94:94:26', '98:01:a7', '9c:04:eb', 'a0:99:9b', 'a4:5e:60',
                  'a8:20:66', 'ac:1f:74', 'b0:34:95', 'b4:18:d1', 'b8:09:8a', 'bc:3b:af',
                  'c0:1a:da', 'c4:2c:03', 'c8:1e:e7', 'cc:08:8d', 'd0:03:4b', 'd4:90:9c',
                  'd8:00:4d', 'dc:0c:5c', 'e0:5f:45', 'e4:25:e7', 'e8:04:62', 'ec:35:86',
                  'f0:18:98', 'f4:0f:24', 'f8:1e:df', 'fc:25:3f'],
        'Samsung': ['00:00:f0', '00:07:ab', '00:12:47', '00:13:77', '00:15:99', '00:16:32',
                    '04:1b:ba', '08:08:c2', '0c:14:20', '10:30:47', '14:49:e0', '18:3f:47',
                    '1c:62:b8', '20:13:e0', '24:da:9b', '28:39:5e', '2c:44:01', '30:07:4d',
                    '34:08:04', '38:0a:94', '3c:5a:37', '40:0e:85', '44:4e:1a', '48:02:2a',
                    '4c:3c:16', '50:01:bb', '54:33:cb', '58:1f:28', '5c:0a:5b', '60:21:c0',
                    '64:16:f0', '68:14:01', '6c:2f:2c', '70:2a:d5', '74:40:bb', '78:1f:db',
                    '7c:11:cb', '80:18:a7', '84:00:d2', '88:32:9b', '8c:71:f8', '90:18:7c',
                    '94:0c:6d', '98:0c:82', '9c:02:98', 'a0:07:98', 'a4:9a:58', 'a8:7c:01',
                    'ac:36:13', 'b0:72:bf', 'b4:07:f9', 'b8:5e:7b', 'bc:14:85', 'c0:97:27',
                    'c4:42:02', 'c8:19:f7', 'cc:03:fa', 'd0:17:6a', 'd4:87:d8', 'd8:57:ef',
                    'dc:71:44', 'e4:12:1d', 'e8:03:9a', 'ec:9b:f3', 'f0:08:f1', 'f4:7b:5e',
                    'f8:04:2e', 'fc:03:9f'],
        'Xiaomi': ['00:9e:c8', '04:cf:4b', '08:57:00', '0c:1d:af', '10:2a:b3', '14:75:5b',
                   '18:59:36', '1c:1b:0d', '20:34:fb', '28:6c:07', '2c:3a:fd', '34:5b:8e',
                   '38:83:45', '3c:bd:d8', '40:31:3c', '44:03:2c', '50:64:2b', '54:25:ea',
                   '58:13:d0', '5c:c9:d3', '64:09:80', '68:3e:34', '6c:fa:89', '70:e7:2c',
                   '74:23:44', '78:02:b7', '7c:1d:d9', '80:35:c1', '84:a8:e4', '88:c3:97',
                   '8c:be:be', '90:67:1c', '98:fa:e3', '9c:28:ef', 'a0:86:c6', 'a4:da:22',
                   'a8:7e:ea', 'ac:12:03', 'ac:c1:ee', 'b0:e2:35', 'b4:0b:44', 'b8:f8:53',
                   'c4:0b:cb', 'c8:83:14', 'cc:32:e5', 'd0:6f:cb', 'd4:61:da', 'd8:32:14',
                   'e0:19:1d', 'e4:46:da', 'f0:b4:29', 'f4:8e:92', 'f8:28:19', 'fc:64:ba'],
        'Huawei': ['00:1e:10', '00:25:68', '00:46:4b', '00:9a:cd', '04:02:1f', '08:10:77',
                   '0c:37:dc', '10:1f:74', '18:0f:76', '1c:48:ed', '20:08:ed', '24:09:95',
                   '28:31:52', '2c:ab:a4', '30:2d:2d', '34:00:a3', '38:bc:01', '3c:a9:f4',
                   '40:4d:7f', '44:11:3e', '48:7b:6b', '4c:1f:cc', '50:01:bb', '54:25:ea',
                   '58:2a:f7', '5c:3a:45', '60:de:44', '64:3e:8c', '68:3e:34', '6c:4a:85',
                   '70:72:3c', '74:90:50', '78:d7:52', '7c:60:97', '80:38:bc', '84:a8:e4',
                   '88:28:b3', '8c:0f:6f', '90:17:ac', '94:d9:b3', '98:52:b1', '9c:28:ef',
                   'a0:d8:44', 'a4:50:46', 'a8:4e:3f', 'ac:85:3d', 'b0:c5:59', 'b4:cd:27',
                   'b8:08:d7', 'bc:25:e0', 'c0:18:03', 'c4:0b:cb', 'c8:14:79', 'cc:a2:23',
                   'd0:57:85', 'd4:6e:5c', 'd8:49:0b', 'dc:d9:16', 'e0:19:1d', 'e4:d3:32',
                   'e8:cd:2d', 'ec:23:3d', 'f0:79:59', 'f4:4e:fc', 'f8:7b:8c', 'fc:48:ef'],
        'TP-Link': ['00:27:19', '14:cf:92', '18:d6:c7', '1c:3b:f3', '20:dc:e6', '50:c7:bf',
                    '54:a0:50', '64:66:b3', '74:da:88', '88:25:2c', '8c:21:0a', '90:f6:52',
                    'a0:f3:c1', 'a4:2b:8c', 'ac:15:a2', 'ac:84:c6', 'b0:4e:26', 'b0:95:8e',
                    'c0:4a:00', 'c4:6e:1f', 'c4:e9:84', 'cc:32:e5', 'd4:6e:0e', 'd8:07:b6',
                    'e8:48:b8', 'e8:94:f6', 'ec:08:6b', 'f4:6d:04', 'f4:f2:6d', 'f8:1a:67'],
    }
    
    def __init__(self, timeout=0.3, max_workers=100):
        """
        Инициализация сканера
        
        Args:
            timeout: Таймаут для подключения (в секундах)
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
            network = f"{parts[0]}.{parts[1]}.{parts[2]}"
            
            return local_ip, network
        except Exception as e:
            logger.error(f"Ошибка определения сети: {e}")
            return None, None
    
    def ping_host(self, ip: str) -> bool:
        """Проверяет доступность хоста"""
        try:
            # Windows использует -n, Linux/Mac используют -c
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            timeout_param = '500' if platform.system().lower() == 'windows' else '0.5'
            timeout_flag = '-w' if platform.system().lower() == 'windows' else '-W'
            
            command = ['ping', param, '1', timeout_flag, timeout_param, ip]
            
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False
    
    def get_mac_address(self, ip: str) -> Optional[str]:
        """Получает MAC адрес устройства"""
        try:
            system = platform.system().lower()
            
            # На серверах без прямого доступа к сети MAC адреса недоступны
            if system == 'linux':
                # Проверяем, доступен ли ARP
                try:
                    # Используем ip neigh show (современная альтернатива arp)
                    result = subprocess.run(
                        ['ip', 'neigh', 'show', ip],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                    output = result.stdout
                    
                    # Ищем MAC в формате xx:xx:xx:xx:xx:xx
                    mac_match = re.search(r'([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})', output)
                    if mac_match:
                        return mac_match.group(0).upper()
                except FileNotFoundError:
                    # Если ip команда не найдена, пробуем arp
                    try:
                        result = subprocess.run(
                            ['arp', '-n', ip],
                            capture_output=True,
                            text=True,
                            timeout=1
                        )
                        output = result.stdout
                        
                        mac_match = re.search(r'([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})', output)
                        if mac_match:
                            return mac_match.group(0).upper()
                    except FileNotFoundError:
                        logger.debug(f"Ни 'ip', ни 'arp' команды недоступны на этой системе")
                        return None
                        
            elif system == 'windows':
                result = subprocess.run(
                    ['arp', '-a', ip],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                output = result.stdout
                
                # Ищем MAC в формате xx-xx-xx-xx-xx-xx
                mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', output)
                if mac_match:
                    mac = mac_match.group(0).replace('-', ':').upper()
                    return mac
            
            return None
        except Exception as e:
            logger.debug(f"Ошибка получения MAC для {ip}: {e}")
            return None
    
    def get_hostname(self, ip: str) -> Optional[str]:
        """Получает имя хоста по IP"""
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except:
            return None
    
    def check_port(self, ip: str, port: int) -> bool:
        """Проверяет открыт ли порт"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def identify_vendor(self, mac: str) -> str:
        """Определяет производителя по MAC адресу"""
        if not mac:
            return 'Unknown'
        
        mac_prefix = mac[:8]  # Первые 3 байта (XX:XX:XX)
        
        for vendor, prefixes in self.VENDOR_DB.items():
            if any(mac.upper().startswith(prefix.upper()) for prefix in prefixes):
                return vendor
        
        return 'Unknown'
    
    def identify_device_type(self, mac: str, open_ports: List[int], hostname: str) -> Dict:
        """Определяет тип устройства"""
        vendor = self.identify_vendor(mac)
        device_type = 'Неизвестное устройство'
        icon = 'fa-question-circle'
        
        # Определение по производителю
        if vendor == 'Apple':
            if any(port in open_ports for port in [5000, 7000, 62078]):
                device_type = 'iPhone/iPad/Mac'
                icon = 'fa-mobile-alt'
            else:
                device_type = 'Устройство Apple'
                icon = 'fa-apple'
        elif vendor in ['Samsung', 'Xiaomi', 'Huawei']:
            device_type = f'Телефон {vendor}'
            icon = 'fa-mobile-alt'
        elif vendor == 'TP-Link':
            device_type = 'Роутер'
            icon = 'fa-wifi'
        
        # Определение по открытым портам
        if 80 in open_ports or 443 in open_ports:
            if 554 in open_ports or 8000 in open_ports:
                device_type = 'IP Камера'
                icon = 'fa-video'
            elif device_type == 'Неизвестное устройство':
                device_type = 'Роутер/Сервер'
                icon = 'fa-server'
        
        if 445 in open_ports or 3389 in open_ports:
            device_type = 'Компьютер Windows'
            icon = 'fa-desktop'
        elif 22 in open_ports and device_type == 'Неизвестное устройство':
            device_type = 'Linux/Unix Server'
            icon = 'fa-server'
        
        # Проверка по hostname
        if hostname:
            hostname_lower = hostname.lower()
            # Fritz!Box роутер - только точное совпадение hostname
            if hostname_lower == 'fritz.box' or hostname_lower == 'fritzbox':
                device_type = 'Роутер Fritz!Box'
                vendor = 'AVM'
                icon = 'fa-wifi'
            elif 'iphone' in hostname_lower or 'ipad' in hostname_lower:
                device_type = 'iPhone/iPad'
                vendor = 'Apple'
                icon = 'fa-mobile-alt'
            elif 'android' in hostname_lower:
                device_type = 'Android устройство'
                icon = 'fa-mobile-alt'
            elif 'smart-tv' in hostname_lower or 'samsung-tv' in hostname_lower:
                device_type = 'Smart TV'
                icon = 'fa-tv'
            elif 'router' in hostname_lower or 'gateway' in hostname_lower:
                device_type = 'Роутер'
                icon = 'fa-wifi'
            elif 'printer' in hostname_lower:
                device_type = 'Принтер'
                icon = 'fa-print'
            elif 'pc' in hostname_lower or 'desktop' in hostname_lower:
                device_type = 'Компьютер'
                icon = 'fa-desktop'
            elif 'laptop' in hostname_lower:
                device_type = 'Ноутбук'
                icon = 'fa-laptop'
        
        return {
            'device_type': device_type,
            'vendor': vendor,
            'icon': icon
        }
    
    def scan_device(self, ip: str) -> Optional[Dict]:
        """Сканирует одно устройство"""
        try:
            # Получаем MAC и hostname (не делаем ping - используем только ARP)
            mac = self.get_mac_address(ip)
            if not mac:
                return None  # Если нет MAC - устройство не в сети
                
            hostname = self.get_hostname(ip)
            
            # Быстро проверяем только важные порты
            open_ports = []
            important_ports = [80, 443, 22]  # Только 3 порта для скорости
            for port in important_ports:
                if self.check_port(ip, port):
                    open_ports.append(port)
            
            # Определяем тип устройства
            device_info = self.identify_device_type(mac, open_ports, hostname)
            
            return {
                'ip': ip,
                'mac': mac,
                'hostname': hostname or 'N/A',
                'device_type': device_info['device_type'],
                'vendor': device_info['vendor'],
                'icon': device_info['icon'],
                'open_ports': open_ports,
                'is_online': True
            }
        except Exception as e:
            logger.debug(f"Ошибка сканирования {ip}: {e}")
            return None
    
    def get_arp_table(self) -> List[str]:
        """Получает список IP из ARP таблицы (быстрее чем ping всех)"""
        active_ips = []
        try:
            system = platform.system().lower()
            
            if system == 'windows':
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=3)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    # Ищем строки с IP адресами
                    match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                    if match:
                        ip = match.group(1)
                        # Пропускаем широковещательные, multicast и служебные адреса
                        if (not ip.endswith('.255') and 
                            not ip.endswith('.0') and
                            not ip.startswith('224.') and  # Multicast
                            not ip.startswith('239.') and  # Multicast
                            not ip.startswith('255.') and
                            not ip.startswith('0.')):
                            active_ips.append(ip)
            else:
                # Пробуем современную команду ip neigh
                try:
                    result = subprocess.run(['ip', 'neigh', 'show'], capture_output=True, text=True, timeout=3)
                    lines = result.stdout.split('\n')
                    
                    for line in lines:
                        match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                        if match:
                            ip = match.group(1)
                            if (not ip.endswith('.255') and 
                                not ip.endswith('.0') and
                                not ip.startswith('224.') and
                                not ip.startswith('239.') and
                                not ip.startswith('255.') and
                                not ip.startswith('0.')):
                                active_ips.append(ip)
                except FileNotFoundError:
                    # Если ip команда не найдена, пробуем arp
                    try:
                        result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=3)
                        lines = result.stdout.split('\n')
                        
                        for line in lines:
                            match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                            if match:
                                ip = match.group(1)
                                if (not ip.endswith('.255') and 
                                    not ip.endswith('.0') and
                                    not ip.startswith('224.') and
                                    not ip.startswith('239.') and
                                    not ip.startswith('255.') and
                                    not ip.startswith('0.')):
                                    active_ips.append(ip)
                    except FileNotFoundError:
                        logger.warning("Ни 'ip', ни 'arp' команды недоступны - WiFi сканирование невозможно на этом сервере")
                        return []
                        return []
            
            return list(set(active_ips))  # Убираем дубликаты
        except Exception as e:
            logger.error(f"Ошибка чтения ARP таблицы: {e}")
            return []
    
    def quick_ping_sweep(self, network: str, progress_callback=None):
        """Быстро пингует всю подсеть чтобы заполнить ARP таблицу"""
        logger.info(f"Быстрый ping sweep сети {network}.0/24...")
        
        # Генерируем все IP адреса подсети (192.168.1.1 - 192.168.1.254)
        all_ips = [f"{network}.{i}" for i in range(1, 255)]
        
        # Многопоточный ping (очень быстро - ~2-3 секунды для всей сети)
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(self.ping_host, ip): ip for ip in all_ips}
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if progress_callback and completed % 25 == 0:  # Обновляем каждые 25 хостов
                    progress = 5 + int((completed / len(all_ips)) * 30)
                    progress_callback(progress)
        
        logger.info("Ping sweep завершён, ARP таблица обновлена")
    
    def scan_network(self, progress_callback=None) -> Dict:
        """Сканирует всю локальную сеть"""
        start_time = time.time()
        
        # Определяем локальную сеть
        local_ip, network = self.get_local_network()
        if not network:
            return {
                'success': False,
                'error': 'Не удалось определить локальную сеть'
            }
        
        logger.info(f"Сканирование сети {network}.0/24")
        
        # ШАГ 1: Быстро пингуем всю сеть чтобы заполнить ARP таблицу (2-3 сек)
        if progress_callback:
            progress_callback(5)
        
        self.quick_ping_sweep(network, progress_callback)
        
        # ШАГ 2: Читаем ARP таблицу (теперь там будут ВСЕ устройства!)
        logger.info("Читаю ARP таблицу...")
        if progress_callback:
            progress_callback(35)
            
        arp_ips = self.get_arp_table()
        logger.info(f"Найдено {len(arp_ips)} устройств в ARP таблице")
        
        if len(arp_ips) == 0:
            return {
                'success': False,
                'error': 'WiFi-сканирование недоступно на облачном сервере. Эта функция работает только на локальных компьютерах с доступом к WiFi сети.',
                'is_cloud_server': True
            }
        
        if progress_callback:
            progress_callback(40)
        
        devices = []
        total_hosts = len(arp_ips)
        scanned = 0
        
        logger.info(f"Сканирую {total_hosts} устройств...")
        
        # Многопоточное сканирование
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ip = {executor.submit(self.scan_device, ip): ip for ip in arp_ips}
            
            for future in as_completed(future_to_ip):
                scanned += 1
                if progress_callback:
                    progress = 40 + int((scanned / total_hosts) * 50)
                    progress_callback(progress)
                
                result = future.result()
                if result:
                    devices.append(result)
                    logger.info(f"Найдено устройство: {result['ip']} ({result['device_type']})")
        
        scan_duration = time.time() - start_time
        
        # Сортируем устройства по IP
        devices.sort(key=lambda x: tuple(map(int, x['ip'].split('.'))))
        
        if progress_callback:
            progress_callback(100)
        
        logger.info(f"Сканирование завершено за {scan_duration:.2f} сек. Найдено {len(devices)} устройств")
        
        return {
            'success': True,
            'local_ip': local_ip,
            'network': f"{network}.0/24",
            'total_devices': len(devices),
            'devices': devices,
            'scan_duration': round(scan_duration, 2)
        }
