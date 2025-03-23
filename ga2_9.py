import uvicorn  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from fastapi import FastAPI, Query, HTTPException  # type: ignore
import csv
import os

app = FastAPI()

# Middleware for CORS support
app.add_middleware(
     CORSMiddleware,
     allow_origins=["*"],  # Allows all origins
     allow_credentials=True,
     allow_methods=["*"],  # Allows all methods
     allow_headers=["*"],  # Allows all headers
     )

def read_student_data(file_path: str):
    students_data = []
    print(file_path)
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            students_data.append(
            {"studentId": int(row["studentId"]), "class": row["class"]})

@app.get("/api")
async def get_students(class_: list[str] = Query(default=None, alias="class")):
    """Fetch all students or filter by class(es)."""
    students_data = read_student_data(os.getcwd() + "/uploads/q-fastapi.csv")
    print(students_data)
    # if not students_data:
    #      raise HTTPException(status_code=400, detail="No data available.")

    print(class_)
    if class_:
        filtered_students = [
            student for student in students_data if student["class"] in class_]
        return JSONResponse(content={"students": filtered_students})
    return JSONResponse(content={"students": students_data})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, reload=True)
