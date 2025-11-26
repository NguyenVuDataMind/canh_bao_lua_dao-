import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import os

load_dotenv()

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", EMAIL)  # Email nhận thông báo SOS

def send_otp_email(to_email, otp_code):
    msg = MIMEText(f"Your OTP code is: {otp_code}")
    msg["Subject"] = "OTP Verification"
    msg["From"] = EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)


def send_sos_email(sos_request, test_mode=False):
    """Gửi email thông báo SOS cho admin"""
    
    created_local = sos_request.created.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    
    # Nếu test mode, chỉ log ra console
    if test_mode or not EMAIL or not APP_PASSWORD:
        print("=" * 60)
        print("🚨 SOS EMAIL (TEST MODE - Email không được gửi)")
        print(f"To: {ADMIN_EMAIL}")
        print(f"Subject: 🚨 SOS CẦU CỨU KHẨN CẤP")
        print(f"Thời gian: {created_local.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Vị trí: {sos_request.latitude}, {sos_request.longitude}")
        print(f"Độ chính xác: {sos_request.accuracy} mét")
        print(f"Link Google Maps: https://www.google.com/maps?q={sos_request.latitude},{sos_request.longitude}")
        print(f"IP: {sos_request.ip_address}")
        print(f"User Agent: {sos_request.user_agent}")
        print(f"ID Request: {sos_request.id}")
        print("=" * 60)
        return
    
    # Tạo link Google Maps
    maps_url = f"https://www.google.com/maps?q={sos_request.latitude},{sos_request.longitude}"
    
    # Nội dung email
    subject = "🚨 SOS CẦU CỨU KHẨN CẤP"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #ff0000; border-radius: 10px;">
            <h2 style="color: #ff0000; text-align: center;">🚨 CÓ YÊU CẦU SOS CẦU CỨU KHẨN CẤP</h2>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>⏰ Thời gian:</strong> {created_local.strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            
            <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">📍 Vị trí:</h3>
                <ul style="list-style: none; padding: 0;">
                    <li><strong>Latitude (Vĩ độ):</strong> {sos_request.latitude}</li>
                    <li><strong>Longitude (Kinh độ):</strong> {sos_request.longitude}</li>
                    <li><strong>Độ chính xác:</strong> {sos_request.accuracy} mét</li>
                </ul>
                
                <p style="margin-top: 15px;">
                    <a href="{maps_url}" 
                       target="_blank" 
                       style="background: #00c16a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        📍 Xem vị trí trên Google Maps
                    </a>
                </p>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">ℹ️ Thông tin khác:</h3>
                <ul style="list-style: none; padding: 0;">
                    <li><strong>IP Address:</strong> {sos_request.ip_address or 'N/A'}</li>
                    <li><strong>User Agent:</strong> {sos_request.user_agent or 'N/A'}</li>
                    <li><strong>ID Request:</strong> {sos_request.id}</li>
                </ul>
            </div>
            
            <div style="background: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
                <p style="color: #d32f2f; font-weight: bold; font-size: 18px; margin: 0;">
                    ⚠️ Vui lòng kiểm tra và phản hồi ngay!
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = ADMIN_EMAIL
    
    msg.attach(MIMEText(body, "html"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print(f"✅ SOS email đã được gửi đến {ADMIN_EMAIL}")
    except Exception as e:
        print(f"❌ Lỗi gửi SOS email: {e}")
        # Không raise exception để không làm fail request

