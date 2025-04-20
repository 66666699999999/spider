from fastapi import FastAPI
from main.api.router import routerss

app = FastAPI(title="Auto work API")

app.include_router(routerss)