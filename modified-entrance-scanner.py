import cv2
import numpy as np
import aiohttp
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import firebase_admin
from firebase_admin import credentials, firestore

# Define the IP address of your ESP32
ESP32_IP = 'todamoonentrance.local'

# Initialize Firebase Admin SDK
cred = credentials.Certificate("service-account-key-python.json")  # Your Firebase service account file
firebase_admin.initialize_app(cred)

db = firestore.client()

# AES key (must be 16 bytes)
SECRET_KEY = b'Todamoon_drivers'

async def decrypt(encrypted_data, key):
    try:
        cipher = AES.new(key, AES.MODE_ECB)
        encrypted_data_bytes = base64.b64decode(encrypted_data)
        decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)
        return decrypted_data.decode('utf-8')
    except Exception:
        #await send_message_to_oled("Entry Error: Invalid QR Code")
        await trigger_buzzer_on_esp32()
        return None

async def fetch_user_data_from_firestore(user_id):
    try:
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        return user_doc.to_dict() if user_doc.exists else None  # Corrected exists check
    except Exception:
        return None

async def fetch_terminal_fee():
    try:
        fee_ref = db.collection("dashboard-counts").document("terminal-fee")
        fee_doc = fee_ref.get()
        return fee_doc.to_dict().get("fee") if fee_doc.exists else None  # Corrected exists check
    except Exception:
        return None

async def trigger_buzzer_on_esp32(session):
    try:
        buzzer_url = f'http://{ESP32_IP}/activate_buzzer'
        async with session.get(buzzer_url) as response:
            if response.status != 200:
                print("Failed to trigger the buzzer")
    except Exception as e:
        print(f"Error triggering buzzer: {e}")

async def send_message_to_oled(message, session):
    try:
        url = f'http://{ESP32_IP}/display_message'
        data = message.encode('utf-8')
        async with session.post(url, data=data, headers={'Content-Type': 'text/plain'}) as response:
            if response.status != 200:
                print("Failed to send message to OLED")
    except Exception as e:
        print(f"Error sending message to OLED: {e}")

async def join_queue(user_data, session):
    user_id = user_data['uid']
    barangay_name = user_data.get('barangay', 'default_barangay')  # Use default if barangay is missing
    user_ref = db.collection("users").document(user_id)
    barangay_ref = db.collection("barangays").document(barangay_name)
    queue_ref = barangay_ref.collection("queue")
    history_ref = db.collection("queueing_history")
    terminal_fee = await fetch_terminal_fee()

    try:
        # Fetch user data
        user_doc = user_ref.get()
        if not user_doc.exists:  # Corrected exists check
            print(f"User does not exist.")
           # await send_message_to_oled(f"User does not exist.", session)
            await trigger_buzzer_on_esp32(session)
            return

        user_data = user_doc.to_dict()
        in_queue = user_data.get("inQueue")
        user_balance = user_data.get("balance")
        current_balance = user_balance - terminal_fee
       
        if in_queue:
            print("User is already in the queue.")
           # await send_message_to_oled("User is already in the queue.", session)
            await trigger_buzzer_on_esp32(session)
            return

        if user_balance < terminal_fee:
            print("Insufficient balance.")
           # await send_message_to_oled("Insufficient balance.", session)
            await trigger_buzzer_on_esp32(session)
            return

        # Create a batch to perform multiple writes
        batch = db.batch()

        # Update user inQueue and balance
        batch.update(user_ref, {
            "inQueue": True,
            "balance": user_balance - terminal_fee
        })

        # Queue data
        queue_data = {
            "uid": user_id,
            "name": user_data.get("name"),
            "tricycleNumber": user_data.get("tricycleNumber"),
            "inQueue": True,
            "joinTime": firestore.SERVER_TIMESTAMP
        }
        batch.set(queue_ref.document(user_id), queue_data)

        # Transaction history
        transaction_data = {
            "amount": terminal_fee,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "description": "Queue Entry"
        }
        batch.set(user_ref.collection("queueing-transactions").document(), transaction_data)

        # History log
        history_data = {
            "driverId": user_id,
            "name": user_data.get("name"),
            "barangay": barangay_name,
            "action": "join",
            "amount": terminal_fee,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        batch.set(history_ref.document(), history_data)

        # Commit the batch
        batch.commit()
        print("Joined queue successfully!")
       # await send_message_to_oled(f"Joined success! Balance: {current_balance}.00", session)
        await trigger_buzzer_on_esp32(session)

    except Exception as e:
        print(f"Error: {e}")
       # await send_message_to_oled(f"{e}", session)

def parse_qr_data(decrypted_data):
    return dict(line.split(": ", 1) for line in decrypted_data.split("\n") if ": " in line)

async def main():
    url = f'http://{ESP32_IP}/capture'
    prev = ""
    detector = cv2.QRCodeDetector()
    session = aiohttp.ClientSession()

    while True:
        try:
            # Attempt to fetch an image from the ESP32
            async with session.get(url, timeout=5) as img_resp:
                if img_resp.status != 200:
                    print("Failed to get image from ESP32. Retrying...")
                    await asyncio.sleep(5)  # Wait before retrying
                    continue  # Skip to the next iteration

                imgnp = np.array(bytearray(await img_resp.read()), dtype=np.uint8)
                frame = cv2.imdecode(imgnp, -1)

                if frame is None:
                    print("Failed to decode image, skipping...")
                    continue

                data, points, _ = detector.detectAndDecode(frame)

                if data and prev != data:
                    print(f"QR Code Data: {data}")
                    decrypted_data = await decrypt(data, SECRET_KEY)
                    if decrypted_data:
                        qr_data = parse_qr_data(decrypted_data)
                        user_id = qr_data.get("uid")
                        if user_id:
                            print(f"Fetching data for user ID: {user_id}")
                            user_data = await fetch_user_data_from_firestore(user_id)
                            if user_data:
                                await join_queue(user_data, session)

                    prev = data

        except asyncio.TimeoutError:
            print("Request timed out. Retrying...")
            #await send_message_to_oled("Request timed out. Retrying...", session)
            await asyncio.sleep(5)  # Wait before retrying

        except Exception as e:
            print(f"Unexpected error: {e}")
            await asyncio.sleep(1)  # Short wait before retrying
            

if __name__ == "__main__":
    asyncio.run(main())