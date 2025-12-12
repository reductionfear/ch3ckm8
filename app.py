#!/usr/bin/env python3

import os
import sys
import subprocess

REPO_URL = "https://github.com/isnotsin/checkmate.git"
CHECKER_SCRIPT = "checker.py"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

def printBanner():
    banner = f"""
{Colors.CYAN}░▄▀▀░█▄█▒██▀░▄▀▀░█▄▀░█▄▒▄█▒▄▀▄░▀█▀▒██▀
░▀▄▄▒█▒█░█▄▄░▀▄▄░█▒█░█▒▀▒█░█▀█░▒█▒░█▄▄
"""
    print(banner)

def checkGit():
    try:
        subprocess.run(['git', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

def installGit():
    print(f"{Colors.CYAN}[*] Installing git...{Colors.RESET}")
    try:
        subprocess.check_call(['pkg', 'install', 'git', '-y'])
        print(f"{Colors.GREEN}[✓] Git installed{Colors.RESET}")
        return True
    except:
        print(f"{Colors.RED}[✗] Failed to install git{Colors.RESET}")
        return False

def cloneRepo():
    print(f"{Colors.CYAN}[*] Downloading checker...{Colors.RESET}")
    try:
        if os.path.exists('checkmate'):
            subprocess.check_call(['rm', '-rf', 'checkmate'])
        
        subprocess.check_call(['git', 'clone', REPO_URL])
        print(f"{Colors.GREEN}[✓] Downloaded successfully{Colors.RESET}")
        return True
    except:
        print(f"{Colors.RED}[✗] Failed to download{Colors.RESET}")
        return False

def updateRepo():
    print(f"{Colors.CYAN}[*] Updating checker...{Colors.RESET}")
    try:
        os.chdir('checkmate')
        subprocess.check_call(['git', 'pull'])
        os.chdir('..')
        print(f"{Colors.GREEN}[✓] Updated successfully{Colors.RESET}")
        return True
    except:
        print(f"{Colors.RED}[✗] Failed to update{Colors.RESET}")
        return False

def runChecker():
    if not os.path.exists('checkmate'):
        print(f"{Colors.RED}[✗] Checker not installed{Colors.RESET}")
        return
    
    os.chdir('checkmate')
    subprocess.call([sys.executable, CHECKER_SCRIPT])
    os.chdir('..')

def main():
    printBanner()
    
    if not checkGit():
        print(f"{Colors.CYAN}[!] Git not found{Colors.RESET}")
        if not installGit():
            return
    
    print(f"\n{Colors.WHITE}[1]{Colors.RESET} Install Checker")
    print(f"{Colors.WHITE}[2]{Colors.RESET} Update Checker")
    print(f"{Colors.WHITE}[3]{Colors.RESET} Run Checker")
    print(f"{Colors.WHITE}[4]{Colors.RESET} Exit")
    print()
    
    choice = input(f"{Colors.WHITE}Choose: {Colors.RESET}").strip()
    
    if choice == '1':
        if cloneRepo():
            print(f"\n{Colors.GREEN}[✓] Installation complete!{Colors.RESET}")
            print(f"{Colors.CYAN}[*] Run with: python app.py -> [3] Run Checker{Colors.RESET}")
    elif choice == '2':
        if os.path.exists('checkmate'):
            updateRepo()
        else:
            print(f"{Colors.RED}[✗] Checker not installed. Install first.{Colors.RESET}")
    elif choice == '3':
        runChecker()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}Goodbye!{Colors.RESET}")