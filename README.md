
# Hospital‑to‑Hospital Data Exchange POC

**End‑to‑end demo:** two hospitals tokenise their private datasets as ERC‑20 tokens, swap access rights, and unlock analytics—all on an Ethereum chain you can run locally or point at a public testnet.

- **Portable** – one codebase works in free‑gas mode *and* gas‑fee mode.
- **Hands‑free wallets** – if you don’t set any private keys the scripts create, fund, and persist two brand‑new wallets for you.
- **Verifiable** – every contract address, tx hash, token balance, and gas burn is saved or printed so you can show auditors.

---

## Repo layout

*(**`contracts/Token.sol`** ****is committed**** so anyone can verify or recompile the exact byte‑code.)*

```
MonetisedPOC/
├── aggregate_query.py  #used to communciate with hospital APIs to show aggregate outputs of average age
├── aggregate_query_he.py  #same as aggregate_query but uses HE
├── check_balances.py   #show token balaces
├── contracts
│   └── Token.sol  # minimal ERC‑20 (represents a hospital dataset)
├── deploy.py
├── hospital_A  
│   ├── app.py  #api endpoint and data generation
│   ├── he_service.py  #endpoint and data generation + HE
│   ├── paillier.py   #used for HE
│   └── requirements.txt
├── hospital_B
│   ├── app.py
│   ├── he_service.py
│   ├── paillier.py
│   └── requirements.txt
├── main.py  #provides CLI interface
├── paillier.py  #used for HE 
├── requirements.txt
└── swap.py
```
---

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. launch a dev chain  (choose ↓)
#    —— FREE‑GAS demo ——         # no ETH needed at all
anvil --base-fee 0 --port 8545 &

#    —— GAS‑FEE simulation ——    # 1 ETH auto‑funded to each wallet
anvil --base-fee 10 --port 8545 &

# 2. setup the APIs in separate terminals
python -m uvicorn hospital_A.app:app --reload --port 8001 #run this from the directory/MonetisedPOC
python -m uvicorn hospital_B.app:app --reload --port 8002

#3. run main
python3 main.py #press 1, then 3. 5 can be used to check balances

```

Or run the scripts yourself:

```bash
python deploy.py      # compile & deploy HAPD/HBTD (wallets auto‑generated)
python aggregate_query.py [condition]  # i.e. python aggregate_query.py diabetes
python check_balances.py   # (optional) see token + ETH balances
```

---

## What the on‑chain *contract* actually does

`contracts/Token.sol` is a **40‑line, dependency‑free ERC‑20** whose *only* purpose is to treat each hospital’s dataset as a fungible, transferable asset.

- **Total supply = dataset size proxy.** We mint the whole supply (1 M tokens) to the data owner at deployment; no further mint/burn—so token balance directly mirrors access rights.
- **No advanced features.** No pausing, blacklisting, or owner‑only hooks. Keeping the ABI minimal makes the byte‑code trivial to audit.
- **18 decimals** to stay compatible with wallets and off‑the‑shelf explorers.
- **Why not ERC‑721 / Ocean datatokens?** ERC‑20 is universally supported; for this POC we care about *provable exchange*, not fine‑grained licensing.

The contract therefore serves as a **cryptographic receipt**: holding HAPD or HBTD is equivalent to holding permission to analyse Hospital A’s patient data or Hospital B’s treatment data.

---

## What the demo proves

| Phase            | On‑chain artefacts                                                | Off‑chain evidence                                         |
| ---------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- |
| **Tokenisation** | Two ERC‑20 byte‑codes + ABIs; contract addrs in `deploy.json`     | `deploy.py` console logs + JSON metadata                   |
| **Ownership**    | 1 000 000 HAPD minted to Hospital A; 1 000 000 HBTD to Hospital B | `check_balances.py` shows initial split                    |
|                     but transferred to requestor wallet (illustrating token buying)  |                                                            |
| **Value unlock** | n/a                                                               | `aggregate_query.py diabetes`                              |

### Seeing gas fees

Run in gas‑fee mode and then:

```bash
python check_balances.py   # shows ETH balance drop (~0.00005 ETH per tx)
```


MIT License – fork, adapt, improve.




