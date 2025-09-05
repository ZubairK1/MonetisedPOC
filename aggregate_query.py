
import sys
import json
import asyncio
import httpx
from web3 import Web3
from eth_account import Account



RPC_URL = "http://127.0.0.1:8545"
CHAIN_ID = 31337
HOSPITAL_A_API = "http://127.0.0.1:8001/query"
HOSPITAL_B_API = "http://127.0.0.1:8002/query"
TOKEN_AMOUNT = 10 * 10**18  # Amount to pay each hospital 

# --- Load deploy info ---
with open("deploy.json") as f:
    meta = json.load(f)
with open("abi.json") as f:
    abi = json.load(f)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected(), f"Web3 not connected to {RPC_URL}"

hapd = w3.eth.contract(address=meta["HAPD"]["address"], abi=abi)
hbtd  = w3.eth.contract(address=meta["HBTD"]["address"], abi=abi)

requestor_pk = meta["priv_req"]
acct_req = Account.from_key(requestor_pk)

# --- Helper to send tokens ---

def send_token(contract, sender_pk, to_addr, amount):
    sender = Account.from_key(sender_pk).address
    tx = contract.functions.transfer(to_addr, amount).build_transaction({
        "from": sender,
        "nonce": w3.eth.get_transaction_count(sender),
        "chainId": CHAIN_ID,
        "gas": 200_000,
        "gasPrice": 0,
    })
    signed = w3.eth.account.sign_transaction(tx, sender_pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✓ Sent {amount // 10**18} HAPD to {to_addr[:8]}… (gasUsed={receipt.gasUsed})")
    return tx_hash.hex()

# --- Differential privacy 
import random
def apply_differential_privacy(value, epsilon=1.0):
    # Laplace mechanism
    scale = 1.0 / epsilon
    noise = random.gauss(0, scale)
    return value + noise

# --- Main logic ---

async def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate_query.py <condition>")
        sys.exit(1)
    condition = sys.argv[1]


    # Check requestor's token balance
    buyer_id = acct_req.address
    tokens_remaining = hapd.functions.balanceOf(buyer_id).call()
    if tokens_remaining < 2 * TOKEN_AMOUNT:
        print(json.dumps({"error": "Insufficient tokens to pay both hospitals."}, indent=2))
        return

    

    # Fetch data from hospitals
    urls = [
        f"{HOSPITAL_A_API}?condition={condition}",
        f"{HOSPITAL_B_API}?condition={condition}"
    ]
    results = []
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if "avg_age" in data:
                        results.append(data["avg_age"])
            except Exception:
                continue  # Skip if a hospital is down

    if len(results) < 2:
        print(json.dumps({"error": "Data from both hospitals required. Payment cancelled, not all hospitals returned data."}, indent=2))
        return
    
    #  Pay both hospitals  only after 
    tx_a = send_token(hapd, requestor_pk, meta["acct_a"], TOKEN_AMOUNT)
    tx_b = send_token(hbtd, requestor_pk, meta["acct_b"], TOKEN_AMOUNT)

    # Display balance for debug and testing
    tokens_remaining = {
        "HAPD": hapd.functions.balanceOf(buyer_id).call() // 10**18,
        "HBTD": hbtd.functions.balanceOf(buyer_id).call() // 10**18
    }
    hospital_earnings = {
        "Hospital_A": hapd.functions.balanceOf(meta["acct_a"]).call() // 10**18,
        "Hospital_B": hbtd.functions.balanceOf(meta["acct_b"]).call() // 10**18
    }



    # Aggregate results
    combined_avg = sum(results) / len(results)
    noisy_avg = apply_differential_privacy(combined_avg)

    result = {
        "buyer_id": buyer_id,
        "condition": condition,
        "noisy_average_age": round(noisy_avg, 2),
        "sources": len(results),
        "tokens_remaining": tokens_remaining,
        "hospital_earnings": hospital_earnings
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
