FROM python:3.12

WORKDIR /app

# Install utility tools
RUN apt-get update && \
    apt-get install poppler-utils -y

# Install python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./ /app

COPY --chown=root:root entrypoint.sh setup.sh /
RUN chmod +x /entrypoint.sh

ARG IS_BACKEND
ENV IS_BACKEND=$IS_BACKEND

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]