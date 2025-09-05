from fastapi import FastAPI, Query
import pandas as pd
import numpy as np

app = FastAPI()

# Simulated hospital A data
df = pd.DataFrame({
    #"age": np.random.randint(20, 80, size=200),
    "age": [100] * 200,
    "condition": np.random.choice(["diabetes", "cancer", "asthma"], 200)
})

@app.get("/query")
def query_average_age(condition: str = Query(...)):
    result = df[df["condition"] == condition]["age"].mean()
    return {"hospital": "A", "avg_age": result}
