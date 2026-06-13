from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

AMO_DOMAIN = 'skillteam.amocrm.ru'
AMO_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImJjNGQzYWY5Y2RlYjE2NTA3NmRlYmU1Zjg2NWQxMzBjOTg5OGFlOTI2MmU0ZjUxNTIyYjI1ODZmZDE3ZDEwZWU2NzE4ZWJmNTA4ZGYwY2JiIn0.eyJhdWQiOiIwNWNkZTZkMy0zNTVmLTQ4YTItYjQwNi1iYTg0NjQ3NjM5ZWIiLCJqdGkiOiJiYzRkM2FmOWNkZWIxNjUwNzZkZWJlNWY4NjVkMTMwYzk4OThhZTkyNjJlNGY1MTUyMmIyNTg2ZmQxN2QxMGVlNjcxOGViZjUwOGRmMGNiYiIsImlhdCI6MTc4MTI1NTM4OCwibmJmIjoxNzgxMjU1Mzg4LCJleHAiOjE4MzI5NzYwMDAsInN1YiI6IjEwNTcyNDk4IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMxMzU0Nzk4LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJwdXNoX25vdGlmaWNhdGlvbnMiLCJmaWxlcyIsImNybSIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiZWFjN2RhMDMtYjZjOC00Mjk3LThhYTgtZWRlZTYzNTFhMzYxIiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.ORDRTjERzwgh1jYkeunw1Nc7yw2Yp8yR_swv0_id_i-Kg0kCoQ3WGvLsLUZPTwNAZ0RHG4cguzJAlkDzYPrWBFDxkQmrhAcpEvy3rhZkS8GtoLKecdKlydDR9GO8KyjwZp0P9RP2kvB6aMiVKFSO6P1LL2_XTgW3nSc9meMq3LEGfqD7oqWyJoT4pmIJFcBcwTqK9R2jeheuBC9gs33pg-dvNfufSHF4uxq1eWB_JyiA5Vjxnx3QrDN1HlshbU6ExVIRzYz4iYRIWqh2LtAJfia6v25YNR-c35lsWwI39yjNCs0M_acSO1Duygh6CbGGRlKMYAuZ87X7GC-lv0bU-Q'

HEADERS = {
    'Authorization': f'Bearer {AMO_TOKEN}',
    'Content-Type': 'application/json'
}

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    
    phone = str(data.get('chat_id', ''))
    name = data.get('first_name', 'WhatsApp клиент')
    text = data.get('user_message', '')

    if not phone:
        return jsonify({'status': 'no phone'}), 200

    phone = ''.join(filter(str.isdigit, phone))

    # Поиск контакта
    r = requests.get(
        f'https://{AMO_DOMAIN}/api/v4/contacts?query={phone}',
        headers=HEADERS
    )
    contacts = r.json().get('_embedded', {}).get('contacts', [])
    contact_id = contacts[0]['id'] if contacts else None

    if contact_id:
        r2 = requests.get(
            f'https://{AMO_DOMAIN}/api/v4/contacts/{contact_id}?with=leads',
            headers=HEADERS
        )
        leads = r2.json().get('_embedded', {}).get('leads', [])
        lead_id = leads[0]['id'] if leads else None
        if lead_id and text:
            requests.post(
                f'https://{AMO_DOMAIN}/api/v4/leads/{lead_id}/notes',
                headers=HEADERS,
                json=[{'note_type': 'common', 'params': {'text': f'📱 WhatsApp: {text}'}}]
            )
    else:
        r3 = requests.post(
            f'https://{AMO_DOMAIN}/api/v4/contacts',
            headers=HEADERS,
            json=[{'name': name, 'custom_fields_values': [{'field_code': 'PHONE', 'values': [{'value': phone, 'enum_code': 'WORK'}]}]}]
        )
        new_contacts = r3.json().get('_embedded', {}).get('contacts', [])
        contact_id = new_contacts[0]['id'] if new_contacts else None
        if contact_id:
            requests.post(
                f'https://{AMO_DOMAIN}/api/v4/leads',
                headers=HEADERS,
                json=[{'name': f'WhatsApp: {name}', '_embedded': {'contacts': [{'id': contact_id}]}}]
            )

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
