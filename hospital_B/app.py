from fastapi import FastAPI, Query
import pandas as pd
import numpy as np

app = FastAPI()

# Simulated hospital B data
df = pd.DataFrame({
    #"age": np.random.randint(30, 90, size=200),
    "age": [50] * 200,
    "condition": np.random.choice(["diabetes", "cancer", "asthma"], 200)
})

@app.get("/query")
def query_average_age(condition: str = Query(...)):
    result = df[df["condition"] == condition]["age"].mean()
    return {"hospital": "B", "avg_age": result}
