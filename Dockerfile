FROM python:3.9

WORKDIR /home/api

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./scripts ./scripts
COPY ./data ./data
COPY ./api ./api
COPY ./src ./src

ARG PORT=80
ARG HOST=0.0.0.0
ARG APP_MODULE=api.app:app
ARG WORKERS_PER_CORE=1

ENV MODE=production
ENV APP_MODULE=${APP_MODULE}
ENV WORKERS_PER_CORE=${WORKERS_PER_CORE}
ENV HOST=${HOST}
ENV PORT=${PORT}

#EXPOSE ${PORT}

ENTRYPOINT ["./scripts/start.sh" ]