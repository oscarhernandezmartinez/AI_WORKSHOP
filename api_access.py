import json
import requests
import urllib3
import math

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH_LOGIN_URL = 'https://pse-console-auth.intel.com/api/v1/aad/login'
SYSTEM_LIST_URL = 'https://pse-console-data.intel.com/api/v1/inventory/systems'
SHORT_LIST_URL = 'https://pse-console-query-bot-relay.intel.com/api/v1/mongodb/downloads_short'
TIMEOUT = 3600

def auth_login(email, password):
    headers = {
        'accept': 'application/json'
    }

    data = {
        'email': f'{email}',
        'password': f'{password}',
    }

    try:
        response = requests.post(
            AUTH_LOGIN_URL,
            headers=headers,
            verify=False,  # nosec B501
            json=data,
            timeout=TIMEOUT,
        )

        response.raise_for_status()
        system_info_response_json = response.json()

        print('Successfully authorized')
        return True, system_info_response_json['access_token']
    except requests.RequestException as e:
        print('Could not authorize', e)
        return False, ''
    except Exception as e:
        print('Unexpected error during auth', e)
        return False, ''

def get_all_system_ids(token):
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    data = {
        'attributes_filter': {},
        'system_filters': [],
        'system_ids': [],
    }

    try:
        response = requests.post(
            'https://pse-console-data.intel.com/api/v1/systems/systems-filter?system_id_only=true',
            headers=headers,
            verify=False,  # nosec B501
            json=data,
            timeout=TIMEOUT,
        )

        response.raise_for_status()
        system_list = response.json()

        return True, system_list
    except requests.RequestException as e:
        print('Could not fetch system ids %s', e)
        return False, []
    except Exception as e:
        print('Unexpected error during gathering system ids %s', e)
        return False, []

def get_short_list(token, system_ids):
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    data = {
        "system_ids": system_ids,
        "field_names" : [
                "System Name",
                "System Type",
                "CPU",
                "Memory",
                "BIOS",
                "Board Product",
                "Board Serial",
                "Group",
                "Pool",
                "Product",
                "Activity",
                "Owner",
                "Active State",
                "NGA Project",
                "NGA Activity",
                "NGA Config",
                "Last Scan",
                "BAT Result",
                "HMA Version",
                "Location",
                "HMA Status"
                ]
    }

    try:
        response = requests.post(
            SHORT_LIST_URL,
            headers=headers,
            verify=False,  # nosec B501
            json=data,
            timeout=TIMEOUT,
            stream=True
        )

        response.raise_for_status()
        
        with open('shortlist.csv', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print('Wrote to shortlist.csv')

        return True
    except requests.RequestException as e:
        print('Could not get short list', e)
        return False
    except Exception as e:
        print('Unexpected error during short list', e)
        return False

def main(email, password):
    success, token = auth_login(email, password)

    if not success:
        print('Cannot continue with invalid auth')
        exit(1)

    print('Acquired access token')

    success, system_ids = get_all_system_ids(token)

    print('system id count: ', len(system_ids))

    if success:
        get_short_list(token, system_ids)

if __name__ == '__main__':
    import sys
    email = sys.argv[1]
    password = sys.argv[2]

    main(email, password)

