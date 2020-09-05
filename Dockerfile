FROM node:latest as builder
WORKDIR /app

# Install dependencies
COPY client/package.json client/yarn.lock /app/
RUN yarn --frozen-lockfile
# Build
COPY client/ /app/
RUN yarn build

FROM python:3.8-slim as runtime

EXPOSE 8000
WORKDIR /app

# Install dependencies
COPY ./setup.py /app/
RUN pip install --no-cache-dir .
# Build
COPY startup.sh /app/startup.sh
COPY ./workspacesio /app/workspacesio
RUN pip install --no-deps .

COPY --from=builder /app/dist/ /app/static/

CMD ["/app/startup.sh"]
