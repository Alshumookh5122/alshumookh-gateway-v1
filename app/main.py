from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "ALSHUMOOKH API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/transactions")
def get_transactions():
    return {
        "status": "success",
        "data": []
    }
