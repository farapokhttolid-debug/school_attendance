from datetime import datetime
try:
    import jdatetime
    JALALI_AVAILABLE = True
except ImportError:
    JALALI_AVAILABLE = False
    print("⚠️ jdatetime not available, using fallback")
def to_jalali(gregorian_date):
    """تبدیل تاریخ میلادی به شمسی"""
    if not JALALI_AVAILABLE:
        if isinstance(gregorian_date, str):
            return gregorian_date
        return gregorian_date.strftime('%Y-%m-%d') if hasattr(gregorian_date, 'strftime') else str(gregorian_date)
    try:
        if isinstance(gregorian_date, str):
            gregorian_date = datetime.strptime(gregorian_date, '%Y-%m-%d')
        jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
        return jalali_date.strftime('%Y/%m/%d')
    except Exception as e:
        print(f"⚠️ Jalali conversion error: {e}")
        return gregorian_date.strftime('%Y-%m-%d') if hasattr(gregorian_date, 'strftime') else str(gregorian_date)
def getTodayJalali():
    """دریافت تاریخ امروز شمسی"""
    if not JALALI_AVAILABLE:
        return datetime.now().strftime('%Y-%m-%d')
    try:
        return jdatetime.date.today().strftime('%Y/%m/%d')
    except Exception as e:
        print(f"⚠️ Today jalali error: {e}")
        return datetime.now().strftime('%Y-%m-%d')
def format_time(time_str):
    """فرمت‌دهی زمان"""
    if not time_str:
        return ''
    try:
        if len(time_str) == 5:  # HH:MM
            return time_str
        elif ':' in time_str:
            return time_str.split(':')[0] + ':' + time_str.split(':')[1]
        else:
            return time_str
    except:
        return time_str
def validate_personnel_code(code):
    """اعتبارسنجی کد پرسنلی"""
    if not code:
        return False
    return str(code).isdigit() and len(str(code)) == 4

def getTomorrowJalali():
    """برگرداندن تاریخ فردا به صورت شمسی"""
    from datetime import datetime, timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    return to_jalali(tomorrow)