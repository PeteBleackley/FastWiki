#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 09:31:31 2024

@author: peter
"""
import datetime
from typing import Annotated
from FastAPI import Depends, HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError
import yaml
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel


import ZODB
import persistent

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel, persistent.Persistent):
    username: str
    email: str
    hashed_password: str
    blocked: datetime.date(1970,1,1)
    admin: bool = False
    
    
class Token(BaseModel):
    access_token: str
    token_type: str


storage = ZODB.FileStorage.FileStorage('.FastWiki_users.fs')
userdb = ZODB.DB(storage)
with open('.Fastwiki_coonfig.yaml') as config_yaml:
    config = yaml.load(config_yaml)
    
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
forbidden = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User is not authorized to do this",
    headers={"WWW-Authenticate":"Bearer"})

def transaction(func):
    """
    Wraps a function in a ZODB transaction. Makes the connection available to 
    the wrapped function as `users`

    Parameters
    ----------
    func : callable
        Function that requires ZODB access.

    Returns
    -------
    callable
        Wrapped function.

    """
    async def inner(*args):
        """
        Wrapped function

        Parameters
        ----------
        *args : Any
            Arguments of the function.

        Returns
        -------
        Any
            Result of the wrapped function.

        """
        with userdb.transaction() as users:
            return await func(*args)
        return inner
            

class requires_authentication:
    """
    Wraos a function to make it require authentication
    """
    
    def __init__(self,func, requires_admin=False):
        """
        

        Parameters
        ----------
        func : Callable
            Function that requires authentication

        Returns
        -------
        None.

        """
        self.func = func
        self.requires_admin = requires_admin
    
    @transaction
    async def __call__(self,url,token,body):
        nonlocal users
        result = None
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise unauthorized
        except InvalidTokenError:
            raise unauthorized
        if username in users:
            user = users[username]
            if self.requires_admin and not  user.admin:
                raise forbidden
            elif datetime.date.today() < user.blocked:
                raise forbidden
            result = await(self.func(url,token,body))
        else:
            raise unauthorized
        return result
    
def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@transaction    
async def register(url,body):
    nonlocal users
    user = User(username=body.username,
                email=body.email,
                hashed_password=pwd_context.hash(body.password))
    users[body.username]=user
    
@transaction
async def login(url,body):
    nonlocal users
    token = None
    if body.username in users:
        user = users[body.username]
        if pwd_context.verify(body.password,user.hashed_password):
            access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub": user.username}, 
                                               expires_delta=access_token_expires)
            token = Token(access_token=access_token,
                          token_type='bearer')
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return token
    
        
    

@transaction
async def logout(url):
    pass