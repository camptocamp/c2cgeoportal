INSTANCE_ID = test

MOBILE = FALSE
#NGEO = TRUE
TILECLOUD_CHAIN = FALSE

REQUIREMENTS += -e /home/travis/build/camptocamp/c2cgeoportal
DISABLE_BUILD_RULES = test-packages

include test.mk

$(PACKAGE)/locale/$(PACKAGE)-db.pot:
	mkdir -p $(dir $@)
	touch $@
