# Shadowrocket 分流配置（大陆 / 香港 / 新加坡）

三份按网络位置划分的 Shadowrocket 配置，规则每天从公开上游自动拉取、去重、生成。

| 配置 | 适用网络 | 代理策略 | 直连策略 |
|---|---|---|---|
| 大陆 | 中国大陆 | 境外网站、AI、Siri AI、Apple、流媒体 | 国内网站/App、局域网、captive portal |
| 香港 | 中国香港 | AI（OpenAI / Claude / Gemini）、Siri AI | Apple 核心服务、Google 非 AI、社交、流媒体（默认香港区）、国内 App |
| 新加坡 | 新加坡 / 境外 | 无（AI、Siri AI、Apple 全部直连） | 全部 |

所有配置共同点：

- 广告规则自动从公开上游拉取并去重；
- 每天北京时间 07:00 自动构建；
- 仅在 **港版 iPhone + 港区 Apple ID** 上测试过。

> 完整的取舍、未覆盖项和风险见 [LIMITATIONS.md](LIMITATIONS.md)。

---

## 配置地址

> 推荐使用 GitHub Pages；如果访问不了，使用 raw 备用地址。

| 配置 | 推荐地址 | 备用地址 |
|---|---|---|
| 大陆 | `https://feifanmoke.github.io/ShadowrocketRules/sr_cn.conf` | `https://raw.githubusercontent.com/FeiFanMoKe/ShadowrocketRules/release/sr_cn.conf` |
| 香港 | `https://feifanmoke.github.io/ShadowrocketRules/sr_hk.conf` | `https://raw.githubusercontent.com/FeiFanMoKe/ShadowrocketRules/release/sr_hk.conf` |
| 新加坡 | `https://feifanmoke.github.io/ShadowrocketRules/sr_sg.conf` | `https://raw.githubusercontent.com/FeiFanMoKe/ShadowrocketRules/release/sr_sg.conf` |


---

## 更新配置

### 第一次添加

1. 打开 Shadowrocket，进入「配置」页面。
2. 点击右上角 `+`，把上面的配置地址粘贴到 URL 处，点击「下载」。
3. 点击下载好的配置，选择「使用配置」。
4. 断开并重新连接一次 Shadowrocket，确保规则生效。

### 手动更新

1. 进入「配置」页面。
2. 点击当前配置右侧的 `ⓘ`（或长按配置），选择「更新」/ 重新下载。
3. 如果没有「更新」按钮，删除旧配置后重新添加 URL。
4. 更新完成后，断开并重新连接一次 Shadowrocket。


---

## 代理分组

配置里包含七个代理分组：

| 分组 | 作用 | 可选值 |
|---|---|---|
| `PCDN` | P2P CDN 域名 | `REJECT` / `DIRECT` / `PROXY` |
| `Ads` | 广告、跟踪和 HTTPDNS 域名 | `REJECT` / `DIRECT` / `PROXY` |
| `AI` | OpenAI / Claude / Gemini | `PROXY` / `DIRECT` |
| `SiriAI` | Siri / Apple Intelligence 相关域名 | `PROXY` / `DIRECT` |
| `Streaming` | Netflix / Disney+ / HBO 等 | `DIRECT` / `PROXY` |
| `Apple` | Apple 核心服务 | `DIRECT` / `PROXY` |
| `BackCN` | 国内网站/App/媒体的回源策略 | `DIRECT` / `PROXY` |

`PCDN` 和 `Ads` 默认都是 `REJECT`，行为和以前一致。需要排查某个广告/PCDN 域名是否影响正常服务时，可以临时把对应分组改成 `DIRECT` 或 `PROXY`，测试完再切回 `REJECT`。

`PROXY` 表示使用 Shadowrocket 首页当前选中的节点，配置里不写死节点名。换节点时只需要在首页切换，不需要改配置。

修改分组：

1. 进入「配置」页面。
2. 点击当前配置右侧的 `ⓘ`。
3. 进入「代理分组」。
4. 选择分组，然后选择 `PROXY` 或 `DIRECT`。

### 各配置默认值

| 分组 | 大陆 | 香港 | 新加坡 |
|---|---|---|---|
| `PCDN` | `REJECT` | `REJECT` | `REJECT` |
| `Ads` | `REJECT` | `REJECT` | `REJECT` |
| `AI` | `PROXY` | `PROXY` | `DIRECT` |
| `SiriAI` | `PROXY` | `PROXY` | `DIRECT` |
| `Streaming` | `PROXY` | `DIRECT` | `DIRECT` |
| `Apple` | `PROXY` | `DIRECT` | `DIRECT` |
| `BackCN` | `DIRECT` | `DIRECT` | `DIRECT` |

### 按场景设置

一般不需要改分组，默认值已经对应三份配置：

| 使用场景 | 建议 |
|---|---|
| 大陆 | `AI`、`SiriAI`、`Apple`、`Streaming` 用 `PROXY`；`BackCN` 用 `DIRECT` |
| 香港 | `AI`、`SiriAI` 用 `PROXY`；`Apple`、`Streaming` 用 `DIRECT`；`BackCN` 用 `DIRECT` |
| 新加坡 | 全部用 `DIRECT` |

如果只想调整某个服务，按下面找分组：

| 想调整的服务 | 对应分组 |
|---|---|
| P2P CDN / PCDN | `PCDN` |
| 广告、跟踪、HTTPDNS | `Ads` |
| OpenAI / Claude / Gemini | `AI` |
| Siri / Apple Intelligence | `SiriAI` |
| Netflix / YouTube / Disney+ / Spotify | `Streaming` |
| App Store / iCloud / 系统服务 | `Apple` |
| 国内 App / 网站 | `BackCN` |

`PROXY` 不是节点名，而是“使用 Shadowrocket 首页当前选中的节点”；`DIRECT` 是直连。节点在首页切换，不需要改配置。

例子：

- 在香港希望 Netflix 走代理：把 `Streaming` 切到 `PROXY`；
- 希望 Siri 直连：把 `SiriAI` 切到 `DIRECT`；
- 需要回国内节点：把 `BackCN` 切到 `PROXY`，并在首页选中大陆节点。默认 `DIRECT`，不切换就保持直连；
- 排查广告或 PCDN 是否误伤某个服务：把 `Ads` 或 `PCDN` 单独切到 `DIRECT`，测试完切回 `REJECT`。

### 冲突优先级

同一个域名/IP 同时出现在多个类别时，构建会按下面的顺序保留高优先级规则、删除低优先级规则：

```text
PCDN > Ads > LAN > AI > SiriAI > Streaming > Apple > Google > GitHub > BackCN > FINAL
```

- PCDN/Ads 最高，`peiluyou.com` 这类域名会保留拦截；
- PCDN 排在 Ads 前面：同时出现在两个列表里的域名归 `PCDN` 分组，方便单独切换测试；
- LAN 只影响本地网络；被 PCDN/Ads 覆盖的 LAN 规则会删除；
- AI/SiriAI/Streaming/Apple/Google/GitHub 是服务类别，高于 BackCN/China；
- 顺序在 `sources.yaml` 的 `priority` 中配置，以后出现冲突直接调整这个列表即可。

> 当前优先级过滤只处理 `DOMAIN`、`DOMAIN-SUFFIX`、`IP-CIDR`；`DOMAIN-KEYWORD` 和 `USER-AGENT` 不参与覆盖判断。

---

## 分流逻辑

### 大陆

- 境外网站：代理；
- AI（OpenAI / Claude / Gemini）：代理；
- Siri AI：代理；
- Apple：全部代理；
- 流媒体：代理；
- 国内网站/App：走 `BackCN`（默认 `DIRECT`）；
- captive portal：始终直连；
- 兜底：`FINAL,PROXY`，并用 `GEOIP,CN,BackCN` 让国内 IP 走 `BackCN`（默认直连）。

### 香港

- AI（OpenAI / Claude / Gemini）：代理；
- Siri AI：代理；
- Apple 核心服务：直连；
- Google 搜索、Gmail、YouTube 等非 AI 服务：直连；
- 流媒体：默认香港区直连，需要美区/日区时把 `Streaming` 切到 `PROXY`；
- 国内 App/媒体：走 `BackCN`（默认 `DIRECT`）；
- captive portal：始终直连；
- 兜底：`FINAL,DIRECT`。

### 新加坡 / 境外

- AI、Siri AI、Apple、流媒体：全部直连；
- 其他网站：直连；
- 国内 App/媒体：走 `BackCN`（默认 `DIRECT`）；
- captive portal：始终直连；
- 兜底：`FINAL,DIRECT`。

---

## 测试范围

本项目只在以下环境测试过：

- 港版 iPhone；
- 港区 Apple ID；
- Shadowrocket 最新正式版。

其他设备型号、设备地区、Apple ID 地区可能需要调整 `AI`、`SiriAI`、`Streaming` 或 `Apple` 分组。遇到问题欢迎开 issue，请在 issue 中附上：

- 设备型号、iOS 版本、设备地区；
- Apple ID 地区；
- 当前网络（大陆 / 香港 / 新加坡 / 其他）；
- 使用的配置（大陆 / 香港 / 新加坡）；
- 出问题的域名或 App；
- 期望结果和实际结果。

不保证所有环境都能直接使用。

---

## 广告问题请到上游维护

本项目的广告规则来自以下公开上游。仓库只负责拉取、归一化和去重，不维护手工广告规则。

| 上游 | 覆盖内容 |
|---|---|
| [EasyList China](https://github.com/easylist/easylistchina) | 中文网页广告 |
| [EasyList](https://github.com/easylist/easylist) | 全球网页广告 |
| [乘风广告过滤规则](https://github.com/xinggsf/Adblock-Plus-Rule) | 中文视频/网页广告 |
| [Peter Lowe 广告和跟踪域名](https://pgl.yoyo.org/adservers/) | 全球广告/跟踪域名 |
| [anti-AD](https://github.com/privacy-protection-tools/anti-AD) | 国内 App 广告和跟踪域名 |
| [ACL4SSR BanAD](https://github.com/ACL4SSR/ACL4SSR/blob/master/Clash/BanAD.list) | 广告联盟 |
| [ACL4SSR BanProgramAD](https://github.com/ACL4SSR/ACL4SSR/blob/master/Clash/BanProgramAD.list) | 常用 App 去广告 |
| [AdRules](https://github.com/Cats-Team/AdRules) | 合并广告列表 |
| [blackmatrix7 BlockHTTPDNS](https://github.com/blackmatrix7/ios_rule_script/tree/master/rewrite/Shadowrocket/BlockHTTPDNS) | 拦截 HTTPDNS，防止 App 绕过 DNS 广告过滤 |

> HTTPDNS 说明：部分 App 不通过系统 DNS，而是用 HTTP 接口（如 `httpdns.*`、`dns.*`）直接解析 IP，会绕过本项目的域名级广告拦截。合入 `BlockHTTPDNS` 后，这些 HTTPDNS 端点会归入 `Ads` 分组（默认 `REJECT`），迫使 App 回退到系统 DNS，让广告拦截生效。这也是纯域名/IP 规则，**不需要 MITM**。

如果出现以下问题：

- 广告没有拦住；
- 正常网站或 App 被误杀；

请直接到对应上游反馈。上游修复后，第二天的自动构建会自动带上。

只有「规则生成、去重、配置渲染」本身有问题时，才需要在本仓库开 issue。本项目不接受手工广告/PCDN 规则 PR。


### PCDN

PCDN（P2P CDN）不是广告，但会把设备当作内容分发节点，占用上行带宽。以下上游会进入独立的 `PCDN` 分组，默认 `REJECT`：

| 上游 | 覆盖内容 |
|---|---|
| [anti-AD pcdn](https://github.com/privacy-protection-tools/anti-AD/blob/master/discretion/pcdn.txt) | 通用 PCDN 域名 |
| [blackmatrix7 WangXinKeJi](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Shadowrocket/WangXinKeJi) | 网心科技/迅雷 PCDN |
| [uselibrary/PCDN](https://github.com/uselibrary/PCDN) | 通用 CDN、视频平台 P2P |

例如 `kuiniuca.com`（网心科技/星域 CDN）会命中 `DOMAIN-SUFFIX,kuiniuca.com,PCDN`。如果同一个域名同时出现在 PCDN 和 Ads 中，构建时归 `PCDN` 分组；如果出现在 PCDN 和其他分组（Lan、AI、Streaming、Apple、Google、China 等）里，构建时会删除其他分组里的规则（例如 `peiluyou.com`）。如果你依赖的某个服务因此受影响，可以先把 `PCDN` 分组切到 `DIRECT` 做测试，或从 `sources.yaml` 的 `pcdn` 列表里移除对应源。

---

## 自动构建与新鲜度检查

- GitHub Actions 每天北京时间 07:00（UTC 23:00）自动构建。
- 构建流程：拉取上游 → 归一化 → 去重 → 校验 → 生成三份配置 → 发布。
- 关键类别、canary 域名缺失，或有源被跳过时，preflight 会失败，不会发布；workflow 失败会自动创建 issue 通知。
- 每个上游都会记录**规则内容的哈希**：
  - 只看规则内容有没有变化，不看列表里的日期或版本号；
  - 如果某个上游连续 **2 年（730 天）** 规则内容没有变化，构建报告会标记 `STALE`，提醒更换源；
  - 上游拉取失败时会重试，仍失败则使用上次缓存，并在构建日志中输出 `WARN`。
- 上游内容哈希保存在 `state/sources.json`，由工作流自动提交回 `main` 分支。
- Siri AI 域名从公开的 Apple AI 列表拉取，并与 Apple 官方文档核对。

---

## 上游

本项目只做规则聚合和格式转换，规则版权归各上游所有。主要上游：

- [gfwlist](https://github.com/gfwlist/gfwlist)
- [Loyalsoldier/cn-blocked-domain](https://github.com/Loyalsoldier/cn-blocked-domain)
- [anti-AD](https://github.com/privacy-protection-tools/anti-AD)
- [ACL4SSR](https://github.com/ACL4SSR/ACL4SSR)
- [AdRules](https://github.com/Cats-Team/AdRules)
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)
- [uselibrary/PCDN](https://github.com/uselibrary/PCDN)
- [RocM301/Apple-Rule](https://github.com/RocM301/Apple-Rule)
- [EasyList](https://github.com/easylist/easylist) / [EasyList China](https://github.com/easylist/easylistchina)
- [乘风广告过滤规则](https://github.com/xinggsf/Adblock-Plus-Rule)
- [Peter Lowe 广告和跟踪域名](https://pgl.yoyo.org/adservers/)

Siri AI 相关域名参考 Apple 官方文档 [Use Apple products on enterprise networks](https://support.apple.com/en-us/101555)。

---

## 特别声明

1. 本项目仅用于学习、研究和个人合法的网络管理，不构成任何形式的“翻墙”工具、服务或教程。
2. 本项目所有规则均来自互联网公开上游，本项目只做聚合、去重和格式转换，不对规则内容的合法性、准确性、完整性和有效性作任何保证。
3. 使用者必须遵守中华人民共和国法律法规。以下为相关条文节选，完整条文以全国人大、国务院等官方发布的正式文本为准：
   - **《中华人民共和国网络安全法》（2025年修正，2026年1月1日起施行）第十三条第二款**：任何个人和组织使用网络应当遵守宪法法律，遵守公共秩序，尊重社会公德，不得危害网络安全，不得利用网络从事危害国家安全、荣誉和利益，煽动颠覆国家政权、推翻社会主义制度，煽动分裂国家、破坏国家统一，宣扬恐怖主义、极端主义，宣扬民族仇恨、民族歧视，传播暴力、淫秽色情信息，编造、传播虚假信息扰乱经济秩序和社会秩序，以及侵害他人名誉、隐私、知识产权和其他合法权益等活动。
   - **《中华人民共和国网络安全法》第二十九条**：任何个人和组织不得从事非法侵入他人网络、干扰他人网络正常功能、窃取网络数据等危害网络安全的活动；不得提供专门用于从事侵入网络、干扰网络正常功能及防护措施、窃取网络数据等危害网络安全活动的程序、工具；明知他人从事危害网络安全的活动的，不得为其提供技术支持、广告推广、支付结算等帮助。
   - **《中华人民共和国计算机信息网络国际联网管理暂行规定》（2024年修订）第六条**：计算机信息网络直接进行国际联网，必须使用国家公用电信网提供的国际出入口信道。任何单位和个人不得自行建立或者使用其他信道进行国际联网。
   - **《中华人民共和国计算机信息网络国际联网管理暂行规定》第十四条**：违反本规定第六条、第八条和第十条的规定的，由公安机关责令停止联网，给予警告，可以并处15000元以下的罚款；有违法所得的，没收违法所得。
   - **《中华人民共和国刑法》第二百八十五条（节选）**：违反国家规定，侵入国家事务、国防建设、尖端科学技术领域的计算机信息系统的，处三年以下有期徒刑或者拘役。……提供专门用于侵入、非法控制计算机信息系统的程序、工具，或者明知他人实施侵入、非法控制计算机信息系统的违法犯罪行为而为其提供程序、工具，情节严重的，依照前款的规定处罚。
   - **《中华人民共和国刑法》第二百八十六条（节选）**：违反国家规定，对计算机信息系统功能进行删除、修改、增加、干扰，造成计算机信息系统不能正常运行，后果严重的，处五年以下有期徒刑或者拘役；后果特别严重的，处五年以上有期徒刑。……
4. 使用者应自行判断并承担使用本项目的一切后果；本项目作者及贡献者不承担任何直接或间接责任。
5. 本项目不鼓励、不支持任何违反法律法规的行为。如所在地区法律禁止使用相关功能，请立即停止使用并删除本项目内容。
6. 未经许可，禁止任何公众号、自媒体转载、发布本项目内容。
7. 本项目与任何第三方硬件、软件、服务无关；使用第三方软硬件造成的后果由使用者自行承担。
8. 本项目保留随时补充或修改本声明的权利；直接或间接使用本项目内容，视为接受本声明。

> 以上内容不构成法律意见。
