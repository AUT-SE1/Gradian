FROM python:3.13-slim
WORKDIR /app
COPY --from=packages . /tmp/packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /tmp/packages/gradian-keycloak /tmp/packages/gradian-auth
COPY . .
EXPOSE 8008
CMD ["python", "manage.py", "runserver", "0.0.0.0:8008"]
