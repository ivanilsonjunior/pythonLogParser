/*
 * Copyright (c) 2020, Institute of Electronics and Computer Science (EDI)
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 *
 * Author: Atis Elsts <atis.elsts@edi.lv>
 */

/* Logging */
#define LOG_CONF_LEVEL_RPL                         LOG_LEVEL_INFO
#define LOG_CONF_LEVEL_TCPIP                       LOG_LEVEL_NONE
#define LOG_CONF_LEVEL_IPV6                        LOG_LEVEL_NONE
#define LOG_CONF_LEVEL_6LOWPAN                     LOG_LEVEL_NONE
#define LOG_CONF_LEVEL_MAC                         LOG_LEVEL_INFO
/*#define LOG_CONF_LEVEL_FRAMER                      LOG_LEVEL_DBG*/
#define TSCH_LOG_CONF_PER_SLOT                     0

/* Enable printing of packet counters */
#define LINK_STATS_CONF_PACKET_COUNTERS          1


/* IEEE802.15.4 PANID */
#define IEEE802154_CONF_PANID 0x0DE1

/* Application settings */
#define APP_SEND_INTERVAL_SEC 1
#define APP_WARM_UP_PERIOD_SEC 300
#define RPL_CONF_OF_OCP RPL_OCP_OF0 /* tells to use OF0 for DAGs rooted at this node */
#define RPL_CONF_SUPPORTED_OFS {&rpl_of0, &rpl_mrhof} /* tells to compile in support for both OF0 and MRHOF */
/* TSCH SLOT FRAME*/
/* 6TiSCH schedule length */
#define TSCH_SCHEDULE_CONF_DEFAULT_LENGTH 19
#define TSCH_CONF_MAC_MAX_FRAME_RETRIES 3
#define TSCH_QUEUE_CONF_NUM_PER_NEIGHBOR 32
#define ENERGEST_CONF_ON 1

#define SICSLOWPAN_CONF_FRAG 1 /* No fragmentation */
#define UIP_CONF_BUFFER_SIZE 200
/*#define RPL_CONF_WITH_MC 1*/
/*#define RPL_CONF_DAG_MC RPL_DAG_MC_ETX*/
#define TSCH_STATS_CONF_ON 1
#define TSCH_STATS_CONF_SAMPLE_NOISE_RSSI 1 
