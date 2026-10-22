FROM python:3.13-slim
WORKDIR /app
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_EXTRA_INDEX_URL=https://pypi.org/simple
COPY --from=packages . /tmp/packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /tmp/packages/gradian-keycloak /tmp/packages/gradian-auth
COPY . .
EXPOSE 8008
CMD ["python", "manage.py", "runserver", "0.0.0.0:8008"]
