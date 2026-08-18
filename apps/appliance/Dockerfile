FROM python:3.12-slim

# Why: pypdfium2 ships prebuilt wheels, so no toolchain needed. Keep the image
# minimal — this appliance holds financial records and should present a small
# surface.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Why: run unprivileged. The bind-mounted data dirs are chowned by the entry
# path at startup if needed.
RUN useradd --create-home --uid 10001 ledger && \
    mkdir -p /data/inbox /data/archive /data/review && \
    chown -R ledger:ledger /data /srv
USER ledger

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
