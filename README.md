# Clash Auto

language: [English (out of date)](./README_EN.md) | [中文](./README.md)

## 开发此软件的原因

1.  我一般有多个机场链接, 因为有些机场并不能保证 24 小时能上网。所以喜欢将多个机场写在一个配置文件, 方便切换。
2.  可以用自己的分流规则。这样做会更加安全。再整个黑白名单模式切换。
    -   黑名单模式好处是省流量, 安全 (不需要走代理的网站不走代理)。坏处是遇到不匹配的网站要切换到白名单模式。
    -   白名单模式的好处是规则如果没有匹配到该网站时也可以访问, 不用切换模式。坏处是不省流量, 可以不走代理的网站走了代理, 不安全。
3.  自己写的配置一般会有依赖的网络资源 (比如: `url` 字段) 时, 所以可能会出现这种情况:
    -   [Clash 更新这些资源是不走代理的。](https://github.com/Dreamacro/clash/issues/2368)
    -   [[Feature] 让providers可以通过代理来更新](https://github.com/Dreamacro/clash/issues/2046)
    -   [windows11 error](https://github.com/Fndroid/clash_for_windows_pkg/issues/2384)
    -   [[Feature] rule-providers 和 proxy-providers 能不能提供选择直连或代理选项](https://github.com/Dreamacro/clash/issues/1385)

我根据自己平时的使用, 开发了这个软件实现了上述的功能和解决了上述的问题。如果你使用 clash 的习惯和我相同, 这个软件应该适合你。

## 特点

-   通过自身代理来更新配置而不是直连。
-   可定义配置模块来生成 Clash 配置。对于有多个订阅链接的用户可以将所有订阅合并到一个配置文件, 而且订阅之间不混乱。
-   可自定义后端地址将订阅链接转换为 Clash 配置。
-   小巧高效。平时只需运行一个 Clash Server 在后台。ClashAuto 要用时再打开即可。

## 支持的平台

-   Windows
-   Linux

## 依赖

1.  安装 python, python-pip
2.  pip install ruamel.yaml requests

## 安装

1.  从 release 下载软件包 (免安装)。
2.  双击运行 `clashauto.bat`。
3.  选择 `install` 后, Windows 会安装一个开机启动的 clash 服务。

## 使用

### 软件的文件的作用

-   clashauto.bat: 启动 Windows 平台的 ClashAuto
-   clashauto: 启动 Linux 平台的 ClashAuto
-   data: 放置用户的数据。
    -   config.ini: ClashAuto 的配置。
    -   profiles: 用于放置 profile 文件。
    -   basic_clash_config.yaml: 用于配置 clash 的基础配置。修改该文件后, 记得重启 clashauto.bat
    -   tpl: 用于根据 Clash 模板配置文件生成新的配置文件。
        -   proxy_provider_urls: 放置有 proxies 字段的 Clash 配置。
        -   .yaml 文件: Clash 模板配置文件
-   final_clash_config.yaml: 通过 basic_clash_config 和 profile 文件合并后配置文件, clash 是用这个配置文件启动的。
-   clash_config: 是 clash 的配置目录。

### clashauto.bat 的选项

双击运行 `clashauto.bat` 后, 会有如下选项:

-   update_final_config: 表示更新 final_clash_config.yaml 这个文件依赖的资源。
-   update_profile

    表示更新 profile 文件依赖的资源。

    可以用一个后缀是 `_url` 的文件放置 profile 的链接。它会将链接的内容保存到将 `_url` 为 `.yaml` 的文件。同时会更新该 profile 依赖的资源。
    
    如果链接的内容不是一个 clash 配置文件, 可以通过一些订阅转换网站转换成 clash 的配置。比如: https://acl4ssr-sub.github.io/
    
    比如:

    profiles/example_url
    
    ```
    <your clash config url>
    ```
    
    同时也支持 `vmess://, trojan://` 等开头的链接并且可以将它们一起放在一个 url 文件。比如:
    
    profiles/example_url

    ```
    <your clash config url>
    vmess://...
    trojan://...
    ```
    
    选择该选项后会将 url 的内容保存到 profiles/example.yaml, 且更新该配置依赖的资源。更新成功后, 用户在 select_profile 选项中选择该配置即可。
    
-   select_profile: 表示选择一个 `profile` 和 `basic_clash_config.yaml` 合并到 `final_clash_config.yaml`。同时重启 clash 服务使配置文件生效。
-   restart/stop/config/install/uninstall clash_service: 都是用于操作 clash 服务。
-   test_config: 测试 `final_clash_config.yaml` 配置文件。
-   create_yaml: 用于根据 Clash 模板配置文件生成新的配置文件。
-   tun_mode: 启用/关闭 tun 模式
-   uwp_loopback: 允许应用程序在本地回环地址（loopback address）上进行网络通信。为了增强应用程序的安全性，Microsoft 在默认情况下禁用了微软商店的应用在本地回环地址上进行网络通信的功能。

*Clash Auto 会使用自身作为代理来更新 clash 配置文件的依赖和更新 clash 的配置文件。*

### Clash 的客户端

浏览器访问 http://127.0.0.1:9090/ui 即可。

### Clash Auto 的配置

sc_host: 表示订阅转换的后端地址。在转换 url 时, 如果发现 url 的内容不是 Clash 配置, 则使用订阅转换来转换该 url。
tun_mode: 表示启动/关闭 tun 模式。

### 根据模板配置生成新的配置

目的: 如何有多个有 proxies 字段的配置合并在一个配置文件中使用时, 一般会为每个配置文件写一个 proxy-provider, Select Group 和 Auto Group。该功能是为每个配置每个文件的生成这些组。

比如:

<details>
<summary> tpl_basic.yaml </summary>

```yaml
proxy-groups:
  - name: "Entry"
    type: select
    proxies:
      - AllAuto
      - AllSelect
      # 使用名为 "Auto" 组下的所有组
      - <Auto>
    url: http://www.gstatic.com/generate_204
    interval: 300

  - name: "AllSelect"
    type: select
    use:
      # 使用名为 "provider" 下的 providers
      - <provider>
    url: http://www.gstatic.com/generate_204
    interval: 300

  - name: "AllAuto"
    type: url-test
    proxies:
      - <Auto>
    url: http://www.gstatic.com/generate_204
    interval: 30

  # 为模板名为 "provider" 下的 providres 生成组
  - name: "Select"
    tpl_param:
      providers: ["provider"]
    type: select
    use: null
    url: http://www.gstatic.com/generate_204
    interval: 300

  - name: "Auto"
    tpl_param:
      providers: ["provider"]
    type: url-test
    use: null
    url: http://www.gstatic.com/generate_204
    interval: 300

  - name: "RuleMode"
    type: select
    proxies:
      - DIRECT
      - Entry

  - name: "RuleMode-LastMatch"
    type: select
    proxies:
      - Entry
      - DIRECT

proxy-providers:
  # 为所有 url 生成 providers
  provider:
    tpl_param:
    type: http
    url: null
    path: null
    interval: 3600
    health-check:
      enable: true
      interval: 600
      url: http://www.gstatic.com/generate_204
```

</details>

<details>
<summary> proxy_provider_urls (如果这些 url 的内容如果没有 proxies 的内容, 会使用 SubConverter 来转换。) </summary>

```yaml
https://example1.com
https://example2.com
```

</details>

<details>
<summary> 生成的 tpl_basic.yaml </summary>

```yaml
proxy-groups:
- name: Entry
  type: select
  proxies:
  - AllAuto
  - AllSelect
  - Auto-provider0
  - Auto-provider1
  url: http://www.gstatic.com/generate_204
  interval: 300
- name: AllSelect
  type: select
  use:
  - provider0
  - provider1
  url: http://www.gstatic.com/generate_204
  interval: 300
- name: AllAuto
  type: url-test
  proxies:
  - Auto-provider0
  - Auto-provider1
  url: http://www.gstatic.com/generate_204
  interval: 30
- name: Select-provider0
  type: select
  use:
  - provider0
  url: http://www.gstatic.com/generate_204
  interval: 300
- name: Select-provider1
  type: select
  use:
  - provider1
  url: http://www.gstatic.com/generate_204
  interval: 300
- name: Auto-provider0
  type: url-test
  use:
  - provider0
  url: http://www.gstatic.com/generate_204
  interval: 300
- name: Auto-provider1
  type: url-test
  use:
  - provider1
  url: http://www.gstatic.com/generate_204
  interval: 300
- name: RuleMode
  type: select
  proxies:
  - DIRECT
  - Entry
- name: RuleMode-LastMatch
  type: select
  proxies:
  - Entry
  - DIRECT
proxy-providers:
  provider0:
    type: http
    url: 
      https://example1.com
    path: proxy-providers/tpl/provider0.yaml
    interval: 3600
    health-check:
      enable: true
      interval: 600
      url: http://www.gstatic.com/generate_204
  provider1:
    type: http
    url: 
      https://example1.com
    path: proxy-providers/tpl/provider1.yaml
    interval: 3600
    health-check:
      enable: true
      interval: 600
      url: http://www.gstatic.com/generate_204
```

</details>

会将合并后的文件复制到 profiles 目录, 然后更新并选择这个 profile 即可。

## 更新 ClashAuto

从 Release 下载软件, 解压软件压缩包, 然后将之前的 data 的文件 (选择自己需要的) 复制到安装目录下即可。

## Q&A

Q: 如果 clash 客户端可以连上服务端, 但是无法翻墙?

A: 设置 Windows 防火墙, 使 clash.exe 允许通过防火墙。

## Linux

### 依赖

和 Windows 平台一样。

### 安装

比如:

1.  安装 Clash premium。并确保有 clash server unit (`systemctl cat clash@` 可以查看)。比如 ArchLinux: `yay -S clash-premium-bin`
2.  运行 `clashauto`, 选择 config_clash_server。

    ```
    [Service]
    # 删除原先的 ExecStart
    ExecStart=
    # 修改 `-d, -f` 参数。
    ExecStart=/usr/bin/clash -d /opt/clash-auto/clash_config -f /opt/clash-auto/final_clash_config.yaml
    ```

3.  修改 `/opt/clash-auto/clash_config` 的文件属性

    ```sh
    cd /opt/clash-auto
    sudo chown root:<your user name> clash_config
    sudo chmod g+w clash_config
    ```

### 使用

和 Windows 平台差不多。

## Screenshots

![](./screenshots/clashauto.png)
