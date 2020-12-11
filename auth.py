from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, APIRouter, BackgroundTasks, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_mail import ConnectionConfig, MessageSchema, FastMail
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import *
from pydantic import EmailStr
from random import randint
from MONGO import users_collection
from pymongo.errors import DuplicateKeyError

SECRET_KEY = "40974ed31cfeaf1f9ed2550c96edef3125a5a78d36e6b3b294665437f7b6ad14"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    user_dict = users_collection.find_one({"username": username})
    return UserInDB(**user_dict)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User, tags=["users"])
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return current_user


template = """
    <html> 
    <body>
    <h3>this mail is from kako app</h3>
    <p>Complete your registration</p>
    <p><b>your activation code is: {}</b></p>
    <p>enter this code in kako app.</p> 
    </body> 
    </html>
    """

conf = ConnectionConfig(
    MAIL_USERNAME=EmailStr("kakoapp.mail@gmail.com"),
    MAIL_PASSWORD="###############",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False
)


async def send_activation_email(user: UserInDB):
    email_template = template.format(str(user.activation_code))
    print(email_template)
    message = MessageSchema(
        subject="Kako app - activation code",
        recipients=[user.email],
        body=email_template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


@router.post("/users/register", response_model=User, tags=["users"])
async def register_user(user_data: UserIn, background_tasks: BackgroundTasks):
    user_dict = user_data.dict()
    hashed_password = get_password_hash(user_dict.pop("password"))
    user_dict.update(
        {"hashed_password": hashed_password, "disabled": True, "activation_code": randint(1000000, 10000000)})

    try:
        print("##########", user_dict)
        result = users_collection.insert_one(user_dict)

    except DuplicateKeyError:
        raise HTTPException(400, detail=" duplicate info, user not registered.")
    user = UserInDB(**(users_collection.find_one({"_id": result.inserted_id})))
    print(user)
    background_tasks.add_task(send_activation_email, user)

    return user


@router.post("/users/activate", tags=["users"])
async def activate_user(activation_data: ActivationData, user: UserInDB = Depends(get_current_user)):
    if user.activation_code == activation_data.code:
        user.disabled = False
        user.save()
        return {"message": "user activation was successful", "result": True}
    return {"message": "user activation was not successful", "result": False}
