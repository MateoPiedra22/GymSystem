import re
import uuid
import hashlib
import secrets
import string
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import phonenumbers
from phonenumbers import NumberParseException
from PIL import Image
import io
import base64
from pathlib import Path
import json
from .config import settings

# Validation utilities
class ValidationUtils:
    """Utility functions for data validation"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str, country_code: str = "MX") -> tuple[bool, Optional[str]]:
        """Validate and format phone number"""
        try:
            parsed_number = phonenumbers.parse(phone, country_code)
            if phonenumbers.is_valid_number(parsed_number):
                formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                return True, formatted
            return False, None
        except NumberParseException:
            return False, None
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, List[str]]:
        """Validate password strength and return issues"""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_mexican_curp(curp: str) -> bool:
        """Validate Mexican CURP format"""
        pattern = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}\d{2}$'
        return re.match(pattern, curp.upper()) is not None
    
    @staticmethod
    def validate_mexican_rfc(rfc: str) -> bool:
        """Validate Mexican RFC format"""
        # Person RFC: 4 letters + 6 digits + 3 alphanumeric
        person_pattern = r'^[A-Z]{4}\d{6}[A-Z0-9]{3}$'
        # Company RFC: 3 letters + 6 digits + 3 alphanumeric
        company_pattern = r'^[A-Z]{3}\d{6}[A-Z0-9]{3}$'
        
        rfc_upper = rfc.upper()
        return (re.match(person_pattern, rfc_upper) is not None or 
                re.match(company_pattern, rfc_upper) is not None)
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&=]*)$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace unsafe characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
        return filename

# Formatting utilities
class FormatUtils:
    """Utility functions for data formatting"""
    
    @staticmethod
    def format_currency(amount: float, currency: str = "MXN") -> str:
        """Format currency amount"""
        currency_symbols = {
            "MXN": "$",
            "USD": "$",
            "EUR": "€",
            "GBP": "£"
        }
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{amount:,.2f}"
    
    @staticmethod
    def format_phone_display(phone: str) -> str:
        """Format phone number for display"""
        try:
            parsed = phonenumbers.parse(phone, None)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        except:
            return phone
    
    @staticmethod
    def format_date_spanish(date_obj: Union[date, datetime]) -> str:
        """Format date in Spanish"""
        months = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        
        return f"{date_obj.day} de {months[date_obj.month]} de {date_obj.year}"
    
    @staticmethod
    def format_time_duration(minutes: int) -> str:
        """Format time duration in human readable format"""
        if minutes < 60:
            return f"{minutes} min"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours}h"
        
        return f"{hours}h {remaining_minutes}min"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

# Date and time utilities
class DateUtils:
    """Utility functions for date and time operations"""
    
    @staticmethod
    def get_age(birth_date: date) -> int:
        """Calculate age from birth date"""
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    @staticmethod
    def get_week_dates(week_offset: int = 0) -> tuple[date, date]:
        """Get start and end dates of a week"""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week
    
    @staticmethod
    def get_month_dates(month_offset: int = 0) -> tuple[date, date]:
        """Get start and end dates of a month"""
        today = date.today()
        if month_offset == 0:
            start_of_month = today.replace(day=1)
        else:
            # Calculate target month
            target_month = today.month + month_offset
            target_year = today.year
            
            while target_month > 12:
                target_month -= 12
                target_year += 1
            while target_month < 1:
                target_month += 12
                target_year -= 1
            
            start_of_month = date(target_year, target_month, 1)
        
        # Get last day of month
        if start_of_month.month == 12:
            end_of_month = date(start_of_month.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = date(start_of_month.year, start_of_month.month + 1, 1) - timedelta(days=1)
        
        return start_of_month, end_of_month
    
    @staticmethod
    def is_business_day(date_obj: date) -> bool:
        """Check if date is a business day (Monday-Friday)"""
        return date_obj.weekday() < 5
    
    @staticmethod
    def get_next_business_day(date_obj: date) -> date:
        """Get next business day"""
        next_day = date_obj + timedelta(days=1)
        while not DateUtils.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    @staticmethod
    def parse_time_string(time_str: str) -> Optional[datetime.time]:
        """Parse time string in various formats"""
        formats = ['%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
        
        return None

# File utilities
class FileUtils:
    """Utility functions for file operations"""
    
    @staticmethod
    def generate_unique_filename(original_filename: str, directory: Path) -> str:
        """Generate unique filename to avoid conflicts"""
        base_name = Path(original_filename).stem
        extension = Path(original_filename).suffix
        
        counter = 1
        new_filename = original_filename
        
        while (directory / new_filename).exists():
            new_filename = f"{base_name}_{counter}{extension}"
            counter += 1
        
        return new_filename
    
    @staticmethod
    def get_file_hash(file_path: Path) -> str:
        """Get MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def is_image_file(filename: str) -> bool:
        """Check if file is an image"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        return Path(filename).suffix.lower() in image_extensions
    
    @staticmethod
    def is_video_file(filename: str) -> bool:
        """Check if file is a video"""
        video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
        return Path(filename).suffix.lower() in video_extensions
    
    @staticmethod
    def resize_image(image_data: bytes, max_width: int = 800, max_height: int = 600, quality: int = 85) -> bytes:
        """Resize image while maintaining aspect ratio"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Calculate new dimensions
            width, height = image.size
            ratio = min(max_width / width, max_height / height)
            
            if ratio < 1:
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            image_format = image.format or 'JPEG'
            image.save(output, format=image_format, quality=quality, optimize=True)
            return output.getvalue()
        
        except Exception:
            return image_data  # Return original if resize fails

# Security utilities
class SecurityUtils:
    """Utility functions for security operations"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID4"""
        return str(uuid.uuid4())
    
    @staticmethod
    def hash_string(text: str, salt: str = "") -> str:
        """Hash string with optional salt"""
        return hashlib.sha256((text + salt).encode()).hexdigest()
    
    @staticmethod
    def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
        """Mask sensitive data showing only last few characters"""
        if len(data) <= visible_chars:
            return '*' * len(data)
        return '*' * (len(data) - visible_chars) + data[-visible_chars:]
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: List[str]) -> bool:
        """Check if redirect URL is safe"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Allow relative URLs
            if not parsed.netloc:
                return True
            
            # Check against allowed hosts
            return parsed.netloc in allowed_hosts
        except:
            return False

# Notification utilities
class NotificationUtils:
    """Utility functions for notifications"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, is_html: bool = False, attachments: List[Dict] = None) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True
        
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    @staticmethod
    def format_notification_template(template: str, variables: Dict[str, Any]) -> str:
        """Format notification template with variables"""
        try:
            return template.format(**variables)
        except KeyError as e:
            print(f"Missing template variable: {e}")
            return template
        except Exception as e:
            print(f"Template formatting error: {e}")
            return template
    
    @staticmethod
    def send_whatsapp_message(phone: str, message: str) -> bool:
        """Send WhatsApp message (placeholder for integration)"""
        # TODO: Implement WhatsApp Business API integration
        print(f"WhatsApp message to {phone}: {message}")
        return True
    
    @staticmethod
    def send_sms(phone: str, message: str) -> bool:
        """Send SMS message (placeholder for integration)"""
        # TODO: Implement SMS service integration (Twilio, etc.)
        print(f"SMS to {phone}: {message}")
        return True

# Data processing utilities
class DataUtils:
    """Utility functions for data processing"""
    
    @staticmethod
    def paginate_query(query, page: int, per_page: int):
        """Paginate SQLAlchemy query"""
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def export_to_csv(data: List[Dict], filename: str) -> str:
        """Export data to CSV format"""
        import csv
        import io
        
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    @staticmethod
    def import_from_csv(csv_content: str) -> List[Dict]:
        """Import data from CSV content"""
        import csv
        import io
        
        reader = csv.DictReader(io.StringIO(csv_content))
        return list(reader)
    
    @staticmethod
    def clean_dict(data: Dict, remove_none: bool = True, remove_empty: bool = False) -> Dict:
        """Clean dictionary by removing None/empty values"""
        cleaned = {}
        
        for key, value in data.items():
            if remove_none and value is None:
                continue
            if remove_empty and value == "":
                continue
            cleaned[key] = value
        
        return cleaned
    
    @staticmethod
    def merge_dicts(*dicts: Dict) -> Dict:
        """Merge multiple dictionaries"""
        result = {}
        for d in dicts:
            result.update(d)
        return result
    
    @staticmethod
    def flatten_dict(data: Dict, separator: str = '.') -> Dict:
        """Flatten nested dictionary"""
        def _flatten(obj, parent_key=''):
            items = []
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                if isinstance(value, dict):
                    items.extend(_flatten(value, new_key).items())
                else:
                    items.append((new_key, value))
            return dict(items)
        
        return _flatten(data)

# Business logic utilities
class BusinessUtils:
    """Utility functions for business logic"""
    
    @staticmethod
    def calculate_membership_expiry(start_date: date, duration_days: int) -> date:
        """Calculate membership expiry date"""
        return start_date + timedelta(days=duration_days)
    
    @staticmethod
    def calculate_prorated_amount(total_amount: float, days_used: int, total_days: int) -> float:
        """Calculate prorated amount"""
        if total_days <= 0:
            return 0.0
        return total_amount * (days_used / total_days)
    
    @staticmethod
    def calculate_late_fee(amount: float, days_late: int, daily_rate: float = 0.01) -> float:
        """Calculate late payment fee"""
        return amount * daily_rate * days_late
    
    @staticmethod
    def generate_membership_number() -> str:
        """Generate unique membership number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(secrets.choice(string.digits) for _ in range(4))
        return f"MEM{timestamp}{random_part}"
    
    @staticmethod
    def generate_invoice_number() -> str:
        """Generate unique invoice number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(secrets.choice(string.digits) for _ in range(4))
        return f"INV{timestamp}{random_part}"
    
    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        """Calculate Body Mass Index"""
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
    
    @staticmethod
    def get_bmi_category(bmi: float) -> str:
        """Get BMI category"""
        if bmi < 18.5:
            return "Bajo peso"
        elif bmi < 25:
            return "Peso normal"
        elif bmi < 30:
            return "Sobrepeso"
        else:
            return "Obesidad"

# Export all utility classes
__all__ = [
    'ValidationUtils',
    'FormatUtils', 
    'DateUtils',
    'FileUtils',
    'SecurityUtils',
    'NotificationUtils',
    'DataUtils',
    'BusinessUtils'
]