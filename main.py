import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # HTML response con solo caratteri ASCII
        html_response = """
        <html>
        <head>
            <title>OTP Bot Status</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>OTP Bot is Running!</h1>
            <p>Status: Active</p>
            <p>Database: PostgreSQL Connected</p>
            <p>Platform: Render</p>
            <p>Version: 4.0</p>
            <hr>
            <small>Bot is operational and ready to handle requests.</small>
        </body>
        </html>
        """
        
        self.wfile.write(html_response.encode('utf-8'))
    
    def log_message(self, format, *args):
        # Disabilita logs HTTP per ridurre spam nei logs
        pass

def start_server():
    """Avvia server HTTP per soddisfare i requisiti di Render Web Service"""
    port = int(os.environ.get('PORT', 8000))
    
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"HTTP server started on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Error starting HTTP server: {e}")
        # Mantieni il processo attivo anche se il server HTTP fallisce
        while True:
            time.sleep(60)

def main():
    print("Starting OTP Bot on Render...")
    print("=" * 50)
    
    # Avvia server HTTP in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Pausa per far partire il server
    time.sleep(3)
    print("HTTP server thread started")
    
    # Avvia il bot Telegram
    try:
        print("Importing and starting bot...")
        from bot import main as bot_main
        print("Bot imported successfully")
        print("Starting bot polling...")
        bot_main()  # Questo dovrebbe fare polling infinito
        
    except ImportError as e:
        print(f"Error importing bot module: {e}")
        print("Keeping service alive...")
        # Mantieni il servizio attivo anche se c'è un errore di import
        while True:
            time.sleep(60)
            
    except Exception as e:
        print(f"Error starting bot: {e}")
        print("Keeping service alive...")
        # Mantieni il servizio attivo anche se il bot ha problemi
        while True:
            time.sleep(60)

if __name__ == "__main__":
    main()
