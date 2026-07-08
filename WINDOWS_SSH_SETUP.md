# Windows OpenSSH 配置指南

## 1. 安装 OpenSSH Server

### Windows 10/11 (1809+)

1. 打开 **设置** → **应用** → **可选功能**
2. 点击 **添加功能**
3. 搜索 **OpenSSH 服务器**，安装

### 或使用 PowerShell (管理员)

```powershell
# 检查是否已安装
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'

# 安装
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 启动服务
Start-Service sshd

# 设置为自动启动
Set-Service -Name sshd -StartupType Automatic

# 配置防火墙
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

## 2. 配置 SSH

编辑 `C:\ProgramData\ssh\sshd_config`:

```powershell
notepad C:\ProgramData\ssh\sshd_config
```

确保以下配置存在且未注释:

```
Port 22
PubkeyAuthentication yes
PasswordAuthentication yes
```

重启服务:

```powershell
Restart-Service sshd
```

## 3. 测试连接

从 Linux 测试:

```bash
ssh <your-user>@<your-windows-host>
```

如果成功，说明 OpenSSH Server 已就绪。

## 4. 配置 SSH Key (推荐)

### 在 Linux 生成密钥

```bash
ssh-keygen -t rsa -b 4096
```

### 复制公钥到 Windows

```bash
ssh-copy-id <your-user>@<your-windows-host>
```

或手动复制:

```bash
cat ~/.ssh/id_rsa.pub | ssh <your-user>@<your-windows-host> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Windows 端权限设置

```powershell
# 修复 authorized_keys 权限
icacls C:\Users\<your-user>\.ssh\authorized_keys /inheritance:r /grant "<your-user>:(R)" /grant "SYSTEM:(R)"
```

## 5. 验证 SCP

```bash
scp test.txt <your-user>@<your-windows-host>:D:\\T32\\debugforge\\
```

如果成功，说明文件传输已就绪。

## 6. 常见问题

### 连接超时

- 检查防火墙是否允许端口 22
- 检查 sshd 服务是否运行: `Get-Service sshd`

### 权限拒绝

- 检查 `authorized_keys` 文件权限
- 检查 `sshd_config` 中 `PubkeyAuthentication yes`

### 中文用户名/密码

- 确保 Windows 用户名是英文 (如 `username`)
- 密码建议使用英文字符
