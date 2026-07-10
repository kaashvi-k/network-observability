FROM debian:bookworm-slim

# Install a current, full-featured Net-SNMP agent
RUN apt-get update && \
    apt-get install -y snmpd	 && \
    apt-get clean

# Our config will be bind-mounted in at runtime, same as before
EXPOSE 161/udp

# Run snmpd in the foreground (containers need a process to stay alive;
# the real snmpd normally daemonizes/backgrounds itself, which would
# make Docker think the container exited immediately)
CMD ["snmpd", "-f", "-Lo"]
