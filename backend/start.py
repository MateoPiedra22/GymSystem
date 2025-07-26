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
    force_uvicorn = os.environ.get('USE_UVICORN', '').lower() in ('1', 'true', 'yes')
    is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
    
    print(f"Environment: {environment}")
    print(f"Platform: {platform.system()}")
    print(f"Railway deployment: {is_railway}")
    print(f"Force uvicorn: {force_uvicorn}")
    
    if environment == 'development':
        print(f"Starting development server on port {port}...")
        # Use uvicorn with reload for development
        command = [
            'python', '-m', 'uvicorn', 
            'app.main:app',
            '--host', '0.0.0.0',
            '--port', str(port),
            '--reload'
        ]
    elif is_windows or force_uvicorn or is_railway:
        reason = "Windows" if is_windows else "Railway" if is_railway else "forced by USE_UVICORN"
        print(f"Starting production server on port {port} ({reason} - using uvicorn)...")
        # Use uvicorn for Windows, Railway, or when forced
        command = [
            'python', '-m', 'uvicorn', 
            'app.main:app',
            '--host', '0.0.0.0',
            '--port', str(port),
            '--workers', '1',
            '--access-log',
            '--log-level', 'info'
        ]
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
    
    # Test import before starting server
    try:
        print("Testing application import...")
        from app.main import app
        print("Application import successful")
    except Exception as e:
        print(f"Error importing application: {e}")
        print("Attempting to start anyway...")
    
    try:
        # Run the server
        result = subprocess.run(command, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        print(f"Exit code: {e.returncode}")
        
        # Try fallback command with uvicorn if gunicorn fails
        if 'gunicorn' in command[1]:
            print("Gunicorn failed, trying uvicorn fallback...")
            fallback_command = [
                'python', '-m', 'uvicorn', 
                'app.main:app',
                '--host', '0.0.0.0',
                '--port', str(port),
                '--workers', '1'
            ]
            print(f"Fallback command: {' '.join(fallback_command)}")
            try:
                result = subprocess.run(fallback_command, check=True)
                return result.returncode
            except subprocess.CalledProcessError as fallback_e:
                print(f"Fallback also failed: {fallback_e}")
                return fallback_e.returncode
        
        return e.returncode
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())