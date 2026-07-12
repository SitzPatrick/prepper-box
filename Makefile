SHELL := /bin/bash
PYTHON ?= python3
REPO_ROOT := $(abspath .)
HOMEPAGE_SECTIONS ?= services/homepage/sections
HOMEPAGE_OUTPUT ?= services/homepage/services.yaml
DEPLOY_HOST ?= patrick@10.1.10.140
DEPLOY_PATH ?= /srv/homepage
ARCHIVE ?= prepper-box-configs.tar.gz
DEST ?= $(REPO_ROOT)
RSYNC ?= rsync

.PHONY: help homepage-build deploy-homepage backup restore backup-list

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make homepage-build          Render services/homepage/services.yaml from sections/' \
	  '  make deploy-homepage         Build and sync Homepage files to $(DEPLOY_HOST):$(DEPLOY_PATH)' \
	  '  make backup ARCHIVE=...      Create a tar.gz of tracked repo files' \
	  '  make restore ARCHIVE=...     Extract a tar.gz back into the repo tree' \
	  '  make backup-list ARCHIVE=... List archive contents'

homepage-build:
	$(PYTHON) scripts/render-homepage.py --sections $(HOMEPAGE_SECTIONS) --output $(HOMEPAGE_OUTPUT)

deploy-homepage: homepage-build
	$(RSYNC) -av \
	  $(HOMEPAGE_OUTPUT) \
	  services/homepage/bookmarks.yaml \
	  services/homepage/settings.yaml \
	  services/homepage/widgets.yaml \
	  services/homepage/custom.css \
	  services/homepage/custom.js \
	  services/homepage/docker.yaml \
	  services/homepage/kubernetes.yaml \
	  services/homepage/proxmox.yaml \
	  $(DEPLOY_HOST):$(DEPLOY_PATH)/

backup:
	$(PYTHON) scripts/box-configs.py backup $(ARCHIVE) --root $(REPO_ROOT)

restore:
	$(PYTHON) scripts/box-configs.py restore $(ARCHIVE) --dest $(DEST)

backup-list:
	$(PYTHON) scripts/box-configs.py list $(ARCHIVE)
