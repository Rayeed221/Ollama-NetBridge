import os
import sys
import socket
import platform
import subprocess
import concurrent.futures
import urllib.request

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def check_ip(ip):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        result = sock.connect_ex((ip, 11434))
        sock.close()
        
        if result == 0:
            req = urllib.request.Request(f"http://{ip}:11434/api/tags")
            with urllib.request.urlopen(req, timeout=0.5) as response:
                if response.getcode() == 200:
                    return ip
    except Exception:
        pass
    return None

def auto_discover():
    local_ip = get_local_ip()
    if local_ip == '127.0.0.1':
        return None

    base_ip = '.'.join(local_ip.split('.')[:-1])
    print(f"{Colors.CYAN}[*] Scanning network ({base_ip}.X) for host PC...{Colors.ENDC}")
    
    ips_to_check = [f"{base_ip}.{i}" for i in range(1, 255)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_ip, ip) for ip in ips_to_check]
        for future in concurrent.futures.as_completed(futures):
            found_ip = future.result()
            if found_ip:
                return found_ip
    return None

def main():
    if os.name == 'nt':
        os.system('color')

    print(f"{Colors.BOLD}--- OLLAMA AUTO-CONNECT SHELL ---{Colors.ENDC}")
    
    server_ip = auto_discover()
    
    if not server_ip:
        print(f"{Colors.FAIL}[-] Could not auto-discover Ollama PC.{Colors.ENDC}")
        server_ip = input(f"Enter host PC IP manually: ").strip()
        if not server_ip:
            sys.exit(1)

    host_url = f"http://{server_ip}:11434"
    print(f"{Colors.GREEN}[+] Connected to Ollama at {host_url}{Colors.ENDC}")
    
    # 1. Set the environment variable for the child process
    os.environ["OLLAMA_HOST"] = host_url

    print(f"\n{Colors.WARNING}>>> Spawning an Ollama-ready terminal session! <<<{Colors.ENDC}")
    print(f"You can now run native commands like: {Colors.BOLD}ollama run llama3{Colors.ENDC}")
    print(f"Type {Colors.BOLD}'exit'{Colors.ENDC} to leave this session.\n")

    # 2. Launch the interactive shell based on the OS
    system_os = platform.system()
    try:
        if system_os == "Windows":
            # Opens CMD on Windows
            subprocess.run(["cmd.exe"])
        else:
            # Opens Bash, Zsh, or whatever default shell is on Linux/Mac/Termux
            shell = os.environ.get("SHELL", "/bin/bash")
            subprocess.run([shell])
    except Exception as e:
        print(f"{Colors.FAIL}Error launching shell: {e}{Colors.ENDC}")

    print(f"\n{Colors.CYAN}[*] Ollama session closed. Returning to normal terminal.{Colors.ENDC}")

if __name__ == "__main__":
    main()
