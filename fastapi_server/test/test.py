from server.service.auth_utils import pwd_context
code = "123456"

def get_password_hash(password: str) -> str:
    """生成密码的bcrypt哈希"""
    return pwd_context.hash(password)

print(get_password_hash(code))
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码与哈希是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)
print(verify_password(code, get_password_hash(code)))
