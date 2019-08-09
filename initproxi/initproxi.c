/* SPDX-License-Identifier: (GPL-2.0-only OR BSD-3-Clause) */
/*
 * Based on https://github.com/linux-can/can-utils/blob/master/candump.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <string.h>
#include <ctype.h>
#include <libgen.h>
#include <time.h>
#include <errno.h>

#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/uio.h>
#include <net/if.h>

#include <linux/can.h>
#include <linux/can/raw.h>

#include "lib.h"

int main(int argc, char **argv)
{
    static __u32 dropcnt;
    static __u32 last_dropcnt;
    const int canfd_on = 1;
    static volatile int running = 1;

	fd_set rdfs;
	int s;
	int count = 500; // candump -n
	int ret;
	char *devname;
	struct sockaddr_can addr;
	char ctrlmsg[CMSG_SPACE(sizeof(struct timeval) + 3*sizeof(struct timespec) + sizeof(__u32))];
	struct iovec iov;
	struct msghdr msg;
	struct cmsghdr *cmsg;
	struct canfd_frame frame;
	int nbytes, maxdlen;
	struct ifreq ifr;
	struct timeval timeout, timeout_config = { 0, 0 }, *timeout_current = NULL;

    timeout_config.tv_usec = 3000; // candump -T
    timeout_config.tv_sec = timeout_config.tv_usec / 1000;
    timeout_config.tv_usec = (timeout_config.tv_usec % 1000) * 1000;
    timeout_current = &timeout;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <device>\n", argv[0]);
        return 1;
    }

    devname = argv[1];

    s = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (s < 0) {
        perror("socket");
        return 1;
    }

    nbytes = strlen(devname);
    addr.can_family = AF_CAN;

    memset(&ifr.ifr_name, 0, sizeof(ifr.ifr_name));
    strncpy(ifr.ifr_name, devname, nbytes);

    if (ioctl(s, SIOCGIFINDEX, &ifr) < 0) {
        perror("SIOCGIFINDEX");
        exit(1);
    }
    addr.can_ifindex = ifr.ifr_ifindex;

    /* try to switch the socket into CAN FD mode */
    setsockopt(s, SOL_CAN_RAW, CAN_RAW_FD_FRAMES, &canfd_on, sizeof(canfd_on));

    if (bind(s, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }

	/* these settings are static and can be held out of the hot path */
	iov.iov_base = &frame;
	msg.msg_name = &addr;
	msg.msg_iov = &iov;
	msg.msg_iovlen = 1;
	msg.msg_control = &ctrlmsg;

	while (running) {
		FD_ZERO(&rdfs);
        FD_SET(s, &rdfs);

		if (timeout_current)
			*timeout_current = timeout_config;

		if ((ret = select(s+1, &rdfs, NULL, NULL, timeout_current)) <= 0) {
			running = 0;
			continue;
		}

        if (FD_ISSET(s, &rdfs)) {
            /* these settings may be modified by recvmsg() */
            iov.iov_len = sizeof(frame);
            msg.msg_namelen = sizeof(addr);
            msg.msg_controllen = sizeof(ctrlmsg);
            msg.msg_flags = 0;

            nbytes = recvmsg(s, &msg, 0);

            if (nbytes < 0) {
                if ((errno == ENETDOWN)) {
                    fprintf(stderr, "%s: interface down\n", devname);
                    continue;
                }
                perror("read");
                return 1;
            }

            if ((size_t)nbytes == CAN_MTU)
                maxdlen = CAN_MAX_DLEN;
            else if ((size_t)nbytes == CANFD_MTU)
                maxdlen = CANFD_MAX_DLEN;
            else {
                fprintf(stderr, "read: incomplete CAN frame\n");
                return 1;
            }

            if (count && (--count == 0))
                running = 0;


            for (cmsg = CMSG_FIRSTHDR(&msg);
                 cmsg && (cmsg->cmsg_level == SOL_SOCKET);
                 cmsg = CMSG_NXTHDR(&msg,cmsg)) {
                if (cmsg->cmsg_type == SO_RXQ_OVFL)
                    memcpy(&dropcnt, CMSG_DATA(cmsg), sizeof(__u32));
            }

            /* check for (unlikely) dropped frames on this specific socket */
            if (dropcnt != last_dropcnt) {

                __u32 frames = dropcnt - last_dropcnt;
                printf("DROPCOUNT: dropped %d CAN frame%s on '%s' socket (total drops %d)\n",
                       frames, (frames > 1)?"s":"", devname, dropcnt);

                last_dropcnt = dropcnt;
            }

            if ((frame.can_id & CAN_EFF_MASK) == 0x1E114003) {
                struct canfd_frame out;
                int required_mtu = parse_canframe("1E114021#362630045880", &out);
                if (write(s, &out, required_mtu) != required_mtu) {
                    perror("write");
                    return 1;
                } else {
                    printf("PROXI correctly answered!\n");
                }

                fprint_long_canframe(stdout, &frame, NULL, 0, maxdlen);
                printf("\n");
            }

            if ((frame.can_id & CAN_EFF_MASK) == 0x0E094003) {
                struct canfd_frame out;
                int required_mtu = parse_canframe("0E094021#000E", &out);
                if (write(s, &out, required_mtu) != required_mtu) {
                    perror("write");
                    return 1;
                } else {
                    printf("Status correctly answered!\n");
                }

                fprint_long_canframe(stdout, &frame, NULL, 0, maxdlen);
                printf("\n");
            }
        }

        fflush(stdout);
	}

    close(s);
	return 0;
}
