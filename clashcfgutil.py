#!/usr/bin/env python3
# _*_ coding: UTF-8 _*_

import sys, os, shutil, urllib.parse
import ruamel.yaml, requests

def update_res(sections, cfg_dir, profile_dir, *, profile_name, profile_url=None, is_cfw=None, proxy=None, timeout=None, sc_host=None):
    profile_path, temp_profile_url = get_cfg_path(profile_dir, profile_name, is_cfw)
    if temp_profile_url:
        profile_url = temp_profile_url
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})
    if proxy:
        protocol, address = proxy.split("://")
        session.proxies = {
            protocol: address
        }
    if timeout:
        session.timeout = timeout
    
    # Fetch the profile from profile_url
    if profile_url:
        if os.path.exists(profile_path):
            cfg_path_bak = profile_path + "~"
            shutil.copy(profile_path, cfg_path_bak)

        content = download_sub_url(profile_url, session, sc_host)
        if content:
            with open(profile_path, "wb") as f:
                f.write(content)
            print(f'Updated cfg successfully: "{profile_path}", "{profile_url}"')
        else:
            print(f'Updated cfg failed: "{profile_path}", "{profile_url}"')

    if not os.path.exists(profile_path):
        sys.stderr.write(f'cfg_path: "{profile_path}" isn\'t exists.')
        sys.exit(os.EX_USAGE)

    updated_res = []
    res = []
    for s in sections:
        res = get_net_res(profile_path, [s])
        updated_res += update_net_res(session, res, s, cfg_dir, sc_host)
    print(f'Updated resource(s) needed by "{profile_path}"')
    return updated_res

def get_cfg_path(profile_dir, profile_name, is_cfw=None):
    yaml = ruamel.yaml.YAML(typ="safe")
    
    profile_path = ""
    profile_url = ""
    if is_cfw:
        list_path = os.path.join(profile_dir, "list.yml")
        if not os.path.exists(list_path):
            sys.stderr.write(f'list.yml: "{list_path}" isn\'t exist!\n')
            sys.exit(os.EX_USAGE)
        with open(list_path, "r", encoding="utf-8") as f:
            list_data = yaml.load(f)
        for x in list_data["files"]:
            if x["name"] == profile_name:
                profile_path = os.path.join(profile_dir, x["time"])
                profile_url = x["url"]
    else:
        profile_path = os.path.join(profile_dir, profile_name)

    return profile_path, profile_url

def get_net_res(profile_path, sections):
    # ## Load cfg
    yaml = ruamel.yaml.YAML(typ="safe")
    with open(profile_path, "r", encoding="utf-8") as f:
        cfg_data = yaml.load(f)

    net_res = []
    for s in sections:
        # ## extras data from section
        s_data = cfg_data.get(s)
        if not s_data:
            continue

        # ## Put the url and path of items with type == "http" into net_res.
        for i in s_data.values():
            if i["type"] == "http":
                net_res.append([i["url"], i["path"]])

    return net_res

def update_net_res(session, net_res, section, cfg_dir, sc_host=None):
    oldcwd = os.getcwd()
    os.chdir(cfg_dir)
    
    updated_res = []
    for i in net_res:
        dirpath = os.path.dirname(i[1])
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        
        if section == "proxy-providers":
            content = download_sub_url(i[0], session, sc_host)
        else:
            with session.get(i[0]) as response:
                content = response.content

        if content:
            with open(i[1], "wb") as f:
                f.write(content)
            print(f'Updated successfully: "{i[1]}", "{i[0]}"')
            updated_res.append(i)
        else:
            print(f'Updated failed: "{i[1]}", "{i[0]}"')

    os.chdir(oldcwd)

    return updated_res;

# The path src_cfg_dir of net_res_files is a relative path.
def install_proxy_providers(net_res_files, src_cfg_dir, dest_cfg_dir):
    for x in net_res_files:
        src_file = os.path.join(src_cfg_dir, x)
        dest_file = os.path.join(dest_cfg_dir, x)
        if not os.path.exists(os.path.dirname(dest_file)):
            os.system(f'sudo -u nobody mkdir -p {os.path.dirname(dest_file)}')
        os.system(f'sudo install -o nobody -g nobody -m 0644 {src_file} {dest_file}')
        
def download_sub_url(url, session, sc_host=None):
    out_url, out_conent = convert_to_clash_yaml_url(url, sc_host, session)
    return out_conent

def convert_to_clash_yaml_url(url, sc_host, session):
    out_url = []
    out_content = []
    try:
        with session.get(url) as response:
            yaml_data = ruamel.yaml.safe_load(response.content.decode("utf-8"))
            if is_clash_yaml(yaml_data):
                out_url = url
                out_content = response.content
                return out_url, out_content
            else:
                sc_url = create_subconverter_url(url, sc_host)

        with session.get(sc_url) as response:
            yaml_data = ruamel.yaml.safe_load(response.content.decode("utf-8"))
            if is_clash_yaml(yaml_data):
                out_url = sc_url
                out_content = response.content
    except requests.exceptions.RequestException as e:
        print("requests exceptions：", e)
        return out_url, out_content

    return out_url, out_content

def create_subconverter_url(url, host):
    encoded_url = urllib.parse.quote(url, safe='')
    subconverter_url = r"{}".format(f'https://{host}/sub?target=clash&url={encoded_url}')
    return subconverter_url

def is_clash_yaml(yaml_data):
    if isinstance(yaml_data, str):
        return False
    if yaml_data.get("proxies") or yaml_data.get("proxy-groups"):
        return True
    else:
        return False