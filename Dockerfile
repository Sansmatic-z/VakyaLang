FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml MANIFEST.in README.md LICENSE NOTICE LICENSE_AGPL LICENSE_APACHE ./
COPY runtime ./runtime
COPY sansmatic ./sansmatic
COPY atmalipi ./atmalipi
COPY sanskrit_coder ./sanskrit_coder
COPY examples ./examples
COPY tests ./tests
COPY vak.py ./
COPY vpm.py ./
COPY master_test.py ./
COPY .env.example ./

RUN python -m pip install --upgrade pip && \
    python -m pip install .

CMD ["python", "master_test.py"]
