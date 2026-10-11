import os
from dotenv import load_dotenv

load_dotenv()
def require_env_var(var_name:str) -> str:
    env_var = os.getenv(var_name)
    if env_var is None:
        raise RuntimeError(f"{var_name} is not configured")
    
    return env_var

DATABASE_URL = require_env_var('DATABASE_URL')
REDIS_URL = require_env_var('REDIS_URL')
SECRET_KEY = require_env_var('SECRET_KEY')
JWT_ALGORITHM = require_env_var('JWT_ALGORITHM')
JWT_EXPIRE_MINUTES = int(require_env_var('JWT_EXPIRE_MINUTES'))