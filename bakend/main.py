from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware

from integrations.airtable import authorize_airtable, get_items_airtable, oauth2callback_airtable\
    ,get_airtable_credentials
from integrations.notion import authorize_notion, get_items_notion, oauth2callback_notion, get_notion_credentials
from integrations.hubspot import authorize_hubspot, get_hubspot_credentials, get_items_hubspot, oauth2callback_hubspot

app = FastAPI()

origins = [
    "http://localhost:3000" ,# React app address
    "http://localhost:*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}


# Airtable
@app.post('/integrations/airtable/authorize')
async def authorize_airtable_integration(user_id: str = Form(...), org_id: str = Form(...)):
#    return (user_id, org_id)
    response = await authorize_airtable(user_id, org_id)
    return response

@app.get('/integrations/airtable/oauth2callback')
async def oauth2callback_airtable_integration(request: Request):
    response = await oauth2callback_airtable(request)
    return  response

@app.post('/integrations/airtable/credentials')
async def get_airtable_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
#async def get_airtable_credentials_integration(user_id: str ='krushna.021523@gmail.com', org_id: str ='testorg'):
    response = await get_airtable_credentials(user_id, org_id)
    return  response

@app.post('/integrations/airtable/load')
async def get_airtable_items(credentials: str = Form(...)):
    response = await get_items_airtable(credentials)
    return  response


#Hubspot

# API to Create the authorization url from CLIENT ID and other params
@app.post('/integrations/hubspot/authorize')
async def authorize_hubspot_integration(user_id: str = Form(...), org_id: str = Form(...)):
    response = await authorize_hubspot(user_id,org_id)
    return response

# API to get code from OAuth response and request for access-token
@app.get('/integrations/hubspot/oauth2callback')
async def oauth2callback_hubspot_integration(request: Request):
    response = await oauth2callback_hubspot(request)
    return  response

# API to get the response with access-token from redis
@app.post('/integrations/hubspot/credentials')
async def get_hubspot_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
     response = await get_hubspot_credentials(user_id, org_id)
     return  response

# API to fetch all CRM contacts from Hubspot
@app.post('/integrations/hubspot/load')
async def get_hubspot_items(credentials: str = Form(...)):
    response = await get_items_hubspot(credentials)
    return  response

# Notion
@app.post('/integrations/notion/authorize')
async def authorize_notion_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_notion(user_id, org_id)

@app.get('/integrations/notion/oauth2callback')
async def oauth2callback_notion_integration(request: Request):
    return await oauth2callback_notion(request)

@app.post('/integrations/notion/credentials')
async def get_notion_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_notion_credentials(user_id, org_id)

@app.post('/integrations/notion/load')
async def get_notion_items(credentials: str = Form(...)):
    return await get_items_notion(credentials)


