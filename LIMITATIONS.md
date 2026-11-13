# 已知局限与未覆盖项

这份文档说明当前配置和自动构建里**没有做的事**、为什么没做，以及可能带来的后果。它不是使用说明，使用说明见 [README.md](README.md)。

---

## 1. 广告规则

### 1.1 只做域名级拦截

当前广告解析只输出两类规则：

```ini
DOMAIN-SUFFIX,example.com,REJECT
IP-CIDR,1.2.3.4/32,REJECT,no-resolve
```

**局限：**

- 不支持网页元素隐藏（ABP 的 `##`、`#@#`、`#?#`）；
- 不支持只针对某个路径、某个脚本、某个域上下文的广告；
- 不支持 `DOMAIN-KEYWORD` 形式的广告规则（广告源里的 keyword 会被丢弃，避免宽泛误杀）；
- 因此，一些依赖路径或页面元素的广告不会被拦。

### 1.2 路径 / URL / `$` 选项规则会被跳过

ABP 规则里带以下内容的，会整条跳过：

- `$` 选项，例如 `$third-party`、`$script`、`$domain=...`；
- 域名后的路径，例如 `/ads/`、`/vip888vip/ug/main/`；
- 域名后的通配符，例如 `*`、`?`。

例子：

```text
||githubusercontent.com/vip888vip/ug/main/*.gif
||cloudflare.com/ajax/libs/jBox/$domain=localmv1.com
@@||qq.com^*?ADTAG=
```

这些规则**不会变成** `DOMAIN-SUFFIX,githubusercontent.com,REJECT` 这类整域规则，也不会进入最终配置。

**局限：**

- 这些路径级广告不会被拦；
- 如果确实需要拦，只能写 `URL-REGEX`，但 HTTPS 路径通常要开启 MITM/HTTPS 解密才可见；
- 为了拦一个路径广告去开 MITM，会引入证书安装、兼容性和隐私风险，所以当前选择不做。

### 1.3 广告/PCDN 列表按上游原样保留

没有本地广告白名单，也没有 `manual_*.txt`。上游列表里的域名会按原样进入最终配置。

当前配置里真实存在的非广告类 REJECT 例子：

- `doh.dns.apple.com`，来自 `adrules_dns` 的 `||doh.dns.apple.com^`；
- `httpdns.huaweicloud.com`，来自 `adrules_dns` 的 `||httpdns.huaweicloud.com^`；
- `metrics.icloud.com`，来自 Peter Lowe 的 `||metrics.icloud.com^`，是 Apple 设备诊断端点；
- `crashlytics.com`，来自 Peter Lowe 的 `||crashlytics.com^`。

这些不是解析 bug，是上游有意收录的：

- AdRules DNS 会把 DoH/HTTPDNS 端点一起拦掉，避免应用绕过 DNS 过滤；
- Peter Lowe 把 Crashlytics、Apple 设备诊断等归到跟踪/隐私类；
- `metrics.icloud.com` 是 Apple 的 iCloud 设备诊断端点，不承载 iCloud 同步数据；它被拦截通常只会影响诊断上报。

**当前策略：**

- 不做本地例外，遵循上游；
- `PCDN` 和 `Ads` 已拆成独立分组，默认都是 `REJECT`；排查问题时可以把对应分组临时切到 `DIRECT` 或 `PROXY`；
- 如果实际使用中确认受到影响，再开 issue 分析，必要时调整源或向上游反馈；
- 因为没有手工白名单，不能单独放行 `kuiniuca.com` 这类域名（只能整体切换 `PCDN` 分组）。

> 注意：规则命中不等于功能一定受影响。比如 `doh.dns.apple.com` 被 REJECT 时，实测 iCloud Private Relay 仍可能正常，因为系统级流量可能不走这些规则，或者有回退路径。具体以真机测试为准。

### 1.4 lite / full 两种广告模式

- 默认 `lite`：ACL4SSR BanAD、BanProgramAD、AdRules DNS、EasyList China、乘风、Peter Lowe + PCDN；
- `--ad-mode full`：额外加入 anti-AD、EasyList。

**局限：**

- `lite` 覆盖不到 anti-AD 和完整 EasyList 的一些广告；
- `full` 规则数会明显增加，之前测算是约 12 万广告域名，文件可能到数 MB；
- `full` 尚未在真机上做过加载性能和误杀测试；
- 两种模式都没有逐域名的误杀统计。

### 1.5 PCDN

PCDN 源：

- [anti-AD pcdn](https://github.com/privacy-protection-tools/anti-AD/blob/master/discretion/pcdn.txt)
- [blackmatrix7 WangXinKeJi](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Shadowrocket/WangXinKeJi)
- [uselibrary/PCDN](https://github.com/uselibrary/PCDN)

**局限：**

- `uselibrary/PCDN` 里有 3 条 `DOMAIN-REGEX`，Shadowrocket 不支持 `DOMAIN-REGEX`，已跳过；
- 没有基于 UDP 端口/流量特征的 PCDN 检测（例如 UDP 3478、异常高位端口）；
- PCDN 厂商和域名会变，未收录的新域名需要等上游更新；
- `WangXinKeJi` 最后更新是 2025-06，目前还没到 730 天，但后面可能会被标记 `STALE`；
- PCDN 拦截可能影响依赖 PCDN 加速的服务，本地没有白名单；需要测试时只能把整个 `PCDN` 分组切到 `DIRECT`；
- 构建时会按 `priority` 从高到低删除被高优先级规则覆盖的低优先级规则；`PCDN` 高于 `Ads`，两者都高于 LAN，且渲染在 LAN 前面，所以 LAN 父域不会遮蔽 PCDN 子域；
- 同时出现在 PCDN 和 Ads 的域名归 `PCDN` 分组；把 `Ads` 切到 `DIRECT` 时，这些重叠域名仍会被 `PCDN` 拦截。

### 1.6 上游依赖与新鲜度检查

**现状：**

- `state/sources.json` 记录每个源的归一化规则哈希；
- 只有规则内容真的变化才更新 `last_changed`；
- 连续超过 730 天没变化，构建日志打印 `STALE`。

**局限：**

- `STALE` 只是日志输出，不会自动开 issue、发邮件或阻止发布；
- 拉取失败时会重试 3 次，仍失败则用 `factory/cache/` 缓存；
- 状态文件会记录 `from_cache` 和 `fetch_error`；被完全跳过、没有缓存的源不会写入状态；
- CI 第一次运行时没有缓存，如果 GitHub/jsDelivr 拉取失败，可能直接失败或规则缺失；
- 没有为每个类别配置 primary/secondary 自动切换；
- 没有检查源仓库本身是否归档/停更。

---

## 2. 分流规则

### 2.1 `GEOIP,CN,BackCN` 兜底

大陆配置最终是：

```ini
GEOIP,CN,BackCN
FINAL,PROXY
```

**局限：**

- 没有显式域名规则的站点，会走到 `GEOIP`；
- 如果 DNS 污染或 CDN 返回了国内 IP，可能被误判为走 `BackCN`（默认直连）；
- 我们已经为 Google、GitHub 加了显式规则，但**其他未知服务仍可能落进这个兜底**；
- 如果发现某个海外服务在大陆配置下走了直连，需要在 `sources.yaml` 里加对应的显式规则。

### 2.2 Apple

**现状：**

- `apple_suffixes` 统一走 `Apple` 组；
- 大陆 `Apple = PROXY`，香港/新加坡 `Apple = DIRECT`；
- `captive.apple.com` 在 `skip-proxy` 里；
- `e.crashlytics.com` 在 `skip-proxy` 里。

**局限：**

- 所有 Apple 流量（包括 App Store、iCloud、系统更新）都跟随 `Apple` 组，没有按服务拆分；
- 大陆走代理可能更慢，香港/新加坡直连；
- `skip-proxy` 只保证不走代理服务器，是否绕过广告 REJECT 取决于 Shadowrocket 的匹配实现，未实测；所以 `e.crashlytics.com` 虽然在一个 `skip-proxy` 里，`crashlytics.com` 仍可能被广告规则 REJECT；
- 如果某个 Apple 服务需要单独直连或单独代理，当前没有更细的组。

### 2.3 本地静态过滤

这些是本地静态列表，不是上游：

- `ai_blocklist`：过滤 BM7 AI 列表里过宽的第三方域名（Stripe、Auth0、Sentry 等）；
- `streaming_keyword_blocklist`：过滤 GlobalMedia 里的 `anthropic`、`claude` 关键词；
- `siri_blocklist`：过滤 Apple AI 列表里范围过大的域名。

**局限：**

- 如果上游新增了新的宽域名，需要手动补进 blocklist；
- 如果清空 blocklist，会出现无关流量被带进 AI/Streaming/SiriAI 组；
- 这些列表本身也需要维护，只是规模很小。

### 2.4 `DOMAIN-KEYWORD` 与规则顺序

上游列表里有一些宽关键词，例如：

```ini
DOMAIN-KEYWORD,microsoft,BackCN   # China 列表
DOMAIN-KEYWORD,spotify,Streaming
DOMAIN-KEYWORD,youtube,Streaming
DOMAIN-KEYWORD,openai,AI
```

**局限：**

- 关键词匹配范围大，可能把非目标域名也带进对应组；
- 规则按优先级渲染：PCDN > Ads > LAN > AI > SiriAI > Streaming > Apple > Google > GitHub > BackCN；
- 构建会按 `sources.yaml` 的 `priority` 删除被高优先级覆盖的同名规则，例如 `googlevideo.com` 属于 Streaming，Google 里的同名规则会被删除；
- 优先级过滤只处理 `DOMAIN`、`DOMAIN-SUFFIX`、`IP-CIDR`；`DOMAIN-KEYWORD`、`USER-AGENT` 不参与覆盖判断，也不在精确冲突报告里；
- 冲突报告只覆盖完全相同的 `(type,payload)`，按策略名统计；正常情况下优先级处理完后报告为空。

### 2.5 没有 `RULE-SET` / 全内联

**现状：**

- 三份配置都是全内联，不依赖 `RULE-SET`/`DOMAIN-SET` 远程加载。

**局限：**

- 单文件较大（lite 约 550 KB，full 会更大）；
- 每次更新需要重新下载整份配置；
- 好处是大陆网络下不依赖额外远程规则集，坏处是文件体积和加载时间；
- 没有在低端设备上做过加载性能测试。

---

## 3. 测试与验证

**现状：**

- 构建前会做一次轻量检查：
  - 有没有 `PCDN`、`Ads`、`AI`、`SiriAI`、`Streaming`、`Apple`、`BackCN` 组；
  - 规则目标是否存在；
  - 是否只有一个 `FINAL` 且在最后；
  - 是否有未替换的 `{{...}}`；
  - `skip-proxy` 是否包含 `*.ls.apple.com`；
  - 规则数、Ads/PCDN 规则数、AI/SiriAI/Apple 规则数是否低于阈值；
  - 文件大小。

**局限：**

- 没有完整的路由模拟测试；
- 不会验证“某个域名最终命中哪个策略”；
- 不会发现规则顺序错误、`skip-proxy` 覆盖规则、组默认值错误；
- 构建前检查会校验 Streaming/BackCN 规则数和 canary 域名；`build_status.json` 中 `skipped` 的源会直接失败，`from_cache` 的源只警告；
- 不会验证真实广告拦截率、误杀率；
- 只在港版 iPhone + 港区 Apple ID 上做过人工验证；
- 没有在大陆/新加坡设备、Android、Clash、Surge 等其他客户端上测试；
- 没有自动化真机 smoke test。

---

## 4. 自动构建 / 部署

**现状：**

- GitHub Actions 每天 23:00 UTC（北京 07:00）构建；
- 默认 `lite`，手动触发可选 `full`；
- 部署到 `release` 分支，`force_orphan: true`；
- `release` 分支需要手动在 Settings → Pages 启用；
- `state/sources.json` 会尝试提交回 `main`。

**局限：**

- GitHub Actions 的 action 已固定到 commit SHA，并通过 Dependabot 每周检查更新；升级 action 时需要人工确认；
- 第一次运行时没有 `factory/cache` 缓存；如果 raw.githubusercontent.com 或 jsDelivr 拉取失败，可能构建失败；
- `state` 提交使用 `git push origin HEAD:main`，并且 `continue-on-error: true`；如果 `main` 有分支保护，状态可能提交失败，下一次运行的新鲜度判断会不准确；
- `STALE` 只出现在日志里，没有自动通知；
- `release` 分支每次构建都会重建，不能手动修改；
- 构建失败会自动创建 GitHub issue，但每次失败都会新建一条，没有去重；
- 没有构建失败自动重试/自动回滚到上一次成功配置；
- GitHub Pages 首次启用需要手动操作，workflow 不能替你打开。

---

## 5. 未做事项清单

| 未做事项 | 当前做法 | 局限 | 什么时候需要补 |
|---|---|---|---|
| 路径级广告拦截 | 跳过带路径/`$`/`*`/`?` 的规则 | 部分广告漏拦 | 确实需要时，加 `URL-REGEX` + MITM |
| 广告白名单 / manual | 无 | 上游误杀会直接生效 | 遇到关键误杀且上游不修时 |
| 路由模拟测试 | 只有构建前检查 | 规则顺序/策略错误发现不了 | 配置复杂到人工验证不够时 |
| 源失败自动切换 | 重试 3 次 + 缓存 | 首次运行或缓存缺失会失败 | 有多个可靠镜像/备用源时 |
| 新鲜度通知 | 日志打印 `STALE` | 不主动提醒 | 想自动开 issue/发消息时 |
| PCDN 流量识别 | 域名列表 | 新 PCDN 域名、非域名流量漏掉 | 需要更强 PCDN 治理时 |
| `RULE-SET` 远程规则 | 全内联 | 配置文件大 | 设备加载慢或规则继续膨胀时 |
| 多客户端支持 | 只做 Shadowrocket | Clash/Surge 等不能直接用 | 需要跨客户端时 |

---

## 6. 当前最值得优先补的三件事

1. **路由模拟测试**：至少覆盖 AI、SiriAI、Apple、Google、GitHub、广告 REJECT、`FINAL` 的预期策略，防止规则顺序/`skip-proxy` 回归。
2. **关键误杀监控**：即使没有本地白名单，也可以定期扫描最终 REJECT 列表里是否出现 `apple.com`、`google.com`、`cloudflare.com`、`github.com` 等关键域，发现时报警。
3. **源失败通知**：`STALE` 和 `FETCH_FAILED` 目前只在日志里，最好能自动开 issue 或发消息。

---

这份文档会随着配置调整继续更新。如果某一项你决定要补，我可以按优先级实现。
