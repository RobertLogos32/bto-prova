import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'''
        <html><body>
        <h1>🤖 OTP Bot is Running!</h1>
        <p>Status: ✅ Active</p>
        <p>Database: 🐘 PostgreSQL</p>
        <p>Platform: 🚀 Render</p>
        </body></html>
        ''')
    
    def log_message(self, format, *args):
        pass  # Disabilita logs HTTP

def start_server():
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🌐 HTTP server started on port {port}")
    server.serve_forever()

def main():
    print("🚀 Starting OTP Bot...")
    
    # Avvia server HTTP in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Avvia il bot
    try:
        from bot import main as bot_main
        print("✅ Bot started successfully!")
        bot_main()  # Questo farà polling infinito
    except Exception as e:
        print(f"❌ Bot error: {e}")
        # Mantieni il server attivo anche se il bot ha problemi
        while True:
            time.sleep(60)

if __name__ == "__main__":
    main()
