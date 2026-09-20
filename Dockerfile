FROM python:3.12-slim
WORKDIR /app
COPY groundwork/ ./groundwork/
COPY tests/ ./tests/
RUN python -m unittest discover -s tests
VOLUME ["/data", "/repos"]
ENV GW_DB=/data/groundwork.db
EXPOSE 8765
CMD ["sh", "-c", "python -m groundwork --db $GW_DB init && python -m groundwork --db $GW_DB serve --host 0.0.0.0 --port 8765"]
