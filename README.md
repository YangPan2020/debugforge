# DebugForge

将 TRACE32 接入 AI Agent，实现自动化调试、Debug 定位的 MCP Server 工具。支持本地和远程环境。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│  本地 Linux (Agent)                                         │
│  - 源码/ELF/CMM                                             │
│  - AI Agent (PYRCL 客户端)                                  │
│  - DebugForge MCP Server                                    │
└────────────────┬────────────────────────┬───────────────────┘
                 │ SCP (端口 22)          │ PYRCL (端口 20000)
                 │ 传输 ELF/CMM           │ 远程控制 TRACE32
                 ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│  远程 Windows (your-windows-host)                           │
│  - OpenSSH Server                                           │
│  - TRACE32                                                  │
│  - 硬件板子 (TC38x/TC39x)                                   │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 安装

```bash
pip install -e .
```

### 2. 配置

复制配置模板并填入实际信息：

```bash
cp debugforge.toml.example debugforge.toml
```

编辑 `debugforge.toml`：

```toml
[mode]
mode = "remote"  # 或 "local"

[connection]
node = "192.168.1.100"  # TRACE32 所在主机 IP
port = 20000

[remote]
host = "192.168.1.100"
winrm_user = "user@domain.local"
winrm_password = "your_password"
ssh_user = "username"
staging_dir = "D:\\T32\\debugforge"

[project]
elf = "/path/to/your/firmware.elf"

[scripts]
flash = "/path/to/your/flash_script.cmm"
```

> **注意**: `debugforge.toml` 包含敏感凭据信息，已被 `.gitignore` 排除，不会被提交到仓库。

### 3. 配置远程 Windows

参考 [WINDOWS_SSH_SETUP.md](WINDOWS_SSH_SETUP.md) 安装 OpenSSH Server。

### 4. 运行 MCP Server

```bash
debugforge
```

或通过 examples 中的脚本直接测试：

```bash
python examples/remote_debug.py
python examples/remote_debug.py --pyrcl
```

## 工作流

### Remote 模式

1. **文件传输**: SCP/WinRM 传输 ELF + CMM 到 Windows staging 目录
2. **CMM Wrapper**: 生成 wrapper CMM，将 ELF 路径替换为 Windows 路径
3. **PYRCL 连接**: 通过 TCP 连接远程 TRACE32
4. **执行 CMM**: 远程 TRACE32 执行 CMM 烧录 ELF
5. **源码映射**: 设置 `Symbol.SourcePATH.Translate` 让 TRACE32 找到源码

### Local 模式

1. **PYRCL 连接**: 连接本地 TRACE32
2. **执行 CMM**: 直接执行本地 CMM 脚本

## 配置详解

参考 `debugforge.toml.example` 获取完整配置项说明。

### 模式选择

```toml
[mode]
mode = "remote"  # "local" 或 "remote"
```

### 远程连接

```toml
[remote]
host = "192.168.1.100"        # 远程 Windows IP
winrm_port = 5985             # WinRM 端口
winrm_user = "user@domain"    # WinRM 用户名
winrm_password = "password"   # WinRM 密码
ssh_user = "username"         # SSH 用户名
ssh_password = ""             # SSH 密码 (留空使用 key)
ssh_port = 22                 # SSH 端口
staging_dir = "D:\\T32\\debugforge"  # 文件传输目标目录
```

### 源码路径映射

```toml
[[remote.source_translates]]
from = "/home/user/project"
to   = "D:\\project"
```

让 TRACE32 在 debug 时能找到源码文件。需要先将源码复制到 Windows 对应目录。

## 依赖

```bash
pip install paramiko scp pywinrm
```

## 文件说明

```
debugforge/
├── src/debugforge/          # MCP Server 核心代码
├── examples/                # 示例脚本
│   ├── remote_debug.py      # 远程调试示例 (WinRM + PYRCL)
│   ├── remote_debug_tc38x.py  # TC38x 远程调试示例
│   ├── test_all_tools.py    # 全工具测试
│   └── debug_tc397_live.py  # TC397 完整调试工作流
├── debugforge.toml.example  # 配置模板
├── WINDOWS_SSH_SETUP.md     # Windows OpenSSH 配置指南
└── README.md                # 本文档
```

## 故障排查

### SSH 连接失败

```
[FATAL] 连接失败: SSH connection failed
```

- 检查 Windows OpenSSH Server 是否安装并运行
- 检查防火墙是否允许端口 22
- 测试: `ssh <your-user>@<your-host>`

### PYRCL 连接失败

```
[FATAL] 连接失败: Connection refused
```

- 检查远程 TRACE32 是否启动
- 检查 TRACE32 配置: `RCL=NETTCP PORT=20000`
- 检查防火墙是否允许端口 20000
- 测试: `telnet <your-host> 20000`

### CMM 执行失败

```
CMM 异常: ...
```

- 检查 ELF 文件是否成功传输到 staging_dir
- 检查 CMM 中的路径是否正确
- 查看远程 TRACE32 窗口错误信息

## License

MIT
