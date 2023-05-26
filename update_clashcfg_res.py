#!/usr/bin/env python3
# _*_ coding: UTF-8 _*_

import argparse
import clashcfgutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--cfg_dir", dest="cfg_dir", required=True, help="configuration directory")
    parser.add_argument("-f", "--profile_dir", dest="profile_dir", required=True, help="profile directory")
    parser.add_argument("-n", "--profile_name", dest="profile_name", required=True, help="profile name")
    parser.add_argument("--is_cfw", dest="is_cfw", action="store_true", help="is Clash for Windows")
    parser.add_argument("-p", "--proxy", dest="proxy", help="proxy")
    parser.add_argument("-i", "--timeout", dest="timeout", help="timeout for network requests")
    parser.add_argument("-r", "--rule", dest="does_update_rules", action="store_true", help="does update rules")
    parser.add_argument("-u", "--url", dest="profile_url", help="profile_url")
    parser.add_argument("-t", "--tun_dir", dest="tun_dir", help="tun dir")
    args = parser.parse_args()

    sections = ["proxy-providers"]
    if args.does_update_rules:
        sections.append("rule-providers")
    net_res = clashcfgutil.update_res(sections, args.cfg_dir, args.profile_dir, profile_name=args.profile_name, profile_url=args.profile_url, \
                         proxy=args.proxy, timeout=args.timeout, is_cfw=args.is_cfw)
    if len(net_res) == 0:
        return 1

    if args.tun_dir:
        # ## updated files
        updated_files = [x[1] for x in net_res]

        # ## install updated files to <tun_dir>
        src_cfg_dir = args.cfg_dir
        dest_cfg_dir = args.tun_dir
        clashcfgutil.install_proxy_providers(updated_files, src_cfg_dir, dest_cfg_dir)
        print(f'Installed updated files {updated_files} from "{src_cfg_dir}" to "{dest_cfg_dir}"')
        
if __name__ == "__main__":
    main()