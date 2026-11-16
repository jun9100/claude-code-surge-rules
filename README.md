# Claude Code 分流规则集 · Surge RULE-SET

Claude Code / Anthropic 全量域名分流规则，按 Surge `RULE-SET` 文本格式编写，可直接被 Surge Mac / iOS 远程引用。

规则内容依据 [Claude Code 域名分流规则大全（Net.Coffee）](https://ip.net.coffee/claude/site.html) 整理转写，覆盖原文全部条目：

- **核心域名**：`anthropic.com`、`claude.ai`、`claude.com`、`clau.de`、`claudemcpclient.com`、`claudemcpcontent.com`、`claudeusercontent.com`
- **CDN**：`servd-anthropic-website.b-cdn.net`、`anthropic.com.cdn.cloudflare.net`
- **认证 / 内容**：`anthropic.auth0.com`、`anthropic-com.ghost.io`
- **KYC**：`maps.googleapis.com`、`withpersona.com`、`frompersona.com`
- **监控 / 遥测 / 反欺诈**：`sentry.io`、`statsigapi.net`、`browser-intake-us5-datadoghq.com` + 关键词 `datadog`、`sentry`、`sift`
- **第三方 widget**：`intercom.io`、`intercomcdn.com`、`cdn.usefathom.com`
- **IP / ASN 兜底**：`160.79.104.0/21`、`2607:6bc0::/32`、`AS399358`
- **NTP 时区同步**：UDP/123 逻辑规则

## 用法

### 1. 远程引用（推荐）

在 Surge 配置的 `[Rule]` **最前面**加一行，把 `Proxy` 换成你自己的策略组名：

```
RULE-SET,https://raw.githubusercontent.com/jun9100/claude-code-surge-rules/main/ClaudeCode.list,Proxy
```

需要定期自动更新可加 `update-interval`（秒，默认 86400）：

```
RULE-SET,https://raw.githubusercontent.com/jun9100/claude-code-surge-rules/main/ClaudeCode.list,Proxy,update-interval=86400
```

### 2. 国内网络拉不到 raw.githubusercontent.com 时

用 jsDelivr 镜像（同样内容，CDN 加速）：

```
RULE-SET,https://cdn.jsdelivr.net/gh/jun9100/claude-code-surge-rules@main/ClaudeCode.list,Proxy
```

### 3. 本地文件

下载 `ClaudeCode.list` 放进 Surge 的 Profiles 目录，然后：

```
RULE-SET,ClaudeCode.list,Proxy
```

### 4. 作为模块使用

本仓库只提供 RULE-SET。若想「一键插入规则」而不用手改 `[Rule]`，把 `[Rule]` 里那一行包成模块即可：

```
#!name=Claude Code 分流
#!arguments=policy:Proxy

[Rule]
RULE-SET,https://raw.githubusercontent.com/jun9100/claude-code-surge-rules/main/ClaudeCode.list,{{{policy}}}
```

## 规则顺序

Claude 规则必须排在 `GEOIP,CN`、`RULE-SET,LAN` 等通用规则**之前**，否则会被后置规则抢走匹配。典型结构：

```
[Rule]
RULE-SET,ClaudeCode.list,Proxy      # ← Claude 规则置顶
RULE-SET,LAN,DIRECT,no-resolve
GEOIP,CN,DIRECT
FINAL,Proxy
```

## 几个必须知道的点

1. **节点要支持 UDP 中继**。最后一条 `AND,((PROTOCOL,UDP),(DEST-PORT,123))` 负责 NTP；SS / SOCKS5 需要显式 `udp-relay=true`，Trojan / VMess / Snell v3+ / Hysteria2 / TUIC / VLESS 默认支持。建议在 `[General]` 设 `udp-policy-not-supported-behaviour = REJECT`，宁可失败也不要偷偷直连泄露真实 IP。
2. **Mac 系统代理模式接管不到 UDP**。要让 NTP 真正按规则走，需要 Enhanced Mode 或网关模式；否则更省事的办法是直接关掉系统自动对时。
3. **IPv6**。建议 `ipv6 = false`，避免双栈出口不一致；`IP-CIDR6` 那条在关闭 IPv6 时不生效，保留不影响。
4. **`no-resolve`**。IP 规则都带该参数：域名未解析时跳过，不额外触发 DNS 查询，降低首包延迟。

## 与原文的格式差异

原文给的是 sing-box / Clash.Meta 风格列表，本仓库转成 Surge 语法时的处理：

| 原文 | 本仓库 | 说明 |
| --- | --- | --- |
| `geosite:anthropic` | 展开为具体 `DOMAIN-SUFFIX` / `DOMAIN` | Surge 没有 geosite 概念 |
| `keyword:datadog` / `keyword:sentry` / `keyword:sift` | `DOMAIN-KEYWORD,...` | 语义等价 |
| `geosite:category-ntp` | `AND,((PROTOCOL,UDP),(DEST-PORT,123))` | Surge 对 UDP 使用同一套规则系统，精确命中 UDP/123 |
| `IP-ASN,399358` | 原样保留 | Surge 原生支持，走内置 GeoLite2 ASN 库 |
| 原文的纯域名通配列表 | 不使用 | 该列表不含 `auth0.com`、`b-cdn.net`、`cloudflare.net` 等跨根域条目，会漏代理 |

另外：`cdn.` / `mcp.` / `console.` / `workbench.` / `api.anthropic.com` 已被 `DOMAIN-SUFFIX,anthropic.com` 覆盖，未重复写入；`withpersona.com` / `frompersona.com` 使用 `DOMAIN-SUFFIX` 以覆盖子域。

## 验证

```bash
# 校验配置（需本机安装 Surge Mac）
surge-cli --check /path/to/profile.conf

# 运行时逐条核对命中情况
surge-cli rule match claude.ai
surge-cli rule match browser-intake-us5-datadoghq.com
surge-cli rule explain claude.ai
```

本仓库的 `ClaudeCode.list` 已通过 `surge-cli --check`（放进配置引用后返回 `OK`），并由 CI 检查语法与重复项。

## 同类规则集横评

GitHub 上针对 Claude / Anthropic 的规则集不多，能查到的都逐个下载做过实测对比（2026-11-16）：

| 规则集 | 星标 | 最后更新 | 有效规则 | 说明 |
| --- | --- | --- | --- | --- |
| **本仓库** | — | 2026-11-16 | **45** | 覆盖最全，含 KYC / NTP / IP-ASN |
| [VPSDance/ai-proxy-rules](https://github.com/VPSDance/ai-proxy-rules) | 717 | 2026-11-16 | 52 | 覆盖最广，含大量 Anthropic 边缘域名与 `PROCESS-NAME`；但缺 KYC、NTP，且含 6 条无 A 记录的无效条目 |
| [HotKids/Rules](https://github.com/HotKids/Rules) | 479 | 2026-11-15 | 21 | 与 Net.Coffee 文档的类型前缀列表**逐条一致**，未补充 KYC / NTP |
| [xiaolai/anthropic-claude-surge-rules-set](https://github.com/xiaolai/anthropic-claude-surge-rules-set) | 64 | 2026-04-14 | 13 | 多格式（Clash/sing-box/QX/Loon），但漏了 `anthropic.auth0.com` 等关键项 |
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) · `Claude` / `Anthropic` | 28.6k | 2026-10-27 | 3 / 3 | 极简，只有主域名 + 一个 CDN，适合「只代理主站」的克制用法 |

### 与 VPSDance 那份的差异（值得吸收的部分）

它列了一批看起来可疑、但我逐个用 DoH 查过 A 记录的域名，**确实解析到 `160.79.104.0/21`（Anthropic 自有段）**：

```
claude.app  claude.new  claude.site  claude.dev  claudepages.dev  claudestudio.com
claudeacademy.com  antspace.dev  muthos.com  sillylittleguy.org  lcicollections.org
lcicat.org  interface.feedback  mcpservertest.online
```

这些已全部并入本仓库（第 9 节）。为什么要按域名写、而不是靠 IP 段兜底？因为 `IP-CIDR` 带 `no-resolve`，域名尚未解析时该规则会被跳过，纯靠 IP 兜底会漏。

**它列了但没有生效记录、因此本仓库未收录的**（A 记录为空，加进去只是噪音）：`chatbotclaude.com`、`anthropic.com.cn`、`anthropic.team`、`ant.dev`、`modelcontextprotocol.com`。

**它比本仓库多、但本仓库按需提供的**：`DOMAIN,storage.googleapis.com` —— Google 共享基础设施，默认注释。

### 结论

没有找到比本仓库更完整的 Claude 分流规则集。VPSDance 那份在「边缘域名」上最全，但缺 KYC 身份核验、NTP 时区同步和 `sentry`/`sift` 关键词兜底；HotKids 那份等同文档原样；blackmatrix7 走极简路线。需要更严格的风控一致性，用本仓库；只关心能不能连上，三者都够用。

## License

[MIT](LICENSE)。规则内容整理自 Net.Coffee 的公开文档，版权归原作者；如需要请自行留意外链说明。
