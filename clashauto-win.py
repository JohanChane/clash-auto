#!/usr/bin/env python3
# _*_ coding: UTF-8 _*_

import os, sys, subprocess, shutil, configparser
sys.path.append(".")
from enum import Enum
import ruamel.yaml
import requests
from clashautoutil import ClashUtil

# ## Global Vars
SCRIPT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(SCRIPT_PATH, "data")
CLASH_CFG_DIR = os.path.join(SCRIPT_PATH, "clash_config")
PROFILE_DIR = os.path.join(DATA_DIR, "profiles")
TPL_DIR = os.path.join(DATA_DIR, "tpl")

BASIC_CLASH_CONFIG_PATH = os.path.join(DATA_DIR, "basic_clash_config.yaml")
FINAL_CLASH_CONFIG_PATH = os.path.join(SCRIPT_PATH, "final_clash_config.yaml")
CLASHAUTO_CONFIG_PATH = os.path.join(DATA_DIR, "config.ini")
PROXY_PROVIDERS_URL_PATH = os.path.join(TPL_DIR, "proxy_provider_urls")
CLASH_CORE = os.path.join(SCRIPT_PATH, "clash.exe")

TIMEOUT = 5
PATH_OF_UPDATE_CFG_RES = os.path.join(SCRIPT_PATH, "update_clashcfg_res.py")

def select(options):
    print("Please select an option:")
    for i, item in enumerate(options):
        print(i, item)

    try:
        choice = int(input("Enter your choice (num): "))
    except ValueError:
        choice = len(options)
    if choice < 0:
        choice = len(options)

    return choice

def get_file_names(dir_path):
    file_names = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    file_names.sort()
    return file_names

class ServerCmd(Enum):
    RESTART = 1
    STOP = 2
    CONFIG = 3
    INSTALL = 4
    UNINSTALL = 5
    TEST = 6

def clash_server_ctl(server_cmd):
    os.chdir(SCRIPT_PATH)

    cmd = ""
    if server_cmd == ServerCmd.RESTART:
        cmd = f"nssm.exe restart clash"
    elif server_cmd == ServerCmd.STOP:
        cmd = f"nssm.exe stop clash"
    elif server_cmd == ServerCmd.CONFIG:
        cmd = f"nssm.exe edit clash"
    elif server_cmd == ServerCmd.INSTALL:
        cmd = f'nssm.exe install clash "{CLASH_CORE}" -d "{CLASH_CFG_DIR}" -f "{FINAL_CLASH_CONFIG_PATH}"'
    elif server_cmd == ServerCmd.UNINSTALL:
        cmd = f"nssm.exe remove clash confirm"
    elif server_cmd == ServerCmd.TEST:
        cmd = f'{CLASH_CORE} -d "{CLASH_CFG_DIR}" -f "{FINAL_CLASH_CONFIG_PATH}" -t'
        print(cmd)

    os.system(cmd)

def win_system_proxy_ctl(enable, proxy=None):
    try:
        if enable:
            # Use reg command to enable the proxy with ProxyEnable = 1
            subprocess.run(["reg", "add", R"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "1", "/f"])
            subprocess.run(["reg", "add", R"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", "/v", "ProxyServer", "/t", "REG_SZ", "/d", proxy, "/f"])

            print("System proxy has been enabled.")
        else:
            # Use reg command to disable the proxy with ProxyEnable = 0
            subprocess.run(["reg", "add", R"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "0", "/f"])
            #subprocess.run(["reg", "delete", R"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", "/v", "ProxyServer", "/f"])

            print("System proxy has been disabled.")
    except Exception as e:
        print("Error occurred while configuring the system proxy:", str(e))

def main():
    os.chdir(SCRIPT_PATH)
    
    config = configparser.ConfigParser()
    config.read(CLASHAUTO_CONFIG_PATH)
    sc_host = config.get("main", "sc_host")

    with open(BASIC_CLASH_CONFIG_PATH, "r", encoding="utf-8") as f:
        basic_yaml_data = ruamel.yaml.safe_load(f)
    proxy = ClashUtil.get_proxy(basic_yaml_data)
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"})
    if proxy:
        protocol, address = proxy.split("://")
        session.proxies = {
            protocol: address
        }
    session.timeout = TIMEOUT

    clash_util = ClashUtil(session, CLASH_CFG_DIR, PROFILE_DIR, sc_host);

    options = ["update_final_config", "update_profile", "select_profile", \
               "restart_clash_service", "stop_clash_service", \
               "test_config", "create_yaml", \
               "tun_mode", "system_proxy", "uwp_loopback", \
               "config_clash_service", "install_clash_service", "uninstall_clash_service", \
               "restart_clash_auto", "exit"]
    while True:
        print()
        choice = select(options)
        if choice >= len(options):
            print("Invalid selection, please try again")
            continue
        choiced_option = options[choice]
        if choiced_option == "update_final_config":
            updated_res, no_update_res = clash_util.update_dep_net_res(FINAL_CLASH_CONFIG_PATH)
            print("updated_res:")
            [print(f'-   {s}, {i}') for s, r in updated_res.items() for i in r]
            print("no_update_res:")
            [print(f'-   {s}, {i}') for s, r in no_update_res.items() for i in r]

            clash_server_ctl(ServerCmd.RESTART)
        elif choiced_option == "update_profile":
            file_names = get_file_names(PROFILE_DIR)
            profiles = [f for f in file_names if not f.endswith("~")]
            profile_index = select(profiles)
            if profile_index >= len(profiles):
                print("backward")
                continue
            choiced_profile_name = profiles[profile_index]
            if choiced_profile_name.endswith("_url"):
                profile_name = choiced_profile_name[:-4] + ".yaml"
                profile_path = os.path.join(PROFILE_DIR, profile_name)

                urls = ClashUtil.extra_urls(os.path.join(PROFILE_DIR, choiced_profile_name))
                profile_url = ""
                if urls:
                    profile_url = "|".join(urls)
                out_url, out_content = clash_util.fetch_sub_url(profile_url)
                if out_content:
                    with open(profile_path, "wb") as f:
                        f.write(out_content)
                        print(f'Updated profile: "{profile_path}", "{out_url}"')
                else:
                    print(f'Failed to update profile: out_url="{out_url}"')
                    print("backward")
                    continue
            else:
                profile_name = choiced_profile_name
                profile_path = os.path.join(PROFILE_DIR, profile_name)

            sections = ["proxy-providers", "rule-providers"]
            updated_res, no_update_res = clash_util.update_dep_net_res(profile_path, sections)
            print("updated_res:")
            [print(f'-   {s}, {i}') for s, r in updated_res.items() for i in r]
            print("no_update_res:")
            [print(f'-   {s}, {i}') for s, r in no_update_res.items() for i in r]
        
        elif choiced_option == "select_profile":
            file_names = get_file_names(PROFILE_DIR)
            profiles = [f for f in file_names if not f.endswith("~") and not f.endswith("_url")]
            profile_index = select(profiles)
            if profile_index >= len(profiles):
                print("backward")
                continue
            choiced_profile_name = profiles[profile_index]
            profile_name = choiced_profile_name
            
            profile_path = os.path.join(PROFILE_DIR, profile_name)
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_yaml_data = ruamel.yaml.safe_load(f)
            merged_yaml_data = ClashUtil.merge_profile(basic_yaml_data, profile_yaml_data)
            with open(FINAL_CLASH_CONFIG_PATH, "w", encoding="utf-8", newline="") as f:
                ruamel.yaml.round_trip_dump(merged_yaml_data, f)
            print(f'Merged "{BASIC_CLASH_CONFIG_PATH}" and "{profile_path}" into "{FINAL_CLASH_CONFIG_PATH}"')

            tun_mode = config.getboolean("main", "tun_mode", fallback=None)
            if tun_mode:
                ClashUtil.tun_ctl(enable=True, config_path=FINAL_CLASH_CONFIG_PATH)
            else:
                ClashUtil.tun_ctl(enable=False, config_path=FINAL_CLASH_CONFIG_PATH)
            clash_server_ctl(ServerCmd.RESTART)

        elif choiced_option == "restart_clash_service":
            clash_server_ctl(ServerCmd.RESTART)
        elif choiced_option == "stop_clash_service":
            clash_server_ctl(ServerCmd.STOP)
        elif choiced_option == "config_clash_service":
            clash_server_ctl(ServerCmd.CONFIG)
            clash_server_ctl(ServerCmd.RESTART)
        elif choiced_option == "test_config":
            clash_server_ctl(ServerCmd.TEST)
        elif choiced_option == "create_yaml":
            file_names = get_file_names(os.path.join(DATA_DIR, "tpl"))
            file_names = [i for i in file_names if os.path.splitext(i)[1] == ".yaml"]
            index = select(file_names)
            if index >= len(file_names):
                print("backward")
                continue
            tpl_config_path = os.path.join(TPL_DIR, file_names[index])
            tpl_out_config_path = os.path.join(PROFILE_DIR, file_names[index])
            url_path = PROXY_PROVIDERS_URL_PATH
            urls = ClashUtil.extra_urls(url_path)
            proxy_urls, failed_urls = clash_util.create_yaml_base_on_tpl(urls, tpl_config_path, tpl_out_config_path)
            print("used providers:")
            [print(f"-   {i}") for i in proxy_urls]
            print("failed providers:")
            [print(f"-   {i}") for i in failed_urls]
            print(f'created "{tpl_out_config_path}"')
        elif choiced_option == "tun_mode":
            opts = ["enable", "disable"]
            idx = select(opts)
            if idx >= len(opts):
                print("backward")
                continue

            if opts[idx] == "enable":
                enable = True
            else:
                enable = False

            config.set("main", "tun_mode", "True" if enable else "False")
            with open(CLASHAUTO_CONFIG_PATH, "w", encoding="utf-8", newline="") as f:
                config.write(f)

            ClashUtil.tun_ctl(enable, FINAL_CLASH_CONFIG_PATH)
            print(f'Switched tun mode: {enable}')

            clash_server_ctl(ServerCmd.RESTART)
        elif choiced_option == "system_proxy":
            opts = ["enable", "disable"]
            idx = select(opts)
            if idx >= len(opts):
                print("backward")
                continue

            if opts[idx] == "enable":
                enable = True
            else:
                enable = False
            win_system_proxy_ctl(enable=enable, proxy=proxy)
        elif choiced_option == "uwp_loopback":
            cmd = f'EnableLoopback.exe'
            os.system(cmd)
        elif choiced_option == "install_clash_service":
            clash_server_ctl(ServerCmd.INSTALL)
            clash_server_ctl(ServerCmd.RESTART)
        elif choiced_option == "uninstall_clash_service":
            clash_server_ctl(ServerCmd.STOP)
            clash_server_ctl(ServerCmd.UNINSTALL)
            win_system_proxy_ctl(enable=False)
        elif choiced_option == "restart_clash_auto":
            #exec = sys.executable
            #os.execl(exec, exec, * sys.argv)
            os.execl("clashauto.bat", "clashauto.bat")
        elif choiced_option == "exit":
            break;
        else:
            sys.stderr.write("Not match the option")

if __name__ == "__main__":
    main()
