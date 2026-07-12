# Kiwix Connector

Local OpenAPI tool for Open WebUI that searches the Ubuntu box’s offline Kiwix library.

## Live service

- Base URL: `http://10.1.10.140:3003/`
- OpenAPI spec: `http://10.1.10.140:3003/openapi.json`
- Health check: `http://10.1.10.140:3003/health`

## What it does

- searches the local Kiwix mirror using the live `/search?pattern=...` endpoint
- fetches article text from the mirrored content pages
- returns JSON that Open WebUI can consume as a tool

## Main endpoints

- `GET /search?pattern=...&limit=...`
- `GET /lookup?pattern=...`
- `GET /page?url=...`

## Open WebUI import

Import the tool using the OpenAPI URL above from Workspace → Tools.

If Open WebUI runs in the container on this same host, `host.docker.internal:3003` should also reach the service from inside the container.
