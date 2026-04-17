from fastapi import APIRouter, Request
from eth_abi import decode
from web3 import Web3
import json

router = APIRouter()

USDT_CONTRACT = Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")  # Ethereum USDT

@router.post("/webhook")
async def alchemy_webhook(request: Request):
    data = await request.json()

    print("=== ALCHEMY WEBHOOK RECEIVED ===")
    print(json.dumps(data, indent=2))

    try:
        logs = data.get("event", {}).get("data", {}).get("block", {}).get("logs", [])

        for log in logs:
            address = log.get("address")

            # تحقق انه USDT
            if address.lower() != USDT_CONTRACT.lower():
                continue

            topics = log.get("topics", [])
            data_hex = log.get("data")

            # Transfer signature
            if topics[0] != Web3.keccak(text="Transfer(address,address,uint256)").hex():
                continue

            from_address = "0x" + topics[1][-40:]
            to_address = "0x" + topics[2][-40:]

            amount = int(data_hex, 16) / (10 ** 6)  # USDT = 6 decimals

            print("=== PAYMENT DETECTED ===")
            print(f"FROM: {from_address}")
            print(f"TO: {to_address}")
            print(f"AMOUNT: {amount} USDT")

            # 🔥 هنا تقدر تضيف:
            # save_to_db()
            # match_order()
            # trigger payout

    except Exception as e:
        print("ERROR:", str(e))

    return {"status": "ok"}
