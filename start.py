#!/usr/bin/env python3
import os
import subprocess
import sys
import platform

def main():
    # Get port from environment variable, default to 8000
    port = os.environ.get('PORT', '8000')
    
    # Validate port is a number
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            raise ValueError("Port must be between 1 and 65535")
    except ValueError as e:
        print(f"Invalid port: {e}")
        sys.exit(1)
    
    # Determine environment
    environment = os.environ.get('ENVIRONMENT', 'production').lower()
    is_windows = platform.system() == 'Windows'
    
    if environment == 'development' or is_windows:
        print(f"Starting development server on port {port}...")
        # Use uvicorn with reload for development or Windows
        command = [
            'python', '-m', 'uvicorn', 
            'app.main:app',
            '--host', '0.0.0.0',
            '--port', str(port)
        ]
        if environment == 'development':
            command.append('--reload')
    else:
        print(f"Starting production server on port {port}...")
        # Set PORT environment variable for gunicorn
        os.environ['PORT'] = str(port)
        # Use gunicorn for production on Unix systems
        command = [
            'python', '-m', 'gunicorn',
            'app.main:app',
            '-c', 'gunicorn.conf.py'
        ]
    
    print(f"Command: {' '.join(command)}")
    
    try:
        # Run the server
        result = subprocess.run(command, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        return e.returncode
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())