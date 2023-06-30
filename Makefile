CONTIKI_PROJECT = node
all: $(CONTIKI_PROJECT)

PLATFORMS_EXCLUDE = sky nrf52dk native

CONTIKI=../..

MAKE_MAC = MAKE_MAC_TSCH
#MAKE_MAC = MAKE_MAC_CSMA
#MAKE_ROUTING = MAKE_ROUTING_RPL_CLASSIC
MAKE_ROUTING = MAKE_ROUTING_RPL_LITE

# Energy usage estimation
MODULES += os/services/simple-energest
#MODULES += os/services/orchestra
#ORCHESTRA_EXTRA_RULES = &unicast_per_neighbor_rpl_ns

include $(CONTIKI)/Makefile.dir-variables
include $(CONTIKI)/Makefile.include

