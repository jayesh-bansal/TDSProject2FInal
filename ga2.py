import csv
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Query, HTTPException
import os
import zipfile
import requests
import base64
from PIL import Image
import numpy as np
import colorsys

def extract_zip_file(source: str, extract_folder: str) -> str:
    """Extracts a ZIP file from a URL or local path."""

    zip_path = "temp.zip" if source.startswith("http") else source

    if source.startswith("http"):  # Download ZIP if source is a URL
        try:
            with requests.get(source, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    f.write(r.content)
        except requests.RequestException as e:
            raise ValueError(f"Error downloading ZIP file: {e}")

    if os.path.isfile(extract_folder):  # Prevent extracting into a file
        raise ValueError(f"'{extract_folder}' is a file, not a directory.")

    os.makedirs(extract_folder, exist_ok=True)  # Ensure directory exists

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_folder)
    except zipfile.BadZipFile:
        raise ValueError(
            f"Failed to extract ZIP file: {zip_path} is not a valid ZIP archive.")

    if source.startswith("http"):
        os.remove(zip_path)  # Cleanup downloaded ZIP

    return extract_folder

def GA2_2(file_path, output_path=None, max_size=1500):
    # Ensure file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get file extension
    file_extension = os.path.splitext(file_path)[1].lower()

    # If output_path is not provided, generate a new filename
    if output_path is None:
        output_path = "compressed" + file_extension

    if file_extension in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
        img = Image.open(file_path)

        # Try saving with optimization
        img.save(output_path, optimize=True)

        # Check file size
        if os.path.getsize(output_path) > max_size:
            # If still too large, adjust compression settings
            if file_extension == ".png":
                # Reduce color depth
                img = img.convert("P", palette=Image.ADAPTIVE)
                img.save(output_path, optimize=True,
                         bits=4)  # Reduce bit depth

            elif file_extension in [".jpg", ".jpeg"]:
                quality = 85  # Start with 85% quality
                while os.path.getsize(output_path) > max_size and quality > 10:
                    img.save(output_path, "JPEG",
                             quality=quality, optimize=True)
                    quality -= 5  # Reduce quality in steps of 5

    else:
        # If it's not an image, just copy the file
        with open(file_path, "rb") as f_in, open(output_path, "wb") as f_out:
            f_out.write(f_in.read())

    # Ensure final size is within the limit
    if os.path.getsize(output_path) > max_size:
        raise ValueError(
            f"Compression failed: File is still larger than {max_size} bytes")

    # Read and encode the file in Base64
    with open(output_path, "rb") as file:
        base64_encoded = base64.b64encode(file.read()).decode("utf-8")

    return base64_encoded  # Return file path & Base64 string

def count_light_pixels(image_path: str, threshold: float = 0.814):
    """Counts the number of pixels in an image with lightness above the threshold."""
    image = Image.open(image_path).convert("RGB")
    rgb = np.array(image) / 255.0
    lightness = np.apply_along_axis(lambda x: colorsys.rgb_to_hls(*x)[1], 2, rgb)
    light_pixels = np.sum(lightness > threshold)
    print(f'Number of pixels with lightness > {threshold}: {light_pixels}')
    return light_pixels

def GA2_9(file_path: str, port: int):
    app = FastAPI()

    # Add CORS middleware to allow cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    students_data = []  # Global variable for student data

    def load_student_data():
        """Load student data from the given CSV file."""
        nonlocal students_data
        students_data.clear()
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                students_data = [
                    {"studentId": int(row["studentId"]), "class": row["class"]}
                    for row in reader
                ]
        except FileNotFoundError:
            raise HTTPException(
                status_code=500, detail=f"File {file_path} not found.")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error loading data: {str(e)}")

    load_student_data()

    @app.get("/api")
    async def get_students(class_: list[str] = Query(default=None, alias="class")):
        """
        Fetch all students or filter by class(es).
        - If no 'class' query parameter is provided, return all students.
        - If 'class' query parameter(s) is provided, filter by the specified class(es).
        """
        if class_:
            filtered_students = [
                student for student in students_data if student["class"] in class_]
            return JSONResponse(content={"students": filtered_students})
        return JSONResponse(content={"students": students_data})

    # uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
    return "http://127.0.0.1:" + str(port) + "/api"
