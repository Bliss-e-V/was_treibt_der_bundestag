# Use an official Python runtime as the base image
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

COPY . .

RUN apt update 
RUN apt install -y imagemagick locales

# Set the locale
RUN sed -i '/de_DE.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG de_DE.UTF-8  
ENV LANGUAGE de_DE:de  
ENV LC_ALL de_DE.UTF-8  

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Run the command to start your application
CMD ["flask",  "--app",  "main",  "run", "--host",  "0.0.0.0"]