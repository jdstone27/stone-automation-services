# LocalLedger appliance

Self-hosted receipt and invoice extraction. Accepts images and PDFs, reads the
fields with a local vision model, and writes validated records to PostgreSQL.
Nothing leaves the machine.

## Architecture, and one deliberate exception

| Component  | Runs as                  | Why                                            |
|------------|--------------------------|------------------------------------------------|
| PostgreSQL | Docker (`unless-stopped`)| Persistent volume at `./data/postgres`          |
| API        | Docker (`unless-stopped`)| FastAPI + inbox watcher                         |
| Ollama     | **Natively on the host** | Docker on Apple Silicon cannot reach the GPU    |

That last row is the one thing that departs from "everything in Compose", and
it is not optional. On macOS, Docker runs containers inside a Linux VM which has
no access to the Metal GPU. A containerised vision model falls back to CPU and
becomes too slow to use. Running Ollama natively keeps full GPU access, and
`brew services` provides the same start-on-boot behaviour that
`restart: unless-stopped` was there to give.

The appliance is still fully offline: `host.docker.internal` is a loopback to
this machine, and both exposed ports bind to `127.0.0.1` only.

## First run

```bash
# 1. Ollama on the host
brew install ollama
brew services start ollama
ollama pull <your-vision-model>

# 2. Configure
cp .env.example .env
#    Set POSTGRES_PASSWORD and OLLAMA_VISION_MODEL. The service refuses to
#    start without a model name rather than silently choosing one for you.

# 3. Start
docker compose up -d --build

# 4. Check
curl -s localhost:8000/health/ready | python3 -m json.tool
```

`health/ready` reports the database and the model separately, and tells you the
exact `ollama pull` command if the configured model is not present.

## Using it

**Folder drop** — put files in `./data/inbox/`. The watcher polls every few
seconds and only ingests a file once its size has stopped changing, so copying a
large scan in does not get read half-written.

**API**

```bash
curl -F "file=@receipt.jpg" localhost:8000/documents
curl "localhost:8000/documents?status=review"
curl localhost:8000/stats
```

Interactive docs at `http://localhost:8000/docs`.

## Where files end up

```
data/inbox/     drop zone; emptied as files are ingested
data/archive/   originals of successfully extracted documents, by YYYY/MM
data/review/    anything that failed, plus a .reason.json explaining why
```

## The two guarantees

**Idempotent.** A document is identified by the SHA-256 of its bytes, with a
unique constraint in the database behind it. Dropping the same receipt twice —
or renaming it first — records it once.

**Never fatal.** A corrupt PDF, an unreachable model, a response that is prose
instead of JSON, an arithmetic mismatch, a missing total: each sends the
original to `data/review/` with a written reason. None of them stop the service
or interrupt the queue.

Extraction is deliberately conservative. Amounts are `Decimal`, never float.
Amounts beyond a plausible bound, future dates, and subtotal+tax≠total are all
treated as review-worthy rather than recorded.

## Tests

Schema behaviour is asserted against a real PostgreSQL instance — the tables use
ENUM, JSONB and IDENTITY columns, so a SQLite stand-in would not be testing what
ships.

```bash
export LOCALLEDGER_TEST_DSN="postgresql+psycopg://user@127.0.0.1:5432/scratch_db"
pytest apps/appliance/tests -q
```

Database tests skip cleanly when `LOCALLEDGER_TEST_DSN` is unset. The vision
model is stubbed throughout; it is exercised for real on the Mini.

## Not yet verified on hardware

Everything here is tested apart from the pieces that need the Mini: real Ollama
inference, PDF rendering against real scans, and Docker Compose startup on
macOS. Those need a pass on the machine itself.
