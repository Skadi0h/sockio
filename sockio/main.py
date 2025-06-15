from fastapi import FastAPI

app = FastAPI()


@app.get('/')
def main() -> str:
    return 'Hello Vanya!'
