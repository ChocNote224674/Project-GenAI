# Use the latest Python 3.11 base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Set the environment variable to ensure Python outputs everything to the terminal
ENV PYTHONUNBUFFERED=True

# Copy the requirements file into the container
COPY requirements.txt /requirements.txt

# Install the dependencies from the requirements file
RUN pip install --no-cache-dir --upgrade -r /requirements.txt

# Set environment variables for the application (including your project-related ones)
COPY .env /app/.env

# Expose the port the app will run on
EXPOSE 8080

# Copy the project files into the container (presumably your Streamlit app)
COPY . ./app

# Set the entry point to run the Streamlit app
# If you want to use the default PORT from .env, make sure it is in .env or defined here
ENV PORT=8080

ENTRYPOINT ["streamlit", "run", "app/app.py", "--server.port", "${PORT}", "--server.address", "0.0.0.0"]
