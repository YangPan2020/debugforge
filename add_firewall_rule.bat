@echo off
REM ============================================================
REM add_firewall_rule.bat
REM 在远程电脑上以管理员身份运行，放行 TRACE32 RCL 端口 20000 (TCP)
REM
REM 用法:
REM   右键点击 -> 以管理员身份运行
REM   或在管理员 PowerShell 中运行:
REM     New-NetFirewallRule -DisplayName "TRACE32 RCL" -Direction Inbound -Protocol TCP -LocalPort 20000 -Action Allow
REM ============================================================

echo.
echo === 添加 TRACE32 RCL TCP 20000 防火墙规则 ===
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本！
    echo        右键点击 -^> 以管理员身份运行
    pause
    exit /b 1
)

echo 1. 添加入站规则 (TCP 20000)...
netsh advfirewall firewall add rule name="TRACE32 RCL TCP 20000 Inbound" dir=in action=allow protocol=TCP localport=20000

echo 2. 添加出站规则 (TCP 20000)...
netsh advfirewall firewall add rule name="TRACE32 RCL TCP 20000 Outbound" dir=out action=allow protocol=TCP localport=20000

echo 3. 同时放行 UDP 20000 (备用)...
netsh advfirewall firewall add rule name="TRACE32 RCL UDP 20000 Inbound" dir=in action=allow protocol=UDP localport=20000

echo.
echo === 当前端口 20000 监听状态 ===
netstat -an | findstr "20000"

echo.
echo === 完成！ ===
echo 如果上面 netstat 显示 LISTENING，且防火墙规则已添加，
echo 远程调试应该可以连接了。
echo.
pause
