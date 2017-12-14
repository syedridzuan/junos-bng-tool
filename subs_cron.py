"""Module that handle xml parsing."""
import csv
from datetime import datetime
from collections import defaultdict
import utils
from jnpr.junos import Device, exception
from datetime import datetime
import argparse

parse_item = {
    'user_name': "user-name",
    'access_type': "access-type",
    'interface': "interface",
    'ip_address': "ip-address",
    'ipv6_user_prefix': "ipv6-user-prefix",
    'profile': 'profile',
    'session_id': 'session-id',
    'state': 'state',
    'login_time': 'login-time',
    'routing_instance': 'routing-instance',
    'mac_address': 'mac-address',
    'agent_circuit_id': 'agent-circuit-id'
}


def main():
    """Main program."""
    # Create writer for duplicate csv

    timestamp = datetime.now().strftime('%m-%d-%Y-%H-%M-%S')

    args = create_arg()
    dev = connect(args.host, args.username, args.password, args.port)
    print_basic_info(dev)
    dev.timeout = 300
    # start querying subs info via RPC
    query_msg = ("Querying subscribers information for client type {}, "
                 "Profile name {}, via RPC "
                 .format(args.client_type, args.profile_name))
    print(query_msg)
    result_xml = dev.rpc.get_subscribers(profile_name=args.profile_name,
                                         client_type=args.client_type,
                                         detail=True, normalize=True)
    print("Query completed")

    print("Reading csv file..")
    subscribers = result_xml.findall("subscriber")
    sub_def_dict = defaultdict(lambda: defaultdict(list))

    # iterate <subscriber>
    for subscriber in subscribers:
        user_name = subscriber.find('user-name').text
        get_user_def(parse_item, subscriber, user_name, sub_def_dict)

    dup_file_name = "/home/tmubuntu/subscriber/subs/" + args.output_dup_file + "-" + timestamp + ".csv"
    # Ceate writer for duplicate subs csv
    csvfile_dup = open(dup_file_name, 'w')
    dupwriter = csv.writer(csvfile_dup,
                           delimiter=',',
                           quotechar='"',
                           quoting=csv.QUOTE_ALL)

    # Ceate writer for all csv
    all_file_name = "/home/tmubuntu/subscriber/subs/" + args.output_all_file + "-" + timestamp + ".csv"
    csvfile_all = open(all_file_name, 'w')
    allwriter = csv.writer(csvfile_all,
                           delimiter=',',
                           quotechar='"',
                           quoting=csv.QUOTE_ALL)
    # write csv header
    header_list_all = sub_def_dict.itervalues().next().keys()
    header_list_dup = sub_def_dict.itervalues().next().keys()
    header_list_all.append("duplicate")
    header_list_dup.extend(["duplicate", "retain"])

    dupwriter.writerow(header_list_dup)
    allwriter.writerow(header_list_all)

    # iterate to find duplicate subscriber
    check_duplicate(sub_def_dict, allwriter, dupwriter)

    # close dev
    dev.close()

    # close the files
    csvfile_dup.close()
    csvfile_all.close()
    print_summary(sub_def_dict, subscribers)


def print_summary(sub_def_dict, subscribers):
    """Printing subscriber's summary."""
    print(utils.banner("Summary"))
    total_subs = len(subscribers)
    total_unique_sub = len(sub_def_dict)
    print("Total subscriber: {}").format(total_subs)
    print("Total unique subscriber: {}").format(total_unique_sub)
    print("Total duplicate "
          "subscriber:{}").format(total_subs - total_unique_sub)
    print(utils.banner("End of Summary"))


def check_duplicate(sub_def_dict, allwriter, dupwriter):
    """Check for duplicate subscriber."""
    print("Iterating all subscriber info, writing to csv file. "
          "And finding for duplicate subscriber")
    for key, value in sub_def_dict.iteritems():
        # if duplicate found write to allsubs & duplsub csv.
        if len(sub_def_dict[key]['user_name']) > 1:
            latest_sub_idx = check_latest_date(sub_def_dict[key]['login_time'])
            for idx, sub_flat_list in flat_dict(sub_def_dict[key]).items():
                # append duplicate is true
                sub_flat_list.append("True")
                # append retain = true if to retain
                allwriter.writerow(sub_flat_list)
                if idx == latest_sub_idx:
                    sub_flat_list.append("True")
                else:
                    sub_flat_list.append("False")
                dupwriter.writerow(sub_flat_list)
        # if no duplicate found write to allsubs csv.
        else:
            for _, sub_flat_list in flat_dict(sub_def_dict[key]).items():
                sub_flat_list.append("False")
                allwriter.writerow(sub_flat_list)


def get_user_def(parse_item, item, user_name, sub_def_dict):
    """Get subscriber information and return to dictionary."""
    for key, value in parse_item.items():
        try:
            sub_def_dict[user_name][key].append(item.find(value).text)
        except AttributeError:
            msg = ("Session id: {}, Missing value for: {}"
                   .format(item.find('session-id').text, value))
            print(msg)
            sub_def_dict[user_name][key].append("")


def check_latest_date(login_time):
    """Check the latest date, return index number for latest subs list."""
    login_time_list = []
    for item in login_time:
        login_time_list.append(datetime.strptime
                               (item.strip("MYT").
                                strip(), '%Y-%m-%d %H:%M:%S'))
    return login_time_list.index(max(login_time_list))


def flat_dict(item):
    """Flattern dict."""
    ax = defaultdict(list)
    for key, value in item.items():
        for idx, item in enumerate(value):
            ax[idx].append(item)
    return ax


def create_arg():
    """Create argument and pass the parser."""
    parser = argparse.ArgumentParser(description="Get subscribers "
                                     "information and check ")
    parser.add_argument('host', type=str,
                        help='host name or ip address')
    parser.add_argument('username', type=str,
                        help='Username')
    parser.add_argument('password', type=str,
                        help='Password')
    parser.add_argument('port', type=int,
                        help="RPC's Port")
    parser.add_argument('client_type', type=str,
                        help='Client type e.g pppoe')
    parser.add_argument('profile_name', type=str,
                        help='Profile name e.g RESIDENTIAL-PPPOE-PROFILE')
    parser.add_argument('output_all_file', type=str,
                        help="CSV's output file name for all subscriber \
                        e.g: result_ppoe.csv")
    parser.add_argument('output_dup_file', type=str,
                        help="CSV's output file name for duplicate subscriber \
                        e.g: result_ppoe_dup.csv")
    parser.add_argument("-v", "--verbose", help="Verbose mode",
                        action="store_true")
    return parser.parse_args()


def connect(host, user, password, port):
    """Connect to the router, get fact to verify and return the connection."""
    print("Connecting to {}, using username {}, "
          "via port {}").format(host, user, port)
    dev = Device(host=host, user=user, password=password, port=port)
    try:
        dev.open()
    except exception.ConnectUnknownHostError:
        print("Unknown host or host unreachable , "
              "please check your connection")
    except exception.ConnectAuthError:
        print("Wrong username/password supplied,"
              "please modify your username/password")
    except exception.ConnectRefusedError:
        print("RPC not enable on remote device, please enable RPC.")
    else:
        print("Connection to {} success").format(host)
        return dev


def print_basic_info(dev):
    """Print basic info."""
    facts = dev.facts
    print("Hostname: {}, Master RE: {}, "
          "Junos Version: {}").format(facts['hostname'],
                                      facts['master'], facts['version'])

if __name__ == "__main__":
    main()
