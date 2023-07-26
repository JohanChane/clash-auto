import sys, os, copy, urllib.parse
import ruamel.yaml, requests

class ClashUtil():
    def __init__(self, session, cfg_dir, profile_dir, sc_host=None):
        self.__session = session
        self.__cfg_dir = cfg_dir
        self.__profile_dir = profile_dir
        self.__sc_host = sc_host

    def update_dep_net_res(self, profile_path, sections=["proxy-providers"], list=True):
        oldcwd = os.getcwd()
        os.chdir(self.__cfg_dir)
        
        net_res = self.get_dep_net_res(profile_path, sections)
        updated_res = {}
        no_update_res = {}
        for s, r in net_res.items():
            updated_res[s] = []
            no_update_res[s] = []
            for i in r:
                dirpath = os.path.dirname(i["path"])
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)
                
                if s == "proxy-providers":
                    url, content = self.fetch_sub_url(i["url"], list)
                else:
                    with self.__session.get(i["url"]) as response:
                        content = response.content

                if content:
                    with open(i["path"], "wb") as f:
                        f.write(content)
                    updated_res[s].append(i)
                else:
                    no_update_res[s].append(i)

        os.chdir(oldcwd)
        return updated_res, no_update_res;

    def get_dep_net_res(self, profile_path, sections):
        # ## Load cfg
        with open(profile_path, "r", encoding="utf-8") as f:
            cfg_data = ruamel.yaml.safe_load(f)

        net_res = {}
        for s in sections:
            # ## extras data from section
            s_data = cfg_data.get(s)
            if not s_data:
                continue

            # ## Put the url and path of items with type == "http" into net_res.
            net_res[s] = []
            for i in s_data.values():
                if i["type"] == "http":
                    net_res[s].append({"url": i["url"], "path": i["path"]})

        return net_res

    def fetch_sub_url(self, url, list=False, rename=None):
        out_url, out_conent = self.convert_to_clash_yaml_url(url, list=True)
        return out_url, out_conent

    def convert_to_clash_yaml_url(self, url, *, must_use_sc_host=False, list=False, rename=None):
        out_url = None
        out_content = None
        try:
            if not must_use_sc_host:
                # If url content is clash yaml
                if url.startswith("http"):
                    with self.__session.get(url) as response:
                        yaml_data = ruamel.yaml.safe_load(response.content.decode("utf-8"))
                        if self.is_clash_yaml(yaml_data):
                            out_url = url
                            out_content = response.content
                            return out_url, out_content

            # use subconverter
            sc_url = self.create_subconverter_url(url, self.__sc_host, list, rename)
            with self.__session.get(sc_url) as response:
                yaml_data = ruamel.yaml.safe_load(response.content.decode("utf-8"))
                if self.is_clash_yaml(yaml_data):
                    out_url = sc_url
                    out_content = response.content
                else:
                    out_url = sc_url
                    out_content = None
        except Exception as e:
            print("exceptions：", e)
            return None, None

        return out_url, out_content

    @staticmethod
    def create_subconverter_url(url, host, list=False, rename=None):
        encoded_url = urllib.parse.quote(url, safe="")
        subconverter_url = r"{}".format(f"https://{host}/sub?target=clash&url={encoded_url}")
        if list:
            subconverter_url += r"&list=true"
        if rename:
            encode_rename = urllib.parse.quote(rename, safe="")
            subconverter_url += r"&rename={}".format(encode_rename)
        return subconverter_url

    @staticmethod
    def is_clash_yaml(yaml_data):
        result = False
        try:
            if yaml_data.get("proxies") or yaml_data.get("proxy-groups"):
                result = True
        except Exception as e:
            return False
        
        return result

    @staticmethod
    def merge_profile(basic_yaml_data, profile_yaml_data):
        merged_data = {}
        for key, value in basic_yaml_data.items():
            if key not in merged_data:
                merged_data[key] = value
        for key, value in profile_yaml_data.items():
            if key not in ["proxy-groups", "proxy-providers", "proxies", "rules", "rule-providers"]:
                continue
            if key not in merged_data:
                merged_data[key] = value
        return merged_data
        
    def create_yaml_base_on_tpl(self, urls, tpl_yaml_path, out_yaml_path):
        proxy_urls = []
        failed_urls = []
        if self.__sc_host:
            for i, url in enumerate(urls):
                out_url, out_content = self.convert_to_clash_yaml_url(url, must_use_sc_host=True, list=True)
                if out_content:
                    proxy_urls.append(out_url)
                else:
                    failed_urls.append(url)
        else:
            proxy_urls = urls

        with open(tpl_yaml_path, "r", encoding="utf-8") as f:
            tpl_yaml_data = ruamel.yaml.safe_load(f)

        out_yaml_data = copy.deepcopy(tpl_yaml_data)

        # ## proxy-providers
        pp_section_name = "proxy-providers"
        provider_data, provider_names = self.__create_providers_base_on_tpl(proxy_urls, tpl_yaml_data[pp_section_name])
        out_yaml_data[pp_section_name] = provider_data
        
        # ## proxy-groups
        pg_section_name = "proxy-groups"
        new_group_data = self.__create_proxy_groups_base_on_tpl(provider_names, tpl_yaml_data[pg_section_name])
        out_yaml_data[pg_section_name] = new_group_data

        os.makedirs(os.path.dirname(out_yaml_path), exist_ok=True)
        with open(out_yaml_path, "w", encoding="utf-8", newline="") as f:
                yaml = ruamel.yaml.YAML()
                #yaml.indent(mapping=2, sequence=4, offset=2)
                #yaml.explicit_start = True
                #yaml.default_flow_style = False
                yaml.dump(out_yaml_data, f)
            
        return proxy_urls, failed_urls

    @staticmethod
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

    @staticmethod
    def extra_urls(file_path):
        urls = []
        with open(file_path) as f:
            lines = f.readlines()
            for i in lines:
                i = i.strip()
                if i and not i.startswith("#"):
                    urls.append(r"{}".format(i))
        return urls

    @staticmethod
    def __create_providers_base_on_tpl(proxy_urls, tpl_proxy_providers):
        provider_names = {}
        new_provider_data = {}
        for name, value in tpl_proxy_providers.items():
            if "tpl_param" not in value:
                new_provider_data[name] = value
                continue
            
            provider_names[name] = []
            for i, u in enumerate(proxy_urls):
                n = f"{name}{i}"
                provider_names[name].append(n)
                new_provider_data[n] = copy.deepcopy(value)
                rename = r"{}".format(f"(^.*$)@{n}\|$1")
                encode_rename = urllib.parse.quote(rename, safe="")
                new_provider_data[n]["url"] = f'{u}&rename={encode_rename}'
                new_provider_data[n]["path"] = f"proxy-providers/tpl/{n}.yaml"
                del new_provider_data[n]["tpl_param"]

        return new_provider_data, provider_names
    
    @staticmethod
    def __create_proxy_groups_base_on_tpl(provider_names, tpl_proxy_groups):
        new_group_names = {}
        new_group_data = []
        for i, group in enumerate(tpl_proxy_groups):
            if "tpl_param" not in group:
                new_group_data.append(group)
                continue
            
            new_group_names[group["name"]] = []
            for pn in group["tpl_param"]["providers"]:
                for n in provider_names[pn]:
                    name = f'{group["name"]}-{n}'
                    new_group_names[group["name"]].append(name)
                    new_group = copy.deepcopy(group)
                    new_group["name"] = name
                    new_group["use"] = [n]
                    del new_group["tpl_param"]

                    new_group_data.append(new_group)

        ClashUtil.__replace_special_key_in_proxy_groups(provider_names, new_group_names, new_group_data)

        return new_group_data

    @staticmethod
    def __replace_special_key_in_proxy_groups(provider_names, new_group_names, group_data):
        for group in group_data:
            def replace_special_key(replaced_key, replace_data):
                new_value_data = []
                if replaced_key in group:
                    for i in group[replaced_key]:
                        if i.startswith("<") and i.endswith(">") and i[1:-1] in replace_data:
                            new_value_data.extend(replace_data[i[1:-1]])
                        else:
                            new_value_data.append(i)
                    group[replaced_key] = new_value_data
            replace_special_key("use", provider_names)
            replace_special_key("proxies", new_group_names)

    @staticmethod
    def tun_ctl(enable, config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = ruamel.yaml.safe_load(f)

        try:
            yaml_data.get("tun").get("enable")
            does_have_tun = True
        except Exception as e:
            does_have_tun = False
        try:
            yaml_data.get("dns").get("enable")
            does_have_dns = True
        except Exception as e:
            does_have_dns = False
    
        if does_have_tun:
            yaml_data["tun"]["enable"] = enable
        if does_have_dns:
            yaml_data["dns"]["enable"] = enable

        with open(config_path, "w", encoding="utf-8", newline="") as f:
            yaml = ruamel.yaml.YAML()
            yaml.dump(yaml_data, f)
