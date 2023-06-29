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

    def fetch_sub_url(self, url, list=False):
        out_url, out_conent = self.convert_to_clash_yaml_url(url, list)
        return out_url, out_conent

    def convert_to_clash_yaml_url(self, url, list=False):
        out_url = None
        out_content = None
        try:
            # If url content is clash yaml
            if url.startswith("http"):
                with self.__session.get(url) as response:
                    yaml_data = ruamel.yaml.safe_load(response.content.decode("utf-8"))
                    if self.is_clash_yaml(yaml_data):
                        out_url = url
                        out_content = response.content
                        return out_url, out_content

            # Otherwise
            sc_url = self.create_subconverter_url(url, self.__sc_host, list)
            with self.__session.get(sc_url) as response:
                yaml_data = ruamel.yaml.safe_load(response.content.decode("utf-8"))
                if self.is_clash_yaml(yaml_data):
                    out_url = sc_url
                    out_content = response.content
                else:
                    out_url = sc_url
                    out_content = None
        except requests.exceptions.RequestException as e:
            print("requests exceptions：", e)
            return None, None

        return out_url, out_content

    @staticmethod
    def create_subconverter_url(url, host, list=False):
        encoded_url = urllib.parse.quote(url, safe="")
        subconverter_url = r"{}".format(f"https://{host}/sub?target=clash&url={encoded_url}")
        if list:
            subconverter_url += r"&list=true"
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
                out_url, out_content = self.convert_to_clash_yaml_url(url, list=True)
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
        tpl_provider_data = tpl_yaml_data[pp_section_name]["provider"]
        for i, pu in enumerate(proxy_urls):
            new_provider_data = copy.deepcopy(tpl_provider_data)
            name = f"provider{i}"
            new_provider_data["url"] = pu
            new_provider_data["path"] = f"proxy-providers/tpl/{name}.yaml"

            out_yaml_data[pp_section_name][name] = new_provider_data

        del out_yaml_data[pp_section_name]["provider"]

        # ## proxy-groups
        pg_section_name = "proxy-groups"
        provider_names = []
        select_group_names = []
        auto_group_names = []
        for i in range(0, len(out_yaml_data[pp_section_name])):
            pv_name = f"provider{i}"
            provider_names.append(pv_name)
            sg_name = f"Group{i}Select"
            select_group_names.append(sg_name)
            ag_name = f"Group{i}Auto"
            auto_group_names.append(ag_name)

        def create_pg_groups_by_tpl(tpl_group_name, group_names, provider_names):
            index_of_tpl_group = next(\
                (i for i, g in enumerate(out_yaml_data[pg_section_name]) if g["name"] == tpl_group_name), None)
            if not index_of_tpl_group:
                sys.stderr.print(f"{group_name} not found.")
            tpl_group = out_yaml_data[pg_section_name][index_of_tpl_group]
            new_groups = []
            for g_name, pv_name in zip(group_names, provider_names):
                new_group_data = copy.deepcopy(tpl_group)
                new_group_data["name"] = g_name
                new_group_data["use"] = [pv_name]
                new_groups.append(new_group_data)
            out_yaml_data[pg_section_name][index_of_tpl_group + 1 : index_of_tpl_group + 1] = new_groups
            del out_yaml_data[pg_section_name][index_of_tpl_group]

        # ### GroupSelect
        create_pg_groups_by_tpl("GroupSelect", select_group_names, provider_names)
        create_pg_groups_by_tpl("GroupAuto", auto_group_names, provider_names)

        # ## Repalce select_groups, auto_groups, providers
        def replace_special_key_in_proxy_groups(special_key, replace_value, key, group):
            value = group.get(key)
            if not value:
                return False
            for i, group_name in enumerate(value):
                if group_name == special_key:
                    group[key][i + 1 : i + 1] = replace_value
                    del group[key][i]
                    break

        for group in out_yaml_data[pg_section_name]:
            replace_special_key_in_proxy_groups("<select_groups>", select_group_names, "proxies", group)
            replace_special_key_in_proxy_groups("<auto_groups>", auto_group_names, "proxies", group)
            replace_special_key_in_proxy_groups("<providers>", provider_names, "use", group)

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
