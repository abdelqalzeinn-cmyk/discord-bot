from fastapi import FastAPI
import uvicorn
import os
from dotenv import load_dotenv

app = FastAPI()

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Bot is running"}

def run():
    load_dotenv()
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    run()
