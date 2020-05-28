import socket
import time

import dns
import dns.resolver
from dnslib import DNSRecord, RR, DNSHeader, QTYPE, A

from cache import Cache


def cache_records(result, cache: Cache):
    for answer in result.response.answer:
        cache.put(str(answer.name),
                  [record.address for record in answer.items.keys()],
                  answer.ttl)
    for answer in result.response.additional:
        cache.put(str(answer.name),
                  [record.address for record in answer.items.keys()],
                  answer.ttl)


def handle_request(data, addr, sock: socket.socket, cache):
    question = DNSRecord.parse(data)
    reply = DNSRecord(DNSHeader(id=question.header.id, qr=1, aa=1, ra=1), q=question.q)
    name = str(question.q.qname)

    cache.update()
    if not cache.contains(name):
        try:
            result = dns.resolver.resolve(name, 'A')
        except:  # (dns.resolver.NXDOMAIN, dns.resolver.Timeout):
            sock.sendto(reply.pack(), addr)
            return

        cache_records(result, cache)

    ans = make_response(reply, cache, name)
    sock.sendto(ans, addr)


def make_response(reply, cache: Cache, name):
    ans = reply.reply()
    record = cache.get(name)
    for address in record.value:
        ans.add_answer(RR(name, QTYPE.A,
                          rdata=A(address),
                          ttl=record.ttl - int(time.time()) + record.time))
    return ans.pack()


def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', 53))

    cache = Cache('cache')

    while True:
        data, addr = sock.recvfrom(512)
        handle_request(data, addr, sock, cache)


if __name__ == '__main__':
    run()
