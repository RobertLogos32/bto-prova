import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

# Force output flushing per Render
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
    """Server HTTP per Render Web Service"""
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
    
    # Check environment variables
    required_vars = ['DATABASE_URL', 'BOT_TOKEN', 'SMS_ACTIVATE_API_KEY', 'ADMIN_CHAT_IDS', 'COUNTRY_CODE']
    print("[ENV] Checking environment variables:", flush=True)
    
    for var in required_vars:
        if var in os.environ:
            if var in ['DATABASE_URL', 'BOT_TOKEN']:
                val = os.environ[var][:15] + "..." if len(os.environ[var]) > 15 else os.environ[var]
                print(f"  ✅ {var}: {val}", flush=True)
            else:
                print(f"  ✅ {var}: {os.environ[var]}", flush=True)
        else:
            print(f"  ❌ {var}: MISSING", flush=True)
    
    # Start HTTP server per Render
    print("[STEP 1] Starting HTTP server for Render...", flush=True)
    server_thread = threading.Thread(target=start_http_server, daemon=True)
    server_thread.start()
    time.sleep(3)
    print("[STEP 1] ✅ HTTP server started", flush=True)
    
    # Initialize database and start bot (LA TUA LOGICA ORIGINALE)
    try:
        print("[STEP 2] Initializing database...", flush=True)
        from init_db import initialize_database
        initialize_database()
        print("[STEP 2] ✅ Database initialized", flush=True)
        
        print("[STEP 3] Starting OTP Bot...", flush=True)
        from bot import OTPBot
        
        bot = OTPBot()
        print("[STEP 3] ✅ OTPBot instance created", flush=True)
        
        print("[STEP 3] Starting bot polling...", flush=True)
        print("🤖 Bot is now listening for messages...", flush=True)
        
        # Avvia il polling (questo è bloccante)
        bot.start_polling()
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}", flush=True)
        print("[ERROR] Available files:", flush=True)
        for f in os.listdir('.'):
            if f.endswith('.py'):
                print(f"  - {f}", flush=True)
                
    except Exception as e:
        print(f"[ERROR] Bot startup failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    # Mantieni servizio attivo se il bot si ferma
    print("[INFO] Keeping service alive...", flush=True)
    while True:
        print("[HEARTBEAT] Service running...", flush=True)
        time.sleep(300)  # Log ogni 5 minuti

if __name__ == "__main__":
    main()
