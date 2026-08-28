from fastapi import FastAPI
from api.routes import health, lectures, jobs, quiz, chatbot

app = FastAPI(title="LectureLens API")

app.include_router(health.router)
app.include_router(lectures.router)
app.include_router(jobs.router)
app.include_router(quiz.router)
app.include_router(chatbot.router)

@app.get("/")
def root():
    return {"message": "LectureLens API is running"}