
import sys, json, asyncio, httpx
from paillier import keygen, e_add, decrypt
from web3 import Web3
from eth_account import Account

# chain copied from normal aggregate_query
RPC_URL = "http://127.0.0.1:8545"
CHAIN_ID = 31337

HOSPITAL_A_HE = "http://127.0.0.1:8001/he_query"
HOSPITAL_B_HE = "http://127.0.0.1:8002/he_query"
TOKEN_AMOUNT = 10 * 10**18

with open("deploy.json") as f: meta = json.load(f)
with open("abi.json") as f: abi = json.load(f)
w3 = Web3(Web3.HTTPProvider(RPC_URL))
hapd = w3.eth.contract(address=meta["HAPD"]["address"], abi=abi)
hbtd = w3.eth.contract(address=meta["HBTD"]["address"], abi=abi)
requestor_pk = meta["priv_req"]
acct_req = Account.from_key(requestor_pk)

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
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()

def apply_differential_privacy(value, epsilon=1.0):
    import random
    scale = 1.0 / epsilon
    noise = random.gauss(0, scale)
    return value + noise

async def fetch_enc(client, url, condition, n_decimal):
    r = await client.post(url, json={"condition": condition, "n": n_decimal})
    r.raise_for_status()
    d = r.json()
    return int(d["enc_sum"]), int(d["enc_count"])

async def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate_query_he.py <condition>")
        sys.exit(1)
    condition = sys.argv[1]

    # generate keypair
    pub, priv = keygen(1024)
    n_dec = str(pub.n)

    # Check balance first 
    buyer_id = acct_req.address
    if hapd.functions.balanceOf(buyer_id).call() < 2 * TOKEN_AMOUNT:
        print(json.dumps({"error": "Insufficient tokens to pay both hospitals."}, indent=2))
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        (es_a, ec_a), (es_b, ec_b) = await asyncio.gather(
            fetch_enc(client, HOSPITAL_A_HE, condition, n_dec),
            fetch_enc(client, HOSPITAL_B_HE, condition, n_dec)
        )

    # Homomorphic add
    enc_sum_total  = e_add(pub, es_a, es_b)
    enc_count_total = e_add(pub, ec_a, ec_b)

    sum_total = decrypt(priv, enc_sum_total)
    count_total = decrypt(priv, enc_count_total)
    if count_total == 0:
        print(json.dumps({"error": "No matching records."}, indent=2)); return

    avg = sum_total / count_total
    noisy_avg = apply_differential_privacy(avg)

    # Pay both hospitals
    tx_a = send_token(hapd, requestor_pk, meta["acct_a"], TOKEN_AMOUNT)
    tx_b = send_token(hbtd, requestor_pk, meta["acct_b"], TOKEN_AMOUNT)

    out = {
        "buyer_id": buyer_id,
        "condition": condition,
        "average_age": round(avg, 4),
        "noisy_average_age": round(noisy_avg, 4),
        "sources": 2
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
