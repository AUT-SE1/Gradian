FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_EXTRA_INDEX_URL=https://pypi.org/simple
COPY --from=packages . /packages
COPY requirements.txt .
# Editable, so that Compose can mount ./packages over /packages and pick up edits without a rebuild.
# The test helpers are here too: this is a development image, and `make itest` runs in it.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        -e /packages/gradian-keycloak \
        -e "/packages/gradian-auth[drf]" \
        -e "/packages/gradian-testing[drf]"

FROM base AS runtime
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS dev
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
