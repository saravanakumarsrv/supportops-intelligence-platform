from fastapi import FastAPI

app = FastAPI(title="SupportOps Intelligence Platform API")

@app.get("/")
def root():
    return {"message": "SupportOps API is running"}
