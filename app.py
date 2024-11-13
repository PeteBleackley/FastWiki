#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 09:04:27 2024

@author: peter
"""

from typing import Annotated
from enum import Enum
from pydantic import BaseModel
from fastapi import FastAPI, Depends
from security import requires_authentication, requires_admin, login, register, logout, oath2_scheme

app=FastAPI()

class View(str, Enum):
    register = 'register'
    login = 'login'
    create = 'create'
    edit = 'edit'
    history = 'history'
    upload = 'upload'
    

async def register_form(url):
    pass
    
async def login_form(url):
    pass

@requires_authentication
async def create_form(url,token,body=None):
    pass

@requires_authentication
async def edit_form(url,token,body=None):
    pass

@requires_authentication
async def history_form(url,token,body=None):
    pass

@requires_authentication()
async def upload_form(url,token,body=None): 
    pass

@app.get('/{url:path}')
async def get_handler(url:str, 
                      view:View, 
                      token:Annotated[str, oath2_scheme]=None,
                      body:BaseModel=None):
    result = None
    if view == View.register:
        result = await register_form(url)
    elif view == View.login:
        result = await login_form(url)
    elif view == View.edit:
        result = await edit_form(url,token)
    elif view == View.history:
        result = await history_form(url,token)
    elif view == View.upload:
        result = await upload_form(url,token)
    return result


@requires_authentication
async def edit(url,token,body):
    pass

@requires_authentication
async def revert(url,token,body):
    pass

@app.put('{/url:path}')
async def put_handler(url: str, 
                      view:View, 
                      token:Annotated[str, oath2_scheme]=None,
                      body:BaseModel=None):
    result = None
    if view == View.login:
        result = await login(url,body)
    elif view == View.edit:
        result = await edit(url)
    elif view == View.history:
        result = await revert(url)
    return result

@requires_authentication
async def create(url,token,body):
    pass

@requires_authentication
async def upload(url,token,body):
    pass
       
@app.post('{/url:path}')
async def post_handler(url:str, 
                       view:View,
                       token:Annotated[str,oath2_scheme],
                       body:BaseModel):
    result = None
    if view == View.register:
        result = await register(url,body)
    elif view == View.upload:
        result = await upload(url,token,body)
    return result
        
    