from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import health, lectures, jobs, quiz, chatbot

app = FastAPI(title="LectureLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # add your deployed frontend URL too
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(lectures.router)
app.include_router(jobs.router)
app.include_router(quiz.router)
app.include_router(chatbot.router)

@app.get("/")
def root():
    return {"message": "LectureLens API is running"}