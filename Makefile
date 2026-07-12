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
	  'prepper-box make targets' \
	  '' \
	  'Usage:' \
	  '  make <target> [VAR=value ...]' \
	  '' \
	  'Core targets:' \
	  '  homepage-build     Rebuild services/homepage/services.yaml from services/homepage/sections/*.yaml' \
	  '  deploy-homepage    Build Homepage, then rsync the Homepage config set to $(DEPLOY_HOST):$(DEPLOY_PATH)' \
	  '  backup             Create a tar.gz snapshot of repo-tracked files and unignored working-tree files' \
	  '  restore            Extract a tar.gz snapshot into the repo tree or another directory' \
	  '  backup-list        List the contents of a snapshot archive' \
	  '' \
	  'Common variables:' \
	  '  ARCHIVE            Archive path for backup / restore / backup-list' \
	  '  DEST               Restore destination directory (default: repo root)' \
	  '  DEPLOY_HOST        SSH target used by deploy-homepage' \
	  '  DEPLOY_PATH        Remote Homepage directory used by deploy-homepage' \
	  '  HOMEPAGE_SECTIONS  Directory containing Homepage fragments' \
	  '  HOMEPAGE_OUTPUT    Generated Homepage services file path' \
	  '' \
	  'Examples:' \
	  '  make homepage-build' \
	  '  make deploy-homepage' \
	  '  make backup ARCHIVE=/tmp/prepper-box.tar.gz' \
	  '  make restore ARCHIVE=/tmp/prepper-box.tar.gz DEST=/tmp/prepper-box-restore' \
	  '  make backup-list ARCHIVE=/tmp/prepper-box.tar.gz'

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
