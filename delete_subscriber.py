#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""Class to delete subscriber.

This class will read subsciber information from csv file
generate by subsciber.py and will delete
subsciber from the router if the column set to
duplicate = True and retain = False

"""
import argparse
import csv
from jnpr.junos import Device
from delete import DeleteSubscriber


def main():
    """Main program."""
    # Create writer for duplicate csv
    args = create_arg()
    dev = dev = Device(host=args.host, user=args.username,
                       password=args.password, port=args.port)
    dev.open()
    delete_subs = DeleteSubscriber(dev)
    for item in parse_csv_input_file(args.delete_input_file):
        if item['duplicate'] == "True" and item['retain'] == "False":
            print("delete subscriber: {}, session-id: {}, "
                  "inteface: {}").format(item['user_name'],
                                         item['session_id'],
                                         item['interface'])
            delete_subs.set_subsriber(sub_int=item['interface'])
            delete_subs.delete_interface()
    dev.close()


def create_arg():
    """Create argument and pass the parser."""
    parser = argparse.ArgumentParser(description="Delete subscriber "
                                     "from given csv file ")
    parser.add_argument('host', type=str,
                        help='host name or ip address')
    parser.add_argument('username', type=str,
                        help='Username')
    parser.add_argument('password', type=str,
                        help='Password')
    parser.add_argument('port', type=int,
                        help="RPC's Port")
    parser.add_argument('delete_input_file', type=str,
                        help="CSV's output file name for duplicate subscriber \
                        e.g: result_ppoe_dup.csv")
    parser.add_argument("-v", "--verbose", help="Verbose mode",
                        action="store_true")
    return parser.parse_args()


def parse_csv_input_file(input_file):
    """Parse input csv file."""
    with open(input_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for item in reader:
            dict = {i: x for i, x in item.items()}
            yield(dict)


if __name__ == "__main__":
    main()

