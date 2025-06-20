# slack.py

import asyncio
import base64
import json
import os
import secrets
import httpx
import requests
from dotenv import load_dotenv
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
#from hubspot.crm.contacts import SimplePublicObjectInputForCreate
#from hubspot.crm.contacts.exceptions import ApiException
#from hubspot import hubspot
# from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from integrations.integration_item import IntegrationItem

# load different keys and IDs
load_dotenv()
account_id =os.getenv("HUB_ACCOUNT_ID")
client_id = os.getenv("HUB_CLIENT_ID")
client_secret = os.getenv("HUB_CLIENT_SECRET")
baseurl = os.getenv("HUB_BASEURL")
redirect_uri = os.getenv("HUB_REDIRECT_URI")
scope = os.getenv("HUB_SCOPE")
allcontacts_api = os.getenv("HUB_AllContacts_API")
accesstoken_api = os.getenv("HUB_GET_AccessToken_API")

# Generates the authorization URL required for  selecting the Hubspot challenge in Hubspot UI
async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')
    auth_url = f'{baseurl}/authorize?scope={scope}&redirect_uri={redirect_uri}&client_id={client_id}&state={encoded_state}'
    print(auth_url)
    await asyncio.gather(
        add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)
    )
    return auth_url

# OAuth callback which gets the input from the request as specified in the OAuth redirect_uri
# The code returned after successful authorization is used in calling https://api.hubapi.com/oauth/v1/token to get token
# Returns the response from API which has the access-token if successful
async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error_description'))
    code = request.query_params.get('code')
    print("code" + str(code))
    encoded_state = request.query_params.get('state')
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await asyncio.gather(
       get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    )
    saved_data = saved_state[0].decode('utf-8')
    print(str(saved_state))

    if not saved_state or original_state != json.loads(str(saved_data)).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        response,_ = await asyncio.gather(
            client.post(
                accesstoken_api,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                    'client_id': client_id,
                    'client_secret': client_secret,
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            ),

            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )
        print(response)

    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)

    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)
# Gets the response having access-token from redis and Saves the response containing
# the access-token as credentials which is useful other APIs
async def get_hubspot_credentials(user_id, org_id):
    # print("creds")
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    # print("creds" + str(credentials))
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')

    return credentials
# creates integration item metadata object from the get_items_hubspot response
async def create_integration_item_metadata_object(response_json) -> IntegrationItem:
    integration_item_metadata = IntegrationItem(
    id = response_json.get('contacts').get(0).get('portal_id')
    )
    return integration_item_metadata
# fetches the CRM contacts using the access-token obtained earlier and returns response
def fetch_items(
    access_token: str, url: str, aggregated_response: list, offset=None
) -> list:
    """Fetching the list of contacts"""
    params = {}
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json().get('contacts', {})

        for item in results:
            aggregated_response.append(item)

    return results

# API for getting CRM contacts from hubspot
async def get_items_hubspot(credentials):
    credentials = json.loads(credentials)
    list_of_integration_item_metadata = []
    list_of_responses = []

    results =fetch_items(credentials.get('access_token'), allcontacts_api, list_of_responses)

    print(f'Results from calling : {allcontacts_api}: {results}')
    return results

# Optional API code to which used hubspot client library to access the APIs
async  def create_hubspot_crm_contact(credentials):
    pass
    # credentials = json.loads(credentials)
    # api_client = hubspot(access_token=credentials.get('access_token'))
    # try:
    #     simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
    #         properties={"email": "yss2022test@gmail.com"}
    #     )
    #     api_response = api_client.crm.contacts.basic_api.create(
    #         simple_public_object_input_for_create=simple_public_object_input_for_create
    #     )
    # except ApiException as e:
    #     print("Exception when creating contact: %s\n" % e)