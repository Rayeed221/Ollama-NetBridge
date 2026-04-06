import os
import subprocess
import sys
import ctypes
import socket
import time

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_local_ip():
    """Retrieve the local IP address of this Windows PC."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def run_ollama_server():
    # Relaunch script with Admin rights if it doesn't have them
    if not is_admin():
        print("Requesting administrator privileges to manage the firewall...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    print("--- Temporary Ollama Network Server ---")

    # 1. Open Firewall Temporarily
    print("[*] Adding temporary firewall rule for port 11434...")
    subprocess.run(
        'netsh advfirewall firewall add rule name="Ollama Temporary" dir=in action=allow protocol=TCP localport=11434',
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # 2. Kill existing Ollama background tasks to free up the port
    print("[*] Stopping background Ollama processes...")
    subprocess.run("taskkill /F /IM ollama.exe /T", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("taskkill /F /IM \"ollama app.exe\" /T", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2) # Give Windows a moment to release the port

    # 3. Set temporary environment variables (only applies to this Python script's children)
    os.environ["OLLAMA_HOST"] = "0.0.0.0"
    os.environ["OLLAMA_ORIGINS"] = "*"

    local_ip = get_local_ip()
    print(f"\n[+] Ollama is starting!")
    print(f"[+] Connect from your other devices using this IP:")
    print(f"    http://{local_ip}:11434")
    print("\n>>> Press Ctrl+C in this window to stop the server and revert to private mode. <<<\n")

    # 4. Start Ollama Server
    process = None
    try:
        # Ollama will inherit the OLLAMA_HOST from the os.environ we just set
        process = subprocess.Popen(["ollama", "serve"])
        process.wait()
    except KeyboardInterrupt:
        print("\n[*] Shutting down temporary server...")
    finally:
        if process:
            process.terminate()
            
        # 5. Clean up firewall rule
        print("[*] Removing temporary firewall rule...")
        subprocess.run('netsh advfirewall firewall delete rule name="Ollama Temporary"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Server stopped. Your PC is private again.")

if __name__ == "__main__":
    run_ollama_server()
