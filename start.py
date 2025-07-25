#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    # Get PORT from environment variable, default to 8000
    port = os.environ.get('PORT', '8000')
    
    # Validate that port is a valid integer
    try:
        int(port)
    except ValueError:
        print(f"Error: PORT '{port}' is not a valid integer. Using default port 8000.")
        port = '8000'
    
    # Build the uvicorn command
    cmd = [
        'python', '-m', 'uvicorn',
        'backend.app.main:app',
        '--host', '0.0.0.0',
        '--port', port
    ]
    
    print(f"Starting server on port {port}...")
    print(f"Command: {' '.join(cmd)}")
    
    # Execute uvicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)

if __name__ == '__main__':
    main