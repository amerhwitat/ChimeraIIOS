# SPDX-License-Identifier: GPL-3.0
#
# Aurora userspace install (Linux-style: DESTDIR staging, no hardcoded paths).
#
#   make all                 validate units and helper scripts
#   make install DESTDIR=... install units, sysusers/tmpfiles/dbus policy and helpers
#   make check               run the contract checks (also used by CI)

DESTDIR ?=
PREFIX ?= /usr
SYSTEMD_UNIT_DIR ?= $(PREFIX)/lib/systemd/system
USER_SYSTEMD_UNIT_DIR ?= $(PREFIX)/lib/systemd/user
SYSUSERS_DIR ?= $(PREFIX)/lib/sysusers.d
TMPFILES_DIR ?= $(PREFIX)/lib/tmpfiles.d
DBUS_DIR ?= $(PREFIX)/share/dbus-1/system.d
BINDIR ?= $(PREFIX)/local/bin
DOCDIR ?= $(PREFIX)/share/doc/aurora

UNITS := $(wildcard systemd/*.service systemd/*.target)
USER_UNITS := $(wildcard systemd/user/*.service)
HELPERS := bin/aurora-session bin/aurora-profile-apply bin/aurora-profile-set bin/aurora-network-wait bin/voiceconnect-broker

.PHONY: all install check uninstall help

help:
	@echo "Aurora userspace"
	@echo "  make all | install DESTDIR=... | check | uninstall"

all: check

$(SYSTEMD_UNIT_DIR):
	@mkdir -p $(DESTDIR)$(SYSTEMD_UNIT_DIR)

install:
	@install -d $(DESTDIR)$(SYSTEMD_UNIT_DIR) $(DESTDIR)$(SYSUSERS_DIR) \
		$(DESTDIR)$(TMPFILES_DIR) $(DESTDIR)$(DBUS_DIR) $(DESTDIR)$(BINDIR) $(DESTDIR)$(DOCDIR) \
		$(DESTDIR)$(USER_SYSTEMD_UNIT_DIR)
	@install -m 0644 $(UNITS) $(DESTDIR)$(SYSTEMD_UNIT_DIR)/
	@if [ -n "$(USER_UNITS)" ]; then install -m 0644 $(USER_UNITS) $(DESTDIR)$(USER_SYSTEMD_UNIT_DIR)/; fi
	@install -m 0644 sysusers/aurora.conf $(DESTDIR)$(SYSUSERS_DIR)/
	@install -m 0644 tmpfiles/aurora.conf $(DESTDIR)$(TMPFILES_DIR)/
	@install -m 0644 dbus/aurora.conf $(DESTDIR)$(DBUS_DIR)/aurora.conf
	@install -m 0755 $(HELPERS) $(DESTDIR)$(BINDIR)/
	@install -m 0644 README.md $(DESTDIR)$(DOCDIR)/README.md
	@install -d $(DESTDIR)$(SYSTEMD_UNIT_DIR)/graphical.target.wants \
		$(DESTDIR)$(SYSTEMD_UNIT_DIR)/multi-user.target.wants \
		$(DESTDIR)$(USER_SYSTEMD_UNIT_DIR)/default.target.wants
	@ln -sfn ../aurora.target $(DESTDIR)$(SYSTEMD_UNIT_DIR)/graphical.target.wants/aurora.target
	@ln -sfn ../aurora-network.service $(DESTDIR)$(SYSTEMD_UNIT_DIR)/multi-user.target.wants/aurora-network.service
	@ln -sfn ../aurora-polkit-agent.service $(DESTDIR)$(USER_SYSTEMD_UNIT_DIR)/default.target.wants/aurora-polkit-agent.service
	@echo "  INSTALL units -> $(DESTDIR)$(SYSTEMD_UNIT_DIR)"

check:
	@python3 scripts/check_units.py --units systemd --helpers bin

uninstall:
	@for u in $(UNITS); do rm -f $(DESTDIR)$(SYSTEMD_UNIT_DIR)/$$(basename $$u); done
	@rm -f $(DESTDIR)$(SYSUSERS_DIR)/aurora.conf $(DESTDIR)$(TMPFILES_DIR)/aurora.conf
	@rm -f $(DESTDIR)$(DBUS_DIR)/aurora.conf
	@for h in $(HELPERS); do rm -f $(DESTDIR)$(BINDIR)/$$(basename $$h); done
	@echo "  UNINSTALL aurora userspace"
