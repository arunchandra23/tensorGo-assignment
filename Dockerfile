
FROM python:3.11
EXPOSE 8080
# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install fastapi uvicorn

COPY ./seamless_app.py /app


# Run app.py when the container launches
CMD ["uvicorn", "seamless_app:app", "--host", "0.0.0.0", "--port", "8080"]
