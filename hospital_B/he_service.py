# separate api for homomorphic encryption
from fastapi import FastAPI
from pydantic import BaseModel
from paillier import PublicKey, encrypt
from app import df  # same data as normal api 

app = FastAPI()

class HEReq(BaseModel):
    condition: str
    n: str  

@app.post("/he_query")
def he_query(req: HEReq):
    pub = PublicKey(int(req.n))
    sub = df[df["condition"] == req.condition]["age"]
    s = int(sub.sum())
    c = int(sub.shape[0])
    return {
        "enc_sum": str(encrypt(pub, s)),
        "enc_count": str(encrypt(pub, c)),
        "count_plain": c  # for testing
    }
