import sys, copy
import ruamel.yaml
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.comments import CommentedSeq
import clashcfgutil

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
    
def create_yaml_base_on_tpl(urls, tpl_yaml_path, out_yaml_path, sc_host=None, session=None):
    proxy_urls = []
    if sc_host:
        for i, url in enumerate(urls):
            out_url, out_content = clashcfgutil.convert_to_clash_yaml_url(url, session, sc_host)
            if url:
                proxy_urls.append(out_url)
    else:
        proxy_urls = urls

    yaml = ruamel.yaml.YAML()
    #yaml.indent(mapping=2, sequence=4, offset=2)
    #yaml.explicit_start = True
    #yaml.default_flow_style = False

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
    tpl_group_select = next((group for group in tpl_yaml_data[pg_section_name] if group["name"] == "GroupSelect"), None)
    if not tpl_group_select:
        sys.stderr.print("GroupSelect not found.")
    tpl_group_auto = next((group for group in tpl_yaml_data[pg_section_name] if group["name"] == "GroupAuto"), None)
    if not tpl_group_auto:
        sys.stderr.print("GroupAuto not found.")
    for i in range(0, len(out_yaml_data[pp_section_name])):
        # ### GroupSelect
        new_select_group_data = copy.deepcopy(tpl_group_select)
        name = f"Group{i}Select"
        new_select_group_data["name"] = name
        new_select_group_data["use"] = [f"provider{i}"]
        out_yaml_data[pg_section_name].append(new_select_group_data)

        # ### GroupAuto
        new_auto_group_data = copy.deepcopy(tpl_group_auto)
        name = f"Group{i}Auto"
        new_auto_group_data["name"] = name
        new_auto_group_data["use"] = [f"provider{i}"]
        out_yaml_data[pg_section_name].append(new_auto_group_data)
        
    out_yaml_data[pg_section_name] = [group for group in out_yaml_data[pg_section_name] if group["name"] not in ["GroupSelect", "GroupAuto"]]

    with open(out_yaml_path, "w", encoding="utf-8", newline="") as f:
        yaml.dump(out_yaml_data, f)