#!/usr/bin/env python

"""
The module will ping subscriber from given csv list.
 and write the result to csv file.
"""

from jnpr.junos import Device, exception
import csv
from lxml import etree
import jxmlease
import argparse
import sys


def main():
    """Main Program"""
    args = create_arg()
    csvfile = open(args.ping_result_file, 'w')
    fieldnames = ['user-name', 'session-id', 'ip-address',
                  'probes-sent', 'responses-received', 'packet-loss',
                  'rtt-minimum', 'rtt-average', 'rtt-maximum', 'rtt-stddev']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    parser = jxmlease.EtreeParser()
    dev = connect(args.host, args.username,
                  args.password, args.port)

    for item in parse_csv_input_file(args.ping_input_file):
        if item['ip_address']:
            ping_result = parser(do_ping(dev, item['ip_address'],
                                 item['routing_instance'],
                                 args.count, args.rapid))
            ping_ok, parse_summmary_dict = parse_summary(ping_result)
            if ping_ok:
                print_summary(parse_summmary_dict)
                # add username & ip address to dict.
                parse_summmary_dict['user-name'] = item['user_name']
                parse_summmary_dict['session-id'] = item['session_id']
                parse_summmary_dict['ip-address'] = item['ip_address']

                writer.writerow(parse_summmary_dict)
            else:
                print("Ping failed to this session: {} reason: "
                      "{}").format(item['session_id'],
                                   parse_summmary_dict.strip())
        else:
            print(parse_summmary_dict)
            print("Skipping session-id: {} "
                  "for missing ip address".format(item['session_id']))

    # close dev
    dev.close()

    # close csv file
    csvfile.close()


def connect(host, user, password, port):
    """Connect to the router, get fact to verify and return the connection."""
    msg = "Connecting to {}, username: {},port: {}".format(host,
                                                           user,
                                                           port)
    print(msg)
    dev = Device(host=host, user=user, password=password, port=port)
    try:
        dev.open()
    except exception.ConnectUnknownHostError:
        print("Unknown host or host unreachable "
              "please check your connection")
        return False
    except exception.ConnectAuthError:
        print("Wrong username/password supplied, "
              "please modify your username/password")
        return False
    except exception.ConnectRefusedError:
        print("RPC not enable on remote device, please enable RPC.")
        return False
    else:
        print("Connection to {} success").format(host)
        return dev


def create_arg():
    """Create argument and pass the parser."""
    parser = argparse.ArgumentParser(description="Ping subscriber list "
                                     "and write result to csv file ")
    parser.add_argument('host',
                        type=str,
                        help='host name or ip address')
    parser.add_argument('username',
                        type=str,
                        help='Username')
    parser.add_argument('password',
                        type=str,
                        help='Password')
    parser.add_argument('port',
                        type=int,
                        help="RPC's Port")
    parser.add_argument('count',
                        type=str,
                        help='Count Request, Number of ping request')
    parser.add_argument('ping_input_file',
                        type=str,
                        help="CSV's input file for the list of \
                        subscriber to be ping, e.g ping_sub_list.csv")
    parser.add_argument('ping_result_file',
                        type=str,
                        help="CSV's output file for ping result \
                        e.g: ping_result.csv")
    parser.add_argument("-r", "--rapid",
                        help="Rapid Ping",
                        action="store_true")
    parser.add_argument("-v", "--verbose",
                        help="Verbose mode",
                        action="store_true")
    return parser.parse_args()


def print_basic_info(dev):
    """Print router's basic info."""
    facts = dev.facts
    print("Hostname: {}, Master RE: {}, "
          "Junos Version: {}").format(facts['hostname'],
                                      facts['master'],
                                      facts['version'])


def print_summary(ping_summary):
    """Print ping's summary."""
    print("{} packets transmitted, {} packets received, "
          "{}% packet loss").format(ping_summary['probes-sent'],
                                    ping_summary['responses-received'],
                                    ping_summary['packet-loss'])
    if int(ping_summary['packet-loss']) != 100:
        print("round-trip min/avg/max/stddev = {}/{}/{}/{} "
              "ms").format(float(ping_summary['rtt-minimum']) / 1000,
                           float(ping_summary['rtt-average']) / 1000,
                           float(ping_summary['rtt-maximum']) / 1000,
                           float(ping_summary['rtt-stddev']) / 1000)


def do_ping(dev, ip_address, routing_instance, count, rapid):
    """Execute ping command and return the result."""
    if routing_instance != "default":
        print("Ping host:{}, routing instance of {}, "
              "count of {}, rapid = {}").format(ip_address, routing_instance,
                                                count, rapid)
        ping_result = dev.rpc.ping(host=ip_address,
                                   routing_instance=routing_instance,
                                   count=count, rapid=rapid,
                                   normalize=True)
    else:
        print("Ping host:{}, count of {}, rapid = {}").format(ip_address,
                                                              count, rapid)
        ping_result = dev.rpc.ping(host=ip_address,
                                   count=count, rapid=rapid,
                                   normalize=True)
    # print(etree.tostring(ping_result, pretty_print=True))
    return ping_result


def parse_summary(result_dict):
    """Parsing ping summary result."""
    try:
        summary = result_dict['ping-results']['probe-results-summary']
    except KeyError:
        error_msg = result_dict['ping-results']['rpc-error']['error-message']
        return False, error_msg
    else:
        ping_summary_dict = {i: x for i, x in summary.items()}
        return True, ping_summary_dict


def parse_detail(result_dict):
    """Parse ping result into dictionary."""
    ping_result_dict = {}
    try:
        for probe_result in result_dict['ping-results']['probe-result']:
            ping_result_dict = {i: x for i, x in probe_result.items()}
    except KeyError:
        error_message = result_dict['ping-results']['rpc-error']['error-message']
        return False, error_message
    else:
        return True, ping_result_dict


def parse_csv_input_file(input_file):
    """Parse input csv file."""
    with open(input_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for item in reader:
            dict = {i: x for i, x in item.items()}
            yield(dict)

if __name__ == "__main__":
    main()
