import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

# Force output flushing
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_content = """<!DOCTYPE html>
<html>
<head><title>OTP Bot Status</title></head>
<body>
    <h1>OTP Bot is Running</h1>
    <p>Status: Active</p>
    <p>Database: PostgreSQL</p>
    <p>Platform: Render</p>
</body>
</html>"""
        
        self.wfile.write(html_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def start_http_server():
    port = int(os.environ.get('PORT', 8000))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"[HTTP] Server started on port {port}", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"[ERROR] HTTP server error: {e}", flush=True)
        while True:
            time.sleep(60)

def main():
    print("=" * 60, flush=True)
    print("🚀 STARTING OTP BOT ON RENDER", flush=True)
    print("=" * 60, flush=True)
    
    # Debug info
    print(f"[DEBUG] Python version: {sys.version}", flush=True)
    print(f"[DEBUG] Working directory: {os.getcwd()}", flush=True)
    print(f"[DEBUG] Files in directory:", flush=True)
    
    try:
        for f in os.listdir('.'):
            if f.endswith('.py'):
                print(f"  - {f}", flush=True)
    except Exception as e:
        print(f"[ERROR] Cannot list files: {e}", flush=True)
    
    # Check environment variables
    required_vars = ['DATABASE_URL', 'BOT_TOKEN', 'SMS_ACTIVATE_API_KEY', 'ADMIN_CHAT_IDS', 'COUNTRY_CODE']
    print("[ENV] Checking environment variables:", flush=True)
    
    for var in required_vars:
        if var in os.environ:
            if var == 'DATABASE_URL':
                # Show only part of database URL for security
                val = os.environ[var][:30] + "..." if len(os.environ[var]) > 30 else os.environ[var]
                print(f"  ✅ {var}: {val}", flush=True)
            elif var == 'BOT_TOKEN':
                # Show only part of bot token for security
                val = os.environ[var][:10] + "..." if len(os.environ[var]) > 10 else os.environ[var]
                print(f"  ✅ {var}: {val}", flush=True)
            else:
                print(f"  ✅ {var}: {os.environ[var]}", flush=True)
        else:
            print(f"  ❌ {var}: MISSING", flush=True)
    
    # Start HTTP server
    print("[STEP 1] Starting HTTP server...", flush=True)
    server_thread = threading.Thread(target=start_http_server, daemon=True)
    server_thread.start()
    time.sleep(3)
    print("[STEP 1] ✅ HTTP server thread started", flush=True)
    
    # Start bot
    print("[STEP 2] Starting Telegram bot...", flush=True)
    
    try:
        print("[STEP 2] Importing bot module...", flush=True)
        import bot
        print("[STEP 2] ✅ Bot module imported", flush=True)
        
        print("[STEP 2] Calling bot.main()...", flush=True)
        bot.main()
        
    except ImportError as e:
        print(f"[ERROR] Failed to import bot: {e}", flush=True)
        
    except Exception as e:
        print(f"[ERROR] Bot startup failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    print("[INFO] Keeping service alive...", flush=True)
    while True:
        print("[HEARTBEAT] Service running...", flush=True)
        time.sleep(300)  # Log every 5 minutes

if __name__ == "__main__":
    main()
