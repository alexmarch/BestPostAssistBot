# Use an official Python image as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate and configure the locale
RUN echo "uk_UA.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=uk_UA.UTF-8

# Install also Russian locale
RUN echo "ru_RU.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen ru_RU.UTF-8

# Set environment variables for the locale
ENV LANG=uk_UA.UTF-8
ENV LANGUAGE=uk_UA:uk
ENV LC_ALL=uk_UA.UTF-8


# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

RUN git clone https://github.com/alexmarch/aiogram_calendar.git /tmp/aiogram_calendar

# copy to python lib
RUN cp -r /tmp/aiogram_calendar /usr/local/lib/python3.12/site-packages/

# Command to run your application
CMD ["python", "main.py"]
