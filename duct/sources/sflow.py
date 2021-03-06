"""
.. module:: sflow
   :platform: Unix
   :synopsis: A source module which provides an sflow collector

.. moduleauthor:: Colin Alston <colin@imcol.in>
"""

import time

from twisted.internet import reactor

from zope.interface import implementer

from duct.interfaces import IDuctSource
from duct.objects import Source
from duct import utils

from duct.protocol.sflow import server
from duct.protocol.sflow.protocol import flows


class sFlowReceiver(server.DatagramReceiver):
    """sFlow datagram protocol
    """
    def __init__(self, source):
        self.source = source
        self.lookup = source.config.get('dnslookup', True)
        self.counterCache = {}
        self.convoQueue = {}

        self.resolver = utils.Resolver()

    def process_convo_queue(self, queue, host, idx, deltaIn, tDelta):
        """Process the conversation queue
        """
        addr = {'dst':{}, 'src': {}}
        port = {'dst':{}, 'src': {}}

        btotal = 0

        # Try and aggregate chunks of flow information into something that
        # is actually useful in Riemann and InfluxDB.
        for convo in queue:
            src, sport, dst, dport, cbytes = convo

            if not src in addr['src']:
                addr['src'][src] = 0

            if not dst in addr['dst']:
                addr['dst'][dst] = 0

            btotal += cbytes
            addr['src'][src] += cbytes
            addr['dst'][dst] += cbytes

            if not sport in port['src']:
                port['src'][sport] = 0

            if not dport in port['dst']:
                port['dst'][dport] = 0

            port['src'][sport] += cbytes
            port['dst'][dport] += cbytes

        for direction, v in addr.items():
            for ip, cbytes in v.items():
                m = ((cbytes/float(btotal)) * deltaIn)/tDelta

                self.source.queueBack(
                    self.source.createEvent(
                        'ok',
                        'sFlow if:%s addr:%s inOctets/sec %0.2f' % (idx,
                                                                    ip, m),
                        m,
                        prefix='%s.ip.%s.%s' % (idx, ip, direction),
                        hostname=host
                    )
                )

        for direction, v in port.items():
            for port, cbytes in v.items():
                m = ((cbytes/float(btotal)) * deltaIn)/tDelta

                if port:
                    self.source.queueBack(
                        self.source.createEvent(
                            'ok',
                            'sFlow if:%s port:%s inOctets/sec %0.2f' % (idx,
                                                                        port,
                                                                        m),
                            m,
                            prefix='%s.port.%s.%s' % (idx, port, direction),
                            hostname=host
                        )
                    )

    def receive_flow(self, flow, sample, host):
        def queueFlow(host):
            """Queue the incomming flows per host
            """
            if isinstance(sample, flows.IPv4Header):
                if sample.ip.proto in ('TCP', 'UDP'):
                    sport, dport = (sample.ip_sport, sample.ip_dport)
                else:
                    sport, dport = (None, None)

                src, dst = (sample.ip.src.asString(), sample.ip.dst.asString())
                cbytes = sample.ip.total_length

                if not host in self.convoQueue:
                    self.convoQueue[host] = {}

                if not flow.if_inIndex in self.convoQueue[host]:
                    self.convoQueue[host][flow.if_inIndex] = []

                self.convoQueue[host][flow.if_inIndex].append(
                    (src, sport, dst, dport, cbytes))

        if self.lookup:
            return self.resolver.reverse(host).addCallback(
                queueFlow).addErrback(queueFlow)
        else:
            return queueFlow(host)

    def receive_counter(self, counter, host):
        def _hostcb(host):
            idx = counter.if_index

            if not host in self.convoQueue:
                self.convoQueue[host] = {}

            if not host in self.counterCache:
                self.counterCache[host] = {}

            if idx in self.counterCache[host]:
                lastIn, lastOut, lastT = self.counterCache[host][idx]
                tDelta = time.time() - lastT

                self.counterCache[host][idx] = (
                    counter.if_inOctets, counter.if_outOctets, time.time())

                deltaOut = counter.if_outOctets - lastOut
                deltaIn = counter.if_inOctets - lastIn

                inRate = deltaIn / tDelta
                outRate = deltaOut / tDelta

                # Grab the queue for this interface
                if idx in self.convoQueue[host]:
                    queue = self.convoQueue[host][idx]
                    self.convoQueue[host][idx] = []
                    self.process_convo_queue(queue, host, idx, deltaIn, tDelta)

                self.source.queueBack([
                    self.source.createEvent(
                        'ok',
                        'sFlow index %s inOctets/sec %0.2f' % (idx, inRate),
                        inRate,
                        prefix='%s.inOctets' % idx, hostname=host
                    ),
                    self.source.createEvent(
                        'ok',
                        'sFlow index %s outOctets/sec %0.2f' % (idx, outRate),
                        outRate,
                        prefix='%s.outOctets' % idx, hostname=host
                    ),
                ])

            else:
                self.counterCache[host][idx] = (
                    counter.if_inOctets, counter.if_outOctets, time.time())

        if self.lookup:
            return self.resolver.reverse(host).addCallback(
                _hostcb).addErrback(_hostcb)
        else:
            return _hostcb(host)

@implementer(IDuctSource)
class sFlow(Source):
    """Provides an sFlow server Source

    **Configuration arguments:**

    :param port: UDP port to listen on
    :type port: int.
    :param dnslookup: Enable reverse DNS lookup for device IPs (default: True)
    :type dnslookup: bool.

    **Metrics:**

    Metrics are published using the key patterns
    (device).(service name).(interface).(in|out)Octets
    (device).(service name).(interface).ip
    (device).(service name).(interface).port
    """

    def get(self):
        pass

    def startTimer(self):
        """Creates a sFlow datagram server
        """
        reactor.listenUDP(self.config.get('port', 6343), sFlowReceiver(self))
