#!/usr/bin/env python3
# _*_ coding: UTF-8 _*_

import os, sys
from enum import Enum
import ruamel.yaml
import clashutil

# ## Global Vars
SCRIPT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
CLASH_CORE = os.path.join(SCRIPT_PATH, "clash.exe")
CFG_DIR = os.path.join(SCRIPT_PATH, "config")
PROFILE_DIR = os.path.join(SCRIPT_PATH, "profiles")

BASIC_CLASH_CONFIG_PATH = os.path.join(SCRIPT_PATH, "basic_clash_config.yaml")
FINAL_CLASH_CONFIG_PATH = os.path.join(SCRIPT_PATH, "final_clash_config.yaml")
TIMEOUT = 5

PATH_OF_UPDATE_CFG_RES = os.path.join(SCRIPT_PATH, "update_clashcfg_res.py")

def get_proxy(yaml_data):
    port = yaml_data.get("mixed-port")
    if port:
        proxy = f"https://127.0.0.1:{port}"
    port = yaml_data.get("port")
    if port:
        proxy = f"https://127.0.0.1:{port}"
    port = yaml_data.get("socks-port")
    if port:
        proxy = f"socks5://127.0.0.1:{port}"
    
    return proxy if proxy else "https://127.0.0.1:7890"

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

class ServerCmd(Enum):
    RESTART = 1
    STOP = 2
    CONFIG = 3
    INSTALL = 4
    UNINSTALL = 5
    TEST = 6

def clash_server_ctl(server_cmd):
    os.chdir(SCRIPT_PATH)

    if server_cmd == ServerCmd.RESTART:
        cmd = f"nssm.exe restart clash"
    elif server_cmd == ServerCmd.STOP:
        cmd = f"nssm.exe stop clash"
    elif server_cmd == ServerCmd.CONFIG:
        cmd = f"nssm.exe edit clash"
    elif server_cmd == ServerCmd.INSTALL:
        cmd = f'nssm.exe install clash "{CLASH_CORE}" -d "{CFG_DIR}" -f "{FINAL_CLASH_CONFIG_PATH}"'
    elif server_cmd == ServerCmd.UNINSTALL:
        cmd = f"nssm.exe remove clash confirm"
    elif server_cmd == ServerCmd.TEST:
        cmd = f'{CLASH_CORE} -d "{CFG_DIR}" -f "{FINAL_CLASH_CONFIG_PATH}" -t'
        print(cmd)

    os.system(cmd)

def main():
    os.chdir(SCRIPT_PATH)
    
    with open(BASIC_CLASH_CONFIG_PATH, "r", encoding="utf-8") as f:
        basic_yaml_data = ruamel.yaml.safe_load(f)
    proxy = get_proxy(basic_yaml_data)

    options = ["update_final_config", "update_profile", "select_profile", "restart_clash_service", \
               "stop_clash_service", "config_clash_service", "install_clash_service", "uninstall_clash_service", \
               "test_config", "create_yaml", "uwp_loopback", "restart_clash_auto", "exit"]
    while True:
        print()
        choice = select(options)
        if choice >= len(options):
            print("Invalid selection, please try again")
            continue
        choiced_option = options[choice]
        if choiced_option == "update_final_config":
            profile_dir = SCRIPT_PATH
            profile_name = "final_clash_config.yaml"
            cmd = f'python {PATH_OF_UPDATE_CFG_RES} -d "{CFG_DIR}" -f "{profile_dir}"  -n "{profile_name}" -p "{proxy}" -i {TIMEOUT} -r'
            os.system(cmd)
        elif choiced_option == "update_profile":
            profiles = [f for f in os.listdir(PROFILE_DIR) if os.path.isfile(os.path.join(PROFILE_DIR, f))]
            profiles = [f for f in profiles if not f.endswith("~")]
            profile_index = select(profiles)
            if profile_index >= len(profiles):
                print("backward")
                continue
            choiced_profile_name = profiles[profile_index]
            if choiced_profile_name.endswith("_url"):
                with open(os.path.join(PROFILE_DIR, choiced_profile_name), "r") as f:
                    profile_url = r"{}".format(f.readline().strip())
                profile_name = choiced_profile_name[:-4] + ".yaml"
                cmd = f'python {PATH_OF_UPDATE_CFG_RES} -d "{CFG_DIR}" -f "{PROFILE_DIR}"  -n "{profile_name}" -u "{profile_url}" -p "{proxy}" -i {TIMEOUT} -r'
            else:
                profile_name = choiced_profile_name
                cmd = f'python {PATH_OF_UPDATE_CFG_RES} -d "{CFG_DIR}" -f "{PROFILE_DIR}"  -n "{profile_name}" -p "{proxy}" -i {TIMEOUT} -r'

            os.system(cmd)
        
        elif choiced_option == "select_profile":
            profiles = [f for f in os.listdir(PROFILE_DIR) if os.path.isfile(os.path.join(PROFILE_DIR, f))]
            profiles = [f for f in profiles if not f.endswith("~") and not f.endswith("_url")]
            profile_index = select(profiles)
            if profile_index >= len(profiles):
                print("backward")
                continue
            choiced_profile_name = profiles[profile_index]
            profile_name = choiced_profile_name
            
            profile_path = os.path.join(PROFILE_DIR, profile_name)
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_yaml_data = ruamel.yaml.safe_load(f)
            merged_yaml_data = clashutil.merge_profile(basic_yaml_data, profile_yaml_data)
            with open(FINAL_CLASH_CONFIG_PATH, "w", encoding="utf-8", newline="") as f:
                ruamel.yaml.round_trip_dump(merged_yaml_data, f)
            print(f'Merged "{BASIC_CLASH_CONFIG_PATH}" and "{profile_path}" into "{FINAL_CLASH_CONFIG_PATH}"')

            clash_server_ctl(ServerCmd.RESTART)

        elif choiced_option == "restart_clash_service":
            clash_server_ctl(ServerCmd.RESTART)
        elif choiced_option == "stop_clash_service":
            clash_server_ctl(ServerCmd.STOP)
        elif choiced_option == "config_clash_service":
            clash_server_ctl(ServerCmd.CONFIG)
            clash_server_ctl(ServerCmd.RESTART)
        elif choiced_option == "install_clash_service":
            clash_server_ctl(ServerCmd.INSTALL)
            clash_server_ctl(ServerCmd.RESTART)
        elif choiced_option == "uninstall_clash_service":
            clash_server_ctl(ServerCmd.STOP)
            clash_server_ctl(ServerCmd.UNINSTALL)
        elif choiced_option == "test_config":
            clash_server_ctl(ServerCmd.TEST)
        elif choiced_option == "create_yaml":
            tpl_config_path = "tpl/tpl_clash_config.yaml"
            tpl_out_config_path = "tpl/tpl_out_clash_config.yaml"
            url_path = "tpl/proxy_provider_urls"
            with open(url_path, "r", encoding="utf-8") as f:
                urls = [r"{}".format(line.strip()) for line in f.readlines()]
            clashutil.create_yaml_base_on_tpl(urls, tpl_config_path, tpl_out_config_path)
        elif choiced_option == "uwp_loopback":
            cmd = f'EnableLoopback.exe'
            os.system(cmd)
        elif choiced_option == "restart_clash_auto":
            exec = sys.executable
            os.execl(exec, exec, * sys.argv)
        elif choiced_option == "exit":
            break;
        else:
            sys.stderr.write("Not match the option")

if __name__ == "__main__":
    main()
