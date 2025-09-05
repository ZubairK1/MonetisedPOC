import json
from web3 import Web3

RPC_URL = "http://127.0.0.1:8545"          # same node you used before
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# ---- load addresses & ABI ----
with open("deploy.json") as f:
    info = json.load(f)
with open("abi.json") as f:
    abi = json.load(f)

hapd = w3.eth.contract(address=info["HAPD"]["address"], abi=abi)
hbtd = w3.eth.contract(address=info["HBTD"]["address"], abi=abi)

acct_a = info["acct_a"]   # Hospital A wallet
acct_b = info["acct_b"]   # Hospital B wallet

def to_tokens(wei):       # 18‑decimals helper
    return wei / 10**18

print("\nBalances after the swap")
print("-----------------------")
print(f"Hospital A ({acct_a[:8]}…)")
print(f"  HAPD: {to_tokens(hapd.functions.balanceOf(acct_a).call()):,.0f}")
print(f"  HBTD: {to_tokens(hbtd.functions.balanceOf(acct_a).call()):,.0f}")

print(f"\nHospital B ({acct_b[:8]}…)")
print(f"  HAPD: {to_tokens(hapd.functions.balanceOf(acct_b).call()):,.0f}")
print(f"  HBTD: {to_tokens(hbtd.functions.balanceOf(acct_b).call()):,.0f}")

eth_a = w3.from_wei(w3.eth.get_balance(info["acct_a"]), "ether")
eth_b = w3.from_wei(w3.eth.get_balance(info["acct_b"]), "ether")
print(f"ETH   →  A: {eth_a:.6f}   B: {eth_b:.6f}")

# ---- Requestor balances ----
acct_req = info["acct_req"]
print(f"\nRequestor ({acct_req[:8]}…)")
print(f"  HAPD: {to_tokens(hapd.functions.balanceOf(acct_req).call()):,.0f}")
print(f"  HBTD: {to_tokens(hbtd.functions.balanceOf(acct_req).call()):,.0f}")
eth_req = w3.from_wei(w3.eth.get_balance(acct_req), "ether")
print(f"ETH   →  Requestor: {eth_req:.6f}")
