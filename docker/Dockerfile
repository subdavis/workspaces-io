FROM node:latest as builder
WORKDIR /app

# Install dependencies
COPY client/package.json client/yarn.lock /app/
RUN yarn --frozen-lockfile
# Build
COPY client/ /app/
RUN yarn build

FROM python:3.8-slim as runtime

ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]

EXPOSE 8100
WORKDIR /app

# Install dependencies
COPY ./setup.py /app/
RUN pip install --no-cache-dir .

# Add init scripts
COPY docker/startup.sh /app/startup.sh

# Install modules
COPY ./workspacesio /app/workspacesio
RUN pip install --no-deps .

# Copy over frontend from builder
COPY --from=builder /app/dist/ /app/static/

CMD ["/app/startup.sh"]
