"""
邮件发送工具模块
包含：SMTP连接池、验证码发送、验证码验证
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
from dotenv import load_dotenv
import random
import string
from datetime import timedelta
import json
import threading
import time
from typing import Optional

# 尝试导入redis，如果没有则使用内存存储
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

load_dotenv()

# 配置信息
MAX_RETRIES = 3  # 最大重试次数
INITIAL_BACKOFF = 1  # 初始退避时间(秒)
MAX_CONNECTIONS = 5  # 连接池最大连接数
CODE_EXPIRE_MINUTES = 5  # 验证码有效期(分钟)
MAX_ATTEMPTS = 3  # 最大验证尝试次数

# 邮件配置
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM")
FAKE_EMAIL = os.getenv("FAKE_EMAIL", "0") == "1"

# 验证码存储（如果没有Redis则使用内存字典）
verification_codes = {}
codes_lock = threading.Lock()

# 尝试连接Redis
redis_client = None
if REDIS_AVAILABLE:
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
            socket_connect_timeout=2
        )
        redis_client.ping()
        logging.info("Redis连接成功")
    except Exception as e:
        logging.info(f"Redis连接失败，使用内存存储: {e}")
        redis_client = None


# SMTP连接池
class SMTPPool:
    def __init__(self, host, port, username, password, max_connections=5):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()

    def get_connection(self):
        with self.lock:
            # 尝试从池中获取连接
            while self.connections:
                conn = self.connections.pop()
                try:
                    # 检查连接是否仍然有效
                    status = conn.noop()[0]
                    if status == 250:
                        return conn
                    else:
                        try:
                            conn.quit()
                        except:
                            pass
                except:
                    try:
                        conn.quit()
                    except:
                        pass

            # 没有可用连接，创建新连接
            return self._create_new_connection()

    def release_connection(self, conn):
        with self.lock:
            if len(self.connections) < self.max_connections:
                self.connections.append(conn)
            else:
                try:
                    conn.quit()
                except:
                    pass

    def _create_new_connection(self):
        try:
            server = smtplib.SMTP(self.host, self.port, timeout=10)
            server.starttls()
            server.login(self.username, self.password)
            return server
        except Exception as e:
            logging.info(f"创建SMTP连接失败: {e}")
            raise


# 初始化连接池
smtp_pool = None
if EMAIL_USER and EMAIL_PASSWORD:
    try:
        smtp_pool = SMTPPool(
            host=EMAIL_HOST,
            port=EMAIL_PORT,
            username=EMAIL_USER,
            password=EMAIL_PASSWORD,
            max_connections=MAX_CONNECTIONS
        )
        logging.info("SMTP连接池初始化成功")
    except Exception as e:
        logging.info(f"SMTP连接池初始化失败: {e}")


def generate_verification_code(length=6) -> str:
    """生成随机数字验证码"""
    return ''.join(random.choices(string.digits, k=length))


def _store_code_in_redis(email: str, code: str) -> bool:
    """将验证码存储到Redis"""
    if not redis_client:
        return False
    try:
        redis_key = f"verification_code:{email}"
        redis_client.setex(
            redis_key,
            timedelta(minutes=CODE_EXPIRE_MINUTES),
            json.dumps({
                "code": code,
                "attempts": 0
            })
        )
        return True
    except Exception as e:
        logging.info(f"Redis存储验证码失败: {e}")
        return False


def _store_code_in_memory(email: str, code: str):
    """将验证码存储到内存"""
    with codes_lock:
        verification_codes[email] = {
            "code": code,
            "attempts": 0,
            "expire_at": time.time() + CODE_EXPIRE_MINUTES * 60
        }


def _get_code_from_redis(email: str) -> Optional[dict]:
    """从Redis获取验证码"""
    if not redis_client:
        return None
    try:
        redis_key = f"verification_code:{email}"
        data = redis_client.get(redis_key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logging.info(f"Redis获取验证码失败: {e}")
        return None


def _get_code_from_memory(email: str) -> Optional[dict]:
    """从内存获取验证码"""
    with codes_lock:
        data = verification_codes.get(email)
        if data:
            # 检查是否过期
            if time.time() > data["expire_at"]:
                del verification_codes[email]
                return None
            return {"code": data["code"], "attempts": data["attempts"]}
        return None


def _update_code_attempts_in_redis(email: str, code_data: dict) -> bool:
    """更新Redis中的验证码尝试次数"""
    if not redis_client:
        return False
    try:
        redis_key = f"verification_code:{email}"
        code_data["attempts"] += 1
        # 保留剩余过期时间
        ttl = redis_client.ttl(redis_key)
        if ttl > 0:
            redis_client.setex(redis_key, ttl, json.dumps(code_data))
        return True
    except Exception as e:
        logging.info(f"Redis更新验证码失败: {e}")
        return False


def _update_code_attempts_in_memory(email: str):
    """更新内存中的验证码尝试次数"""
    with codes_lock:
        if email in verification_codes:
            verification_codes[email]["attempts"] += 1


def _delete_code_in_redis(email: str) -> bool:
    """删除Redis中的验证码"""
    if not redis_client:
        return False
    try:
        redis_key = f"verification_code:{email}"
        redis_client.delete(redis_key)
        return True
    except Exception as e:
        logging.info(f"Redis删除验证码失败: {e}")
        return False


def _delete_code_in_memory(email: str):
    """删除内存中的验证码"""
    with codes_lock:
        verification_codes.pop(email, None)


def send_verification_email(email: str) -> bool:
    """发送验证码到指定邮箱，带有重试机制"""
    # 生成验证码
    code = generate_verification_code()

    # 压测模式：验证码固定为000000
    if FAKE_EMAIL:
        logging.info(f"[压测模式] 验证码为000000，不发送邮件到 {email}")
        code = "000000"
        # 存储到Redis或内存
        if redis_client:
            _store_code_in_redis(email, code)
        else:
            _store_code_in_memory(email, code)
        return True

    # 存储验证码
    if redis_client:
        if not _store_code_in_redis(email, code):
            _store_code_in_memory(email, code)
    else:
        _store_code_in_memory(email, code)

    # 如果没有配置SMTP，直接返回成功（仅用于测试）
    if not smtp_pool:
        logging.info(f"[测试模式] SMTP未配置，验证码 {code} 已存储但未发送邮件到 {email}")
        return True

    # 邮件内容
    subject = "您的验证码"
    content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 500px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1a237e;">欢迎使用安全漏洞分析平台</h2>
            <p>您好！</p>
            <p>感谢您注册我们的服务。您的验证码是：</p>
            <div style="background: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                <span style="font-size: 32px; font-weight: bold; color: #1a237e; letter-spacing: 8px;">{code}</span>
            </div>
            <p>请在 <strong>{CODE_EXPIRE_MINUTES} 分钟内</strong>使用此验证码完成操作。</p>
            <p style="color: #999; font-size: 12px;">如果这不是您本人的操作，请忽略此邮件。</p>
        </div>
    </body>
    </html>
    """

    # 创建邮件对象
    message = MIMEText(content, "html", "utf-8")
    message["From"] = Header(f"'=?UTF-8?5byA5rqQ6L2v5Lu25ryP5rSe6aKE6K2m5bmz5Y+w=?=' <{EMAIL_FROM}>")
    message["To"] = Header(email, "utf-8")
    message["Subject"] = Header(subject, "utf-8")

    # 指数退避重试机制
    server = None
    for attempt in range(MAX_RETRIES):
        try:
            server = smtp_pool.get_connection()
            server.sendmail(EMAIL_FROM, email, message.as_string())
            smtp_pool.release_connection(server)
            logging.info(f"邮件发送成功 to {email}")
            return True
        except smtplib.SMTPServerDisconnected as e:
            logging.info(f"SMTP服务器断开连接 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
            if server:
                try:
                    server.quit()
                except:
                    pass
                server = None
        except Exception as e:
            logging.info(f"邮件发送失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
            if server:
                try:
                    server.quit()
                except:
                    pass
                server = None

        # 指数退避
        if attempt < MAX_RETRIES - 1:
            backoff_time = INITIAL_BACKOFF * (2 ** attempt)
            logging.info(f"等待 {backoff_time} 秒后重试")
            time.sleep(backoff_time)

    logging.info(f"邮件发送失败，已达到最大重试次数: {email}")
    return False


def verify_email_code(email: str, code: str) -> bool:
    """验证邮箱验证码"""
    # 尝试从Redis获取
    code_data = None
    if redis_client:
        code_data = _get_code_from_redis(email)

    # 如果Redis没有，尝试从内存获取
    if code_data is None:
        code_data = _get_code_from_memory(email)

    # 验证码不存在或已过期
    if not code_data:
        return False

    # 检查尝试次数
    if code_data.get("attempts", 0) >= MAX_ATTEMPTS:
        # 超过最大尝试次数，删除验证码
        if redis_client:
            _delete_code_in_redis(email)
        _delete_code_in_memory(email)
        return False

    # 更新尝试次数
    if redis_client:
        if not _update_code_attempts_in_redis(email, code_data):
            _update_code_attempts_in_memory(email)
    else:
        _update_code_attempts_in_memory(email)

    # 验证码匹配
    if code_data.get("code") == code:
        # 验证成功，删除验证码
        if redis_client:
            _delete_code_in_redis(email)
        _delete_code_in_memory(email)
        return True

    return False
