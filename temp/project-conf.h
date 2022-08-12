#define LOG_CONF_LEVEL_RPL LOG_LEVEL_INFO
#define LOG_CONF_LEVEL_TCPIP LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_IPV6 LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_6LOWPAN LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_MAC LOG_LEVEL_INFO
#define TSCH_LOG_CONF_PER_SLOT 0
#define LINK_STATS_CONF_PACKET_COUNTERS 1
#define APP_SEND_INTERVAL_SEC 5
#define RPL_CONF_OF_OCP RPL_OCP_OF0
#define RPL_CONF_SUPPORTED_OFS {&rpl_of0, &rpl_mrhof}
#define APP_WARM_UP_PERIOD_SEC 300
#define TSCH_SCHEDULE_CONF_DEFAULT_LENGTH 11
#define SICSLOWPAN_CONF_FRAG 1
#define ENERGEST_CONF_ON 1
#define TSCH_CONF_DEFAULT_HOPPING_SEQUENCE TSCH_HOPPING_SEQUENCE_16_16
#define TSCH_CONF_MAC_MAX_FRAME_RETRIES 3
#define UIP_CONF_BUFFER_SIZE 200
#define TSCH_STATS_CONF_ON 1
#define TSCH_STATS_CONF_SAMPLE_NOISE_RSSI 1